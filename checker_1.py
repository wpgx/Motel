from pathlib import Path
import requests
POOL = Path("backup_pool.m3u")
FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")
EPG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'

def fetch(url):
    try: return requests.get(url, timeout=15).text
    except: return ""

def parse(txt):
    lines=txt.splitlines(); out=[]
    for i,l in enumerate(lines):
        if l.strip().startswith('#EXTINF') and i+1 < len(lines):
            u=lines[i+1].strip()
            if u.startswith("http"): out.append((l,u))
    return out

def is_english_guided(ext):
    low=ext.lower()
    if 'tvg-id' not in low or 'tvg-id=""' in low: return False
    bad=["arabic","french","spanish","hindi","punjabi","urdu","tagalog","vietnamese","chinese"]
    return not any(b in low for b in bad)

print("START fast flexible")
all_txt = ""
if POOL.exists(): all_txt += "\n" + POOL.read_text(errors='ignore')
all_txt += "\n" + fetch("https://iptv-org.github.io/iptv/languages/eng.m3u")
all_txt += "\n" + fetch("https://iptv-org.github.io/iptv/countries/ca.m3u")

chans=parse(all_txt)
seen=set(); flex=[]
for ext,url in chans:
    if url in seen: continue
    if not is_english_guided(ext): continue
    seen.add(url); flex.append((ext,url))

print(f" filtered to {len(flex)} english+guide")

out=[f'#EXTM3U url-tvg="{EPG}"']
for e,u in flex: out.append(e); out.append(u)
FULL.write_text("\n".join(out)+"\n", encoding='utf-8')
print(f"WROTE full_ca_us {len(flex)}")

# final_60 = first 60 news priority, no alive test for speed
pri_keys=["cbc news","ctv news","global news","cp24","cbc winnipeg","ctv winnipeg","ctv","cbc"]
pri=[c for c in flex if any(k in c[0].lower() for k in pri_keys)]
oth=[c for c in flex if c not in pri]
final=[f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]
for e,u in pri+oth:
    if len(final)>=122: break
    final.append(e); final.append(u)
FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final_60 {len(final)//2}")
print("DONE")
