from pathlib import Path
import requests, re
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

def sparkle_safe(ext, url):
    # must be m3u8
    if not url.lower().endswith(".m3u8"): return False
    if ".mp4" in url.lower(): return False
    # must have tvg-id
    if 'tvg-id="' not in ext: return False
    # no spaces in url
    if " " in url: return False
    return True

def is_good(url):
    if WELCOME_URL in url: return True
    try:
        r=requests.get(url, timeout=4, headers={"User-Agent":"VLC/3.0.19"}, stream=True)
        return r.status_code not in (403,404) and r.status_code < 400
    except: return False

flex = parse(FULL.read_text(errors='ignore'))
EPG_ORIG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'

final=[f'#EXTM3U url-tvg="{EPG_ORIG}"', WELCOME_EXT, WELCOME_URL]
print(f" FULL {len(flex)}")

# PEI first
for e,u in flex:
    if len(final)//2 >= 66: break
    if not sparkle_safe(e,u): continue
    if any(k in e.lower() for k in ["cbc pei","compass","ctv atlantic","global halifax"]):
        if u not in "\n".join(final) and is_good(u):
            final.append(e); final.append(u)
            print(f" OK PEI {e[:60]}")

# then fill with only sparkle-safe + 403/404 filtered
for e,u in flex:
    if len(final)//2 >= 66: break
    if not sparkle_safe(e,u): 
        print(f" SKIP UNSAFE {e[:60]}")
        continue
    if u in "\n".join(final): continue
    if is_good(u):
        final.append(e); final.append(u)

FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final_60 {len(final)//2} Sparkle-safe")

# also clean FULL of mp4 etc so it doesn't bleed into future finals
clean=[f'#EXTM3U url-tvg="{EPG_ORIG}"']
for e,u in flex:
    if sparkle_safe(e,u) or WELCOME_URL in u:
        clean.append(e); clean.append(u)
Path("full_ca_us.m3u").write_text("\n".join(clean)+"\n", encoding='utf-8')
print(f"CLEANED FULL {len(clean)//2} - removed mp4/bad")
