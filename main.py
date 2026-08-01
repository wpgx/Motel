from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json, re

app = FastAPI()

SAMSUNG_APP = 'https://i.mjh.nz/SamsungTVPlus/.channels.json.gz'

def fetch_gz_json(url):
    r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    data = r.content
    if data[:2]==b'\x1f\x8b':
        data = gzip.decompress(data)
    return json.loads(data.decode('utf-8'))

def fetch_text(url):
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            return r.text
    except:
        return None
    return None

def fetch_gz_bytes(url):
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code!=200:
            return None
        data = r.content
        if data[:2]==b'\x1f\x8b':
            data = gzip.decompress(data)
        return data
    except:
        return None

def get_samsung_ca():
    data = fetch_gz_json(SAMSUNG_APP)
    slug_t = data.get('slug','{id}')
    ca = data['regions'].get('CA',{}).get('channels',{})
    out=[]
    for k in sorted(ca.keys(), key=lambda x: ca[x].get('chno',9999)):
        ch=ca[k]
        if ch.get('license_url'): continue
        name = ch.get('name','Samsung').replace('"',"'").replace(',',"")
        logo = ch.get('logo','')
        group = ch.get('group','Samsung CA').replace('"',"'")
        chno = str(ch.get('chno','')).strip()
        url = f"https://jmp2.uk/{slug_t.format(id=k)}"
        # Sparkle-safe: only include chno if present
        if chno:
            ext = f'#EXTINF:-1 tvg-id="samsung-{k}" tvg-logo="{logo}" group-title="{group}" tvg-chno="{chno}",{name}'
        else:
            ext = f'#EXTINF:-1 tvg-id="samsung-{k}" tvg-logo="{logo}" group-title="{group}",{name}'
        out.append((ext, url))
    return out

def parse_m3u_to_list(m3u_text, prefix):
    if not m3u_text:
        return []
    lines = m3u_text.splitlines()
    out=[]
    for i in range(len(lines)):
        if lines[i].startswith('#EXTINF'):
            ext = lines[i].strip()
            # ensure tvg-id has prefix
            if 'tvg-id="' in ext:
                ext = ext.replace('tvg-id="', f'tvg-id="{prefix}-')
            else:
                ext = ext.replace('#EXTINF:-1', f'#EXTINF:-1 tvg-id="{prefix}-{i}"')
            # next line is url
            if i+1 < len(lines):
                url = lines[i+1].strip()
                if url.startswith('http'):
                    out.append((ext, url))
    return out

def get_pluto_ca():
    # Use Matt's stable CA m3u
    txt = fetch_text('https://i.mjh.nz/PlutoTV/ca.m3u8')
    if not txt:
        txt = fetch_text('https://i.mjh.nz/PlutoTV/all.m3u8')
    return parse_m3u_to_list(txt, 'pluto')

def get_plex_ca():
    txt = fetch_text('https://i.mjh.nz/Plex/ca.m3u8')
    if not txt:
        txt = fetch_text('https://i.mjh.nz/Plex/all.m3u8')
    return parse_m3u_to_list(txt, 'plex')

@app.get("/")
def root():
    return {"master":"/all-ca.m3u", "samsung":"/samsung-ca.m3u"}

@app.get("/samsung-ca.m3u")
def samsung_m3u():
    chans = get_samsung_ca()
    m3u = '#EXTM3U\n'
    for ext, url in chans:
        m3u += f"{ext}\n{url}\n"
    return PlainTextResponse(m3u, media_type="text/plain")

@app.get("/all-ca.m3u")
def all_ca_m3u():
    all_ch = []
    all_ch += get_samsung_ca()
    all_ch += get_pluto_ca()
    all_ch += get_plex_ca()
    m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/all-ca.xml"\n'
    for ext, url in all_ch:
        m3u += f"{ext}\n{url}\n"
    return PlainTextResponse(m3u, media_type="text/plain")

@app.get("/pluto-ca.m3u")
def pluto_m3u():
    chans = get_pluto_ca()
    m3u = '#EXTM3U\n'
    for ext, url in chans:
        m3u += f"{ext}\n{url}\n"
    return PlainTextResponse(m3u, media_type="text/plain")

@app.get("/plex-ca.m3u")
def plex_m3u():
    chans = get_plex_ca()
    m3u = '#EXTM3U\n'
    for ext, url in chans:
        m3u += f"{ext}\n{url}\n"
    return PlainTextResponse(m3u, media_type="text/plain")

@app.get("/all-ca.xml")
def all_xml():
    parts=[]
    for url in [
        'https://i.mjh.nz/SamsungTVPlus/ca.xml.gz',
        'https://i.mjh.nz/PlutoTV/ca.xml.gz',
        'https://i.mjh.nz/Plex/ca.xml.gz'
    ]:
        b = fetch_gz_bytes(url)
        if b:
            parts.append(b)
    merged = b'<?xml version="1.0"?><tv>'
    for p in parts:
        try:
            txt = p.decode('utf-8', errors='ignore')
            m = re.search(r'<tv[^>]*>(.*)</tv>', txt, re.DOTALL)
            if m:
                merged += m.group(1).encode('utf-8')
        except:
            continue
    merged += b'</tv>'
    return Response(content=merged, media_type="application/xml")

@app.get("/samsung-ca.xml")
def s_xml():
    b = fetch_gz_bytes('https://i.mjh.nz/SamsungTVPlus/ca.xml.gz')
    return Response(content=b or b"<tv></tv>", media_type="application/xml")
