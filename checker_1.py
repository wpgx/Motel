import re
from pathlib import Path
from datetime import datetime, timedelta

FINAL = Path("final_60.m3u")
FINAL_M3U8 = Path("final_60.m3u8")
FINAL_XML = Path("final_60.xml")
DC_60_M3U = Path("DCcatalog_60.m3u")

# GITHUB PAGES ADDRESS - not motel.deecee.ca
GITHUB_BASE = "https://deecee-ca.github.io/Motel"
WELCOME_URL = f"{GITHUB_BASE}/welcome/media/media.m3u8"
WELCOME_LOGO = f"{GITHUB_BASE}/logo.png"
WELCOME_EXT = f'#EXTINF:-1 tvg-id="welcome" tvg-name="Cairns Motel Welcome" group-title="Motel Info" tvg-logo="{WELCOME_LOGO}", Cairns Motel - Welcome'
EPG_URLS = f"{GITHUB_BASE}/final_60.xml"
BLACKLIST = ["99991399", "magnolia", "adult", "xxx", "porn", "xman", "x-man"]

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
ID_HINTS = {
    "CBC News Nova Scotia":"CA4600007UE","CBC News PEI":"CA4600002Z5","CBC News":"CABC2300009KD","CTV News":"CA1400004AE",
    "The Weather Network":"CABC23000223U","CBS News 24/7":"CA390002621","NBC News NOW":"CAAJ2700011IF","MLB Channel":"CA1400001PI",
    "NASCAR Channel":"CA700002VS","TSN The Ocho":"CA1400003R3","World Poker Tour":"CABD1200013IH","BUZZR":"653200",
    "Game Show Central":"CAAJ2700027GW","Tastemade":"CABD1200002T9","MagellanTV Wildest":"CAAJ3400017AE","Bob Ross":"CABC2300015UM",
    "History & Warfare":"CA600001C3","Modern Marvels":"CA900004R3","FilmRise Action":"CAAJ2700014EE","FilmRise Western":"CAAJ27000159K",
    "FilmRise Horror":"CA35000044I","The Outer Limits":"68b0b1d296759568b7f1f042",
}

def clean_and_recategorize(ext, new_category):
    if ',' not in ext:
        return ext
    head, title = ext.rsplit(',', 1)
    head = re.sub(r'\s*tvg-chno="[^"]*"\s*', ' ', head)
    head = re.sub(r'#EXTINF:[^\s]*', '#EXTINF:-1', head)
    head = re.sub(r'group-title="[^"]*"', f'group-title="{new_category}"', head)
    if 'group-title=' not in head:
        head += f' group-title="{new_category}"'
    head = re.sub(r'\s+', ' ', head).strip()
    return f"{head}, {title.strip()}"

def load_dccatalog():
    for p in [Path("DCcatalog.m3u"), Path("dccatalog.txt")]:
        if p.exists():
            return p.read_text(errors='ignore').splitlines()
    raise FileNotFoundError("DCcatalog.m3u not found")

def get_best(lines, title):
    cands = []
    for i, l in enumerate(lines):
        if l.startswith('#EXTINF') and l.rsplit(',',1)[-1].strip().lower() == title.lower():
            cands.append((l.strip(), lines[i+1].strip() if i+1 < len(lines) else ''))
    cands.sort(key=lambda x: 10 if "pluto" in x[0].lower() else -5 if "samsung" in x[0].lower() else 0)
    return cands[0] if cands else (None, None)

def get_by_id(lines, id_sub):
    for i, l in enumerate(lines):
        if id_sub in l:
            return l.strip(), lines[i+1].strip() if i+1 < len(lines) else ''
    return None, None

def get_tvg_id(line):
    m = re.search(r'tvg-id="([^"]*)"', line)
    return m.group(1) if m else "unknown"

def get_logo(line):
    m = re.search(r'tvg-logo="([^"]*)"', line)
    return m.group(1) if m else ""

def main():
    lines = load_dccatalog()
    out = [f'#EXTM3U url-tvg="{EPG_URLS}"', WELCOME_EXT, WELCOME_URL]
    xml_channels = [f' <channel id="welcome"><display-name>Cairns Motel - Welcome</display-name><category>Motel Info</category><icon src="{WELCOME_LOGO}" /></channel>']
    xml_programs = []
    now = datetime.utcnow()
    fmt = "%Y%m%d%H%M%S +0000"
    xml_programs.append(f' <programme start="{now.strftime(fmt)}" stop="{(now+timedelta(hours=24)).strftime(fmt)}" channel="welcome"><title lang="en">Welcome to Cairns Motel</title><desc>Hotel info and local attractions</desc><category>Motel Info</category></programme>')

    for title in SEQ:
        id_hint = ID_HINTS.get(title)
        e, u = get_by_id(lines, id_hint) if id_hint else (None, None)
        if not e:
            e, u = get_best(lines, title)
        if e and u:
            if any(b in (e+u).lower() for b in BLACKLIST):
                continue
            cat = CAT_MAP.get(title, "Entertainment")
            new_ext = clean_and_recategorize(e, cat)
            out.append(new_ext)
            out.append(u)
            tvg_id = get_tvg_id(new_ext)
            logo = get_logo(new_ext)
            safe = title.replace("&", "and").replace("<","").replace(">","")
            xml_channels.append(f' <channel id="{tvg_id}"><display-name>{safe}</display-name><category>{cat}</category><icon src="{logo}" /></channel>')
            xml_programs.append(f' <programme start="{now.strftime(fmt)}" stop="{(now+timedelta(hours=24)).strftime(fmt)}" channel="{tvg_id}"><title lang="en">{safe}</title><category>{cat}</category></programme>')

    text = '\n'.join(out) + '\n'
    for p in [FINAL, FINAL_M3U8, DC_60_M3U, Path("DCcatalog_60.m3u8")]:
        p.write_text(text, encoding='utf-8')

    xml_text = '<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="Cairns Motel 60 from DCcatalog">\n' + '\n'.join(xml_channels) + '\n' + '\n'.join(xml_programs) + '\n</tv>\n'
    FINAL_XML.write_text(xml_text, encoding='utf-8')
    Path("DCcatalog_60.xml").write_text(xml_text, encoding='utf-8')
    print(f"Built {len(out)//2} chans - Welcome line 2, guide has {len(xml_programs)} programmes")

if __name__ == "__main__":
    main()
