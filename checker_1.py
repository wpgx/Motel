import requests
from pathlib import Path

FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")

WELCOME_EXT_TOP = '#EXTINF:-1 tvg-id="welcome" tvg-name="Cairns Motel" tvg-logo="https://i.imgur.com/8QJ4sQO.png" group-title="Motel Info",Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
EPG = 'https://iptv-org.github.io/epg/guides/ca.xml'

BANNED = ["deal or no deal","wu tang","wu-tang","wutang","stargate"]

def is_alive(url):
    try:
        r = requests.head(url, timeout=6, allow_redirects=True, headers={"User-Agent":"VLC"})
        if r.status_code in (200,301,302): return True
        r = requests.get(url, timeout=8, stream=True, headers={"User-Agent":"VLC"})
        return r.status_code == 200
    except:
        return False

txt = FULL.read_text(errors='ignore')
lines = txt.splitlines()
pairs=[]
for i in range(len(lines)-1):
    if lines[i].startswith('#EXTINF') and lines[i+1].strip().startswith('http'):
        ext=lines[i].strip()
        url=lines[i+1].strip()
        if any(b in ext.lower() for b in BANNED): continue
        # must have tvg-id for guide
        if 'tvg-id=' not in ext.lower(): continue
        pairs.append((ext,url))

alive=[]
for ext,url in pairs:
    if is_alive(url):
        alive.append((ext,url))
        print(f"OK {len(alive)}/63 {url[:60]}")
    if len(alive)>=63: break

# Build final with EPG header - CRITICAL FOR GUIDE
out=[f'#EXTM3U url-tvg="{EPG}"']
# ONE Welcome only at top - prevents crash
out.append(WELCOME_EXT_TOP)
out.append(WELCOME_URL)
seen={WELCOME_URL}
for ext,url in alive:
    if url not in seen:
        out.append(ext)
        out.append(url)
        seen.add(url)

FINAL.write_text("\n".join(out)+"\n")
print(f"DONE wrote {len(alive)+1} channels, header has EPG")
