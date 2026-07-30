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

def is_really_alive(url):
    if WELCOME_URL in url: return True
    if ".mp4" in url.lower(): return False
    # Xumo expiring links always 403 later - skip them
    if "xumo" in url.lower() and "ads." in url.lower(): 
        return False
    try:
        # must return m3u8 content, not 403 page
        r=requests.get(url, timeout=8, headers={"User-Agent":"VLC/3.0.19 LibVLC/3.0.19", "Accept":"*/*"}, stream=True)
        if r.status_code in (403,404) or r.status_code >= 400:
            print(f" DEAD {r.status_code} {url[:80]}")
            return False
        # peek first 2kb - if it says 403/Forbidden or not m3u8, dead
        chunk = next(r.iter_content(2048), b"").decode(errors='ignore').lower()
        if "403" in chunk or "forbidden" in chunk or "accessdenied" in chunk:
            print(f" DEAD body 403 {url[:80]}")
            return False
        if "#extm3u" not in chunk and "#ext-x-stream" not in chunk:
            print(f" DEAD not m3u8 {url[:80]}")
            return False
        return True
    except Exception as ex:
        print(f" DEAD err {url[:80]} {ex}")
        return False

print("Fetching EPG ids...")
ca_txt = requests.get("https://iptv-org.github.io/epg/guides/ca.xml", timeout=20).text
us_txt = requests.get("https://iptv-org.github.io/epg/guides/us.xml", timeout=20).text
all_ids = set(re.findall(r'<channel id="([^"]+)"', ca_txt)) | set(re.findall(r'<channel id="([^"]+)"', us_txt))
print(f" EPG total ids {len(all_ids)}")

flex = parse(FULL.read_text(errors='ignore'))
print(f" FULL {len(flex)}")

EPG_ORIG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'
middle=[]

# ONLY channels whose tvg-id IS in EPG = no empty guide
for e,u in flex:
    if len(middle)//2 >= 64: break
    m=re.search(r'tvg-id="([^"]+)"', e)
    if not m: continue
    tid=m.group(1)
    if tid in all_ids:
        if u in "\n".join(middle): continue
        if is_really_alive(u):
            middle.append(e); middle.append(u)
            print(f" OK GUIDE {tid}")

print(f" After guide-only pass: {len(middle)//2}")

# if we still need more to reach 64, allow no-guide but must be alive
if len(middle)//2 < 64:
    for e,u in flex:
        if len(middle)//2 >= 64: break
        if u in "\n".join(middle): continue
        if is_really_alive(u):
            middle.append(e); middle.append(u)

final=[f'#EXTM3U url-tvg="{EPG_ORIG}"', WELCOME_EXT, WELCOME_URL] + middle + [WELCOME_EXT, WELCOME_URL, ""]
FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final_60 {len(final)//2} - {len([e for e in middle if any(tid in e for tid in all_ids)])} with guide, 0 403, Sparkle safe")
