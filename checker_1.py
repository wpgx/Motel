import re
from pathlib import Path
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

FINAL = Path("final_60.m3u")
FINAL_M3U8 = Path("final_60.m3u8")
FINAL_XML = Path("final_60.xml")
DC_M3U = Path("DCcatalog.m3u")
DC_XML = Path("DCcatalog.xml")

BASE = "https://motel.deecee.ca"
WELCOME_URL = "https://raw.githubusercontent.com/wpgx/Motel/main/welcome/media.m3u8"
WELCOME_LOGO = f"{BASE}/logo.png"
WELCOME_EXT = f'#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="{WELCOME_LOGO}", Cairns Motel - Welcome'
EPG_URLS = f"{BASE}/final_60.xml"

CAT_MAP = {
    "CBC News Nova Scotia":"News","CBC News PEI":"News","CBC News":"News","CTV News":"News","Global News National":"News",
    "The Weather Network":"News","CBS News 24/7":"News","NBC News NOW":"News","CNN Headlines":"News",
    "NFL Channel":"Sports","NHL":"Sports","MLB Channel":"Sports","NASCAR Channel":"Sports","F1 Channel":"Sports",
    "FIFA+":"Sports","TSN The Ocho":"Sports","World Poker Tour":"Sports","Billiard TV":"Sports",
    "BUZZR":"Game Shows","Game Show Central":"Game Shows",
    "Tastemade":"Lifestyle","MagellanTV Wildest":"Lifestyle","Bob Ross":"Lifestyle","History & Warfare":"Documentary","Modern Marvels":"Documentary",
    "CINEVAULT: Classics":"Movies","At the Movies":"Movies","FilmRise Action":"Movies","FilmRise Western":"Movies","FilmRise Horror":"Movies","Hallmark Movies & More":"Movies",
    "FilmRise Classic TV":"Classic TV","Baywatch":"Classic TV","Nash Bridges":"Classic TV","The FBI":"Classic TV","The Rifleman":"Classic TV","Wanted: Dead or Alive":"Classic TV",
    "Grit Xtra":"Classic TV","Death Valley Days":"Classic TV","Dick Van Dyke":"Classic TV","Johnny Carson TV":"Classic TV","The Carol Burnett Show":"Classic TV","The Ed Sullivan Show":"Classic TV","That Girl":"Classic TV","Western Bound":"Classic TV","Lone Star":"Classic TV","Classic Doctor Who":"Classic TV","American Gladiators by MGM":"Classic TV","The Outer Limits":"Sci-Fi","BBC Sci-Fi":"Sci-Fi","FilmRise Sci-Fi":"Sci-Fi",
    "Stingray Easy Listening":"Music","Stingray Classic Rock":"Music","Stingray Soft Hits":"Music","Stingray Country Greats":"Music",
    "Toon Goggles":"Kids","Moonbug":"Kids","FailArmy":"Entertainment","Stingray Naturescape":"Relax",
}
SEQ = list(CAT_MAP.keys())

def load_xml_id_map():
    """Build display-name -> xml channel id map from DCcatalog.xml"""
    m = {}
    if not DC_XML.exists():
        return m
    try:
        root = ET.parse(DC_XML).getroot()
        for ch in root.findall('channel'):
            cid = ch.get('id')
            for dn in ch.findall('display-name'):
                if dn.text:
                    m[dn.text.strip().lower()] = cid
                    # also store without spaces/punct
                    m[re.sub(r'\W+','', dn.text.lower())] = cid
    except Exception as e:
        print(f"xml map fail {e}")
    return m

def get_tvg_id_from_ext(line):
    mm = re.search(r'tvg-id="([^"]*)"', line)
    return mm.group(1) if mm else ""

