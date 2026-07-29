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

def strip_number(ext):
    if ',' not in ext: return ext
    head,title = ext.rsplit(',',1)
    title_clean = re.sub(r'^\s*\d+\s*-\s*','',title.strip())
    return f'{head}, {title_clean}'

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
        return True

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
    print("=== SAFE checker.py - keep working, only replace bad ===")
    final=parse_m3u(FINAL)
    print(f"final_60.m3u: {len(final)}")
    cleaned=[]
    for e,u in final:
        if is_welcome(e,u): continue
        if not is_valid_hls(u):
            print(f"DROP mp4: {e.split(',')[-1]}")
            continue
        cleaned.append((e,u))

    spares=load_spares()
    final_urls={u for _,u in cleaned}
    spares=[(e,u) for e,u in spares if u not in final_urls]
    print(f"Spares available: {len(spares)}")

    new_list=['#EXTM3U url-tvg="https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"']
    new_list.append(WELCOME_EXT)
    new_list.append(WELCOME_URL)
    ch_no=2
    spare_idx=0

    for ext,url in cleaned:
        if is_alive(url):
            c_ext=strip_number(ext)
            c_ext=re.sub(r'tvg-chno="[^"]*"', f'tvg-chno="{ch_no}"', c_ext) if 'tvg-chno=' in c_ext else c_ext.replace('#EXTINF:', f'#EXTINF: tvg-chno="{ch_no}" ',1)
            new_list.append(c_ext); new_list.append(url); ch_no+=1
        else:
            print(f"DEAD/403: {ext.split(',')[-1]}")
            replaced=False
            while spare_idx < len(spares):
                se,su = spares[spare_idx]; spare_idx+=1
                if is_alive(su):
                    se_clean=strip_number(se)
                    se_clean=re.sub(r'tvg-chno="[^"]*"', f'tvg-chno="{ch_no}"', se_clean) if 'tvg-chno=' in se_clean else se_clean.replace('#EXTINF:', f'#EXTINF: tvg-chno="{ch_no}" ',1)
                    new_list.append(se_clean); new_list.append(su)
                    print(f" -> Replaced with {se_clean.split(',')[-1]}")
                    ch_no+=1; replaced=True; break
            if not replaced:
                print(f" -> No spare, KEEPING original to avoid 1-channel bug")
                c_ext=strip_number(ext)
                c_ext=re.sub(r'tvg-chno="[^"]*"', f'tvg-chno="{ch_no}"', c_ext) if 'tvg-chno=' in c_ext else c_ext.replace('#EXTINF:', f'#EXTINF: tvg-chno="{ch_no}" ',1)
                new_list.append(c_ext); new_list.append(url); ch_no+=1

    FINAL.write_text('\n'.join(new_list)+'\n')
    print(f"DONE - {len(new_list)//2} channels - ONLY m3u8 - Welcome Ch1")

if __name__=="__main__":
    main()
