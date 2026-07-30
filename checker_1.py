import requests, re
from pathlib import Path

FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")

WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" tvg-name="Cairns Motel" group-title="Motel Info",Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
BANNED = ["deal or no deal","wu tang","wu-tang","wutang","stargate"]
EPG = 'https://iptv-org.github.io/epg/guides/ca.xml'

def is_alive(url):
    try:
        r = requests.head(url, timeout=8, allow_redirects=True, headers={"User-Agent":"VLC/3.0"})
        if r.status_code in (200, 302, 301):
            return True
        # some servers block HEAD, try GET small range
        r = requests.get(url, timeout=10, stream=True, headers={"User-Agent":"VLC/3.0"})
        return r.status_code == 200
    except:
        return False

txt = FULL.read_text(errors='ignore')
lines = txt.splitlines()
pairs = []
for i in range(len(lines)-1):
    if '#EXTINF' in lines[i] and lines[i+1].strip().startswith('http'):
        ext = lines[i].strip()
        url = lines[i+1].strip()
        low = ext.lower()
        if any(b in low for b in BANNED): continue
        pairs.append((ext,url))

print(f"Loaded {len(pairs)} from full")

alive = []
for ext,url in pairs:
    if is_alive(url):
        alive.append((ext,url))
        print(f"OK {len(alive)}/64 {url[:80]}")
    if len(alive) >= 64:
        break

print(f"Found {len(alive)} alive")

out = [f'#EXTM3U url-tvg="{EPG}"']
out.append(WELCOME_EXT)
out.append(WELCOME_URL)
seen = {WELCOME_URL}
for ext,url in alive:
    if url not in seen:
        out.append(ext)
        out.append(url)
        seen.add(url)

# always Welcome at end too
out.append(WELCOME_EXT)
out.append(WELCOME_URL)

FINAL.write_text("\n".join(out)+"\n")
print(f"WROTE {len(out)//2} channels = {len(out)} lines to final_60.m3u")
