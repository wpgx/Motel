from pathlib import Path
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

print("FORCE CLEAN 2220")
txt = FULL.read_text(errors='ignore')
chans = parse(txt)
print(f" INPUT {len(chans)}")

clean=[]
for ext,url in chans:
    low=ext.lower()
    # KEEP if it looks like canadian/us english
    # DROP if obvious foreign country codes
    if any(x in low for x in [" tvg-id=\"mx_"," tvg-id=\"es_"," tvg-id=\"fr_"," tvg-id=\"ar_"," tvg-id=\"in_"," tvg-id=\"br_"," tvg-id=\"pt_"," tvg-id=\"de_"," tvg-id=\"it_"," tvg-id=\"tr_"]):
        continue
    if any(w in low for w in ["méxico","españa","france","deutsch","hindi","punjabi","urdu","arabic","turk"]):
        continue
    # keep everything else (including no-guide TSN which has tvg-id="ca_..." or no tvg-id but english name)
    clean.append((ext,url))

# dedup
seen=set(); flex=[]
for ext,url in clean:
    if url not in seen:
        seen.add(url)
        flex.append((ext,url))

print(f" CLEANED {len(flex)} (was 2220)")

out=[f'#EXTM3U url-tvg="{EPG}"']
for e,u in flex: out.append(e); out.append(u)
FULL.write_text("\n".join(out)+"\n", encoding='utf-8')

# final 65
news=["cbc pei","compass","ctv atlantic","global halifax","cbc news","ctv news"]
sports=["tsn","sportsnet"]
news_list=[c for c in flex if any(k in c[0].lower() for k in news)]
sports_list=[c for c in flex if any(k in c[0].lower() for k in sports)][:5]
others=[c for c in flex if c not in news_list and c not in sports_list]

final=[f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]
for e,u in news_list[:15]: final.append(e); final.append(u)
for e,u in sports_list: final.append(e); final.append(u)
for e,u in others:
    if len(final)>=132: break
    final.append(e); final.append(u)

FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE full {len(flex)} final {len(final)//2}")
print("DONE")
