import requests
from pathlib import Path
POOL = Path("backup_pool.m3u")
FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")
EPG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19"}
TIMEOUT = 5

def fetch(url):
    try: return requests.get(url, timeout=20, headers=HEADERS).text
    except: return ""

def parse(txt):
    lines=txt.splitlines(); out=[]
    for i,l in enumerate(lines):
        if l.strip().startswith('#EXTINF') and i+1 < len(lines):
            u=lines[i+1].strip()
            if u.startswith("http"): out.append((l,u))
    return out

def is_english_and_guided(ext):
    low=ext.lower()
    # must have tvg-id for guide
    if 'tvg-id=""' in low or "tvg-id=''" in low: return False
    if 'tvg-id' not in low: return False
    # skip obvious non-english groups
    bad = ["arabic","french","spanish","hindi","punjabi","urdu","tagalog","vietnamese","chinese","korean"]
    if any(b in low for b in bad): return False
    return True

def is_alive(url):
    if ".mp4" in url.lower(): return False
    try:
        r=requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        if r.status_code>=400 or len(r.text)<400: return False
        return "#EXTM3U" in r.text or "#EXT-X" in r.text
    except: return False

print("START english+guide+working pool")
all_txt = ""
if POOL.exists(): all_txt += "\n" + POOL.read_text(errors='ignore')
all_txt += "\n" + fetch("https://iptv-org.github.io/iptv/countries/ca.m3u")
all_txt += "\n" + fetch("https://iptv-org.github.io/iptv/countries/us.m3u")
all_txt += "\n" + fetch("https://iptv-org.github.io/iptv/languages/eng.m3u")

chans=parse(all_txt)
# dedup + filter
seen=set(); flex=[]
for ext,url in chans:
    if url in seen: continue
    if not is_english_and_guided(ext): continue
    seen.add(url); flex.append((ext,url))

print(f" english+guide deduped {len(flex)} -> testing alive...")
alive=[]
for ext,url in flex:
    if is_alive(url):
        alive.append((ext,url))
        if len(alive)%100==0: print(f" {len(alive)} alive...")

print(f" ALIVE pool {len(alive)}")

# write full = that alive pool
out=[f'#EXTM3U url-tvg="{EPG}"']
for e,u in alive: out.append(e); out.append(u)
FULL.write_text("\n".join(out)+"\n", encoding='utf-8')

# final_60 = news first from alive
pri_keys=["cbc news","ctv news","global news","cp24","cbc winnipeg","ctv winnipeg"]
pri=[c for c in alive if any(k in c[0].lower() for k in pri_keys)]
oth=[c for c in alive if c not in pri]
final=[f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]
for e,u in pri+oth:
    if len(final)>=122: break
    final.append(e); final.append(u)
FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE full {len(alive)} and final {len(final)//2}")
print("DONE")
