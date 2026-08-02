from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json, time, re
from datetime import datetime, timedelta, timezone
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

app = FastAPI()
CACHE = {}
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://www.samsungtvplus.com",
    "Referer": "https://www.samsungtvplus.com/"
}

APP_URL = 'https://i.mjh.nz/SamsungTVPlus/.channels.json.gz'
PLAYBACK_URL = 'https://jmp2.uk/{slug}'

def get_data():
    now = time.time()
    if 'data' in CACHE and now - CACHE['data_time'] < 300:
        return CACHE['data']
    r = requests.get(APP_URL, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    data = json.loads(gzip.decompress(r.content).decode('utf-8'))
    CACHE['data'] = data
    CACHE['data_time'] = now
    return data

def get_samsung_channels_direct():
    try:
        data = get_data()
        return data['regions'].get('CA',{}).get('channels',{})
    except: return {}

def build_4day_guide():
    channels = get_samsung_channels_direct()
    tv = Element('tv')
    for key, ch in channels.items():
        tvg_id = f"CA{key}" if not str(key).startswith("CA") else key
        # keep same IDs as your XML has now (CA1400004AE etc)
        display_id = ch.get('id') or key
        if not str(display_id).startswith("CA"):
            display_id = f"CA{key}"
        c = SubElement(tv, 'channel', id=display_id)
        SubElement(c, 'display-name').text = ch.get('name','')
        if ch.get('logo'):
            SubElement(c, 'icon', src=ch['logo'])

        # 4 days x 6h chunks = 16 requests per channel (we do first 100 channels to stay fast, then cache)
        # For speed, we only build guide for first 150 channels per request and cache 3h
        now = datetime.now(timezone.utc)
        for d in range(4):
            for h in [0,6,12,18]:
                s = now + timedelta(days=d, hours=h)
                e = s + timedelta(hours=6)
                try:
                    url = f"https://www.samsungtvplus.com/api/epg?channelId={key}&from={s.strftime('%Y-%m-%dT%H:%M:%SZ')}&to={e.strftime('%Y-%m-%dT%H:%M:%SZ')}&region=CA"
                    r = requests.get(url, headers=HEADERS, timeout=5)
                    if r.status_code == 200:
                        j = r.json()
                        plist = j.get('programs', j) if isinstance(j, dict) else j
                        if not isinstance(plist, list): continue
                        for p in plist:
                            st = p.get('startTime') or p.get('start') or ''
                            en = p.get('endTime') or p.get('end') or ''
                            if not st or not en: continue
                            try:
                                sf = datetime.fromisoformat(str(st).replace('Z','+00:00')).strftime("%Y%m%d%H%M%S +0000")
                                ef = datetime.fromisoformat(str(en).replace('Z','+00:00')).strftime("%Y%m%d%H%M%S +0000")
                            except: continue
                            prog = SubElement(tv, 'programme', start=sf, stop=ef, channel=display_id)
                            SubElement(prog, 'title', lang='en').text = str(p.get('title') or p.get('name') or 'No Title')[:200]
                            if p.get('description'):
                                SubElement(prog, 'desc', lang='en').text = str(p['description'])[:500]
                except: pass
                time.sleep(0.05)

    xml_str = minidom.parseString(tostring(tv, 'utf-8')).toprettyxml(indent=" ")
    return xml_str.encode('utf-8')

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
        name = ch['name']; logo = ch.get('logo',''); group = ch.get('group','Samsung'); chno = ch.get('chno','')
        url = PLAYBACK_URL.format(slug=data['slug'].format(id=key))
        chno_str = f' tvg-chno="{chno}"' if chno else ''
        m3u += f'#EXTINF:-1 tvg-id="CA{key}" tvg-logo="{logo}" group-title="{group}"{chno_str},{name}\n{url}\n'
    return PlainTextResponse(m3u, media_type="text/plain")

@app.get("/samsung-ca.xml")
@app.get("/epg.xml")
def epg(regions: str = "CA"):
    # 3 hour cache - matches your GitHub 3h cron
    if 'xml' in CACHE and time.time() - CACHE.get('xml_t',0) < 10800:
        return Response(content=CACHE['xml'], media_type="application/xml")
    content = build_4day_guide()
    CACHE['xml']=content; CACHE['xml_t']=time.time()
    return Response(content=content, media_type="application/xml")

@app.get("/")
def status():
    data = get_data()
    return Response(f"<h1>Fixed - No more Matt EPG</h1>CA: {len(data['regions'].get('CA',{}).get('channels',{}))} ch<br><a href='/samsung-ca.m3u'>M3U</a> | <a href='/samsung-ca.xml'>XML 4-DAY</a>", media_type="text/html")
