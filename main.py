from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json

app = FastAPI()

APP_URL = 'https://i.mjh.nz/SamsungTVPlus/.channels.json.gz'

@app.get("/")
def root():
    return {"status":"ok direct scrape","source": APP_URL, "ca": "/samsung-ca.m3u", "guide": "/samsung-ca.xml"}

@app.get("/samsung-ca.m3u")
def samsung_ca_m3u():
    try:
        r = requests.get(APP_URL, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        data = json.loads(gzip.decompress(r.content).decode('utf-8'))
        
        # data is dict of all channels worldwide
        m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/samsung-ca.xml"\n'
        ca_count = 0
        for cid, ch in data.items():
            # ch has regions
            regions = ch.get('regions', []) or ch.get('country', []) or []
            # Keep Canada
            if 'CA' not in str(regions).upper() and 'ca' not in [str(x).lower() for x in regions]:
                # some entries use country list inside
                if ch.get('country') != 'CA' and 'CA' not in ch.get('availableCountries', []):
                    # skip non-CA
                    # check if regions empty means global? we skip to be safe for CA only
                    if 'ca' not in cid.lower():
                        # actually filter: if no region info, check if title has CA flag
                        pass
            # Force CA filter: matt's file has region field
            if isinstance(ch, dict):
                if 'CA' not in json.dumps(ch.get('regions','')) and 'ca' not in ch.get('slug','').lower():
                    # stricter: look for country
                    if ch.get('region') != 'CA':
                        # Let's just include if CA in regions or country
                        if 'CA' not in str(ch.get('regions','')) and ch.get('country','') != 'CA':
                            continue

            # Build entry
            title = ch.get('name') or ch.get('title') or cid
            title = str(title).replace('"',"'").replace(',',"")
            logo = ch.get('logo') or ""
            group = ch.get('group') or ch.get('category') or "Samsung CA"
            stream = ch.get('url') or ch.get('streamUrl') or f"https://jmp2.uk/SamsungTVPlus/{cid}.m3u8"
            
            m3u += f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{title}" tvg-logo="{logo}" group-title="{group}",{title}\n{stream}\n'
            ca_count += 1

        # If filter too strict, fallback to all that have CA in key
        if ca_count < 10:
            m3u = '#EXTM3U\n'
            for cid, ch in data.items():
                if 'ca' in cid.lower() or 'CA' in str(ch.get('regions','')):
                    title = ch.get('name') or cid
                    stream = f"https://jmp2.uk/SamsungTVPlus/{cid}.m3u8"
                    m3u += f'#EXTINF:-1 group-title="Samsung CA",{title}\n{stream}\n'

        return PlainTextResponse(m3u, media_type="application/vnd.apple.mpegurl")
    except Exception as e:
        return PlainTextResponse(f"#EXTM3U\n# Error {e}\n", media_type="text/plain")

@app.get("/samsung-ca.xml")
def samsung_ca_xml():
    try:
        r = requests.get('https://i.mjh.nz/SamsungTVPlus/ca.xml.gz', timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        xml = gzip.decompress(r.content)
        return Response(content=xml, media_type="application/xml")
    except Exception as e:
        return Response(content=f"<tv><error>{e}</error></tv>".encode(), media_type="application/xml")
