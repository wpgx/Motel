from pathlib import Path
import requests, re, gzip
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
        r=requests.get(url, timeout=5, headers={"User-Agent":"VLC/3.0.19"}, stream=True)
        return r.status_code not in (403,404) and r.status_code < 400
    except: return False

# get real ca.xml ids so we ONLY pick channels that WILL have guide
print("Fetching ca.xml channel list...")
ca = requests.get("https://iptv-org.github.io/epg/guides/ca.xml", timeout=15).text
ca_ids = set(re.findall(r'<channel id="([^"]+)"', ca))
print(f" ca.xml has {len(ca_ids)} ids like {list(ca_ids)[:5]}")

flex = parse(FULL.read_text(errors='ignore'))
print(f" FULL {len(flex)}")

EPG_ORIG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'
final=[f'#EXTM3U url-tvg="{EPG_ORIG}"', WELCOME_EXT, WELCOME_URL]
middle=[]

# 1. PEI + Canadian with REAL guide first = programs will count
for e,u in flex:
    if len(middle)//2 >= 40: break
    m=re.search(r'tvg-id="([^"]+)"', e)
    if not m: continue
    tid=m.group(1)
    if tid in ca_ids:  # THIS will have guide
        if u not in "\n".join(middle) and is_good(u):
            middle.append(e); middle.append(u)
            print(f" GUIDE {tid}")

# 2. fill rest with any alive (news/music)
for e,u in flex:
    if len(middle)//2 >= 64: break
    if u not in "\n".join(middle) and is_good(u):
        middle.append(e); middle.append(u)

# Sparkle last-entry crash fix: welcome at bottom + blank line
final = final + middle + [WELCOME_EXT, WELCOME_URL, ""]
FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final_60 {len(final)//2} - {len([x for x in middle if 'tvg-id' in x])} with real guide, programs should count to few hundred again")
