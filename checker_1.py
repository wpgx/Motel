import re, requests
from pathlib import Path

FINAL = Path("final_60.m3u")
FULL_CA_US = Path("full_ca_us.m3u")
BACKUP = Path("backup_pool.m3u")
TIMEOUT = 10

WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19 LibVLC/3.0.19"}

# LEGAL ONLY sources - iptv-org is free-to-air legal only
LEGAL_URLS = [
    "https://iptv-org.github.io/iptv/countries/ca.m3u",
    "https://iptv-org.github.io/iptv/countries/us.m3u"
]

def download_legal():
    print("=== Downloading LEGAL CA/US from iptv-org ===")
    all_lines = []
    total = 0
    for url in LEGAL_URLS:
        try:
            r = requests.get(url, timeout=30, headers=HEADERS)
            if r.status_code != 200: 
                print(f" FAIL {url} {r.status_code}")
                continue
            lines = r.text.splitlines()
            for l in lines:
                if l.startswith("#EXTM3U"): 
                    continue
                if not l.strip():
                    continue
                all_lines.append(l)
            cnt = r.text.count("#EXTINF")
            total += cnt
            print(f" OK {url} - {cnt} chans")
        except Exception as e:
            print(f" ERR {url}: {e}")
    
    epg_header = '#EXTM3U url-tvg="https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml"'
    text = epg_header + "\n" + "\n".join(all_lines) + "\n"
    FULL_CA_US.write_text(text, encoding='utf-8')
    print(f" LEGAL full_ca_us.m3u built: {text.count('#EXTINF')} chans -> {FULL_CA_US}")
    return text

def parse_m3u(path):
    if not path.exists(): 
        return []
    lines=path.read_text(errors='ignore').splitlines()
    chans=[]
    for i,l in enumerate(lines):
        l=l.strip()
        if l.startswith('#EXTINF'):
            url=lines[i+1].strip() if i+1 < len(lines) else ''
            if url.startswith("http"): 
                chans.append((l,url))
    return chans

def clean_no_numbers(ext):
    if ',' not in ext: 
        return ext
    head,title=ext.rsplit(',',1)
    title=re.sub(r'^\s*\d+\s*[-\)\.]\s*','',title.strip())
    title=re.sub(r'^\s*\d+\s+','',title.strip())
    head=re.sub(r'\s*tvg-chno="[^"]*"\s*',' ',head)
    head=re.sub(r'#EXTINF:[^\s]*','#EXTINF:-1',head)
    head=re.sub(r'\s+',' ',head).strip()
    return f"{head}, {title}"

def is_welcome(e,u): 
    return 'welcome' in (e+u).lower()

def is_alive(url):
    if url==WELCOME_URL: 
        return True
    if '.mp4' in url.lower():
        return False
    try:
        r=requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True, stream=True)
        if r.status_code in (403,401,404,500,502,503): 
            return False
        # read a chunk
        chunk = ""
        try:
            chunk = r.text[:5000]
        except:
            chunk = ""
        if '#EXTM3U' in chunk or '#EXT-X-STREAM' in chunk or '#EXTINF' in chunk:
            return True
        if len(chunk) < 500:
            return False
        # if blocked page
        if 'AccessDenied' in chunk or '403 Forbidden' in chunk:
            return False
        return True
    except:
        return False

def main():
    print("=== checker_legal - LEGAL ONLY CA/US ===")
    download_legal()
    
    final=parse_m3u(FINAL)
    pool=parse_m3u(FULL_CA_US)
    
    print(f"Start final_60: {len(final)} chans")
    print(f"Pool: {len(pool)} legal chans")

    new_list=['#EXTM3U url-tvg="https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml"']
    new_list.append(WELCOME_EXT)
    new_list.append(WELCOME_URL)

    pool_urls = {u for _,u in pool}
    used = set([WELCOME_URL])
    pool_idx=0

    for ext,url in final:
        if is_welcome(ext,url): 
            continue
        if url in used:
            continue
        if is_alive(url):
            new_list.append(clean_no_numbers(ext))
            new_list.append(url)
            used.add(url)
            print(f" KEEP: {ext.split(',')[-1]}")
        else:
            print(f" DEAD: {ext.split(',')[-1]} - replacing")
            while pool_idx < len(pool):
                se,su = pool[pool_idx]
                pool_idx+=1
                if su in used:
                    continue
                if is_alive(su):
                    new_list.append(se)
                    new_list.append(su)
                    used.add(su)
                    print(f"  -> Replaced with {se.split(',')[-1]}")
                    break

    # fill up to 60 if needed
    while len(new_list)//2 < 61 and pool_idx < len(pool):
        se,su = pool[pool_idx]
        pool_idx+=1
        if su not in used and is_alive(su):
            new_list.append(se)
            new_list.append(su)
            used.add(su)

    FINAL.write_text('\n'.join(new_list)+'\n', encoding='utf-8')
    print(f"\nDONE - {len(new_list)//2} chans in final_60.m3u (legal only)")
    print(f"DONE - {FULL_CA_US.read_text().count('#EXTINF')} chans in full_ca_us.m3u")

if __name__=="__main__":
    main()
