import requests
from pathlib import Path

FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")
POOL = Path("backup_pool.m3u")
EPG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19"}
TIMEOUT = 6

def fetch(url):
    try:
        t = requests.get(url, timeout=20, headers=HEADERS).text
        print(f" fetched {url} -> {t.count('#EXTINF')} chans")
        return t
    except Exception as e:
        print(f" fail {url} {e}")
        return ""

def is_alive(url):
    if WELCOME_URL in url: return True
    if ".mp4" in url.lower(): return False
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        if r.status_code >= 400: return False
        if len(r.text) < 500: return False
        return "#EXTM3U" in r.text or "#EXT-X" in r.text
    except:
        return False

def parse(txt):
    lines = txt.splitlines()
    out = []
    for i,l in enumerate(lines):
        if l.strip().startswith('#EXTINF') and i+1 < len(lines):
            u = lines[i+1].strip()
            if u.startswith("http"):
                out.append((l.strip(), u.strip()))
    return out

print("START flexible checker_1")

# --- BUILD FLEXIBLE FULL ---
all_chans = []
if POOL.exists():
    all_chans += parse(POOL.read_text(errors='ignore'))

# add iptv-org official
all_chans += parse(fetch("https://iptv-org.github.io/iptv/countries/ca.m3u"))
all_chans += parse(fetch("https://iptv-org.github.io/iptv/countries/us.m3u"))
# add free-tv if alive
free = fetch("https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8")
if free.count('#EXTINF') > 50:  # only if not dead
    all_chans += parse(free)

# dedup by URL, keep first
seen = set()
flex = []
for ext,url in all_chans:
    if url not in seen:
        seen.add(url)
        flex.append((ext,url))

print(f" FLEXIBLE total deduped {len(flex)}")

# write full_ca_us.m3u
out_lines = [f'#EXTM3U url-tvg="{EPG}"']
for e,u in flex:
    out_lines.append(e)
    out_lines.append(u)
FULL.write_text("\n".join(out_lines)+"\n", encoding='utf-8')
print(f"WROTE full_ca_us.m3u {len(flex)}")

# --- BUILD final_60 alive + news priority
