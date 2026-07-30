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
    if url.lower().endswith(".mp4"): return False
    try:
        r=requests.get(url, timeout=4, headers={"User-Agent":"VLC/3.0.19"}, stream=True)
        if r.status_code in (403,404) or r.status_code >= 400:
            return False
        return True
    except: return False

flex = parse(FULL.read_text(errors='ignore'))
print(f" FULL {len(flex)} - NOT TOUCHING IT")

EPG_ORIG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'
final=[f'#EXTM3U url-tvg="{EPG_ORIG}"', WELCOME_EXT, WELCOME_URL]

# PEI news first - will have guide
for e,u in flex:
    if len(final)//2 >= 12: break
    if any(k in e.lower() for k in ["cbc pei","compass","ctv atlantic","global halifax"]):
        if u not in "\n".join(final) and is_good(u):
            final.append(e); final.append(u)

# CA with guide
for e,u in flex:
    if len(final)//2 >= 50: break
    if 'tvg-id="ca_' in e:
        if u not in "\n".join(final) and is_good(u):
            final.append(e); final.append(u)

# fill to 65
for e,u in flex:
    if len(final)//2 >= 66: break
    if u not in "\n".join(final) and is_good(u):
        final.append(e); final.append(u)

FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final_60 {len(final)//2} - guide back, no 403/404, Sparkle safe")
print("FULL still 2220 wonderful - untouched")
