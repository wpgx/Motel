import re, requests
from pathlib import Path

FINAL = Path("final_60.m3u")
BACKUP = Path("backup_pool.m3u")
MASTER = Path("master_pool.m3u")
ALT1 = Path("Cairns_FINAL_MOTEL_PLUTO_CA_230_PLUS_CBC.m3u")
ALT2 = Path("PLUTO_CA_WORKING_ONLY.m3u")

TIMEOUT = 10
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" tvg-chno="1" tvg-name="Cairns Welcome" group-title="Motel Info", Cairns Motel - Welcome to Summerside, PEI'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19 LibVLC/3.0.19"}

def parse_m3u(path):
    if not path.exists(): return []
    lines = path.read_text(errors='ignore').splitlines()
    chans = []
    for i, l in enumerate(lines):
        l = l.strip()
        if l.startswith('#EXTINF'):
            url = lines[i+1].strip() if i+1 < len(lines) else ''
            if url.startswith("http"):
                chans.append((l, url))
    return chans

def strip_number(ext_line):
    if ',' not in ext_line: return ext_line
    head, title = ext_line.rsplit(',', 1)
    title_clean = re.sub(r'^\s*\d+\s*-\s*', '', title.strip())
    return f'{head}, {title_clean}'

def is_welcome(ext, url):
    low = (ext + url).lower()
    return 'welcome' in low or 'tvg-id="welcome"' in low or 'welcome.m3u8' in low

def is_valid_hls(url):
    u = url.lower().strip()
    if not u.startswith("http"): return False
    if ".m3u8" not in u: return False
    if u.endswith((".mp4", ".mkv", ".avi", ".mov")): return False
    return True

def is_alive(url):
    if url == WELCOME_URL: return True
    if not is_valid_hls(url): return False
    try:
        r = requests.head(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        if r.status_code in (403, 401, 404): return False
        if r.status_code in (200, 301, 302): return True
        r2 = requests.get(url, timeout=5, headers=HEADERS, stream=True)
        return r2.status_code in (200, 301, 302)
    except:
        return False

def load_spare_tiers():
    tiers = []
    t1 = [c for c in parse_m3u(BACKUP) if is_valid_hls(c[1]) and not is_welcome(c[0], c[1])]
    print(f"Tier1 backup_pool.m3u: {len(t1)}")
    tiers.append(t1)
    t2 = [c for c in parse_m3u(MASTER) if is_valid_hls(c[1]) and not is_welcome(c[0], c[1])]
    print(f"Tier2 master_pool.m3u: {len(t2)}")
    if t2: tiers.append(t2)
    for alt_path in [ALT1, ALT2]:
        alt = [c for c in parse_m3u(alt_path) if is_valid_hls(c[1]) and not is_welcome(c[0], c[1])]
        if alt:
            print(f"Tier3 {alt_path.name}: {len(alt)}")
            tiers.append(alt)
            if sum(len(t) for t in tiers) > 500: break
    return tiers

def main():
    print("=== Cairns Motel - ONLY m3u8 Auto Heal ===")
    final = parse_m3u(FINAL)
    cleaned_final = [(e,u) for e,u in final if not is_welcome(e,u) and is_valid_hls(u)]
    print(f"Current final_60.m3u: {len(cleaned_final)} good m3u8")
    tiers = load_spare_tiers()
    final_urls = {u for _,u in cleaned_final}
    tiers = [[(e,u) for e,u in tier if u not in final_urls] for tier in tiers]
    print(f"Total spares: {sum(len(t) for t in tiers)}")

    new_list = ['#EXTM3U url-tvg="https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"']
    new_list.append(WELCOME_EXT)
    new_list.append(WELCOME_URL)
    ch_no = 2
    tier_pointers = [0]*len(tiers)

    def get_next_spare():
        for ti, tier in enumerate(tiers):
            while tier_pointers[ti] < len(tier):
                e,u = tier[tier_pointers[ti]]
                tier_pointers[ti] += 1
                if is_alive(u):
                    return e,u, ti+1
        return None

    for ext, url in cleaned_final:
        if is_alive(url):
            c_ext = strip_number(ext)
            c_ext = re.sub(r'tvg-chno="[^"]*"', f'tvg-chno="{ch_no}"', c_ext) if 'tvg-chno=' in c_ext else c_ext.replace('#EXTINF:', f'#EXTINF: tvg-chno="{ch_no}" ', 1)
            new_list.append(c_ext); new_list.append(url); ch_no += 1
        else:
            print(f"DEAD/403: {ext.split(',')[-1]}")
            spare = get_next_spare()
            if spare:
                se, su, tier_used = spare
                se_clean = strip_number(se)
                se_clean = re.sub(r'tvg-chno="[^"]*"', f'tvg-chno="{ch_no}"', se_clean) if 'tvg-chno=' in se_clean else se_clean.replace('#EXTINF:', f'#EXTINF: tvg-chno="{ch_no}" ', 1)
                new_list.append(se_clean); new_list.append(su)
                print(f" Replaced Tier{tier_used}: {se_clean.split(',')[-1]}")
                ch_no += 1

    while ch_no <= 61 and (spare := get_next_spare()):
        se, su, tier_used = spare
        se_clean = strip_number(se)
        se_clean = re.sub(r'tvg-chno="[^"]*"', f'tvg-chno="{ch_no}"', se_clean) if 'tvg-chno=' in se_clean else se_clean.replace('#EXTINF:', f'#EXTINF: tvg-chno="{ch_no}" ', 1)
        new_list.append(se_clean); new_list.append(su); ch_no += 1

    FINAL.write_text('\n'.join(new_list)+'\n')
    print(f"DONE - {len(new_list)//2} channels - ONLY m3u8 - Welcome Ch1 locked")

if __name__ == "__main__":
    main()
