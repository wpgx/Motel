from pathlib import Path
import requests
FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" tvg-name="Cairns Motel" group-title="Motel Info",Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'

def parse(txt):
    lines=txt.splitlines(); out=[]
    for i,l in enumerate(lines):
        if l.strip().startswith('#EXTINF') and i+1 < len(lines):
            u=lines[i+1].strip()
            if u.startswith("http"): out.append((l.strip(),u.strip()))
    return out

def is_good(url):
    if WELCOME_URL in url: return True
    if ".mp4" in url.lower(): return False
    try:
        r=requests.get(url, timeout=4, headers={"User-Agent":"VLC/3.0.19"}, stream=True)
        return r.status_code not in (403,404) and r.status_code < 400
    except: return False

flex = parse(FULL.read_text(errors='ignore'))
EPG_ORIG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'

# build 64 real channels + welcome at start
middle=[]
for e,u in flex:
    if len(middle)//2 >= 64: break
    if u in "\n".join(middle): continue
    if is_good(u):
        middle.append(e); middle.append(u)

# final = welcome + 64 + welcome again + double newline = Sparkle won't crash on real channel
final=[f'#EXTM3U url-tvg="{EPG_ORIG}"', WELCOME_EXT, WELCOME_URL] + middle + [WELCOME_EXT, WELCOME_URL, ""]

FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final_60 {len(final)//2} with welcome at top AND bottom + blank line - fixes Sparkle last-entry crash")
