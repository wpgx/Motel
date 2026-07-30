import re, requests
from pathlib import Path
FINAL = Path("final_60.m3u")
BACKUP = Path("backup_pool.m3u")
MASTER = Path("master_pool.m3u")
TIMEOUT = 8
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19 LibVLC/3.0.19"}

REMOTE_POOLS = {
    "https://i.mjh.nz/PlutoTV/ca.m3u8": Path("pluto_ca.m3u"),
    "https://i.mjh.nz/PlutoTV/us.m3u8": Path("pluto_us.m3u"),
    "https://i.mjh.nz/SamsungTVPlus/ca.m3u8": Path("samsung_ca.m3u"),
}

def download_pools():
    print("=== Downloading fresh Pluto / Samsung pools ===")
    for url, path in REMOTE_POOLS.items():
        try:
            r = requests.get(url, timeout=15, headers=HEADERS)
            if r.status_code == 200 and "#EXTINF" in r.text:
                path.write_text(r.text, encoding='utf-8')
                print(f" OK {path.name} - {r.text.count('#EXTINF')} chans")
            else:
                print(f" FAIL {url} - {r.status_code}")
        except Exception as e:
            print(f" ERR {url} - {e}")

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

def clean_no_numbers(ext):
    if ',' not in ext: return ext
    head,title = ext.rsplit(',',1)
    title = re.sub(r'^\s*\d+\s*[-\)\.]\s*', '', title.strip())
    title = re.sub(r'^\s*\d+\s+', '', title.strip())
    head = re.sub(r'\s*tvg-chno="[^"]*"\s*', ' ', head)
    head = re.sub(r'#EXTINF:[^\s]*', '#EXTINF:-1', head)
    head = re.sub(r'\s+', ' ', head).strip()
    return f"{head}, {title}"

def is_welcome(ext,url):
    low=(ext+url).lower()
    return 'welcome' in low

def is_bad(url):
    u=url.lower()
    if '.mp4' in u: return True
    if 'dai.google.com' in u: return True
    if '.m3u8' not in u: return True
    return False

def is_alive(url):
    if url==WELCOME_URL: return True
    if is_bad(url): return False
    try:
        # Use GET not HEAD - catches 403 that HEAD misses
        r=requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True, stream=True)
        if r.status_code in (403,401,404,500,502,503):
            print(f"  -> {r.status_code} dead: {url[:80]}")
            return False
        return True
    except Exception as e:
        print(f"  -> EXCEPTION dead: {e}")
        return False

def load_spares():
    spares=[]
    all_pools = [BACKUP, MASTER] + list(REMOTE_POOLS.values())
    for p in all_pools:
        if p.exists():
            for e,u in parse_m3u(p):
                if not is_bad(u) and not is_welcome(e,u):
                    spares.append((clean_no_numbers(e),u))
    seen=set(); uniq=[]
    for e,u in spares:
        if u not in seen:
            seen.add(u); uniq.append((e,u))
    return uniq

def main():
    print("=== SAFE checker - drops 403 dead, replaces from Pluto/Samsung ===")
    download_pools()
    final=parse_m3u(FINAL)
    cleaned=[]
    for e,u in final:
        if is_welcome(e,u): continue
        if is_bad(u):
            print(f"DROP bad/crash: {e.split(',')[-1]}")
            continue
        cleaned.append((clean_no_numbers(e),u))

    spares=load_spares()
    final_urls={u for _,u in cleaned}
    spares=[(e,u) for e,u in spares if u not in final_urls]
    print(f"Start: {len(cleaned)} good, spares: {len(spares)}")

    new_list=['#EXTM3U url-tvg="https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz, https://i.mjh.nz/PlutoTV/us.xml, https://i.mjh.nz/PlutoTV/ca.xml, https://i.mjh.nz/SamsungTVPlus/us.xml"']
    new_list.append(WELCOME_EXT)
    new_list.append(WELCOME_URL)
    spare_idx=0
    for ext,url in cleaned:
        if is_alive(url):
            new_list.append(ext); new_list.append(url)
        else:
            print(f"DEAD: {ext.split(',')[-1]} - REPLACING")
            replaced=False
            while spare_idx < len(spares):
                se,su = spares[spare_idx]; spare_idx+=1
                if is_alive(su):
                    new_list.append(se); new_list.append(su)
                    print(f" -> Replaced with {se.split(',')[-1]}")
                    replaced=True; break
                else:
                    print(f"  spare dead, skipping {se.split(',')[-1]}")
            if not replaced:
                print(" -> No spare found, dropping")

    while len(new_list)//2 < 60 and spare_idx < len(spares):
        se,su = spares[spare_idx]; spare_idx+=1
        if su not in new_list and is_alive(su):
            new_list.append(se); new_list.append(su)

    FINAL.write_text('\n'.join(new_list)+'\n')
    print(f"DONE - {len(new_list)//2} chans - 403s dropped and replaced")

if __name__=="__main__":
    main()
