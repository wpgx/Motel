import re, requests
from pathlib import Path

FINAL = Path("final_60.m3u")
FULL_CA_US = Path("full_ca_us.m3u")
BACKUP_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info" tvg-logo="https://motel.deecee.ca/logo.png", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19 LibVLC/3.0.19"}
TIMEOUT = 8
EPG_URLS = "https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml,https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz"
PRIORITY_NEWS = ["cbc news", "ctv news", "global news", "cp24", "cbc winnipeg", "ctv winnipeg", "citynews", "ctv ", "cbc "]

def parse_m3u_text(text):
    lines=text.splitlines()
    chans=[]
    for i,l in enumerate(lines):
        if l.strip().startswith('#EXTINF'):
            url=lines[i+1].strip() if i+1 < len(lines) else ''
            if url.startswith("http"): chans.append((l.strip(),url))
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

def is_alive(url):
    if url==WELCOME_URL: return True
    if '.mp4' in url.lower(): return False
    try:
        r=requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        if r.status_code in (403,401,404,500,502,503): return False
        if 'AccessDenied' in r.text or '403 Forbidden' in r.text: return False
        if '#EXTM3U' not in r.text and '#EXT-X-STREAM' not in r.text and '#EXTINF' not in r.text:
            if len(r.text) < 800: return False
        return True
    except:
        return False

def main():
    print("=== checker_1 - FULL = full source + EPG, FINAL = tested alive ===")
    print
