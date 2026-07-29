import re, requests
from pathlib import Path

FINAL = Path("final_60.m3u")
BACKUP = Path("backup_pool.m3u")
MASTER = Path("master_pool.m3u")

TIMEOUT = 8
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" tvg-chno="1" tvg-name="Cairns Welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome to Summerside, PEI'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19 LibVLC/3.0.19"}

def parse_m3u(path):
    if not path.exists(): return []
    lines = path.read_text(errors='ignore').splitlines()
    chans=[]
    for i,l in enumerate(lines):
        l=l.strip()
        if l.startswith('#EXTINF'):
            url = lines[i+1].strip() if i+1 < len(lines) else ''
            if url.startswith("http"):
                chans.append((l,url))
    return chans

def clean_title(ext):
    # Remove any leading "12 - " or "12. " from display title, NO numbers in name
    if ',' not in ext: return ext
    head,title = ext.rsplit(',',1)
    title = title.strip()
    title = re.sub(r'^\s*\d+\s*[-\.)]\s*', '', title)  # "1 - ", "1. " etc
    title = re.sub(r'^\s*\d+\s+', '', title)  # "1 Hallmark"
    return f'{head}, {title}'

def is_welcome(ext,url):
    low=(ext+url).lower()
    return 'welcome' in low or 'tvg-id="welcome"' in low or 'welcome.m3u8' in low

def is_valid_hls(url):
    u=url.lower().strip()
    if not u.startswith("http"): return False
    if ".m3u8" not in u: return False
    if u.endswith((".mp4",".mkv",".avi",".mov")): return False
    return True

def is_alive(url):
    if url==WELCOME_URL: return True
    if not is_valid_hls(url): return False
    try:
        r=requests.head(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        if r.status_code in (403,401,404): return False
        if r.status_code in (200,301,302): return True
        r2=requests.get(url, timeout=5, headers=HEADERS, stream=True)
        if r2.status_code in (403,401,404): return False
        return True
    except:
        return True  # keep on error

def load_spares():
    spares=[]
    for p in [BACKUP, MASTER, Path("Cairns_FINAL_MOTEL_PLUTO_CA_230_PLUS_CBC.m3u"), Path("PLUTO_CA_WORKING_ONLY.m3u")]:
        if p.exists():
            for e,u in parse_m3u(p):
                if is_valid_hls(u) and not is_welcome(e,u):
                    spares.append((e,u))
    seen=set(); uniq=[]
    for e,u in spares:
        if u not in seen:
            seen.add(u); uniq.append((e,u))
    return uniq

def main():
    print("=== SAFE checker - ONLY m3u8 - NO numbers in titles ===")
    final=parse_m3u(FINAL)
    print(f"final_60.m3u: {len(final)}")
    cleaned=[]
    for e,u in final:
        if is_welcome(e,u): continue
        if not is_valid_hls(u):
            print(f"DROP mp4: {e.split(',')[-1]}")
            continue
        cleaned.append((clean_title(e),u))

    spares=load_spares()
    final_urls={u for _,u in cleaned}
    spares=[(clean_title(e),u) for e,u in spares if u not in final_urls]
    print(f"Spares: {len(spares)}")

    new_list=['#EXTM3U url-tvg="https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"']
    new_list.append(WELCOME_EXT)
    new_list.append(WELCOME_URL)

    spare_idx=0
    for ext,url in cleaned:
        if is_alive(url):
            new_list.append(ext); new_list.append(url)
        else:
            print(f"DEAD: {ext.split(',')[-1]}")
            replaced=False
            while spare_idx < len(spares):
                se,su = spares[spare_idx]; spare_idx+=1
                if is_alive(su):
                    new_list.append(se); new_list.append(su)
                    print(f" -> Replaced with {se.split(',')[-1]}")
                    replaced=True; break
            if not replaced:
                print(f" -> No spare, KEEPING")
                new_list.append(ext); new_list.append(url)

    FINAL.write_text('\n'.join(new_list)+'\n')
    print(f"DONE - {len(new_list)//2} channels - NO numbers in titles - Welcome Ch1 locked")

if __name__=="__main__":
    main()
