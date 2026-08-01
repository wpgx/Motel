@app.get("/samsung-ca.m3u")
def samsung_ca_m3u():
    try:
        r = requests.get(APP_URL, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        j = json.loads(gzip.decompress(r.content).decode('utf-8'))
        
        # j can be dict or list
        items = j.values() if isinstance(j, dict) else j
        
        m3u = '#EXTM3U url-tvg="https://motel-r45n.onrender.com/samsung-ca.xml"\n'
        count = 0
        for ch in items:
            if not isinstance(ch, dict):
                continue
            # Only Canada
            regions = ch.get('regions') or ch.get('availableRegions') or []
            if isinstance(regions, list):
                if 'CA' not in regions and 'ca' not in [str(x).lower() for x in regions]:
                    continue
            elif isinstance(regions, str):
                if 'CA' not in regions.upper():
                    continue
            # Some entries use countryCode
            if ch.get('country') and ch.get('country') != 'CA':
                if 'CA' not in str(ch.get('regions','')):
                    continue

            cid = ch.get('id') or ch.get('slug') or ch.get('name') or "ca"
            title = (ch.get('name') or ch.get('title') or cid).replace('"',"'").replace(',',"")
            logo = ch.get('logo') or ch.get('thumbnail') or ""
            group = ch.get('group') or ch.get('genre') or "Samsung CA"
            # Direct stream via jmp2 proxy
            stream = f"https://jmp2.uk/SamsungTVPlus/{cid}.m3u8"

            m3u += f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{title}" tvg-logo="{logo}" group-title="{group}",{title}\n{stream}\n'
            count += 1

        if count == 0:
            return PlainTextResponse(f"#EXTM3U\n# No CA found, total items={len(list(items))}\n# Sample: {str(list(items)[:1])[:500]}\n", media_type="text/plain")

        return PlainTextResponse(m3u, media_type="application/vnd.apple.mpegurl")
    except Exception as e:
        import traceback
        return PlainTextResponse(f"#EXTM3U\n# Error {e}\n{traceback.format_exc()[:1000]}\n", media_type="text/plain")
