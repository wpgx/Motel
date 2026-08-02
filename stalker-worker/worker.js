const PLAYLIST_URL = "https://raw.githubusercontent.com/wpgx/Motel/main/motel.m3u8";

function parseM3U(text) {
  const lines = text.split('\n');
  let channels = [];
  let id = 1;
  let current = null;
  for (let line of lines) {
    line = line.trim();
    if (line.startsWith('#EXTINF:')) {
      let name = line.split(',').pop().trim() || `Channel ${id}`;
      let logo = (line.match(/tvg-logo="([^"]+)"/) || [])[1] || "";
      let group = (line.match(/group-title="([^"]+)"/) || [])[1] || "General";
      current = { name, logo, group };
    } else if (line &&!line.startsWith('#') && current) {
      channels.push({ id, number: id, name: current.name, cmd: line, logo: current.logo, group: current.group });
      id++; current = null;
    }
  }
  return channels;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const action = url.searchParams.get('action');
    const headers = { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" };
    const m3uText = await fetch(PLAYLIST_URL).then(r=>r.text());
    const channels = parseM3U(m3uText);

    if (action === 'handshake' || action === 'do_handshake' || action === null) {
      // Return handshake for root too so browser test looks cleaner
      if(url.searchParams.has('action')) {
        return new Response(JSON.stringify({ js: { token: "123", id: "1", status: "OK" } }), { headers });
      }
    }
    if (action === 'get_profile') {
      return new Response(JSON.stringify({ js: { id: "1", name: "Motel", status: "OK" } }), { headers });
    }
    if (action === 'get_genres') {
      const genres = [...new Set(channels.map(c=>c.group))].map((g,i)=>({id: (i+1).toString(), title: g, alias: g}));
      return new Response(JSON.stringify({ js: genres }), { headers });
    }
    // This is what STB Emu actually reads
    const js = {
      total_items: channels.length,
      max_page_items: 1000,
      data: channels.map(c=>({
        id: c.id.toString(),
        name: c.name,
        number: c.number.toString(),
        cmd: c.cmd, // <-- NO ffmpeg prefix
        logo: c.logo,
        tv_genre_id: "1"
      }))
    };
    return new Response(JSON.stringify({ js }), { headers });
  }
}
