from pathlib import Path
import requests
FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")
EPG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19"}

def parse(txt):
    lines=txt.splitlines(); out=[]
    for i,l in enumerate(lines):
        if l.strip().startswith('#EXTINF') and i+1 < len(lines):
            u=lines[i+1].strip()
            if u.startswith("http"): out.append((l.strip(),u.strip()))
    return out

def alive(url):
    if WELCOME_URL in url: return True
    try:
        r = requests.get(url, timeout=6, headers=HEADERS, stream=True)
        if r.status_code == 403 or r.status_code >= 400:
            print(f" 403 DEAD {url[:60]}")
            return False
        return True
    except:
        return False

flex = parse(FULL.read_text(errors='ignore'))
print(f" FULL {len(flex)}")

news_keys=["cbc pei","compass","ctv atlantic","global halifax","global maritimes","cbc news","ctv news","cp24","global news"]
sports_keys=["tsn","sportsnet","snet","espn"]

news=[c for c in flex if any(k in c[0].lower() for k in news_keys)]
sports=[c for c in flex if any(k in c[0].lower() for k in sports_keys) and c not in news]
others=[c for c in flex if c not in news and c not in sports]

final=[f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]

def add_until(src, target_total):
    for e,u in src:
        if len(final)//2 >= target_total: break
        if u in "\n".join(final): continue
        if alive(u):
            final.append(e); final.append(u)
            print(f" OK {e[:70]}")
        else:
            print(f" SKIP DEAD {e[:70]}")

# 15 news + 5 sports + 45 rest = 65 total (including welcome = 66 lines? actually 65 chans + welcome = 65)
add_until(news, 16) # welcome + 15 news
add_until(sports, 21) # +5 sports
add_until(others, 66) # to 65 chans + welcome

FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE final_60.m3u {len(final)//2} chans - 0 dead 403s")
