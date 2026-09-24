import re, requests
from pathlib import Path
from datetime import datetime

FINAL = Path("final_60.m3u")
FINAL_M3U8 = Path("final_60.m3u8")
FINAL_XML = Path("final_60.xml")
DC_60_M3U = Path("DCcatalog_60.m3u")
DC_60_M3U8 = Path("DCcatalog_60.m3u8")
DC_60_XML = Path("DCcatalog_60.xml")
FULL_CA_US = Path("full_ca_us.m3u")

# DCcatalog as source
DC_CATALOG = Path("DCcatalog.m3u")
DC_CATALOG_ALT = Path("dccatalog.txt")

TIMEOUT = 8
WELCOME_URL = 'https://motel.deecee.ca/welcome/media/media.m3u8'
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome'
HEADERS = {"User-Agent": "VLC/3.0.19 LibVLC/3.0.19"}
BLACKLIST = ["99991399", "magnolia", "adult", "xxx", "porn", "xman", "x-man"]
EPG_URLS = "https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml,https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"

# CURATED 60 - pulled from DCcatalog
SEQ = [
    ("CBC News Nova Scotia","CA4600007UE"),
    ("CBC News PEI","CA4600002Z5"),
    ("CBC News","CABC2300009KD"),
    ("CTV News","CA1400004AE"),
    ("Global News National",None),
    ("The Weather Network","CABC23000223U"),
    ("CBS News 24/7","CA390002621"),
    ("NBC News NOW","CAAJ2700011IF"),
    ("CNN Headlines",None),
    ("NFL Channel",None),
    ("NHL",None),
    ("MLB Channel","CA1400001PI"),
    ("NASCAR Channel","CA700002VS"),
    ("F1 Channel",None),
    ("FIFA+",None),
    ("TSN The Ocho","CA1400003R3"),
    ("World Poker Tour","CABD1200013IH"),
    ("Billiard TV",None),
    ("BUZZR","653200"),
    ("Game Show Central","CAAJ2700027GW"),
    ("Tastemade","CABD1200002T9"),
    ("MagellanTV Wildest","CAAJ3400017AE"),
    ("Bob Ross","CABC2300015UM"),
    ("History & Warfare","CA600001C3"),
    ("Modern Marvels","CA900004R3"),
    ("CINEVAULT: Classics",None),
    ("At the Movies",None),
    ("FilmRise Action","CAAJ2700014EE"),
    ("FilmRise Western","CAAJ27000159K"),
    ("FilmRise Horror","CA35000044I"),
    ("Hallmark Movies & More",None),
    ("FilmRise Classic TV",None),
    ("Baywatch",None),
    ("Nash Bridges",None),
    ("The FBI",None),
    ("The Rifleman",None),
    ("Wanted: Dead or Alive",None),
    ("Grit Xtra",None),
    ("Death Valley Days",None),
    ("Dick Van Dyke",None),
    ("Johnny Carson TV",None),
    ("The Carol Burnett Show",None),
    ("The Ed Sullivan Show",None),
    ("That Girl",None),
    ("Western Bound",None),
    ("Lone Star",None),
    ("Classic Doctor Who",None),
    ("American Gladiators by MGM",None),
    ("The Outer Limits","68b0b1d296759568b7f1f042"),
    ("BBC Sci-Fi",None),
    ("FilmRise Sci-Fi",None),
    ("Stingray Easy Listening",None),
    ("Stingray Classic Rock",None),
    ("Stingray Soft Hits",None),
    ("Stingray Country Greats",None),
    ("Toon Goggles",None),
    ("Moonbug",None),
    ("FailArmy",None),
    ("Stingray Naturescape",None),
]

def parse_m3u_text(text):
    lines=text.splitlines()
    chans=[]
    for i,l in enumerate(lines):
        l=l.strip()
        if l.startswith('#EXTINF'):
            url=lines[i+1].strip() if i+1 < len(lines) else ''
            if url.startswith("http"): chans.append((l,url))
    return chans

def parse_m3u(path):
    if not path.exists(): return []
    return parse_m3u_text(path.read_text(errors='ignore'))

def clean_no_numbers(ext):
    if ',' not in ext: return ext
    head,title=ext.rsplit(',',1)
    title=re.sub(r'^\s*\d+\s*[-\)\.]\s*','',title.strip())
    title=re.sub(r'^\s*\d+\s+','',title.strip())
    head=re.sub(r'\s*tvg-chno="[^"]*"\s*',' ',head)
    head=re.sub(r'#EXTINF:[^\s]*','#EXTINF:-1',head)
    head=re.sub(r'\s+',' ',head).strip()
    return f"{head}, {title}"

def is_welcome(e,u): return 'welcome' in (e+u).lower()
def is_bad(u): return '.mp4' in u.lower() or 'dai.google.com' in u.lower() or '.m3u8' not in u.lower()
def is_blacklisted(e,u):
    if is_welcome(e,u): return False
    return any(b in (e+u).lower() for b in BLACKLIST)

