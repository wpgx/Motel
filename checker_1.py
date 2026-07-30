import re, requests
from pathlib import Path

FINAL = Path("final_60.m3u")
FULL_CA_US = Path("full_ca_us.m3u")
BACKUP = Path("backup_pool.m3u")
TIMEOUT = 8

WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19 LibVLC/3.0.19"}

BLACKLIST = ["99991399", "magnolia", "adult", "xxx", "porn"]
BACKUP_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"

# EPG that actually has CBC/CTV/Global
EPG_URLS = "https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml,https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"

# Force these good Canadian news into final_60 if they are alive
PRIORITY_NEWS_KEYWORDS = ["cbc news", "ctv news", "global news", "cp24", "cbc winnipeg", "ctv winnipeg", "citynews"]

def parse_m3u_text(text):
    lines=text.splitlines()
    chans=[]
    for i,l in enumerate(lines):
        l=l.strip()
        if l.startswith('#EXTINF'):
            url=lines[i+1].strip() if i+1 < len(lines) else ''
            if url.startswith("http"): chans.append((l,url))
    return chans

def parse_m3u(path):
    if not path.exists(): return []
    return parse_m3u_text(path.read_text(errors='ignore'))

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
        if r.status_code in (403,401,404,500,502,503): return False
        if 'AccessDenied' in r.text or '403 Forbidden' in r.text: return False
        if '#EXTM3U' not in r.text and '#EXT-X-STREAM' not in r.text and '#EXTINF' not in r.text:
            if len(r.text) < 1000: return False
        # check child
        m=re.search(r'(https://[^\s"\']+?\.m3u8[^\s"\']*)', r.text)
        if m:
            child=m.group(1)
            try:
                r2=requests.get(child, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
                if r2.status_code in (403,401,404): return False
            except:
                return False
        return True
    except:
        return False

def download_and_build_full():
    print(f"=== Downloading {BACKUP_URL} ===")
    r = requests.get(BACKUP_URL, timeout=30, headers=HEADERS)
    if r.status_code != 200:
        print(f" FAIL {r.status_code}"); return []
    all_chans = parse_m3u_text(r.text)
    print(f" Total raw: {len(all_chans)}")

    # Filter CA/US
    kept = []
    for e,u in all_chans:
        low=e.lower()
        if is_blacklisted(e,u): continue
        if is_bad(u): continue
        if is_welcome(e,u): continue
        # Keep if it looks like CA/US
        if not ('usa' in low or 'canada' in low or 'united states' in low or 'group-title="us' in low or 'group-title="ca' in low or ' usa ' in low or ' canada ' in low or 'group-title="us:' in low or 'group-title="ca:' in low):
            continue
        kept.append((clean_no_numbers(e),u))
    
    print(f" Filtered CA/US: {len(kept)}")
    print(" Testing alive (this takes a few mins)...")

    alive = []
    for idx,(e,u) in enumerate(kept):
        if idx % 100 == 0:
            print(f"  {idx}/{len(kept)} checked, {len(alive)} alive")
        if is_alive(u):
            alive.append((e,u))

    print(f" ALIVE: {len(alive)} / {len(kept)}")

    # Build FULL with EPG
    epg_header = f'#EXTM3U url-tvg="{EPG_URLS}"'
    out_lines = [epg_header] + [x for pair in alive for x in pair]
    FULL_CA_US.write_text('\n'.join(out_lines)+'\n', encoding='utf-8')
    print(f" Wrote {FULL_CA_US} with {len(alive)} chans + guide")
    return alive

def main():
    print("=== checker_1 - FULL with guide + filter dead + priority CA news ===")
    alive_pool = download_and_build_full()

    final=parse_m3u(FINAL)
    cleaned=[]
    for e,u in final:
        if is_welcome(e,u): continue
        if is_blacklisted(e,u): 
            print(f"BLACKLIST REMOVE: {e.split(',')[-1]}"); continue
        if is_bad(u): continue
        cleaned.append((clean_no_numbers(e),u))

    # Find priority news from alive_pool
    priority = []
    remaining_pool = []
    for e,u in alive_pool:
        low = e.lower()
        if any(k in low for k in PRIORITY_NEWS_KEYWORDS):
            priority.append((e,u))
        else:
            remaining_pool.append((e,u))
    
    # dedup priority
    seen=set(); uniq_priority=[]
    for e,u in priority:
        if u not in seen:
            seen.add(u); uniq_priority.append((e,u))
    priority = uniq_priority[:8]  # take up to 8 good news
    print(f" Priority CA news found alive: {len(priority)}")
    for e,_ in priority: print(f"  - {e.split(',')[-1]}")

    final_urls={u for _,u in cleaned}
    # pool for replacements = priority + remaining, excluding already in final
    spares = [p for p in priority if p[1] not in final_urls] + [p for p in remaining_pool if p[1] not in final_urls]

    new_list=[f'#EXTM3U url-tvg="{EPG_URLS}"']
    new_list.append(WELCOME_EXT)
    new_list.append(WELCOME_URL)

    # First add priority news
    for e,u in priority:
        if u not in final_urls:
            new_list.append(e); new_list.append(u)
    
    # Then check existing final_60
    for ext,url in cleaned:
        if url in new_list: continue  # already added as priority
        if is_alive(url):
            new_list.append(ext); new_list.append(url)
        else:
            print(f"DEAD in final_60: {ext.split(',')[-1]} - REPLACING")
            # replace from spares
            while spares:
                se,su = spares.pop(0)
                if is_alive(su) and su not in new_list:
                    new_list.append(se); new_list.append(su)
                    print(f" -> Replaced with {se.split(',')[-1]}")
                    break

    # Fill to 60
    while len(new_list)//2 < 61 and spares:
        se,su = spares.pop(0)
        if su not in new_list and is_alive(su):
            new_list.append(se); new_list.append(su)

    FINAL.write_text('\n'.join(new_list)+'\n', encoding='utf-8')
    print(f"\nDONE final_60.m3u: {len(new_list)//2} chans (with {len(priority)} CA news + guide)")
    print(f"DONE full_ca_us.m3u: {len(alive_pool)} alive chans + guide")

if __name__=="__main__":
    main()
