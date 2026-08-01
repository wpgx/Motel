from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json, re

app = FastAPI()

CAN_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Forwarded-For": "142.112.195.1",
    "Accept-Language": "en-CA"
}

@app.get("/samsung-ca.m3u")
def samsung_m3u():
    url = 'https://i.mjh.nz/SamsungTVPlus/.channels.json.gz'
    r = requests.get(url, timeout=30, headers=CAN_HEADERS)
    raw = r.content
    if raw[:2]==b'\x1f\x8b':
        raw = gzip.decompress(raw)
    data = json.loads(raw.decode('utf-8'))
    slug_t = data.get('slug','SamsungTVPlus/{id}.m3u8')
    ca = data['regions']['CA']['channels']

    m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/samsung-ca.xml"\n'
    for k in sorted(ca.keys(), key=lambda x: ca[x].get('chno',9999)):
        ch=ca[k]
        if ch.get('license_url'): continue
        name = ch.get('name','').replace('"',"'").replace(',',"")
        logo = ch.get('logo','')
        group = ch.get('group','Samsung').replace('"',"'")
        chno = str(ch.get('chno',''))
        play_url = f"https://jmp2.uk/{slug_t.format(id=k)}"
        if chno:
            m3u += f'#EXTINF:-1 tvg-id="samsung-{k}" tvg-logo="{logo}" group-title="{group}" tvg-chno="{chno}",{name}\n{play_url}\n'
        else:
            m3u += f'#EXTINF:-1 tvg-id="samsung-{k}" tvg-logo="{logo}" group-title="{group}",{name}\n{play_url}\n'
    return PlainTextResponse(m3u, media_type="text/plain")

@app.get("/samsung-ca.xml")
def samsung_xml():
    r = requests.get('https://i.mjh.nz/SamsungTVPlus/ca.xml.gz', timeout=30, headers=CAN_HEADERS)
    data = r.content
    if data[:2]==b'\x1f\x8b':
        data = gzip.decompress(data)
    return Response(content=data, media_type="application/xml")

@app.get("/")
def root():
    return {"samsung": "/samsung-ca.m3u", "epg": "/samsung-ca.xml"}
