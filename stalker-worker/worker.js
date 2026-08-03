export default {
  async fetch(req) {
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null,{headers:{"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"GET, POST, OPTIONS","Access-Control-Allow-Headers":"*"}});

    let p = {};
    url.searchParams.forEach((v,k)=>p[k]=v);
    if (req.method==="POST"){
      const t = await req.text().catch(()=>"" );
      if(t){ try{ new URLSearchParams(t).forEach((v,k)=>p[k]=v); }catch(e){} try{Object.assign(p,JSON.parse(t))}catch(e){} }
    }
    let action = (p.action||"").toLowerCase();
    if(!action) action = "handshake"; // FORCE - if no action, treat as handshake

    const CH = [
      {id:"1", name:"Bunny Test", num:"1", cmd:"ch1", url:"https://test-streams.mux.dev/x36xhzz.m3u8"},
      {id:"2", name:"Sintel Test", num:"2", cmd:"ch2", url:"https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8"},
    ];
    const map = {ch1:CH[0],ch2:CH[1]};

    let js={};
    if(action==="handshake") js={token:"aabbccddeeff11223344556677889900", random:"123456", not_valid:0, id:"1"};
    else if(action==="get_profile") js={stb_type:"MAG250", sn:"0000001", ver:"0.2.18", mac:p.mac||"00:1A:79:00:00:01", auth:1};
    else if(action==="get_genres") js=[{id:"1", alias:"all", title:"All"}];
    else if(action.includes("ordered")||action.includes("all_channels")) js={total_items:2,max_page_items:14,cur_page:1,total_pages:1,data:CH.map(c=>({id:c.id,name:c.name,number:c.num,cmd:c.cmd,tv_genre_id:"1", use_http_tmp_link:0}))};
    else if(action==="create_link"){ const ch=map[p.cmd]||CH[0]; js={cmd:`ffmpeg ${ch.url}`, id:ch.id, storage_name:"", error:""}; }

    return new Response(JSON.stringify({js}),{headers:{"Access-Control-Allow-Origin":"*","Content-Type":"text/plain; charset=utf-8","Cache-Control":"no-cache"}});
  }
}
