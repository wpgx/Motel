from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json

app = FastAPI()

@app.get("/samsung-ca.m3u")
def samsung_m3u():
    try:
        r = requests.get('https://i.mjh.nz/SamsungTVPlus/.channels.json.gz', timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        data = json.loads(gzip.decompress(r.content).decode('utf-8'))
        slug_t = data.get('slug','SamsungTVPlus/{id}.m3u8')
        ca = data['regions']['CA']['channels']
        m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/samsung-ca.xml"\n'
        for k in sorted(ca.keys(), key=lambda x: ca[x].get('chno',9999)):
            ch=ca[k]
            if ch.get('license_url'): continue
            name = ch.get('name','').replace('"',"'").replace(',',"")
            m3u += f'#EXTINF:-1 tvg-id="samsung-{k}" tvg-logo="{ch.get("logo","")}" group-title="{ch.get("group","Samsung")}",{name}\nhttps://jmp2.uk/{slug_t.format(id=k)}\n'
        return PlainTextResponse(m3u, media_type="text/plain")
    except Exception as e:
        return PlainTextResponse(f"#ERROR {e}", media_type="text/plain")

@app.get("/samsung-ca.xml")
def samsung_xml():
    r = requests.get('https://i.mjh.nz/SamsungTVPlus/ca.xml.gz', timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    data = gzip.decompress(r.content) if r.content[:2]==b'\x1f\x8b' else r.content
    return Response(content=data, media_type="application/xml")

@app.get("/")
def root():
    return {"ok": True}
