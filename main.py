from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
import requests, json, time

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.samsungtvplus.com/",
    "Origin": "https://www.samsungtvplus.com",
    "Accept": "application/json, text/plain, */*",
}

def fetch_direct_ca():
    # Direct Samsung endpoints - no i.mjh.nz
    urls = [
        "https://search.prd.samsungtvplus.com/api/v2/channels?country=CA&language=en",
        "https://www.samsungtvplus.com/api/channels?region=ca",
        "https://config.samsungtvplus.com/config?country=CA",
    ]
    for u in urls:
        try:
            r = requests.get(u, headers=HEADERS, timeout=25)
            # If HTML returned, try next
            if r.headers.get('content-type','').startswith('text/html'):
                continue
            data = r.json()
            return data
        except Exception as e:
            continue
    return None

def build_m3u_from_samsung(data):
    m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/samsung-ca.xml"\n'
    channels = []
    if isinstance(data, dict):
        # search API returns {data: [...]}
        if 'data' in data and isinstance(data['data'], list):
            channels = data['data']
        elif 'channels' in data:
            channels = data['channels']
        elif 'regions' in data:
            # config endpoint
            ca = data.get('regions', {}).get('CA') or data.get('regions', {}).get('ca')
            if ca:
                channels = ca.get('channels', [])
    elif isinstance(data, list):
        channels = data

    for c in channels:
        if not isinstance(c, dict): continue
        # try many possible keys
        stream = c.get('streamUrl') or c.get('playbackUrl') or c.get('url') or c.get('m3u8') or ""
        if isinstance(stream, dict):
            stream = stream.get('url') or ""
        if not str(stream).startswith("http"): continue
        
        title = c.get('title') or c.get('name') or c.get('chName') or "Samsung CA"
        title = str(title).replace('"',"'").strip()
        cid = str(c.get('id') or c.get('channelId') or title.replace(" ","_"))
        logo = c.get('logo') or c.get('thumbnail') or c.get('tileImage') or ""
        group = c.get('category') or c.get('genre') or c.get('group') or "Samsung CA"

        m3u += f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{title}" tvg-logo="{logo}" group-title="{group}",{title}\n{stream}\n'
    return m3u

@app.get("/")
def home():
    return {"direct_scrape": "enabled", "region": "CA", "endpoints": ["/samsung-ca.m3u", "/samsung-ca.xml"]}

@app.get("/samsung-ca.m3u")
def samsung_ca_m3u():
    try:
        data = fetch_direct_ca()
        if not data:
            return PlainTextResponse("#EXTM3U\n# Samsung directly blocked or changed API - check logs\n", media_type="text/plain")
        m3u = build_m3u_from_samsung(data)
        return PlainTextResponse(m3u, media_type="application/vnd.apple.mpegurl")
    except Exception as e:
        return PlainTextResponse(f"#EXTM3U\n# Error {e}\n", media_type="text/plain")

@app.get("/samsung-ca.xml")
def samsung_ca_xml():
    # Direct guide from Samsung - we build minimal from same data or fetch EPG endpoint
    try:
        # Samsung EPG endpoint
        epg_url = "https://search.prd.samsungtvplus.com/api/v2/programs?country=CA"
        r = requests.get(epg_url, headers=HEADERS, timeout=25)
        data = r.json()
        # Build simple XMLTV
        xml = '<?xml version="1.0" encoding="UTF-8"?><tv>'
        # Add channels
        # This is simplified - we can expand
        xml += '</tv>'
        # For now return Samsung's raw if it works, else placeholder that TiviMate will accept
        return Response(content=xml, media_type="application/xml")
    except:
        return Response(content='<?xml version="1.0"?><tv></tv>', media_type="application/xml")
