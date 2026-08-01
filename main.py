from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import requests, re, json

app = FastAPI()

@app.get("/samsung-ca.m3u")
def samsung_ca_m3u():
    try:
        # Get the Canadian browse page - it contains all channels in JSON inside
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-CA,en;q=0.9",
            "Referer": "https://www.samsungtvplus.com/ca",
        }
        # This page embeds channels
        r = requests.get("https://www.samsungtvplus.com/ca/live", headers=headers, timeout=30)
        html = r.text

        # Look for embedded channel data
        m = re.search(r'window\.__NEXT_DATA__\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
        if m:
            data = json.loads(m.group(1))
            # Walk the JSON for channels
            text = json.dumps(data)
            # Find all stream URLs
            urls = re.findall(r'"playbackUrl":"(https[^"]+\.m3u8[^"]*)"', text)
            names = re.findall(r'"title":"([^"]+)"', text)
            m3u = '#EXTM3U\n'
            for i, u in enumerate(urls[:300]):
                name = names[i] if i < len(names) else f"Samsung CA {i}"
                name = name.replace('"',"'")
                m3u += f'#EXTINF:-1 group-title="Samsung CA",{name}\n{u}\n'
            if len(urls) > 10:
                return PlainTextResponse(m3u, media_type="application/vnd.apple.mpegurl")

        # Fallback: try to find any m3u8 in page
        urls = re.findall(r'(https://[^\s"]+\.m3u8[^\s"]*)', html)
        if urls:
            m3u = '#EXTM3U\n'
            for u in set(urls):
                m3u += f'#EXTINF:-1 group-title="Samsung CA",Samsung CA\n{u}\n'
            return PlainTextResponse(m3u, media_type="application/vnd.apple.mpegurl")

        return PlainTextResponse(f"#EXTM3U\n# No channels found in HTML len={len(html)}\n# First 500: {html[:500]}\n", media_type="text/plain")
    except Exception as e:
        return PlainTextResponse(f"#EXTM3U\n# Error {e}\n", media_type="text/plain")
