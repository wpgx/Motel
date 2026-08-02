import re, requests
URL = "https://raw.githubusercontent.com/BuddyChewChew/tubi-scraper/main/tubi.m3u"
m3u = requests.get(URL, headers={"User-Agent":"Mozilla/5.0"}, timeout=20).text
pat = re.compile(r'#EXTINF:-1.*?,(.*?)\n(https://live-manifest\.production-public\.tubi\.io/live/([a-f0-9-]{36})/playlist\.m3u8)', re.MULTILINE)
channels=[]
seen=set()
for name, url, cid in pat.findall(m3u):
    if "español" in name.lower(): continue
    if cid in seen: continue
    seen.add(cid)
    channels.append((cid, name.strip(), url))

with open("tubi.m3u","w", encoding="utf-8") as f:
    f.write('#EXTM3U url-tvg="tubi.xml"\n')
    for cid,name,url in channels:
        f.write(f'#EXTINF:-1 tvg-id="tubi-{cid}" group-title="Tubi",{name}\n{url}\n')
print(f"Tubi: {len(channels)} English")
