from pathlib import Path
import requests, datetime
FULL=Path("full_ca_us.m3u")
FINAL=Path("final_60.m3u")
WELCOME_EXT='#EXTINF:-1 tvg-id="welcome" tvg-name="Cairns Motel" group-title="Motel Info",Cairns Motel - Welcome'
WELCOME_URL='https://xman.deecee.ca/welcome/welcome.m3u8'
BANNED=["deal or no deal","wu tang","wu-tang","wutang"]
def parse(txt):
 lines=txt.splitlines(); out=[]
 for i,l in enumerate(lines):
  if l.strip().startswith('#EXTINF') and i+1 < len(lines):
   u=lines[i+1].strip()
   if u.startswith("http"): out.append((l.strip(),u.strip()))
 return out
def banned(s): return any(b in s.lower() for b in BANNED)
flex=parse(FULL.read_text(errors='ignore'))
print(f"FULL {len(flex)} at {datetime.datetime.utcnow()}")
EPG='https://iptv-org.github.io/epg/guides/ca.xml'
final=[f'#EXTM3U url-tvg="{EPG}"',f'#EXTINF:-1 tvg-id="timestamp" group-title="Info",Updated {datetime.datetime.utcnow()}',WELCOME_URL,WELCOME_EXT,WELCOME_URL]
seen=set([WELCOME_URL])
cnt=0
for e,u in flex:
 if len(final)//2 >= 67: break
 if banned(e): continue
 if u not in seen:
  final.append(e); final.append(u); seen.add(u); cnt+=1
final.append(WELCOME_EXT); final.append(WELCOME_URL); final.append("")
FINAL.write_text("\n".join(final)+"\n")
print(f"WROTE {cnt} - check raw github now")
