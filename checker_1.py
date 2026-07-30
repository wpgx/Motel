name: Checker 1 - Final 65 with Guide + News
on:
  workflow_dispatch:
  schedule:
    - cron: '0 */12 * * *'
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install requests
      - run: |
          python - << 'PY'
          from pathlib import Path
          import requests, re
          FULL = Path("full_ca_us.m3u")
          FINAL = Path("final_60.m3u")
          WELCOME_EXT = '#EXTINF:-1 tvg-id="welcome" tvg-name="Cairns Motel" group-title="Motel Info",Cairns Motel - Welcome'
          WELCOME_URL = 'https://xman.deecee.ca/welcome/welcome.m3u8'

          def parse(txt):
              lines=txt.splitlines(); out=[]
              for i,l in enumerate(lines):
                  if l.strip().startswith('#EXTINF') and i+1 < len(lines):
                      u=lines[i+1].strip()
                      if u.startswith("http"): out.append((l.strip(),u.strip()))
              return out

          def alive(url):
              if WELCOME_URL in url: return True
              if ".mp4" in url.lower(): return False
              if "xumo" in url.lower() and "ads." in url.lower(): return False
              try:
                  r=requests.get(url, timeout=8, headers={"User-Agent":"VLC/3.0.19"}, stream=True)
                  if r.status_code in (403,404) or r.status_code >=400: 
                      return False
                  c=next(r.iter_content(2048), b"").decode(errors='ignore').lower()
                  if "403" in c or "forbidden" in c or "accessdenied" in c: 
                      return False
                  return True
              except: 
                  return False

          flex = parse(FULL.read_text(errors='ignore'))
          print(f"FULL {len(flex)} untouched")

          EPG = 'https://iptv-org.github.io/epg/guides/ca.xml,https://iptv-org.github.io/epg/guides/us.xml'
          final=[f'#EXTM3U url-tvg="{EPG}"', WELCOME_EXT, WELCOME_URL]
          seen=set([WELCOME_URL])

          # 1. PEI / Maritimes - 12
          for e,u in flex:
              if len(final)//2 >= 13: break
              if any(k in e.lower() for k in ["pei","compass","cbc","
