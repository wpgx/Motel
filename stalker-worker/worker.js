const PLAYLIST_URL = "https://raw.githubusercontent.com/wpgx/Motel/main/dctv.m3u8";
let CACHE = { text: "", time: 0 };
async function getChannels() {
  if (Date.now() - CACHE.time < 300000 && CACHE.text) return parseM3U(CACHE.text);
  try {
    const txt = await fetch(PLAYLIST_URL).then(r=>r.text());
    CACHE = { text: txt, time: Date.now() };
    return parseM3U(txt);
  } catch { return []; }
}
function parseM3U(t){
  let lines=t.split('\n'),chs=[],id=1,cur=null;
  for(let l of lines){l=l.trim();
    if(l.startsWith('#EXTINF:')){let n=l.split(',').pop().trim()||`Ch ${id}`;let lo=(l.match(/tvg-logo="([^"]+)"/)||[])[1]||"";cur={name:n,logo:lo};}
    else if(l&&!l.startsWith('#')&&cur&&l.startsWith('http')){chs.push({id,name:cur.name,cmd:l,logo:cur.logo});id++;cur=null;}
  } return chs;
}

export default {
  async fetch(req) {
    const url = new URL(req.url);
    const action = url.searchParams.get('action') || "";
    const ua = req.headers.get('User-Agent') || "";
    const isSTB = /MAG|STB|Qt|stb/i.test(ua);

    // If no action
    if (action === "") {
      // STB box asking /c/ -> give it JSON token (so it loads, no HTML shown)
      if (isSTB) {
        return new Response(JSON.stringify({ js: { token: "1", id: "1" } }), {
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
        });
      }
      // Human browser asking /c/ -> show nice page
      return new Response(`<html><body style="background:#000;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif"><h2>Motel Portal Running</h2></body></html>`, {
        headers: { "Content-Type": "text/html", "Access-Control-Allow-Origin": "*" }
      });
    }

    const headers = { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" };
    const channels = await getChannels();

    if (action.includes('handshake')) return new Response(JSON.stringify({ js: { token: "1", id: "1" } }), { headers });
    if (action.includes('get_profile')) return new Response(JSON.stringify({ js: { id: "1", name: "Motel" } }), { headers });
    if (action.includes('get_genres')) return new Response(JSON.stringify({ js: [{ id: "1", title: "Live" }] }), { headers });
    if (action.includes('get_ordered_list') || action.includes('get_all_channels')) {
      const data = channels.slice(0, 300).map(c=>({ id:c.id+"", name:c.name, number:c.id+"", cmd:c.cmd, logo:c.logo, tv_genre_id:"1" }));
      return new Response(JSON.stringify({ js: { total_items: data.length, max_page_items: 500, data } }), { headers });
    }
    if (action.includes('create_link')) {
      const id = url.searchParams.get('id') || "1";
      const ch = channels.find(x=>x.id+""===id) || channels[0];
      return new Response(JSON.stringify({ js: { cmd: ch? ch.cmd : "", id } }), { headers });
    }
    return new Response(JSON.stringify({ js: {} }), { headers });
  }
}
