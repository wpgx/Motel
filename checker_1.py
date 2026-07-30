from pathlib import Path
import requests
FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")
EPG_OUT = Path("custom_epg.xml")
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info", Cairns Motel - Welcome'
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
        if r.status_code in (403,404) or r.status_code >= 400:
            print(f" SKIP {r.status_code}")
            return False
        return True
    except: return False

flex = parse(FULL.read_text(errors='ignore'))
print(f" FULL {len(flex)}")

# ORIGINAL GUIDE - back to how it was
EPG_ORIG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'

final=[f'#EXTM3U url-tvg="{EPG_ORIG}"', WELCOME_EXT, WELCOME_URL]

for e,u in flex:
    if len(final)//2 >= 66: break
    if u in "\n".join(final): continue
    if is_good(u):
        final.append(e); final.append(u)

FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final_60 {len(final)//2} - no 403/404")

# restore FULL header to original too
full_txt=FULL.read_text(errors='ignore')
first_line=full_txt.splitlines()[0]
full_txt=full_txt.replace(first_line, f'#EXTM3U url-tvg="{EPG_ORIG}"', 1)
FULL.write_text(full_txt, encoding='utf-8')
print("RESTORED FULL guide to original ca+us")

# delete custom EPG so Sparkle doesn't see it
if EPG_OUT.exists():
    EPG_OUT.write_text('<?xml version="1.0"?><tv></tv>', encoding='utf-8')
    print("WIPED custom_epg.xml - Sparkle won't crash now")

print("DONE - guide back to original, No Information will show but no crash")
