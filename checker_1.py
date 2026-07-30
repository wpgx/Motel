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

def has_guide_and_english(ext):
    low=ext.lower()
    # MUST have tvg-id="something" not empty
    if 'tvg-id=""' in low: return False
    if 'tvg-id=' not in low: return False
    # quick foreign filter
    bad_words=["arabic","spanish","french","hindi","punjabi","urdu","tagalog","vietnamese","chinese","korean","portuguese","italian","russian"]
    # check group-title and title
    for b in bad_words:
        # allow "french" if it's in english description? no, drop all
        if b in low:
            # exception: keep "french" if it's CBC french? No for PEI motel we want English only
            return False
    return True

print("START strict guide+english")
all_txt = ""
if POOL.exists():
    all_txt += "\n" + POOL.read_text(errors='ignore')

ca = fetch("https://iptv-org.github.io/iptv/countries/ca.m3u")
us = fetch("https://iptv-org.github.io/iptv/countries/us.m3u")

all_chans = parse(all_txt + "\n" + ca + "\n" + us)

seen=set(); flex=[]
for ext,url in all_chans:
    if url in seen: continue
    if not has_guide_and_english(ext): continue
    seen.add(url)
    flex.append((ext,url))

print(f" after strict filter {len(flex)} (was {len(all_chans)})")

out=[f'#EXTM3U url-tvg="{EPG}"']
for e,u in flex: out.append(e); out.append(u)
FULL.write_text("\n".join(out)+"\n", encoding='utf-8')
print(f"WROTE full_ca_us {len(flex)} - all have guide + english")

# PEI final_60
pei_keys=["cbc pei","compass","ctv atlantic","global halifax","global maritimes","cbc news","ctv news","cp24","global news"]
pri=[c for c in flex if any(k in c[0].lower() for k in pei_keys)]
oth=[c for c in flex if c not in pri]
final=[f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]
for e,u in pri+oth:
    if len(final)>=122: break
    final.append(e); final.append(u)
FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE PEI final_60 {len(final)//2}")
print("DONE")
