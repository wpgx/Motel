from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import requests, re, json

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "ca_playlist": "/samsung-ca.m3u"}

@app.get("/samsung-ca.m3u")
def samsung_ca_m3u():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-CA,en;q=0.9",
        }
        r = requests.get("https://www.samsungtvplus.com/ca/live", headers=headers, timeout=30)
        html = r.text
        m = re.search(r'window\.__NEXT_DATA__\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
        if m:
            data = json.loads(m.group(1))
            text = json.dumps(data)
            urls = re.findall(r'"playbackUrl":"(https[^"]+\.m3u8[^"]*)"', text)
            titles = re.findall(r'"title"\s*:\s*"([^"]+)"', text)
            m3u = '#EXTM3U\n'
            for i, u in enumerate(urls):
                name = titles[i] if i < len(titles) else f"Samsung CA {i}"
                name = name.replace('"',"'").replace(',',"")
                m3u += f'#EXTINF:-1 group-title="Samsung CA",{name}\n{u}\n'
            if len(urls) > 5:
                return PlainTextResponse(m3u, media_type="application/vnd.apple.mpegurl")
        # if not found, dump debug
        return PlainTextResponse(f"#EXTM3U\n# DEBUG len={len(html)}\n# {html[:1000]}\n", media_type="text/plain")
    except Exception as e:
        return PlainTextResponse(f"#EXTM3U\n# Error {e}\n", media_type="text/plain")
