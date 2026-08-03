export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders() });

    if (!url.pathname.includes("/stalker_portal/")) {
      return new Response("OK " + new Date().toISOString(), { headers: corsHeaders() });
    }

    // Parse GET + POST together (Pro sends POST)
    let params = {};
    url.searchParams.forEach((v,k) => params[k] = v);
    if (request.method === "POST") {
      try {
        const text = await request.text();
        if (text) {
          const form = new URLSearchParams(text);
          form.forEach((v,k) => params[k] = v);
          try { Object.assign(params, JSON.parse(text)); } catch(e){}
        }
      } catch(e){}
    }

    const action = (params.action || "").toLowerCase();

    // --- THIS IS THE FIX FOR YOUR TOP-LEFT JS ---
    // If no action = initial portal load, must return HTML, not JSON
    if (!action) {
      const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><script>window.onload=function(){}</script></head><body bgcolor="black"></body></html>`;
      return new Response(html, { headers: {...corsHeaders(), "Content-Type": "text/html; charset=utf-8" } });
    }

    const CHANNELS = [
      { id: "1", name: "Bunny Test", number: "1", cmd_id: "ch1", url: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" },
      { id: "2", name: "Sintel Test", number: "2", cmd_id: "ch2", url: "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8" },
    ];
    const map = Object.fromEntries(CHANNELS.map(c=>[c.cmd_id,c]));

    let jsData = {};
    switch (action) {
      case "handshake":
        jsData = { token: "1234567890abcdef1234567890abcdef", random: Math.random().toString(16).slice(2), not_valid:0 };
        break;
      case "get_profile":
        jsData = { mac: params.mac||"00:1A:79:00:00:01", stb_type:"MAG250", ver:"0.2.18", ac:1, auth:1 };
        break;
      case "get_genres":
        jsData = [{id:"1", alias:"all", title:"All"}];
        break;
      case "get_ordered_list":
      case "get_all_channels":
        jsData = {
          total_items: 2, max_page_items: 14, cur_page:1, total_pages:1,
          data: CHANNELS.map(c=>({ id:c.id, name:c.name, number:c.number, cmd:c.cmd_id, tv_genre_id:"1", use_http_tmp_link:0 }))
        };
        break;
      case "create_link":
        const cmd = params.cmd || "ch1";
        const ch = map[cmd] || CHANNELS[0];
        jsData = { cmd: `ffmpeg ${ch.url}`, id: ch.id, storage_name:"", error:"" };
        break;
      default:
        jsData = {};
    }

    // STB Emu Pro sometimes sends JsHttpRequest header - must return raw json, no wrapper
    return new Response(JSON.stringify({ js: jsData }), {
      headers: {...corsHeaders(), "Content-Type": "application/json; charset=utf-8", "Cache-Control":"no-cache" }
    });
  }
}
function corsHeaders(){ return {"
