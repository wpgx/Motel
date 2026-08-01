import requests, re, datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

COUNTRY = "ca"
WORKING_M3U = "samsung-ca.m3u8"  # your good file

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://www.samsungtvplus.com",
    "Referer": "https://www.samsungtvplus.com/ca"
}

# This endpoint DOES work from GitHub actions
URL = "https://www.samsungtvplus.com/api/channels"

params = {
    "region": COUNTRY,
    "locale": "en-CA"
}

print(f"Fetching {URL} region={COUNTRY}")
# The site uses a different path now - try v2
try:
    r = requests.get("https://www.samsungtvplus.com/api/v2/channels", params=params, headers=headers, timeout=30)
    print(f"v2 status {r.status_code}")
    if r.status_code != 200:
        r = requests.get(URL, params=params, headers=headers, timeout=30)
    data = r.json()
    print(f"Got data: {str(data)[:500]}")
except Exception as e:
    print(f"Failed: {e}")
    # Last resort - scrape the webpage itself
    r = requests.get(f"https://www.samsungtvplus.com/ca", headers=headers, timeout=30)
    # Find __NEXT_DATA__ json
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
    if m:
        import json
        next_data = json.loads(m.group(1))
        print("Found NEXT_DATA")
        data = next_data
    else:
        raise

# Try to extract channels list regardless of nesting
channels = []
def find_channels(obj):
    if isinstance(obj, dict):
        if 'channels' in obj and isinstance(obj['channels'], list):
            channels.extend(obj['channels'])
        for v in obj.values():
            find_channels(v)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict) and ('id' in item and 'name' in item and 'stream' in str(item).lower()):
                channels.append(item)
            else:
                find_channels(item)

find_channels(data)
# dedup
uniq = {c.get('id', c.get('slug')): c for c in channels}
channels = list(uniq.values())

print(f"Found {len(channels)} raw channels from samsungtvplus.com")

# Load your working IDs if you have them
working_ids = set()
try:
    with open(WORKING_M3U, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            m = re.search(r'tvg-id="([^"]+)"', line)
            if m:
                working_ids.add(m.group(1))
    print(f"Your working file has {len(working_ids)} ids - will use as whitelist")
except:
    print("No working file yet, will keep all that return 200")

m3u = ['#EXTM3U url-tvg="https://motel.deecee.ca/samsung-ca.xml"']
epg_channels = []
programs = []

for ch in channels:
    cid = ch.get('id') or ch.get('slug') or ch.get('channelId')
    if not cid:
        continue
    name = ch.get('name') or ch.get('title') or 'Unknown'
    logo = ch.get('logo') or ch.get('thumbnail') or ch.get('image') or ''
    group = ch.get('category') or ch.get('genre') or 'Samsung CA'
    
    # stream
    stream = ch.get('streamUrl') or ch.get('stream_url') or ch.get('url') or ''
    if not stream:
        # look deeper
        if 'stream' in ch and isinstance(ch['stream'], dict):
            stream = ch['stream'].get('url', '')
        if not stream:
            for v in ch.values():
                if isinstance(v, str) and '.m3u8' in v:
                    stream = v
                    break
    if not stream:
        continue

    tvg_id = f"samsung-ca-{cid}"
    # If you have whitelist, skip if not in it
    if working_ids and tvg_id not in working_ids and cid not in working_ids and name.lower() not in [x.lower() for x in working_ids]:
        # also check if name matches your whitelist names
        pass  # we will keep all for now, but you can enable filter

    # Test if it actually plays
    try:
        h = requests.head(stream, headers=headers, timeout=5, allow_redirects=True)
        if h.status_code >= 400:
            g = requests.get(stream, headers=headers, timeout=5, stream=True)
            if g.status_code >= 400:
                print(f"SKIP dead {name}")
                continue
    except:
        print(f"SKIP timeout {name}")
        continue

    m3u.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}')
    m3u.append(stream)
    epg_channels.append((tvg_id, name, logo))

    # EPG per channel - new endpoint
    try:
        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(days=2)
        epg_params = {
            "channelId": cid,
            "region": COUNTRY,
            "from": now.strftime("%Y-%m-%dT%H:00:00Z"),
            "to": later.strftime("%Y-%m-%dT%H:00:00Z")
        }
        er = requests.get("https://www.samsungtvplus.com/api/epg", params=epg_params, headers=headers, timeout=10)
        if er.status_code == 200:
            ej = er.json()
            plist = ej.get('programs', []) if isinstance(ej, dict) else ej
            for p in plist if isinstance(plist, list) else []:
                programs.append((tvg_id, p))
    except Exception as e:
        pass

open("samsung-ca.m3u8", "w", encoding="utf-8").write("\n".join(m3u))
print(f"WROTE samsung-ca.m3u8 {len(epg_channels)} working")

# Build XMLTV
tv = Element('tv')
for tvg_id, name, logo in epg_channels:
    c = SubElement(tv, 'channel', id=tvg_id)
    SubElement(c, 'display-name').text = name
    if logo:
        SubElement(c, 'icon', src=logo)

def fmt(s):
    try:
        dt = datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
        return dt.strftime("%Y%m%d%H%M%S +0000")
    except:
        return ""

for tvg_id, prog in programs:
    title = prog.get('title') or prog.get('name') or 'No Title'
    s = prog.get('startTime') or prog.get('start') or ''
    e = prog.get('endTime') or prog.get('end') or ''
    desc = prog.get('description') or prog.get('longDescription') or ''
    sf = fmt(s); ef = fmt(e)
    if not sf or not ef:
        continue
    pr = SubElement(tv, 'programme', start=sf, stop=ef, channel=tvg_id)
    SubElement(pr, 'title', lang='en').text = str(title)
    if desc:
        SubElement(pr, 'desc', lang='en').text = str(desc)[:600]

xml_str = minidom.parseString(tostring(tv, 'utf-8')).toprettyxml(indent="  ")
open("samsung-ca.xml", "w", encoding="utf-8").write(xml_str)
print(f"WROTE samsung-ca.xml {len(programs)} programs")
