def download_and_build_full():
    print(f"=== Downloading {BACKUP_URL} ===")
    r = requests.get(BACKUP_URL, timeout=30, headers=HEADERS)
    all_chans = parse_m3u_text(r.text)
    print(f" Total raw: {len(all_chans)}")
    kept = []
    for e,u in all_chans:
        low=e.lower()
        if is_blacklisted(e,u): continue
        if is_bad(u): continue
        if is_welcome(e,u): continue
        if not ('usa' in low or 'canada' in low or 'group-title="us' in low or 'group-title="ca' in low):
            continue
        kept.append((clean_no_numbers(e),u))
    
    # NO alive check for full list - keep all
    epg_header = f'#EXTM3U url-tvg="{EPG_URLS}"'
    out_lines = [epg_header] + [x for pair in kept for x in pair]
    FULL_CA_US.write_text('\n'.join(out_lines)+'\n', encoding='utf-8')
    print(f" Wrote FULL {len(kept)} chans WITH guide")
    return kept
