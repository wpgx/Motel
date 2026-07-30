from pathlib import Path
POOL = Path("backup_pool.m3u")
FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")
EPG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'

def parse(txt):
    lines=txt.splitlines(); out=[]
    for i,l in enumerate(lines):
        if l.strip().startswith('#EXTINF') and i+1 < len(lines):
            u=lines[i+1].strip()
            if u.startswith("http"): out.append((l.strip(),u.strip()))
    return out

def is_english_only(ext):
    low=ext.lower()
    # block foreign
    block=["spanish","español","french","français","arabic","hindi","punjabi","urdu","tagalog","vietnamese","chinese","korean","portuguese","russian","german","italian","tamil","telugu","turkish"]
    for b in block:
        if b in low:
            return False
    # block iptv-org french canada channels (they have fr in tvg-id)
    if 'tvg-id="ca_' in low and 'french' in low: return False
    if 'tvg-language="fr' in low or 'tvg-language="es' in low: return False
    return True

print("CLEAN 2220 -> english only")
txt = FULL.read_text(errors='ignore') if FULL.exists() else POOL.read_text(errors='ignore')
chans = parse(txt)
print(f" before {len(chans)}")

seen=set(); flex=[]
for ext,url in chans:
    if url in seen: continue
    if not is_english_only(ext): continue
    seen.add(url)
    flex.append((ext,url))

print(f" after english filter {len(flex)}")

out=[f'#EXTM3U url-tvg="{EPG}"']
for e,u in flex: out.append(e); out.append(u)
FULL.write_text("\n".join(out)+"\n", encoding='utf-8')
print(f"WROTE full_ca_us {len(flex)} english only (keeps TSN no-guide)")

# rebuild final_60 as 65
news_keys=["cbc pei","compass","ctv atlantic","global halifax","global maritimes","cbc news","ctv news","cp24"]
sports_keys=["tsn","sportsnet","snet","espn"]

news=[c for c in flex if any(k in c[0].lower() for k in news_keys)]
sports=[c for c in flex if any(k in c[0].lower() for k in sports_keys) and c not in news]
others=[c for c in flex if c not in news and c not in sports]

final=[f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]
for e,u in news:
    if len(final) >= 30: break
    final.append(e); final.append(u)
for e,u in sports[:5]:
    final.append(e); final.append(u)
    print(f" +SPORT {e[:60]}")
while len(final) < 132 and others:
    e,u = others.pop(0)
    final.append(e); final.append(u)

FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final_60 as 65 chans - {len(final)//2}")
print("DONE")
