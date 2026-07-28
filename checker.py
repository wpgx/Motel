import re, requests
from pathlib import Path

FINAL = Path("final_60.m3u")
BACKUP = Path("backup_pool.m3u")
TIMEOUT=10

WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" tvg-name="Cairns Motel Welcome" group-title="Motel Info" tvg-logo="https://raw.githubusercontent.com/wpgx/Motel/main/welcome.jpg", Cairns Motel - Welcome to Summerside, PEI'
WELCOME_URL = 'https://raw.githubusercontent.com/wpgx/Motel/main/welcome.mp4'

def parse_m3u(path):
    lines=path.read_text(errors='ignore').splitlines()
    chans=[]
    for i,l in enumerate(lines):
        if l.startswith('#EXTINF'):
            url = lines[i+1] if i+1 < len(lines) else ''
            chans.append((l, url))
    return chans

def clean_title(ext_line):
    # removes "01 - Hallmark" -> "Hallmark"
    if ',' not in ext_line: return ext_line
    head, title = ext_line.rsplit(',', 1)
    title_clean = re.sub(r'^\d+\s*-\s*', '', title.strip())
    return f'{head}, {title_clean}'

def is_alive(url):
    if url == WELCOME_URL: return True
    try:
        headers = {"User-Agent": "VLC/3.0.19"}
        r = requests.get(url, timeout=TIMEOUT, headers=headers, stream=True, allow_redirects=True)
        return r.status_code in (200,301,302)
    except:
        return False

def main():
    final = parse_m3u(FINAL)
    backup = parse_m3u(BACKUP)
    final_urls = {u for _,u in final}
    spares = [(e,u) for e,u in backup if u not in final_urls and u!= WELCOME_URL]

    new_list=[f'#EXTM3U url-tvg="https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"']
    new_list.append(WELCOME_EXT)
    new_list.append(WELCOME_URL)

    replaced=0; spare_idx=0
    for ext,url in final:
        if url == WELCOME_URL: continue
        if is_alive(url):
            chosen_ext, chosen_url = clean_title(ext), url
        else:
            if spare_idx < len(spares):
                chosen_ext, chosen_url = clean_title(spares[spare_idx][0]), spares[spare_idx][1]
                spare_idx+=1; replaced+=1
            else:
                chosen_ext, chosen_url = clean_title(ext), url
        new_list.append(chosen_ext)
        new_list.append(chosen_url)

    FINAL.write_text('\n'.join(new_list))
    print(f"Done. Welcome is Ch1, Replaced {replaced}")

if __name__=="__main__":
    main()
