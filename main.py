from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
import requests

app = FastAPI()

@app.get("/")
def home():
    return {
        "motel": "live",
        "playlist": "https://motel-r45n.onrender.com/samsung-ca.m3u",
        "guide": "https://motel-r45n.onrender.com/samsung-ca.xml"
    }

@app.get("/samsung-ca.m3u")
def samsung_ca_m3u():
    try:
        # Canadian Samsung - from i.mjh.nz (matthuisman)
        r = requests.get("https://i.mjh.nz/SamsungTVPlus/ca.m3u8", timeout=20, headers={"User-Agent":"Mozilla/5.0"})
        return PlainTextResponse(r.text, media_type="application/vnd.apple.mpegurl")
    except Exception as e:
        return PlainTextResponse(f"#EXTM3U\n# Error {e}\n", media_type="text/plain")

@app.get("/samsung-ca.xml")
def samsung_ca_xml():
    try:
        r = requests.get("https://i.mjh.nz/SamsungTVPlus/ca.xml", timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        return Response(content=r.content, media_type="application/xml")
    except Exception as e:
        return Response(content=f"<tv><error>{e}</error></tv>", media_type="application/xml")
