import requests, re
from pathlib import Path

FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")
POOL = Path("backup_pool.m3u")
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
EPG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'

print("START checker_1.py")

# 1. BUILD full_ca_us - ALWAYS from backup_pool if it exists
if POOL.exists():
    txt = POOL.read_text(errors='ignore')
    print(f" backup_pool found {txt.count('#EXTINF')} chans")
else:
    print(" NO backup_pool, downloading free-tv")
    txt = requests.get("https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8", timeout=30).text
    print(f" free-tv {txt.count('#EXTINF')} chans")

# add EPG header if missing
if not txt.startswith("#EXTM3U"):
    txt = f'#EXTM3U url-tvg="{EPG}"\n' + txt
elif 'url-tvg' not in txt.splitlines()[0]:
    lines = txt.splitlines()
    lines[0] = f'#EXTM3U url-tvg="{EPG}"'
    txt = "\n".join(lines)

FULL.write_text(txt, encoding='utf-8')
print(f"WROTE full_ca_us.m3u {txt.count('#EXTINF')} chans")

# 2. BUILD final_60 - simple copy of first 60 alive-ish from pool + welcome
lines = txt.splitlines()
chans = []
for i,l in enumerate(lines):
    if l.strip().startswith('#EXTINF') and i+1 < len(lines):
        url = lines[i+1].strip()
        if url.startswith("http") and ".mp4" not in url.lower():
            chans.append((l,url))

out = [f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]
for e,u in chans[:60]:
    out.append(e)
    out.append(u)

FINAL.write_text("\n".join(out)+"\n", encoding='utf-8')
print(f"WROTE final_60.m3u {len(out)//2} chans")
print("DONE")