def is_alive(url):
    if url==WELCOME_URL: return True
    if is_bad(url): return False
    try:
        r=requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        if r.status_code in (403,401,404,500,502,503): return False
        if 'AccessDenied' in r.text or '403 Forbidden' in r.text: return False
        if '#EXTM3U' not in r.text and '#EXT-X-STREAM' not in r.text and '#EXTINF' not in r.text:
            if len(r.text) < 1000: return False
        return True
    except:
        return False

def load_dccatalog():
    for p in [DC_CATALOG, DC_CATALOG_ALT, Path("/mnt/data/dccatalog.txt"), Path("DCcatalog.txt")]:
        if p.exists():
            print(f"Loading DCcatalog from {p}")
            return p.read_text(errors='ignore').splitlines()
    raise FileNotFoundError("DCcatalog.m3u not found - put DCcatalog in repo root")

def get_best_exact(catalog_lines, title):
    cands=[]
    for i,l in enumerate(catalog_lines):
        if l.strip().startswith('#EXTINF'):
            t = l.rsplit(',',1)[-1].strip() if ',' in l else ''
            if t.lower() == title.lower():
                url = catalog_lines[i+1].strip() if i+1 < len(catalog_lines) else ''
                cands.append((l.strip(), url))
    def score(x):
        e,u=x
        s=0
        low=e.lower()
        if "pluto" in low: s+=10
        if "samsung" in low: s-=5
        if "tubi" in low: s-=3
        if "plex" in low: s-=2
        return s
    cands.sort(key=score)
    return cands[0] if cands else (None,None)

def get_by_id(catalog_lines, id_sub):
    for i,l in enumerate(catalog_lines):
        if id_sub in l:
            url = catalog_lines[i+1].strip() if i+1 < len(catalog_lines) else ''
            return l.strip(), url
    return None,None

def build_full_from_dccatalog(catalog_lines):
    print("=== Building full_ca_us from DCcatalog ===")
    chans = parse_m3u_text("\n".join(catalog_lines))
    kept=[]
    for e,u in chans:
        if is_welcome(e,u): continue
        if is_blacklisted(e,u): continue
        if is_bad(u): continue
        low=e.lower()
        if not ('usa' in low or 'canada' in low or 'united states' in low or 'group-title="us' in low or 'group-title="ca' in low):
            continue
        kept.append((clean_no_numbers(e),u))
    print(f" Filtered CA/US from DCcatalog: {len(kept)}")
    # quick alive filter (optional - comment out if too slow)
    alive=[]
    for idx,(e,u) in enumerate(kept):
        if idx % 200 == 0: print(f" {idx}/{len(kept)} checked, {len(alive)} alive")
        if is_alive(u): alive.append((e,u))
    print(f" ALIVE: {len(alive)} / {len(kept)}")
    out_lines = [f'#EXTM3U url-tvg="{EPG_URLS}"'] + [x for pair in alive for x in pair]
    FULL_CA_US.write_text('\n'.join(out_lines)+'\n', encoding='utf-8')
    print(f" Wrote {FULL_CA_US} with {len(alive)} chans")
    return alive

def build_final_60_from_dccatalog(catalog_lines):
    print(f"=== Building final_60 from DCcatalog @ {datetime.now()} ===")
    out = [f'#EXTM3U url-tvg="{EPG_URLS}"', WELCOME_EXT, WELCOME_URL]
    failed=[]
    for title, id_hint in SEQ:
        e,u=None,None
        if id_hint:
            e,u = get_by_id(catalog_lines, id_hint)
        if not e:
            e,u = get_best_exact(catalog_lines, title)
        if e and u:
            if is_blacklisted(e,u): continue
            # optional alive check
            if not is_alive(u):
                print(f"DEAD in DCcatalog: {title} - skipping")
                failed.append(title)
                continue
            out.append(clean_no_numbers(e))
            out.append(u)
        else:
            failed.append(title)
    text = '\n'.join(out)+'\n'
    for p in [FINAL, FINAL_M3U8, DC_60_M3U, DC_60_M3U8]:
        p.write_text(text, encoding='utf-8')
    # XML channel map
    xml_channels=[]
    for line in out:
        if line.startswith('#EXTINF'):
            m=re.search(r'tvg-id="([^"]*)"', line)
            if m:
                tvg_id=m.group(1)
                name=line.rsplit(',',1)[-1].strip() if ',' in line else ""
                xml_channels.append(f' <channel id="{tvg_id}"><display-name>{name}</display-name></channel>')
    xml_text = '<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="Cairns 60 from DCcatalog">\n' + "\n".join(xml_channels) + "\n</tv>\n"
    for p in [FINAL_XML, DC_60_XML]:
        p.write_text(xml_text, encoding='utf-8')
    print(f"DONE final_60: {len(out)//2} chans, failed: {failed}")
    return out

def main():
    print("=== checker_1 - DCcatalog source + final_60 60ch ===")
    catalog_lines = load_dccatalog()
    build_full_from_dccatalog(catalog_lines)
    build_final_60_from_dccatalog(catalog_lines)

if __name__=="__main__":
    main()
