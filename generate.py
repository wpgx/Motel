import requests, re, pathlib
# Build tubi+roku already done, now build all.m3u
files = ["tubi.m3u","roku.m3u"]
# OPTIONAL: add your Render Samsung
try:
    samsung_url = "https://YOUR-RENDER-URL.onrender.com/samsung.m3u" # <-- PUT YOURS HERE
    s = requests.get(samsung_url, timeout=20).text
    pathlib.Path("samsung.m3u").write_text(s, encoding="utf-8")
    files.append("samsung.m3u")
except: pass

with open("all.m3u","w", encoding="utf-8") as out:
    out.write("#EXTM3U\n")
    for fn in files:
        try:
            txt = pathlib.Path(fn).read_text(encoding="utf-8")
            out.write(txt.replace("#EXTM3U\n","").replace('#EXTM3U url-tvg="tubi.xml"\n',"").replace('#EXTM3U url-tvg="roku.xml"\n',"") + "\n")
        except: pass

# EPG - just copy tubi epg from source (real source still direct)
try:
    epg = requests.get("https://raw.githubusercontent.com/BuddyChewChew/tubi-scraper/main/tubi_epg.xml", timeout=20).text
    pathlib.Path("tubi.xml").write_text(epg, encoding="utf-8")
    pathlib.Path("all.xml").write_text(epg, encoding="utf-8")
except: pass
print("Done")
