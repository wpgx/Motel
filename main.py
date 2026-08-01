from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response
import requests, gzip, json, re

app = FastAPI()

def get_samsung_ca():
    # HARD WORKING 276 METHOD
    url = 'https://i.mjh.nz/SamsungTVPlus/.channels.json.gz'
    r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    raw = r.content
    if raw[:2]==b'\x1f\x8b':
        raw = gzip.decompress(raw)
    data = json.loads(raw.decode('utf-8'))
    slug_t = data.get('slug','SamsungTVPlus/{id}.m3u8')
    ca = data['regions']['CA']['channels']
    out=[]
    for k in sorted(ca.keys(), key=lambda x: ca[x].get('chno',9999)):
        ch=ca[k]
        if ch.get('license_url'): continue
        name = ch.get('name','').replace('"',"'").replace(',',"").strip()
        logo = ch.get('logo','')
        group = ch.get('group','Samsung CA').replace('"',"'")
        chno = str(ch.get('chno','')).strip()
        play = f"https://jmp2.uk/{slug_t.format(id=k)}"
        if chno:
            ext = f'#EXTINF:-1 tvg-id="samsung-{k}" tvg-logo="{logo}" group-title="{group}" tvg-chno="{chno}",{name}'
        else:
            ext = f'#EXTINF:-1 tvg-id="samsung-{k}" tvg-logo="{logo}" group-title="{group}",{name}'
        out.append((ext, play))
    return out

def fetch_m3u_list(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code!=200: return []
        lines = r.text.splitlines()
        out=[]
        for i,l in enumerate(lines):
            if l.startswith('#EXTINF'):
                if i+1 < len(lines) and lines[i+1].startswith('http'):
                    out.append((l, lines[i+1].strip()))
        return out
    except:
        return []

def get_pluto_ca():
    return fetch_m3u_list('https://i.mjh.nz/PlutoTV/ca.m3u8') or fetch_m3u_list('https://i.mjh.nz/PlutoTV/all.m3u8')

def get_plex_ca():
    return fetch_m3u_list('https://i.mjh.nz/Plex/ca.m3u8') or fetch_m3u_list('https://i.mjh.nz/Plex/all.m3u8')

def build_from_tuples(tuples_list):
    m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/all-ca.xml"\n'
    for ext, url in tuples_list:
        m3u += f"{ext}\n{url}\n"
    return m3u

@app.get("/debug")
def debug():
    try: s=len(get_samsung_ca())
    except Exception as e: s=f"ERR {e}"
    try: pl=len(get_pluto_ca())
    except Exception as e: pl=f"ERR {e}"
    try: px=len(get_plex_ca())
    except Exception as e: px=f"ERR {e}"
    return {"samsung":s, "pluto":pl, "plex":px}

@app.get("/samsung-ca.m3u")
def s_m3u():
    return PlainTextResponse(build_from_tuples(get_samsung_ca()), media_type="text/plain")

@app.get("/pluto-ca.m3u")
def pl_m3u():
    return PlainTextResponse(build_from_tuples(get_pluto_ca()), media_type="text/plain")

@app.get("/plex-ca.m3u")
def px_m3u():
    return PlainTextResponse(build_from_tuples(get_plex_ca()), media_type="text/plain")

@app.get("/all-ca.m3u")
def all_m3u():
    all_ch = get_samsung_ca() + get_pluto_ca() + get_plex_ca()
    return PlainTextResponse(build_from_tuples(all_ch), media_type="text/plain")

@app.get("/all-ca.xml")
def all_xml():
    parts=[]
    for url in ['https://i.mjh.nz/SamsungTVPlus/ca.xml.gz','https://i.mjh.nz/PlutoTV/ca.xml.gz','https://i.mjh.nz/Plex/ca.xml.gz']:
        try:
            r=requests.get(url, timeout=15)
            data=gzip.decompress(r.content) if r.content[:2]==b'\x1f\x8b' else r.content
            parts.append(data)
        except: pass
    merged=b'<?xml version="1.0"?><tv>'
    for p in parts:
        try:
            txt=p.decode('utf-8', errors='ignore')
            m=re.search(r'<tv[^>]*>(.*)</tv>', txt, re.DOTALL)
            if m: merged+=m.group(1).encode()
        except: pass
    merged+=b'</tv>'
    return Response(content=merged, media_type="application/xml")

@app.get("/samsung-ca.xml")
def s_xml():
    r=requests.get('https://i.mjh.nz/SamsungTVPlus/ca.xml.gz', timeout=15)
    data=gzip.decompress(r.content) if r.content[:2]==b'\x1f\x8b' else r.content
    return Response(content=data, media_type="application/xml")
