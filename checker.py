import re, requests
from pathlib import Path

FINAL = Path("final_60.m3u")
FULL_CA_US = Path("full_ca_us.m3u")
BACKUP = Path("backup_pool.m3u")
MASTER = Path("master_pool.m3u")
TIMEOUT = 10

WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19 LibVLC/3.0.19"}

BLACKLIST = ["99991399", "magnolia"]
BACKUP_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
BACKUP_TMP = Path("freetv_all.m3u")
BACKUP_FILTERED = Path("freetv_ca_us.m3u")

def download_and_filter_backup():
    print(f"=== Downloading {BACKUP_URL} ===")
    try:
        r = requests.get(BACKUP_URL, timeout=30, headers=HEADERS)
        if r.status_code != 200:
            print(f" FAIL {r.status_code}"); return
        BACKUP_TMP.write_text(r.text, encoding='utf-8', errors='ignore')
        print(f" OK {r.text.count('#EXTINF')} total")
        lines = r.text.splitlines()
        kept = []
        cnt=0
        for i,l in enumerate(lines):
            if l.startswith('#EXTINF'):
                low=l.lower()
                if not ('usa' in low or 'canada' in low or 'united states' in low or 'group-title="us' in low or 'group-title="ca' in low or ' usa ' in low or ' canada ' in low):
                    if 'group-title="us:' not in low and 'group-title="ca:' not in low and 'usa' not in low and 'canada' not in low:
                        continue
                if 'adult' in low or 'xxx' in low or 'porn' in low: continue
                if any(b in low for b in BLACKLIST): continue
                url = lines[i+1].strip() if i+1 < len(lines) else ''
                if '.m3u8' not in url.lower(): continue
                if '.mp4' in url.lower() or 'dai.google.com' in url.lower(): continue
                kept.append(l); kept.append(url); cnt+=1
        
        # Build FULL with dual EPG for guide
        epg_header = '#EXTM3U url-tvg="https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz,https://raw.githubusercontent.com/Free-TV/IPTV/master/epg.xml"'
        filtered_text = epg_header + '\n' + '\n'.join(kept) + '\n'
        BACKUP_FILTERED.write_text(filtered_text, encoding='utf-8')
        FULL_CA_US.write_text(filtered_text, encoding='utf-8')
        print(f" FILTERED to {cnt} CA/US -> full_ca_us.m3u with dual EPG")
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
def is_bad(u): return '.mp4' in u.lower() or 'dai.google.com' in u.lower() or '.m3u8' not in u.lower()
def is_blacklisted(e,u): return any(b in (e+u).lower() for b in BLACKLIST)

def is_alive(url):
    if url==WELCOME_URL: return True
    if is_bad(url): return False
    try:
        r=requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        if r.status_code in (403,401,404,500,502,503):
            print(f"  -> {r.status_code} dead master"); return False
        if '#EXTM3U' not in r.text and '#EXT-X-STREAM' not in r.text and '#EXTINF' not in r.text:
            if len(r.text) < 1000: return False
        m=re.search(r'(https://[^\s"\']+?\.m3u8[^\s"\']*)', r.text)
        if m:
            child=m.group(1)
            try:
                r2=requests.get(child, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
                if r2.status_code in (403,401,404): 
                    print(f"  -> {r2.status_code} dead child GEO-BLOCK"); return False
                if 'AccessDenied' in r2.text or '403 Forbidden' in r2.text: return False
            except:
                return False
        return True
    except:
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
    print("=== checker - XUMO final60 + full_ca_us with guide ===")
    download_and_filter_backup()
    final=parse_m3u(FINAL)
    cleaned=[]
    for e,u in final:
        if is_welcome(e,u): continue
        if is_blacklisted(e,u):
            print(f"BLACKLIST REMOVE: {e.split(',')[-1]}"); continue
        if is_bad(u): continue
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
            while idx < len(spares):
                se,su=spares[idx]; idx+=1
                if is_alive(su):
                    new_list.append(se); new_list.append(su)
                    print(f" -> Replaced with {se.split(',')[-1]}"); break

    while len(new_list)//2 < 60 and idx < len(spares):
        se,su=spares[idx]; idx+=1
        if su not in new_list and is_alive(su):
            new_list.append(se); new_list.append(su)

    FINAL.write_text('\n'.join(new_list)+'\n')
    print(f"DONE - {len(new_list)//2} chans final_60.m3u (XUMO EPG)")
    if FULL_CA_US.exists():
        print(f"DONE - {FULL_CA_US.read_text().count('#EXTINF')} chans full_ca_us.m3u (dual EPG)")

if __name__=="__main__":
    main()
