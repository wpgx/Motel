const PLAYLIST_URL = "https://raw.githubusercontent.com/wpgx/Motel/main/motel.m3u8";

function parseM3U(text) {
  let lines = text.split('\n'), channels = [], id = 1, cur = null;
  for (let line of lines) {
    line = line.trim();
    if (line.startsWith('#EXTINF:')) {
      let name = line.split(',').pop().trim() || `Ch ${id}`;
      let logo = (line.match(/tvg-logo="([^"]+)"/)||[])[1] || "";
      cur = { name, logo };
    } else if (line &&!line.startsWith('#') && cur) {
      channels.push({ id, name: cur.name, cmd: line, logo: cur.logo });
      id++; cur = null;
    }
  }
  return channels;
}

export default {
  async fetch(req) {
    const url = new URL(req.url);
    const action = url.searchParams.get('action');
    const path = url.pathname;

    // 1. If request is for /c/ or /stalker_portal/c/ WITHOUT action -> return HTML (not JSON)
    // This is what STB shows for 1 second before loading channels
    if (!action && (path.endsWith('/c/') || path.endsWith('/c') || path.includes('/stalker_portal'))) {
      if (!path.includes('load.php')) {
        return new Response(`<html><body style="background:#000;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif"><h2>Portal Loading... Please wait</h2></body></html>`, {
          headers: { "Content-Type": "text/html", "Access-Control-Allow-Origin": "*" }
        });
      }
    }

    // 2. All API calls return JSON
    const headers = { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" };

    let channels = [];
    try {
      const txt = await fetch(PLAYLIST_URL).then(r=>r.text());
      channels = parseM3U(txt);
    } catch(e){}

    if (!action) return new Response(JSON.stringify({js:{token:"1",id:"1"}}),{headers});

    if (action.includes('handshake') || action.includes('do_handshake')) {
      return new Response(JSON.stringify({js:{token:"1",id:"1",random:"123"}}),{headers});
    }
    if (action.includes('get_profile')) {
      return new Response(JSON.stringify({js:{id:"1",name:"Motel",stb_type:"MAG250",version:"2.18"}}),{headers});
    }
    if (action.includes('get_genres')) {
      return new Response(JSON.stringify({js:[{id:"1",title:"All Channels",alias:"all"}]}),{headers});
    }
    if (action.includes('get_ordered_list') || action.includes('get_all_channels') || action.includes('get_ordered')) {
      const data = channels.map(c=>({id:c.id+"",name:c.name,number:c.id+"",cmd:c.cmd,logo:c.logo,tv_genre_id:"1",use_http_tmp_link:0}));
      return new Response(JSON.stringify({js:{total_items:data.length,max_page_items:500,data}}),{headers});
    }
    if (action.includes('create_link') || action.includes('get_link')) {
      const id = url.searchParams.get('id') || "1";
      const ch = channels.find(x=>x.id+""===id) || channels[0];
      return new Response(JSON.stringify({js:{id:id,cmd:ch?ch.cmd:"",storage:0}}),{headers});
    }
    // Anything else STB asks for - return empty ok so it doesn't loop back to handshake
    return new Response(JSON.stringify({js:{}}),{headers});
  }
}
