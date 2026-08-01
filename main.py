from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json
from io import BytesIO

app = FastAPI()

# Master sources - direct dumps from Matt (still Samsung/Pluto/Plex direct data)
SOURCES = {
    "samsung": "https://i.mjh.nz/SamsungTVPlus/.channels.json.gz",
    "pluto": "https://i.mjh.nz/PlutoTV/.channels.json.gz",
    "plex": "https://i.mjh.nz/Plex/.channels.json.gz",
}
EPG_URLS = {
    "samsung": "https://i.mjh.nz/SamsungTVPlus/ca.xml.gz",
    "pluto": "https://i.mjh.nz/PlutoTV/ca.xml.gz",
    "plex": "https://i.mjh.nz/Plex/ca.xml.gz",
}

def load_channels(service):
    r = requests.get(SOURCES[service], timeout=30)
    data = json.loads(gzip.decompress(r.content).decode() if r.content[:2]==b'\x1f\x8b' else r.content.decode())
    slug = data.get('slug', '{id}')
    regions = data.get('regions', {})
    ca = regions.get('CA') or regions.get('ca') or {}
    chans = ca.get('channels', {})
    # Some services use uppercase region key differently
    if not chans and 'all' in regions:
        # fallback search CA inside
        chans = {k:v for k,v in regions.get('all',{}).get('channels',{}).items() if 'CA' in str(v.get('regions','')) or True}
        # Actually use CA region if exists else all
        if 'CA' in regions:
            chans = regions['CA']['channels']
    return chans, slug, data

def build_m3u(service):
    chans, slug_t, _ = load_channels(service)
    prefix = {"samsung":"SamsungTVPlus","pluto":"PlutoTV","plex":"Plex"}[service]
    m3u = ""
    for k in sorted(chans.keys(), key=lambda x: chans[x].get('chno',9999)):
        ch = chans[k]
        if ch.get('license_url'): continue
        name = ch.get('name','').replace('"',"'").replace(',',"")
        logo = ch.get('logo','')
        group = ch.get('group', service.upper())
        chno = ch.get('chno','')
        url = f"https://jmp2.uk/{prefix}/{k}.m3u8"
        m3u += f'#EXTINF:-1 tvg-id="{k}" tvg-logo="{logo}" group-title="{group}" tvg-chno="{chno}",{name}\n{url}\n'
    return m3u, len(chans)

@app.get("/")
def root():
    return {"samsung-ca":"/samsung-ca.m3u", "pluto-ca":"/pluto-ca.m3u", "plex-ca":"/plex-ca.m3u", "MASTER":"/all-ca.m3u"}

@app.get("/samsung-ca.m3u")
def samsung():
    m3u, c = build_m3u("samsung")
    return PlainTextResponse(f'#EXTM3U url-tvg="https://motel-r45n.onrender.com/samsung-ca.xml"\n{m3u}', media_type="application/vnd.apple.mpegurl")

@app.get("/pluto-ca.m3u")
def pluto():
    m3u, c = build_m3u("pluto")
    return PlainTextResponse(f'#EXTM3U url-tvg="https://motel-r45n.onrender.com/pluto-ca.xml"\n{m3u}', media_type="application/vnd.apple.mpegurl")

@app.get("/plex-ca.m3u")
def plex():
    m3u, c = build_m3u("plex")
    return PlainTextResponse(f'#EXTM3U url-tvg="https://motel-r45n.onrender.com/plex-ca.xml"\n{m3u}', media_type="application/vnd.apple.mpegurl")

@app.get("/all-ca.m3u")
def all_ca():
    s_m3u, s_c = build_m3u("samsung")
    p_m3u, p_c = build_m3u("pluto")
    x_m3u, x_c = build_m3u("plex")
    combined = f'#EXTM3U url-tvg="https://motel-r45n.onrender.com/all-ca.xml"\n{s_m3u}{p_m3u}{x_m3u}'
    return PlainTextResponse(combined, media_type="application/vnd.apple