def main():
    xml_name_to_id = load_xml_id_map()
    print(f"Loaded {len(xml_name_to_id)} names from DCcatalog.xml")

    lines = DC_M3U.read_text(errors='ignore').splitlines()
    # build title -> (ext, url) list from m3u
    m3u_by_title = {}
    for i,l in enumerate(lines):
        if l.startswith('#EXTINF'):
            title = l.rsplit(',',1)[-1].strip()
            url = lines[i+1].strip() if i+1 < len(lines) else ""
            m3u_by_title.setdefault(title.lower(), []).append((l, url))

    out_m3u = [f'#EXTM3U url-tvg="{EPG_URLS}"', WELCOME_EXT, WELCOME_URL]
    wanted_xml_ids = set(["welcome"])
    selected = [] # (xml_id, title, cat, logo)

    for title in SEQ:
        key = title.lower()
        if key not in m3u_by_title:
            continue
        ext, url = m3u_by_title[key][0]
        # Find the REAL xml id for this title
        xml_id = xml_name_to_id.get(key) or xml_name_to_id.get(re.sub(r'\W+','', key))
        if not xml_id:
            # fallback to original tvg-id from m3u
            xml_id = get_tvg_id_from_ext(ext) or re.sub(r'\W+','', key)

        # force M3U tvg-id to match XML id - THIS FIXES MIXED UP NUMBERS
        ext = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{xml_id}"', ext)
        if 'tvg-id=' not in ext:
            ext = ext.replace('#EXTINF:-1', f'#EXTINF:-1 tvg-id="{xml_id}"')
        cat = CAT_MAP.get(title, "Entertainment")
        ext = re.sub(r'group-title="[^"]*"', f'group-title="{cat}"', ext)
        ext = re.sub(r'#EXTINF:[^\s]*', '#EXTINF:-1', ext)

        out_m3u.append(ext)
        out_m3u.append(url)
        wanted_xml_ids.add(xml_id)
        m_logo = re.search(r'tvg-logo="([^"]*)"', ext)
        logo = m_logo.group(1) if m_logo else ""
        selected.append((xml_id, title, cat, logo))

    FINAL.write_text('\n'.join(out_m3u)+'\n', encoding='utf-8')
    FINAL_M3U8.write_text('\n'.join(out_m3u)+'\n', encoding='utf-8')

    # Build XML - filter to wanted ids and clean titles
    now = datetime.utcnow()
    fmt = "%Y%m%d%H%M%S +0000"
    start = now.strftime(fmt)
    stop = (now + timedelta(hours=24)).strftime(fmt)

    xml_ch = [f' <channel id="welcome"><display-name>Cairns Motel - Welcome</display-name><icon src="{WELCOME_LOGO}" /></channel>']
    xml_pr = [f' <programme start="{start}" stop="{stop}" channel="welcome"><title lang="en">Welcome to Cairns Motel</title></programme>']

    if DC_XML.exists():
        root = ET.parse(DC_XML).getroot()
        prog_count = {cid:0 for cid in wanted_xml_ids}
        for ch in root.findall('channel'):
            if ch.get('id') in wanted_xml_ids:
                xml_ch.append(' ' + ET.tostring(ch, encoding='utf-8').decode().strip())
        for pr in root.findall('programme'):
            cid = pr.get('channel')
            if cid not in wanted_xml_ids:
                continue
            # CLEAN GARBAGE: "No EPG for Samsung..." -> "No Information"
            t_el = pr.find('title')
            if t_el is not None and t_el.text and 'no epg' in t_el.text.lower():
                t_el.text = "No Information"
                d_el = pr.find('desc')
                if d_el is not None:
                    d_el.text = "No Information"
            prog_count[cid] = prog_count.get(cid,0)+1
            xml_pr.append(' ' + ET.tostring(pr, encoding='utf-8').decode().strip())
        # add No Information for channels with 0 programmes
        for xml_id, title, cat, logo in selected:
            if prog_count.get(xml_id,0)==0:
                xml_pr.append(f' <programme start="{start}" stop="{stop}" channel="{xml_id}"><title lang="en">No Information</title><desc lang="en">No Information</desc></programme>')
            if not any(f'id="{xml_id}"' in s for s in xml_ch):
                safe = title.replace("&","and")
                xml_ch.append(f' <channel id="{xml_id}"><display-name>{safe}</display-name><icon src="{logo}" /></channel>')
    else:
        for xml_id, title, cat, logo in selected:
            safe = title.replace("&","and")
            if not any(f'id="{xml_id}"' in s for s in xml_ch):
                xml_ch.append(f' <channel id="{xml_id}"><display-name>{safe}</display-name><icon src="{logo}" /></channel>')
            xml_pr.append(f' <programme start="{start}" stop="{stop}" channel="{xml_id}"><title lang="en">No Information</title><desc lang="en">No Information</desc></programme>')

    FINAL_XML.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n'+'\n'.join(xml_ch)+'\n'+'\n'.join(xml_pr)+'\n</tv>\n', encoding='utf-8')
    print(f"Done {len(out_m3u)//2} channels, welcome={WELCOME_URL}")

if __name__ == "__main__":
    main()
