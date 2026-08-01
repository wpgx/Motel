from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
import requests, os

app = FastAPI()

# Serve your existing m3u files as static
# app.mount("/", StaticFiles(directory=".", html=False), name="static")

@app.get("/")
def root():
    return {"status":"ok", "endpoints":["/samsung-ca.m3u", "/dcmaster.m3u8", "/dctv.m3u8"]}

@app.get("/samsung-ca.m3u")
def samsung_ca():
    try:
        r = requests.get(
            "https://www.samsungtvplus.com/api/channels",
            params={"region":"ca"},
            headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.samsungtvplus.com/"},
            timeout=20
        )
        data = r.json()
        chs = data.get('data') or data.get('channels') or data
        if isinstance(chs, dict):
            chs = chs.values()
        m3u = '#EXTM3U\n'
        for c in chs:
            if not isinstance(c, dict): continue
            u = c.get('streamUrl') or c.get('url') or c.get('playbackUrl') or ""
            if not u.startswith("http"): continue
            name = (c.get('name') or c.get('title') or "Channel").replace('"',"'")
            cid = str(c.get('id') or name.replace(" ","_"))
            logo = c.get('logo') or c.get('thumbnail') or ""
            group = c.get('group') or c.get('category') or "Samsung CA"
            m3u += f'#EXTINF:-1 tvg-id="{cid}" tvg-logo="{logo}" group-title="{group}",{name}\n{u}\n'
        return PlainTextResponse(m3u, media_type="application/vnd.apple.mpegurl")
    except Exception as e:
        return PlainTextResponse(f"#EXTM3U\n# Error: {e}\n", media_type="text/plain")

# Also serve existing files directly
@app.get("/dcmaster.m3u8")
def serve_dc():
    if os.path.exists("dcmaster.m3u8"):
        with open("dcmaster.m3u8") as f:
            return PlainTextResponse(f.read(), media_type="application/vnd.apple.mpegurl")
    return PlainTextResponse("#EXTM3U\n", media_type="text/plain")
