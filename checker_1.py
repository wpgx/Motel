from pathlib import Path
import requests, re, datetime
FULL = Path("full_ca_us.m3u")
FINAL = Path("final_60.m3u")
EPG_OUT = Path("custom_epg.xml")
WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" group-title="Motel Info", Cairns Motel - Welcome'
WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'
HEADERS = {"User-Agent": "VLC/3.0.19"}

def parse(txt):
    lines=txt.splitlines(); out=[]
    for i,l in enumerate(lines):
        if l.strip().startswith('#EXTINF') and i+1 < len(lines):
            u=lines[i+1].strip()
            if u.startswith("http"): out.append((l.strip(),u.strip()))
    return out

def fetch(url):
    try: return requests.get(url, timeout=20, headers=HEADERS).text
    except: return ""

print("BUILD merged EPG")
ca_xml = fetch("https://iptv-org.github.io/epg/guides/ca.xml")
us_xml = fetch("https://iptv-org.github.io/epg/guides/us.xml")
print(f" ca {len(ca_xml)} us {len(us_xml)}")

flex = parse(FULL.read_text(errors='ignore'))
# build final 65 alive quick
final_lines=[f'#EXTM3U url-tvg="https://xman.deecee.ca/custom_epg.xml"', WELCOME_EXT, WELCOME_URL]
for e,u in flex:
    if len(final_lines)//2 >= 66: break
    if u not in "\n".join(final_lines):
        final_lines.append(e); final_lines.append(u)
FINAL.write_text("\n".join(final_lines)+"\n", encoding='utf-8')

# now build custom_epg.xml = ca + us + fallback
now = datetime.datetime.utcnow()
start = now.strftime("%Y%m%d%H%M%S +0000")
stop = (now + datetime.timedelta(hours=24)).strftime("%Y%m%d%H%M%S +0000")

# start xml, copy channels/programmes from ca and us (strip xml header/footer)
def strip_tv(xml_text):
    if "<tv>" in xml_text:
        inner = xml_text.split("<tv>",1)[1].rsplit("</tv>",1)[0]
        return inner
    return ""

merged = ['<?xml version="1.0" encoding="UTF-8"?><tv>']
merged.append(strip_tv(ca_xml))
merged.append(strip_tv(us_xml))

# add welcome + fallback for any tvg-id in FINAL that is not in ca/us (or has no info)
merged.append('<channel id="welcome"><display-name>Cairns Motel - Welcome</display-name></channel>')
merged.append(f'<programme start="{start}" stop="{stop}" channel="welcome"><title>Welcome</title><desc>Welcome to Cairns Motel - Regularly scheduled programming</desc></programme>')

for ext,url in parse("\n".join(final_lines)):
    m=re.search(r'tvg-id="([^"]*)"', ext)
    if m:
        tid=m.group(1)
        if tid:
            # add fallback programme - if real guide already has it, TV will show real guide, not this
