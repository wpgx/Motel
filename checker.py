import re, requests
from pathlib import Path
FINAL = Path("final_60.m3u")
BACKUP = Path("backup_pool.m3u")
MASTER = Path("master_pool.m3u")
TIMEOUT = 8
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19 LibVLC/3.0.19"}

# Only working backup now - Free-TV IPTV
BACKUP_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
BACKUP_TMP = Path("freetv_all.m3u")
BACKUP_FILTERED = Path("freetv_ca_us.m3u")

def download_and_filter_backup():
    print(f"=== Downloading {BACKUP_URL} ===")
    try:
        r = requests.get(BACKUP_URL, timeout=30, headers=HEADERS)
        if r.status_code != 200:
            print(f" FAIL status {r.status_code}")
            return
        BACKUP_TMP.write_text(r.text, encoding='utf-8', errors='ignore')
        print(f" OK downloaded {r.text.count('#EXTINF')} total chans")

        # Filter to USA / Canada only
        lines = r.text.splitlines()
        kept = []
        kept_count = 0
        for i,l in enumerate(lines):
            if l.startswith('#EXTM3U'):
                kept.append(l)
                continue
            if l.startswith('#EXTINF'):
                low = l.lower()
                # Keep if USA or Canada in group or title
                is_ca_us = ('usa' in low or 'canada' in low or 'united states' in low or 'ca:' in low or 'us:' in low or 'group-title="us"' in low or 'group-title="ca"' in low)
                # If file uses country codes in group, keep also if no group but we want strict so require tag
                # For this list, group-title is usually country name - so we filter hard
                if not is_ca_us:
                    continue
                # Skip junk
                if 'adult' in low or 'xxx' in low or 'porn' in low:
                    continue
                url = lines[i+1].strip() if i+1 < len(lines) else ''
                if '.m3u8' not in url.lower():
                    continue
                if '.mp4' in url.lower() or 'dai.google.com' in url.lower():
                    continue
                kept.append(l)
                kept.append(url)
                kept_count+=1
        BACKUP_FILTERED.write_text('\n'.join(kept)+'\n', encoding='utf-8')
        print(f" FILTERED to {kept_count} CA/US chans -> {BACKUP_FILTERED.name}")
    except Exception as e:
        print(f" ERR downloading backup: {e}")

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
        r=requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True, stream=True)
        if r.status_code in (403,401,404,500,502,503):
            print(f"  -> {r.status_code} dead")
            return False
        return True
    except:
        return False

def load_spares():
    spares=[]
    # Use: your local backup/master + our new filtered Free-TV CA/US
    for p in [BACKUP, MASTER, BACKUP_FILTERED]:
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
    print("=== SAFE checker - XUMO main + Free-TV CA/US backup ===")
    download_and_filter_backup()
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
    print(f"Start: {len(cleaned)} good, spares: {len(spares)} (Free-TV CA/US)")

    # Keep ORIGINAL XUMO EPG only - removed dead i.mjh.nz links
    new_list=['#EXTM3U url-tvg="https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"']
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
            if not replaced:
                print(" -> No spare, dropping")

    while len(new_list)//2 < 60 and spare_idx < len(spares):
        se,su = spares[spare_idx]; spare_idx+=1
        if su not in new_list and is_alive(su):
            new_list.append(se); new_list.append(su)

    FINAL.write_text('\n'.join(new_list)+'\n')
    print(f"DONE - {len(new_list)//2} chans")

if __name__=="__main__":
    main()
