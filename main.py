from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json, time

app = FastAPI()
CACHE = {}

APP_URL = 'https://i.mjh.nz/SamsungTVPlus/.channels.json.gz'
EPG_URL = 'https://i.mjh.nz/SamsungTVPlus/{region}.xml.gz'
PLAYBACK_URL = 'https://jmp2.uk/{slug}'

PLEX_CH_URL = 'https://i.mjh.nz/PlexTV/.channels.json.gz'
PLEX_EPG_URL = 'https://i.mjh.nz/PlexTV/{region}.xml.gz'
PLEX_PLAY_URL = 'https://jmp2.uk/{slug}'

def get_samsung():
    if 'samsung' in CACHE and time.time() - CACHE['samsung_t'] < 300:
        return CACHE['samsung']
    r = requests.get(APP_URL, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    data = json.loads(gzip.decompress(r.content).decode('utf-8'))
    CACHE['samsung'] = data
    CACHE['samsung_t'] = time.time()
    return data

def get_plex():
    if 'plex' in CACHE and time.time() - CACHE['plex_t'] < 300:
        return CACHE['plex']
    r = requests.get(PLEX_CH_URL, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    data = json.loads(gzip.decompress(r.content).decode('utf-8'))
    CACHE['plex'] = data
    CACHE['plex_t'] = time.time()
    return data

# === SAMSUNG CA - WORKING - DO NOT TOUCH ===
@app.get("/samsung-ca.m3u")
def samsung_m3u():
    data = get_samsung()
    ca = data['regions']['CA']['channels']
    slug_t = data.get('slug','SamsungTVPlus/{id}.m3u8')
    m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/samsung-ca.xml"\n'
    for k in sorted(ca.keys(), key=lambda x: ca[x].get('chno',9999)):
        ch=ca[k]
        if ch.get('license_url'): continue
        name = ch.get('name','').replace('"',"'").replace(',',"")
        m3u += f'#EXTINF:-1 tvg-id="samsung-{k}" tvg-logo="{ch.get("logo","")}" group-title="{ch.get("group","Samsung")}" tvg-chno="{ch.get("chno","")}",{name}\nhttps://jmp2.uk/{slug_t.format(id=k)}\n'
    return PlainTextResponse(m3u, media_type="text/plain")

@app.get("/samsung-ca.xml")
def samsung_xml():
    r = requests.get('https://i.mjh.nz/SamsungTVPlus/ca.xml.gz', timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    data = gzip.decompress(r.content) if r.content[:2]==b'\x1f\x8b' else r.content
    return Response(content=data, media_type="application/xml")

# === PLEX CA - NEW ===
@app.get("/plex-ca.m3u")
def plex_m3u():
    try:
        data = get_plex()
        slug_t = data.get('slug','PlexTV/{id}.m3u8')
        ca = data['regions'].get('CA', {}).get('channels', {})
        if not ca: # fallback to all if no CA
            ca = data['regions'].get('US', {}).get('channels', {})
        m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/plex-ca.xml"\n'
        for k in sorted(ca.keys(), key=lambda x: ca[x].get('chno',9999)):
            ch=ca[k]
            if ch.get('license_url'): continue
            name = ch.get('name','').replace('"',"'").replace(',',"")
            m3u += f'#EXTINF:-1 tvg-id="plex-{k}" tvg-logo="{ch.get("logo","")}" group-title="{ch.get("group","Plex")}" tvg-chno="{ch.get("chno","")}",{name}\nhttps://jmp2.uk/{slug_t.format(id=k)}\n'
        return PlainTextResponse(m3u, media_type="text/plain")
    except Exception as e:
        return PlainTextResponse(f"#PLEX ERROR {e}\n", media_type="text/plain")

@app.get("/plex-ca.xml")
def plex_xml():
    try:
        r = requests.get('https://i.mjh.nz/PlexTV/ca.xml.gz', timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code!= 200:
            r = requests.get('https://i.mjh.nz/PlexTV/us.xml.gz', timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        data = gzip.decompress(r.content) if r.content[:2]==b'\x1f\x8b' else r.content
        return Response(content=data, media_type="application/xml")
    except Exception as e:
        return PlainTextResponse(f"#PLEX EPG ERROR {e}", media_type="text/plain")

@app.get("/")
def root():
    return {"samsung": "/samsung-ca.m3u + /samsung-ca.xml", "plex": "/plex-ca.m3u + /plex-ca.xml"}
