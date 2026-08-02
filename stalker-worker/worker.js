const PLAYLIST_URL = "https://raw.githubusercontent.com/wpgx/Motel/main/dctv.m3u8";
let CACHE = { text: "", time: 0 };

async function getChannels() {
  if (Date.now() - CACHE.time < 300000 && CACHE.text) return parseM3U(CACHE.text);
  try {
    const txt = await fetch(PLAYLIST_URL, { cf: { cacheTtl: 300 } }).then(r=>r.text());
    CACHE = { text: txt, time: Date.now() };
    return parseM3U(txt);
  } catch { return []; }
}
function parseM3U(text) {
  let lines = text.split('\n'), channels = [], id = 1, cur = null;
  for (let l of lines) {
    l = l.trim();
    if (l.startsWith('#EXTINF:')) {
      let name = l.split(',').pop().trim() || `Ch ${id}`;
      let logo = (l.match(/tvg-logo="([^"]+)"/)||[])[1] || "";
      cur = { name, logo };
    } else if (l &&!l.startsWith('#') && cur && l.startsWith('http')) {
      channels.push({ id, name: cur.name, cmd: l, logo: cur.logo });
      id++; cur = null;
    }
  }
  return channels;
}

export default {
  async fetch(req) {
    const url = new URL(req.url);
    const action = url.searchParams.get('action') || "";
    const path = url.pathname;

    // 1. NO ACTION = return HTML so you DON'T see {"js":{"token"...}}
    if (action === "") {
      return new Response(`<html><head><meta charset="utf-8"></head><body style="background:#000;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif"><h2>Motel Portal Loading...<br><small>${path}</small></h2></body></html>`, {
        headers: { "Content-Type": "text/html", "Access-Control-Allow-Origin": "*" }
      });
    }

    // 2. WITH ACTION = return JSON
    const headers = { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" };
    const channels = await getChannels();

    if (action.includes('handshake')) {
      return new Response(JSON.stringify({ js: { token: "1", id: "1" } }), { headers });
    }
    if (action.includes('get_profile')) {
      return new Response(JSON.stringify({ js: { id: "1", name: "Motel DCTV" } }), { headers });
    }
    if (action.includes('get_genres')) {
      return new Response(JSON.stringify({ js: [{ id: "1", title: "Live" }] }), { headers });
    }
    if (action.includes('get_ordered_list') || action.includes('get_all_channels')) {
      const data = channels.slice(0, 300).map(c => ({ id: c.id+"", name: c.name, number: c.id+"", cmd: c.cmd, logo: c.logo, tv_genre_id: "1" }));
      return new Response(JSON.stringify({ js: { total_items: data.length, max_page_items: 500, data } }), { headers });
    }
    if (action.includes('create_link')) {
      const id = url.searchParams.get('id') || "1";
      const ch = channels.find(x => x.id+"" === id) || channels[0];
      return new Response(JSON.stringify({ js: { cmd: ch? ch.cmd : "", id } }), { headers });
    }
    return new Response(JSON.stringify({ js: {} }), { headers });
  }
}
