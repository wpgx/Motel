import requests, datetime, re, sys
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

COUNTRY = "ca"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Origin": "https://www.samsungtvplus.com",
    "Referer": "https://www.samsungtvplus.com/"
}

CHANNELS_URL = f"https://api.samsungtvplus.com/api/v2/channels?region={COUNTRY}&locale=en-CA"

print(f"Fetching {CHANNELS_URL}")
try:
    r = requests.get(CHANNELS_URL, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
except Exception as e:
    print(f"Primary API failed: {e}, trying backup...")
    # Backup: try the TV Plus web endpoint
    CHANNELS_URL = "https://platinum.samsungtvplus.com/api/channel?region=ca"
    r = requests.get(CHANNELS_URL, headers=headers, timeout=30)
    data = r.json()

channels = data if isinstance(data, list) else data.get('channels', data.get('data', []))
print(f"Found {len(channels)} raw channels")

m3u_lines = ["#EXTM3U"]
epg_channels = []
programs = []

for ch in channels:
    cid = ch.get('id') or ch.get('channelId') or ch.get('slug') or ch.get('guid')
    name = ch.get('name') or ch.get('title') or 'Unknown'
    logo = ch.get('logo') or ch.get('thumbnail') or ch.get('ch_logo') or ''
    group = ch.get('category') or ch.get('genre') or ch.get('group') or 'Samsung CA'
    
    stream = ch.get('streamUrl') or ch.get('url') or ch.get('stream_url') or ''
    if not stream and 'stream' in ch and isinstance(ch['stream'], dict):
        stream = ch['stream'].get('url') or ''
    if not stream:
        # hunt for any m3u8 in values
        for v in ch.values():
            if isinstance(v, str) and '.m3u8' in v:
                stream = v
                break
    
    if not stream:
        continue

    # FILTER: Only keep working streams (your requirement)
    try:
        test = requests.head(stream, headers=headers, timeout=5, allow_redirects=True)
        if test.status_code >= 400:
            test2 = requests.get(stream, headers=headers, timeout=6, stream=True)
            if test2.status_code >= 400:
                print(f"SKIP dead: {name}")
                continue
    except:
        print(f"SKIP timeout: {name}")
        continue

    tvg_id = f"samsung-ca-{str(cid).replace(' ','-')}"
    # Clean name for m3u
    safe_name = name.replace(',', '').strip()
    m3u_lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{safe_name}')
    m3u_lines.append(stream)
    epg_channels.append((tvg_id, safe_name, logo))

    # Try to get EPG for this channel (next 48h)
    try:
        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(days=2)
        epg_url = f"https://api.samsungtvplus.com/api/v2/epg?channelId={cid}&region={COUNTRY}&from={now.isoformat()}Z&to={later.isoformat()}Z"
        er = requests.get(epg_url, headers=headers, timeout=10)
        if er.status_code == 200:
            ej = er.json()
            plist = ej.get('programs') if isinstance(ej, dict) else ej
            if isinstance(plist, list):
                for prog in plist:
                    programs.append((tvg_id, prog))
    except:
        pass

# Write M3U
open("samsung-ca.m3u8", "w", encoding="utf-8").write("\n".join(m3u_lines))
print(f"WROTE samsung-ca.m3u8 with {len(epg_channels)} WORKING channels")

# Build XMLTV
tv = Element('tv')
for tvg_id, name, logo in epg_channels:
    c = SubElement(tv, 'channel', id=tvg_id)
    SubElement(c, 'display-name').text = name
    if logo:
        SubElement(c, 'icon', src=logo)

def fmt_time(s):
    if not s:
        return ""
    try:
        # Handle 2024-01-01T12:00:00Z
        dt = datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
        return dt.strftime("%Y%m%d%H%M%S +0000")
    except:
        return ""

for tvg_id, prog in programs:
    title = prog.get('title') or prog.get('name') or prog.get('programTitle') or 'No Title'
    start = prog.get('startTime') or prog.get('start') or prog.get('startDate') or ''
    end = prog.get('endTime') or prog.get('end') or prog.get('endDate') or ''
    desc = prog.get('description') or prog.get('desc') or prog.get('longDescription') or ''
    
    s_fmt = fmt_time(start)
    e_fmt = fmt_time(end)
    if not s_fmt or not e_fmt:
        continue
        
    p = SubElement(tv, 'programme', start=s_fmt, stop=e_fmt, channel=tvg_id)
    SubElement(p, 'title', lang='en').text = str(title)
    if desc:
        SubElement(p, 'desc', lang='en').text = str(desc)[:500]

xml_str = minidom.parseString(tostring(tv, 'utf-8')).toprettyxml(indent="  ")
open("samsung-ca.xml", "w", encoding="utf-8").write(xml_str)
print(f"WROTE samsung-ca.xml with {len(programs)} programs for {len(epg_channels)} channels")
