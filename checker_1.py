from pathlib import Path
import requests

FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")

WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" tvg-name="Cairns Motel" group-title="Motel Info",Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'

# BANNED - will never be in final_60
BANNED = ["deal or no deal", "wu tang", "wu-tang", "wutang"]

def parse(txt):
    lines = txt.splitlines()
    out = []
    for i,l in enumerate(lines):
        if l.strip().startswith('#EXTINF') and i+1 < len(lines):
            u = lines[i+1].strip()
            if u.startswith("http"):
                out.append((l.strip(), u.strip()))
    return out

def banned(name):
    low = name.lower()
    return any(b in low for b in BANNED)

def alive(url):
    if WELCOME_URL in url:
        return True
    if ".mp4" in url.lower():
        return False
    if "xumo" in url.lower() and "ads." in url.lower():
        return False
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent":"VLC/3.0.19"}, stream=True)
        if r.status_code in (403,404) or r.status_code >= 400:
            return False
        c = next(r.iter_content(2048), b"").decode(errors='ignore').lower()
        if "403" in c or "forbidden" in c or "accessdenied" in c:
            return False
        return True
    except:
        return False

flex = parse(FULL.read_text(errors='ignore'))
print(f"FULL {len(flex)}")

EPG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'
final = [f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]
seen = set([WELCOME_URL])

# 1. PEI / Maritimes - 12
for e,u in flex:
    if len(final)//2 >= 13: break
    if banned(e): continue
    if any(k in e.lower() for k in ["pei","compass","cbc","ctv atlantic","global halifax"]):
        if u not in seen and alive(u):
            final.append(e); final.append(u); seen.add(u)

# 2. NEWS - 20
for e,u in flex:
    if len(final)//2 >= 33: break
    if banned(e): continue
    if 'group-title="news"' in e.lower() or 'news' in e.lower():
        if u not in seen and alive(u):
            final.append(e); final.append(u); seen.add(u)

# 3. Fill to 65 - no banned
for e,u in flex:
    if len(final)//2 >= 65: break
    if banned(e): continue
    if u not in seen and alive(u):
        final.append(e); final.append(u); seen.add(u)

# Sparkle crash fix
final.append(WELCOME_EXT)
final.append(WELCOME_URL)
final.append("")

FINAL.write_text("\n".join(final)+"\n", encoding='utf-8')
print(f"WROTE {len(final)//2} channels - no deal/wutang, news kept, no 403")
