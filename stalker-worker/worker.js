const SRC = "https://raw.githubusercontent.com/wpgx/Motel/main/dctv.m3u8";
export default {
  async fetch(req){
    const u=new URL(req.url);
    if(u.searchParams.get('action')) return new Response(JSON.stringify({js:{token:"1"}}),{headers:{"Content-Type":"application/json"}});
    const html=`<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{margin:0;padding:0;background:#000;color:#fff;height:100%;font-family:Arial}
#wrap{display:flex;height:100vh}
#list{width:360px;background:#151515;overflow-y:auto}
.item{padding:11px;border-bottom:1px solid #222;color:#ccc}
.item.sel{background:#0a84ff;color:#fff;font-weight:bold}
#box{flex:1;background:#000;display:flex;align-items:center;justify-content:center;flex-direction:column}
video{width:100%;height:100%;background:#000}
#title{padding:8px;background:#222;width:100%;box-sizing:border-box}
</style><script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script></head><body>
<div id="wrap"><div id="list">Loading...</div><div id="box"><div id="title">Motel DCTV - UP/DOWN + OK</div><video id="v" controls autoplay></video></div></div>
<script>
let ch=[],p=0; const L=document.getElementById('list'), V=document.getElementById('v'), T=document.getElementById('title');
function sel(i){ p=i; [...L.children].forEach((e,j)=>e.className=j==i?'item sel':'item'); L.children[i]?.scrollIntoView({block:'nearest'}); }
function play(i){ const c=ch[i]; if(!c) return; p=i; sel(i); T.textContent=c.n; if(Hls.isSupported()&&c.u.includes('m3u8')){ const h=new Hls(); h.loadSource(c.u); h.attachMedia(V); h.on(Hls.Events.MANIFEST_PARSED,()=>V.play()); } else { V.src=c.u; V.play(); } }
document.addEventListener('keydown',e=>{ const k=e.keyCode; if(k==38||k==19){ p=Math.max(0,p-1); sel(p); } if(k==40||k==20){ p=Math.min(ch.length-1,p+1); sel(p); } if(k==13){ play(p); } });
(async()=>{ const t=await fetch("${SRC}").then(r=>r.text()); let cur=null; for(let l of t.split('\\n')){ l=l.trim(); if(l.startsWith('#EXTINF:')) cur=l.split(',').pop(); else if(l&&!l.startsWith('#')&&cur&&l.startsWith('http')){ ch.push({n:cur,u:l}); cur=null; } } L.innerHTML=''; ch.slice(0,400).forEach((c,i)=>{ const d=document.createElement('div'); d.className='item'+(i==0?' sel':''); d.textContent=(i+1)+'. '+c.n; d.onclick=()=>play(i); L.appendChild(d); }); if(ch[0]) play(0); })();
</script></body></html>`;
    return new Response(html,{headers:{"Content-Type":"text/html"}});
  }
}
