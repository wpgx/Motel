from pathlib import Path
import requests, re, datetime
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

def alive(url):
    if WELCOME_URL in url: return True
    if ".mp4" in url.lower(): return False
    try:
        r=requests.get(url, timeout=4, headers={"User-Agent":"VLC/3.0.19"}, stream=True)
        return r.status_code < 400
    except: return False

flex = parse(FULL.read_text(errors='ignore'))
print(f" FULL {len(flex)}")

# 3 EPGs in header - ca + us + our custom fallback
EPG_HEADER = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml,https://xman.deecee.ca/custom_epg.xml'

final=[f'#EXTM3U url-tvg="{EPG_HEADER}"', WELCOME_EXT, WELCOME_URL]

# add with alive check to skip TSN 404 etc
for e,u in flex:
    if len(final)//2 >= 66: break
    if u in "\n".join(final): continue
    if alive(u):
        final.append(e); final.append(u)
        print(f" OK {e[:60]}")
    else:
        print(f" DEAD SKIP {e[:60]}")

FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final {len(final)//2}")

# tiny custom EPG only for fallback
now=datetime.datetime.utcnow()
start=now.strftime("%Y%m%d%H%M%S +0000")
stop=(now+datetime.timedelta(days=7)).strftime("%Y%m%d%H%M%S +0000") # 7 days of regular

xml=['<?xml version="1.0" encoding="UTF-8"?><tv>']
xml.append('<channel id="welcome"><display-name>Cairns Motel</display-name></channel>')
xml.append(f'<programme start="{start}" stop="{stop}" channel="welcome"><title>Welcome</title><desc>Regularly scheduled programming</desc></programme>')

for ext,url in parse("\n".join(final)):
    m=re.search(r'tvg-id="([^"]*)"', ext)
    if m and m.group(1):
        tid=m.group(1)
        xml.append(f'<channel id="{tid}"><display-name>{tid}</display-name></channel>')
        xml.append(f'<programme start="{start}" stop="{stop}" channel="{tid}"><title>Regularly scheduled programming</title><desc>Regularly scheduled programming</desc></programme>')

xml.append('</tv>')
EPG_OUT.write_text("\n".join(xml), encoding='utf-8')
print("WROTE custom_epg.xml small - no red flag")

# also fix FULL header to same 3 EPGs
full_text=FULL.read_text(errors='ignore')
full_text=full_text.replace(full_text.splitlines()[0], f'#EXTM3U url-tvg="{EPG_HEADER}"', 1)
FULL.write_text(full_text, encoding='utf-8')
print("FIXED FULL header to 3 EPGs - DONE")
