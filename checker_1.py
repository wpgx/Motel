import re
from pathlib import Path

FINAL = Path("final_60.m3u")
FINAL_M3U8 = Path("final_60.m3u8")
FINAL_XML = Path("final_60.xml")
DC_60_M3U = Path("DCcatalog_60.m3u")
DC_60_M3U8 = Path("DCcatalog_60.m3u8")
DC_60_XML = Path("DCcatalog_60.xml")
FULL_CA_US = Path("full_ca_us.m3u")

DC_CATALOG = Path("DCcatalog.m3u")
WELCOME_URL = 'https://motel.deecee.ca/welcome/media/media.m3u8'
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome'
EPG_URLS = "https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml"
BLACKLIST = ["99991399", "magnolia", "adult", "xxx", "porn", "xman", "x-man"]

SEQ = [
    ("CBC News Nova Scotia","CA4600007UE"),("CBC News PEI","CA4600002Z5"),("CBC News","CABC2300009KD"),
    ("CTV News","CA1400004AE"),("Global News National",None),("The Weather Network","CABC23000223U"),
    ("CBS News 24/7","CA390002621"),("NBC News NOW","CAAJ2700011IF"),("CNN Headlines",None),
    ("NFL Channel",None),("NHL",None),("MLB Channel","CA1400001PI"),("NASCAR Channel","CA700002VS"),
    ("F1 Channel",None),("FIFA+",None),("TSN The Ocho","CA1400003R3"),("World Poker Tour","CABD1200013IH"),
    ("Billiard TV",None),("BUZZR","653200"),("Game Show Central","CAAJ2700027GW"),("Tastemade","CABD1200002T9"),
    ("MagellanTV Wildest","CAAJ3400017AE"),("Bob Ross","CABC2300015UM"),("History & Warfare","CA600001C3"),
    ("Modern Marvels","CA900004R3"),("CINEVAULT: Classics",None),("At the Movies",None),
    ("FilmRise Action","CAAJ2700014EE"),("FilmRise Western","CAAJ27000159K"),("FilmRise Horror","CA35000044I"),
    ("Hallmark Movies & More",None),("FilmRise Classic TV",None),("Baywatch",None),("Nash Bridges",None),
    ("The FBI",None),("The Rifleman",None),("Wanted: Dead or Alive",None),("Grit Xtra",None),
    ("Death Valley Days",None),("Dick Van Dyke",None),("Johnny Carson TV",None),("The Carol Burnett Show",None),
    ("The Ed Sullivan Show",None),("That Girl",None),("Western Bound",None),("Lone Star",None),
    ("Classic Doctor Who",None),("American Gladiators by MGM",None),("The Outer Limits","68b0b1d296759568b7f1f042"),
    ("BBC Sci-Fi",None),("FilmRise Sci-Fi",None),("Stingray Easy Listening",None),("Stingray Classic Rock",None),
    ("Stingray Soft Hits",None),("Stingray Country Greats",None),("Toon Goggles",None),("Moonbug",None),
    ("FailArmy",None),("Stingray Naturescape",None),
]

def clean(e):
    if ',' not in e:
        return e
    h,t=e.rsplit(',',1)
    t=re.sub(r'^\s*\d+\s*[-\)\.]\s*','',t.strip())
    h=re.sub(r'\s*tvg-chno="[^"]*"\s*',' ',h)
    h=re.sub(r'#EXTINF:[^\s]*','#EXTINF:-1',h)
    return f"{h.strip()}, {t.strip()}"

def load_dccatalog():
    return Path("DCcatalog.m3u").read_text(errors='ignore').splitlines()

def get_best(lines, title):
    cands=[]
    for i,l in enumerate(lines):
        if l.startswith('#EXTINF') and l.rsplit(',',1)[-1].strip().lower()==title.lower():
            cands.append((l.strip(), lines[i+1].strip()))
    cands.sort(key=lambda x: 10 if "pluto" in x[0].lower() else -5 if "samsung" in x[0].lower() else 0)
    return cands[0] if cands else (None,None)

def get_by_id(lines, id_sub):
    for i,l in enumerate(lines):
        if id_sub in l:
            return l.strip(), lines[i+1].strip()
    return None,None

def get_tvg_id(line):
    m=re.search(r'tvg-id="([^"]*)"', line)
    return m.group(1) if m else "unknown"

def get_display_name(line):
    return line.rsplit(",",1)[-1].strip() if "," in line else "Unknown"

def main():
    lines=load_dccatalog()
    out=[f'#EXTM3U url-tvg="{EPG_URLS}"', WELCOME_EXT, WELCOME_URL]
    for title, id_hint in SEQ:
        e,u=get_by_id(lines,id_hint) if id_hint else (None,None)
        if not e:
            e,u=get_best(lines,title)
        if e and u:
            if any(b in (e+u).lower() for b in BLACKLIST):
                continue
            out.append(clean(e))
            out.append(u)

    text='\n'.join(out)+'\n'
    for p in [FINAL, FINAL_M3U8, DC_60_M3U, DC_60_M3U8]:
        p.write_text(text, encoding='utf-8')

    xml_lines=[]
    for l in out:
