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
            if u.startswith("http"): out.append((l.strip(),u.strip()))
    return out

print("START keep 750 + PEI 65")
# rebuild flex from last full if exists to keep your 750
if FULL.exists() and FULL.read_text(errors='ignore').count('#EXTINF') > 600:
    all_chans = parse(FULL.read_text(errors='ignore'))
    print(f" using existing FULL {len(all_chans)}")
else:
    all_txt = ""
    if POOL.exists(): all_txt += "\n" + POOL.read_text(errors='ignore')
    all_txt += "\n" + fetch("https://iptv-org.github.io/iptv/countries/ca.m3u")
    all_txt += "\n" + fetch("https://iptv-org.github.io/iptv/countries/us.m3u")
    all_chans = parse(all_txt)

# dedup keep all 750 (guide + no-guide english)
seen=set(); flex=[]
for ext,url in all_chans:
    if url not in seen:
        seen.add(url)
        flex.append((ext,url))

print(f" flex {len(flex)}")

# write full as-is 750
out=[f'#EXTM3U url-tvg="{EPG}"']
for e,u in flex: out.append(e); out.append(u)
FULL.write_text("\n".join(out)+"\n", encoding='utf-8')
print(f"WROTE full_ca_us {len(flex)}")

# --- BUILD PEI final_65 but named final_60 ---
news_keys=["cbc pei","compass","ctv atlantic","global halifax","global maritimes","cbc news","ctv news","cp24","global news"]
sports_keys=["tsn","sportsnet","snet","espn","fox sports"]

news=[c for c in flex if any(k in c[0].lower() for k in news_keys)]
sports=[c for c in flex if any(k in c[0].lower() for k in sports_keys)]
# dedup sports not already in news
sports=[c for c in sports if c not in news]

others=[c for c in flex if c not in news and c not in sports]

# final = welcome + news (top) + 5 sports bump + rest to reach 65
final=[f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]

# add news
for e,u in news:
    if len(final) >= 32: break # ~15 news
    final.append(e); final.append(u)

# ADD 5 SPORTS BUMP
added_sports=0
for e,u in sports:
    if added_sports >= 5: break
    final.append(e); final.append(u)
    added_sports+=1
    print(f" +SPORTS {e}")

# fill rest to 65 total channels (welcome counts as 1, so need 65 channels = 131 lines incl header? Actually 1+65 = 66 EXTINF)
while len(final) < 132 and others:
    e,u = others.pop(0)
    final.append(e); final.append(u)

FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final_60.m3u as 65 channels (news + 5 sports) - {len(final)//2} total")
print("DONE")
