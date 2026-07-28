import re, requests, sys
from pathlib import Path

FINAL = Path("final_60.m3u")
BACKUP = Path("backup_pool.m3u")
TIMEOUT=10

def parse_m3u(path):
    lines=path.read_text(errors='ignore').splitlines()
    chans=[]
    for i,l in enumerate(lines):
        if l.startswith('#EXTINF'):
            url = lines[i+1] if i+1 < len(lines) else ''
            chans.append((l, url))
    return chans

def is_alive(url):
    try:
        r=requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code in (200,302,301):
            return True
        # fallback get small chunk
        r=requests.get(url, timeout=TIMEOUT, stream=True)
        return r.status_code==200
    except:
        return False

def main():
    final = parse_m3u(FINAL)
    backup = parse_m3u(BACKUP)
    backup_urls = {u for _,u in backup}
    final_urls = {u for _,u in final}
    # pool of spares not in final
    spares = [(e,u) for e,u in backup if u not in final_urls]
    new_list=['#EXTM3U url-tvg="https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"']
    replaced=0
    spare_idx=0
    for ext,url in final:
        if is_alive(url):
            new_list.append(ext); new_list.append(url)
        else:
            # replace
            if spare_idx < len(spares):
                se, su = spares[spare_idx]; spare_idx+=1
                new_list.append(se); new_list.append(su)
                replaced+=1
                print(f"Replaced dead {ext.split(',')[-1]} -> {se.split(',')[-1]}")
            else:
                new_list.append(ext); new_list.append(url)
    FINAL.write_text('\n'.join(new_list))
    print(f"Done. Replaced {replaced} channels.")

if __name__=="__main__":
    main()
