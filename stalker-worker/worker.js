const PLAYLIST_URL = "https://raw.githubusercontent.com/wpgx/Motel/main/dctv.m3u8";
let CACHE = { text: "", time: 0 };

async function getChannels() {
  // cache for 5 min so STB doesn't timeout
  if (Date.now() - CACHE.time < 300000 && CACHE.text) {
    return parseM3U(CACHE.text);
  }
  try {
    const r = await fetch(PLAYLIST_URL, { cf: { cacheTtl: 300 } });
    const txt = await r.text();
    CACHE = { text: txt, time: Date.now() };
    return parseM3U(txt);
  } catch(e) {
    return [];
  }
}

function parseM3U(text) {
  let lines = text.split('\n'), channels = [], id = 1, cur = null;
  for (let line of lines) {
    line = line.trim();
    if (line.startsWith('#EXTINF:')) {
      let name = line.split(',').pop().trim() || `Channel ${id}`;
      let logo = (line.match(/tvg-logo="([^"]+)"/)||[])[1] || "";
      cur = { name, logo };
    } else if (line &&!line.startsWith('#') && cur) {
      if(line.startsWith('http')) {
        channels.push({ id, name: cur.name, cmd: line, logo: cur.logo });
        id++;
      }
      cur = null;
    }
  }
  return channels;
}

export default {
  async fetch(req) {
    const url = new URL(req.url);
    const action = url.searchParams.get('action') || "";
    const headers = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "*",
      "Content-Type": "application/json"
    };

    const channels = await getChannels();

    // STB handshake - must work for /c/ AND /c/server/load.php
    if (action === "" || action.includes('handshake')) {
      return new Response(JSON.stringify({ js: { token: "1", id: "1", random: "123" } }), { headers });
    }
    if (action.includes('get_profile')) {
      return new Response(JSON.stringify({ js: { id: "1", name: "Motel DCTV", stb_type: "MAG250" } }), { headers });
    }
    if (action.includes('get_genres')) {
      return new Response(JSON.stringify({ js: [{ id: "1", title: "Live", alias: "live" }] }), { headers });
    }
    if (action.includes('get_ordered_list') || action.includes('get_all_channels') || action.includes('get_ordered')) {
      const data = channels.slice(0, 400).map(c => ({
        id: c.id+"", name: c.name, number: c.id+"", cmd: c.cmd,
        logo: c.logo, tv_genre_id: "1", use_http_tmp_link: 0
      }));
      return new Response(JSON.stringify({ js: { total_items: data.length, max_page_items: 500, data } }), { headers });
    }
    if (action.includes('create_link') || action.includes('get_link') || action.includes('get_ordered')) {
      const id = url.searchParams.get('id') || "1";
      const ch = channels.find(x => x.id+"" === id) || channels[0];
      return new Response(JSON.stringify({ js: { id: id, cmd: ch? ch.cmd : "", storage: 0, use_http_tmp_link: 0 } }), { headers });
    }
    return new Response(JSON.stringify({ js: {} }), { headers });
  }
}
