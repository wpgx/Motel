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

print("START CA+US pool")
all_txt = ""
if POOL.exists():
    all_txt += "\n" + POOL.read_text(errors='ignore')
    print(f" pool {all_txt.count('#EXTINF')}")

ca = fetch("https://iptv-org.github.io/iptv/countries/ca.m3u")
us = fetch("https://iptv-org.github.io/iptv/countries/us.m3u")
# only keep US that looks like main networks, not 3000 locals
# we keep all CA, but filter US to keep under 700 total
all_chans = parse(all_txt + "\n" + ca)
# add US only if we still under 800
us_chans = parse(us)
for ext,url in us_chans:
    low=ext.lower()
    # skip US locals that are foreign language
    if any(x in low for x in ["spanish","french","arabic","hindi"]): continue
    if 'tvg-id=""' in low: continue
    all_chans.append((ext,url))
    if len(all_chans) > 750: break

# dedup
seen=set(); flex=[]
for ext,url in all_chans:
    if url not in seen:
        seen.add(url)
        flex.append((ext,url))

print(f" flex deduped {len(flex)}")

out=[f'#EXTM3U url-tvg="{EPG}"']
for e,u in flex: out.append(e); out.append(u)
FULL.write_text("\n".join(out)+"\n", encoding='utf-8')

# final_60 with news priority
pri=["cbc news","ctv news","global news","cp24","cbc winnipeg","ctv winnipeg","citytv winnipeg","global winnipeg"]
pri_list=[c for c in flex if any(k in c[0].lower() for k in pri)]
oth=[c for c in flex if c not in pri_list]
final=[f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]
for e,u in pri_list+oth:
    if len(final)>=122: break
    final.append(e); final.append(u)
FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE full {len(flex)} final {len(final)//2}")
print("DONE")
