from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json
from io import BytesIO

app = FastAPI()

APP_URL = 'https://i.mjh.nz/SamsungTVPlus/.channels.json.gz'
EPG_URL = 'https://i.mjh.nz/SamsungTVPlus/{region}.xml.gz'
PLAYBACK_URL = 'https://jmp2.uk/{slug}'

def get_data():
    r = requests.get(APP_URL, timeout=20)
    r.raise_for_status()
    return json.loads(gzip.GzipFile(fileobj=BytesIO(r.content)).read())

@app.get("/")
def root():
    return {"status":"direct samsung scraper", "ca_playlist":"/samsung-ca.m3u", "ca_guide":"/samsung-ca.xml"}

@app.get("/samsung-ca.m3u")
def samsung_ca():
    data = get_data()
    slug_template = data.get('slug', '{id}')
    regions_data = data.get('regions', {})
    ca = regions_data.get('CA') or regions_data.get('ca') or {}
    channels = ca.get('channels', {})

    m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/samsung-ca.xml"\n'
    # Sort by channel number like matt does
    for key in sorted(channels.keys(), key=lambda x: channels[x].get('chno', 9999)):
        ch = channels[key]
        if ch.get('license_url'):
            continue
        name = ch.get('name','Samsung')
        logo = ch.get('logo','')
        group = ch.get('group','Samsung CA')
        chno = ch.get('chno')
        cid = f"samsung-{key}"
        url = PLAYBACK_URL.format(slug=slug_template.format(id=key))
        m3u += f'#EXTINF:-1 channel-id="{cid}" tvg-id="{key}" tvg-logo="{logo}" group-title="{group}" tvg-chno="{chno}",{name}\n{url}\n'
    return PlainTextResponse(m3u, media_type="application/vnd.apple.mpegurl")

@app.get("/samsung-ca.xml")
def samsung_ca_xml():
    r = requests.get(EPG_URL.format(region='ca'), timeout=30)
    # It may be.ca or CA - try both
    if r.status_code!= 200:
        r = requests.get(EPG_URL.format(region='CA'), timeout=30)
    if r.status_code!= 200:
        r = requests.get(EPG_URL.format(region='all'), timeout=30)
    xml = gzip.decompress(r.content) if r.content[:2] == b'\x1f\x8b' else r.content
    return Response(content=xml, media_type="application/xml")
