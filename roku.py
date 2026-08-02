import requests
api = "https://therokuchannel.roku.com/api/v2/content/linear-channels?expand=liveFeed&limit=500"
j = requests.get(api, headers={"Origin":"https://therokuchannel.roku.com","User-Agent":"Mozilla/5.0"}, timeout=20).json()
channels=[]
for c in j.get("items",[]):
    hls = c.get("liveFeed",{}).get("hlsUrl")
    if not hls: continue
    name = c.get("title","Roku")
    if "español" in name.lower(): continue
    channels.append((c["id"], name, hls, c.get("images",[{}])[0].get("url","")))

with open("roku.m3u","w", encoding="utf-8") as f:
    f.write('#EXTM3U url-tvg="roku.xml"\n')
    for cid,name,url,logo in channels:
        f.write(f'#EXTINF:-1 tvg-id="roku-{cid}" tvg-logo="{logo}" group-title="Roku",{name}\n{url}\n')
print(f"Roku: {len(channels)}")
