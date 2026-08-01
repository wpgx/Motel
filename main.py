from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json, os, time
from io import BytesIO

app = FastAPI()
CACHE = {}
CACHE_TIME = 300

APP_URL = 'https://i.mjh.nz/SamsungTVPlus/.channels.json.gz'
EPG_URL = 'https://i.mjh.nz/SamsungTVPlus/{region}.xml.gz'
PLAYBACK_URL = 'https://jmp2.uk/{slug}'

def get_data():
    now = time.time()
    if 'data' in CACHE and now - CACHE['data_time'] < CACHE_TIME:
        return CACHE['data']
    r = requests.get(APP_URL, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    data = json.loads(gzip.decompress(r.content).decode('utf-8'))
    CACHE['data'] = data
    CACHE['data_time'] = now
    return data

@app.get("/samsung-ca.m3u")
@app.get("/playlist.m3u8")
def playlist(request: Request, regions: str = "CA"):
    data = get_data()
    regions_list = [x.strip().lower() for x in regions.split(',')]

    channels = {}
    for reg in regions_list:
        for k,v in data['regions'].items():
            if k.lower() == reg or reg == 'all':
                channels.update(v.get('channels', {}))

    m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/samsung-ca.xml?regions=CA"\n'
    for key in sorted(channels.keys(), key=lambda x: channels[x].get('chno', 9999)):
        ch = channels[key]
        if ch.get('license_url'): continue
        name = ch['name']
        logo = ch.get('logo','')
        group = ch.get('group','Samsung')
        chno = ch.get('chno','')
        url = PLAYBACK_URL.format(slug=data['slug'].format(id=key))
        chno_str = f' tvg-chno="{chno}"' if chno else ''
        m3u += f'#EXTINF:-1 tvg-id="samsung-{key}" tvg-logo="{logo}" group-title="{group}"{chno_str},{name}\n{url}\n'
    return PlainTextResponse(m3u, media_type="text/plain")

@app.get("/samsung-ca.xml")
@app.get("/epg.xml")
def epg(regions: str = "CA"):
    url = EPG_URL.format(region=regions.split(',')[0].lower())
    r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    content = gzip.decompress(r.content) if r.content[:2]==b'\x1f\x8b' else r.content
    return Response(content=content, media_type="application/xml")

@app.get("/")
def status():
    data = get_data()
    html = "<h1>Samsung TV Plus - Working</h1>CA Channels: %d<br><br><a href='/samsung-ca.m3u'>/samsung-ca.m3u</a><br><a href='/samsung-ca.xml'>/samsung-ca.xml</a>" % len(data['regions'].get('CA',{}).get('channels',{}))
    return Response(content=html, media_type="text/html")
