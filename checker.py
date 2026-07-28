import re, requests
from pathlib import Path

FINAL = Path("final_60.m3u")
BACKUP = Path("backup_pool.m3u")
TIMEOUT=10

WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" tvg-name="Cairns Motel Welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/welcome.jpg", Cairns Motel - Welcome to Summerside, PEI'
WELCOME_URL = 'https://motel.deecee.ca/welcome.mp4'

def parse_m3u(path):
    lines=path.read_text(errors='ignore').splitlines()
    chans=[]
    for i,l in enumerate(lines):
        if l.startswith('#EXTINF'):
            url = lines[i+1] if i+1 < len(lines) else ''
            chans.append((l, url))
    return chans

def strip_number(ext_line):
    if ',' not in ext_line:
        return ext_line
    head, title = ext_line.rsplit(',', 1)
    title_clean = re.sub(r'^\s*\d+\s*-\s*', '', title.strip())
    return f'{head}, {title_clean}'

def is_alive(url):
    if url == WELCOME_URL:
        return True
    try:
        headers = {"User-Agent": "VLC/3.0.19"}
        r = requests.get(url, timeout=TIMEOUT, headers=headers, stream=True)
        return r.status_code in (200,301,302)
    except:
        return False

def main():
    final = parse_m3u(FINAL)
    backup = parse_m3u(BACKUP)
    final_urls = {u for _,u in final}
    spares = [(e,u) for e,u in backup if u not in final_urls and u != WELCOME_URL]
    
    new_list=['#EXTM3U url-tvg="https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"']
    new_list.append(WELCOME_EXT)
    new_list.append(WELCOME_URL)
    
    spare_idx=0
    for ext,url in final:
        if url == WELCOME_URL: continue
        if is_alive(url):
            c_ext, c_url = ext, url
        else:
            if spare_idx < len(spares):
                c_ext, c_url = spares[spare_idx]
                spare_idx+=1
            else:
                c_ext, c_url = ext, url
        new_list.append(strip_number(c_ext))
        new_list.append(c_url)
        
    FINAL.write_text('\n'.join(new_list))
    print(f"Done - Welcome first, all numbers stripped")

if __name__=="__main__":
    main()
