from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json, re

app = FastAPI()

SAMSUNG_APP = 'https://i.mjh.nz/SamsungTVPlus/.channels.json.gz'
PLUTO_APP = 'https://i.mjh.nz/PlutoTV/.channels.json.gz'
PLEX_APP = 'https://i.mjh.nz/Plex/.channels.json.gz'

def fetch_gz_json(url):
    r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    data = r.content
    if data[:2]==b'\x1f\x8b':
        data = gzip.decompress(data)
    return json.loads(data.decode('utf-8'))

def fetch_gz_text(url):
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
        if ch.get('license_url'):
            continue
        out.append({
            "id": f"samsung-{k}",
            "name": ch.get('name','Samsung').replace('"',"'"),
            "logo": ch.get('logo',''),
            "group": ch.get('group','Samsung CA'),
            "chno": ch.get('chno',''),
            "url": f"https://jmp2.uk/{slug_t.format(id=k)}"
        })
    return out

def get_pluto_ca():
    try:
        data = fetch_gz_json(PLUTO_APP)
        ca = data['regions'].get('CA',{}).get('channels',{})
        if not ca:
            ca = data['regions'].get('ca',{}).get('channels',{})
        out=[]
        for k,ch in ca.items():
            out.append({
                "id": f"pluto-{k}",
                "name": ch.get('name','Pluto').replace('"',"'"),
                "logo": ch.get('logo',''),
                "group": ch.get('group','Pluto CA'),
                "chno": ch.get('chno',''),
                "url": f"https://jmp2.uk/PlutoTV/{k}.m3u8"
            })
        return out
    except:
        return []

def get_plex_ca():
    try:
        data = fetch_gz_json(PLEX_APP)
        ca = data['regions'].get('CA',{}).get('channels',{})
        if not ca:
            ca = data['regions'].get('ca',{}).get('channels',{})
        out=[]
        for k,ch in ca.items():
            out.append({
                "id": f"plex-{k}",
                "name": ch.get('name','Plex').replace('"',"'"),
                "logo": ch.get('logo',''),
                "group": ch.get('group','Plex CA'),
                "chno": ch.get('chno',''),
                "url": f"https://jmp2.uk/Plex/{k}.m3u8"
            })
        return out
    except:
        return []

def build_m3u(channels):
    m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/all-ca.xml"\n'
    for ch in channels:
        name = ch['name'].replace(',',"")
        m3u += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" group-title="{ch["group"]}" tvg-chno="{ch["chno"]}",{name}\n{ch["url"]}\n'
    return m3u

@app.get("/")
def root():
    return {"master":"/all-ca.m3u", "guide":"/all-ca.xml"}

@app.get("/samsung-ca.m3u")
def samsung_m3u():
    return PlainTextResponse(build_m3u(get_samsung_ca()), media_type="application/vnd.apple.mpegurl")

@app.get("/pluto-ca.m3u")
def pluto_m3u():
    return PlainTextResponse(build_m3u(get_pluto_ca()), media_type="application/vnd.apple.mpegurl")

@app.get("/plex-ca.m3u")
def plex_m3u():
    return PlainTextResponse(build_m3u(get_plex_ca()), media_type="application/vnd.apple.mpegurl")

@app.get("/all-ca.m3u")
def all_ca_m3u():
    all_ch = get_samsung_ca() + get_pluto_ca() + get_plex_ca()
    return PlainTextResponse(build_m3u(all_ch), media_type="application/vnd.apple.mpegurl")

@app.get("/all-ca.xml")
def all_ca_xml():
    parts=[]
    for url in [
        'https://i.mjh.nz/SamsungTVPlus/ca.xml.gz',
        'https://i.mjh.nz/PlutoTV/ca.xml.gz',
        'https://i.mjh.nz/Plex/ca.xml.gz'
    ]:
        data = fetch_gz_text(url)
        if data:
            parts.append(data)
    merged = b'<?xml version="1.0" encoding="UTF-8"?><tv>'
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
def samsung_xml():
    d = fetch_gz_text('https://i.mjh.nz/SamsungTVPlus/ca.xml.gz')
    return Response(content=d or b"<tv></tv>", media_type="application/xml")

@app.get("/pluto-ca.xml")
def pluto_xml():
    d = fetch_gz_text('https://i.mjh.nz/PlutoTV/ca.xml.gz')
    return Response(content=d or b"<tv></tv>", media_type="application/xml")

@app.get("/plex-ca.xml")
def plex_xml():
    d = fetch_gz_text('https://i.mjh.nz/Plex/ca.xml.gz')
    return Response(content=d or b"<tv></tv>", media_type="application/xml")
