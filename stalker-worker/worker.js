const PLAYLIST_URL="https://raw.githubusercontent.com/wpgx/Motel/main/motel.m3u8";
function parseM3U(t){let l=t.split('\n'),c=[],id=1,cur=null;for(let x of l){x=x.trim();if(x.startsWith('#EXTINF:')){let n=x.split(',').pop().trim()||`Ch ${id}`;let lo=(x.match(/tvg-logo="([^"]+)"/)||[])[1]||"";let gr=(x.match(/group-title="([^"]+)"/)||[])[1]||"General";cur={name:n,logo:lo,group:gr}}else if(x&&!x.startsWith('#')&&cur){c.push({id,name:cur.name,cmd:x,logo:cur.logo,group:cur.group});id++;cur=null}}return c}
const HTML_PAGE = `
<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Motel TV</title>
<style>body{margin:0;background:#000;color:#fff;font-family:sans-serif;display:flex;height:100vh}#list{width:380px;background:#111;overflow-y:auto}.ch{padding:14px;border-bottom:1px solid #222;display:flex;gap:10px;align-items:center;outline:none}.ch:focus{background:#0a84ff;outline:3px solid #fff}.ch img{width:44px;height:44px;object-fit:contain}#player{flex:1;background:#000;display:flex;align-items:center;justify-content:center}video{width:100%;height:100%}#search{width:100%;padding:12px;background:#222;color:#fff;border:none;position:sticky;top:0}</style>
</head><body>
<div id="list"><input id="search" placeholder="Search 185 channels..."><div id="channels">Loading...</div></div>
<div id="player"><video id="video" controls autoplay></video></div>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<script>
let allChannels=[];
async function loadList(){
 let r=await fetch('/playlist'); let j=await r.json(); allChannels=j.data;
 let box=document.getElementById('channels'); box.innerHTML='';
 j.data.forEach(function(ch){
  let d=document.createElement('div'); d.className='ch'; d.tabIndex=0;
  d.innerHTML='<img src="'+(ch.logo||'')+'"><div><b>'+ch.name+'</b><br><small>'+ch.group+'</small></div>';
  d.addEventListener('click',function(){playCh(ch.cmd)});
  d.addEventListener('keydown',function(e){if(e.key==='Enter'){playCh(ch.cmd)}});
  box.appendChild(d);
 });
 let f=document.querySelector('.ch'); if(f) f.focus();
}
function playCh(url){
 let v=document.getElementById('video');
 if(window.Hls && Hls.isSupported()){let h=new Hls();h.loadSource(url);h.attachMedia(v);h.on(Hls.Events.MANIFEST_PARSED,function(){v.play()})}
 else{v.src=url;v.play()}
}
document.getElementById('search').addEventListener('input',function(e){
 let q=e.target.value.toLowerCase();
 let filtered=allChannels.filter(function(c){return c.name.toLowerCase().includes(q)});
 let box=document.getElementById('channels'); box.innerHTML='';
 filtered.forEach(function(ch){
  let d=document.createElement('div'); d.className='ch'; d.tabIndex=0;
  d.innerHTML='<img src="'+(ch.logo||'')+'"><div><b>'+ch.name+'</b></div>';
  d.addEventListener('click',function(){playCh(ch.cmd)}); box.appendChild(d);
 });
});
loadList();
</script>
</body></html>
`;
export default {
 async fetch(req){
  const u=new URL(req.url); const a=u.searchParams.get('action'); const p=u.pathname;
  if(p==='/playlist'){const t=await fetch(PLAYLIST_URL).then(r=>r.text());const chs=parseM3U(t);return new Response(JSON.stringify({data:chs}),{headers:{"Access-Control-Allow-Origin":"*","Content-Type":"application/json"}})}
  if(p==='/'&&!a){return new Response(HTML_PAGE,{headers:{"Content-Type":"text/html"}})}
  const h={"Access-Control-Allow-Origin":"*","Content-Type":"application/json"}; const txt=await fetch(PLAYLIST_URL).then(r=>r.text()); const chs=parseM3U(txt);
  if(a==='handshake'||a==='do_handshake'){return new Response(JSON.stringify({js:{token:"1234",id:"1"}}),{headers:h})}
  if(a==='get_profile'){return new Response(JSON.stringify({js:{id:"1",name:"Motel"}}),{headers:h})}
  if(a==='get_genres'){const g=[...new Set(chs.map(c=>c.group))].map((gg,i)=>({id:i+1+"",title:gg}));return new Response(JSON.stringify({js:g}),{headers:h})}
  if(a && (a.includes('ordered_list')||a==='get_all_channels')){const data=chs.map(c=>({id:c.id+"",name:c.name,number:c.id+"",cmd:c.cmd,logo:c.logo,tv_genre_id:"1"}));return new Response(JSON.stringify({js:{total_items:data.length,max_page_items:500,data}}),{headers:h})}
  if(a && (a.includes('create_link')||a.includes('get_link'))){const id=u.searchParams.get('id')||"1";const ch=chs.find(x=>x.id+""===id)||chs[0];return new Response(JSON.stringify({js:{cmd:ch.cmd}}),{headers:h})}
  return new Response(JSON.stringify({js:{total_items:chs.length}}),{headers:h})
 }
}
