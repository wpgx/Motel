import re, requests
from pathlib import Path

FINAL = Path("final_60.m3u")
BACKUP = Path("backup_pool.m3u")
MASTER = Path("master_pool.m3u")
TIMEOUT = 10

WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19 LibVLC/3.0.19"}

# Blacklist - add any dead/geo-blocked ids here
BLACKLIST = ["99991399", "magnolia", "cinevault westerns"]  # you can add more lowercased strings

BACKUP_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
BACKUP_TMP = Path("freetv_all.m3u")
BACKUP_FILTERED = Path("freetv_ca_us.m3u")

def download_and_filter_backup():
    print(f"=== Downloading {BACKUP_URL} ===")
    try:
        r = requests.get(BACKUP_URL, timeout=30, headers=HEADERS)
        if r.status_code != 200:
            print(f" FAIL {r.status_code}")
            return
        BACKUP_TMP.write_text(r.text, encoding='utf-8', errors='ignore')
        print(f" OK {r.text.count('#EXTINF')} total")
        lines = r.text.splitlines()
        kept = []
        cnt=0
        for i,l in enumerate(lines):
            if l.startswith('#EXTM3U'):
                kept.append(l); continue
            if l.startswith('#EXTINF'):
                low=l.lower()
                if not ('usa' in low or 'canada' in low or 'united states' in low or 'group-title="us"' in low or 'group-title="ca"' in low): continue
                if 'adult' in low or 'xxx' in low or 'porn' in low: continue
                if any(b in low for b in BLACKLIST): continue
                url = lines[i+1].strip() if i+1 < len(lines) else ''
                if '.m3u8' not in url.lower(): continue
                if '.mp4' in url.lower() or 'dai.google.com' in url.lower(): continue
                kept.append(l); kept.append(url); cnt+=1
        BACKUP_FILTERED.write_text('\n'.join(kept)+'\n', encoding='utf-8')
        print(f" FILTERED to {cnt} CA/US -> {BACKUP_FILTERED.name}")
    except Exception as e:
        print(f" ERR {e}")

def parse_m3u(path):
    if not path.exists(): return []
    lines=path.read_text(errors='ignore').splitlines()
    chans=[]
    for i,l in enumerate(lines):
        l=l.strip()
        if l.startswith('#EXTINF'):
            url=lines[i+1].strip() if i+1 < len(lines) else ''
            if url.startswith("http"): chans.append((l,url))
    return chans

def clean_no_numbers(ext):
    if ',' not in ext: return ext
    head,title=ext.rsplit(',',1)
    title=re.sub(r'^\s*\d+\s*[-\)\.]\s*','',title.strip())
    title=re.sub(r'^\s*\d+\s+','',title.strip())
    head=re.sub(r'\s*tvg-chno="[^"]*"\s*',' ',head)
    head=re.sub(r'#EXTINF:[^\s]*','#EXTINF:-1',head)
    head=re.sub(r'\s+',' ',head).strip()
    return f"{head}, {title}"

def is_welcome(e,u): return 'welcome' in (e+u).lower()
def is_bad(u): 
    l=u.lower()
    return '.mp4' in l or 'dai.google.com' in l or '.m3u8' not in l
def is_blacklisted(e,u):
    low=(e+u).lower()
    return any(b in low for b in BLACKLIST)

def is_alive(url):
    if url==WELCOME_URL: return True
    if is_bad(url): return False
    try:
        r=requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        if r.status_code in (403,401,404,500,502,503):
            print(f"  -> {r.status_code} dead master: {url[:70]}")
            return False
        if '#EXTM3U' not in r.text and '#EXT-X-STREAM' not in r.text and '#EXTINF' not in r.text:
            if len(r.text) < 1000: 
                print(f"  -> not m3u8")
                return False
        m=re.search(r'(https://[^\s"\']+?\.m3u8[^\s"\']*)', r.text)
        if m:
            child=m.group(1)
            try:
                r2=requests.get(child, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
                if r2.status_code in (403,401,404):
                    print(f"  -> {r2.status_code} dead child GEO-BLOCK")
                    return False
                if 'AccessDenied' in r2.text or '403 Forbidden' in r2.text:
                    print(f"  -> child AccessDenied GEO-BLOCK")
                    return False
            except:
                return False
        return True
    except Exception as e:
        print(f"  -> EX {e}")
        return False

def load_spares():
    spares=[]
    for p in [BACKUP, MASTER, BACKUP_FILTERED]:
        if p.exists():
            for e,u in parse_m3u(p):
                if not is_bad(u) and not is_welcome(e,u) and not is_blacklisted(e,u):
                    spares.append((clean_no_numbers(e),u))
    seen=set(); uniq=[]
    for e,u in spares:
        if u not in seen:
            seen.add(u); uniq.append((e,u))
    return uniq

def main():
    print("=== checker - XUMO + FreeTV CA/US + blacklist + geo-check ===")
    download_and_filter_backup()
    final=parse_m3u(FINAL)
    cleaned=[]
    for e,u in final:
        if is_welcome(e,u): continue
        if is_blacklisted(e,u):
            print(f"BLACKLIST REMOVE: {e.split(',')[-1]}")
            continue
        if is_bad(u): 
            print(f"DROP bad: {e.split(',')[-1]}")
            continue
        cleaned.append((clean_no_numbers(e),u))

    spares=load_spares()
    final_urls={u for _,u in cleaned}
    spares=[(e,u) for e,u in spares if u not in final_urls]
    print(f"Start: {len(cleaned)} good, spares: {len(spares)}")

    new_list=['#EXTM3U url-tvg="https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"']
    new_list.append(WELCOME_EXT)
    new_list.append(WELCOME_URL)
    idx=0
    for ext,url in cleaned:
        if is_alive(url):
            new_list.append(ext); new_list.append(url)
        else:
            print(f"DEAD: {ext.split(',')[-1]} - REPLACING")
            repl=False
            while idx < len(spares):
                se,su=spares[idx]; idx+=1
                if is_alive(su):
                    new_list.append(se); new_list.append(su)
                    print(f" -> Replaced with {se.split(',')[-1]}")
                    repl=True; break
            if not repl:
                print(" -> No spare, dropping")

    while len(new_list)//2 < 60 and idx < len(spares):
        se,su=spares[idx]; idx+=1
        if su not in new_list and is_alive(su):
            new_list.append(se); new_list.append(su)

    FINAL.write_text('\n'.join(new_list)+'\n')
    print(f"DONE - {len(new_list)//2} chans - Magnolia removed")

if __name__=="__main__":
    main()
