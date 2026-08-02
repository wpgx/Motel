const PLAYLIST_URL = "https://raw.githubusercontent.com/wpgx/Motel/main/dctv.m3u8";

export default {
  async fetch(req) {
    const url = new URL(req.url);
    const action = url.searchParams.get('action') || "";

    // API still needed for some STB modes
    if (action) {
      const headers = { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" };
      if (action.includes('handshake')) return new Response(JSON.stringify({ js: { token: "1" } }), { headers });
      if (action.includes('get_profile')) return new Response(JSON.stringify({ js: { name: "Motel" } }), { headers });
      if (action.includes('get_genres')) return new Response(JSON.stringify({ js: [{ id: "1", title: "Live" }] }), { headers });
      // ordered list and create_link will be handled by HTML page directly, not needed
      return new Response(JSON.stringify({ js: {} }), { headers });
    }

    // NO ACTION = serve actual portal HTML player (not JSON!)
    const html = `<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<style>body{margin:0;background:#000;color:#fff;font-family:sans-serif;display:flex;height:100vh} #list{width:320px;background:#111;overflow:auto} #list div{padding:10px;border-bottom:1px solid #222;cursor:pointer} #list div:hover{background:#333} #player{flex:1;background:#000} video{width:100%;height:100%}</style>
</head><body>
<div id="list">Loading dctv.m3u8...</div>
<div id="player"><video id="v" controls autoplay></video></div>
<script>
const PLAYLIST="${PLAYLIST_URL}";
async function load(){
  const txt=await fetch(PLAYLIST).then(r=>r.text());
  let lines=txt.split('\\n'),chs=[],cur=null;
  for(let l of lines){l=l.trim();if(l.startsWith('#EXTINF:')){cur=l.split(',').pop();}else if(l&&!l.startsWith('#')&&cur&&l.startsWith('http')){chs.push({name:cur,url:l});cur=null;}}
  const list=document.getElementById('list');list.innerHTML='';
  const v=document.getElementById('v');
  chs.slice(0,300).forEach(c=>{
    const d=document.createElement('div');d.textContent=c.name;
    d.onclick=()=>{v.src=c.url;v.play();};
    list.appendChild(d);
  });
  if(chs[0]){v.src=chs[0].url;v.play();}
}
load();
</script>
</body></html>`;
    return new Response(html, { headers: { "Content-Type": "text/html", "Access-Control-Allow-Origin": "*" } });
  }
}
