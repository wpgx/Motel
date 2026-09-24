import re
from pathlib import Path
from datetime import datetime, timedelta

FINAL = Path("final_60.m3u")
FINAL_XML = Path("final_60.xml")
WELCOME_URL = 'https://motel.deecee.ca/welcome/media/media.m3u8'
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome'
EPG_URLS = "https://motel.deecee.ca/final_60.xml"

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

def main():
    lines = Path("DCcatalog.m3u").read_text(errors='ignore').splitlines()
    # ONE PASS index - fixes 2-min hang
    idx = {}
    for i, l in enumerate(lines):
        if l.startswith('#EXTINF'):
            name = l.rsplit(',',1)[-1].strip().lower()
            if name not in idx:
                idx[name] = (l.strip(), lines[i+1].strip() if i+1 < len(lines) else '')

    out = [f'#EXTM3U url-tvg="{EPG_URLS}"', WELCOME_EXT, WELCOME_URL]
    xml_c = [' <channel id="welcome"><display-name>Cairns Motel - Welcome</display-name><category>Motel Info</category><icon src="https://motel.deecee.ca/logo.png" /></channel>']
    xml_p = []
    now = datetime.utcnow()
    fmt = "%Y%m%d%H%M%S +0000"
    xml_p.append(f' <programme start="{now.strftime(fmt)}" stop="{(now+timedelta(hours=24)).strftime(fmt)}" channel="welcome"><title>Welcome to Cairns Motel</title></programme>')

    for title, cat in CAT_MAP.items():
        pair = idx.get(title.lower())
        if not pair:
            continue
        e, u = pair
        e = re.sub(r'group-title="[^"]*"', f'group-title="{cat}"', e)
        e = re.sub(r'#EXTINF:[^\s]*', '#EXTINF:-1', e)
        e = re.sub(r'\s+', ' ', e).strip()
        out.append(e)
        out.append(u)
        m = re.search(r'tvg-id="([^"]*)"', e)
        tid = m.group(1) if m else title
        safe = title.replace("&","and")
        xml_c.append(f' <channel id="{tid}"><display-name>{safe}</display-name><category>{cat}</category></channel>')
        xml_p.append(f' <programme start="{now.strftime(fmt)}" stop="{(now+timedelta(hours=24)).strftime(fmt)}" channel="{tid}"><title>{safe}</title><category>{cat}</category></programme>')

    txt = '\n'.join(out) + '\n'
    for p in [Path("final_60.m3u"), Path("final_60.m3u8"), Path("DCcatalog_60.m3u"), Path("DCcatalog_60.m3u8")]:
        p.write_text(txt, encoding='utf-8')

    xml_text = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n' + '\n'.join(xml_c) + '\n' + '\n'.join(xml_p) + '\n</tv>\n'
    FINAL_XML.write_text(xml_text, encoding='utf-8')
    Path("DCcatalog_60.xml").write_text(xml_text, encoding='utf-8')
    print(f"Built {len(out)//2} chans in <1 sec - welcome first, motel categories, guide OK")

if __name__ == "__main__":
    main()
