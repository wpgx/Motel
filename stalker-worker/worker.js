export default{
  async fetch(req){
    const url=new URL(req.url);
    const act=url.searchParams.get('action')||"";
    const J={"Content-Type":"application/json","Access-Control-Allow-Origin":"*"};
    if(act.includes('handshake')||act.includes('get_profile')||act.includes('get_genres')||act.includes('get_ordered_list')||act.includes('create_link')||act.includes('get_events')){
      // dummy JSON so Pro doesn't crash if it tries API
      return new Response(JSON.stringify({js:{token:"1",id:"1",data:[],total_items:2}}),{headers:J});
    }
    // MAIN TV BOX UI - served at /c/
    const html=`<html><head><meta charset="utf-8"><style>
body{margin:0;background:#0a1628;color:#fff;font-family:Arial;display:flex;height:100vh}
#list{width:380px;background:#12233f;overflow-y:auto;border-right:2px solid #1e3a5f}
.ch{padding:14px 16px;border-bottom:1px solid #1a2f50;cursor:pointer;display:flex;align-items:center}
.ch.active{background:#1e90ff}
#videoWrap{flex:1;background:#000;position:relative;display:flex;align-items:center;justify-content:center}
#player{width:100%;height:100%;background:#000}
#info{position:absolute;bottom:20px;left:20px;background:rgba(0,0,0,.7);padding:10px 20px;border-radius:6px}
</style></head><body>
<div id="list"></div>
<div id="videoWrap"><video id="player" controls autoplay></video><div id="info">Select channel</div></div>
<script>
const CHS=[
 {name:"BUNNY HD",url:"https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"},
 {name:"SINTEL HD",url:"https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8"},
 {name:"DCTV TEST",url:"https://raw.githubusercontent.com/wpgx/Motel/main/dctv.m3u8"}
];
const list=document.getElementById('list'), video=document.getElementById('player'), info=document.getElementById('info');
let idx=0;
function render(){
 list.innerHTML='';
 CHS.forEach((c,i)=>{
  const d=document.createElement('div'); d.className='ch'+(i===idx?' active':''); d.textContent=(i+1)+'. '+c.name;
  d.onclick=()=>play(i); list.appendChild(d);
 });
}
function play(i){
 idx=i; const c=CHS[i]; info.textContent=c.name;
 try{
  if(window.gSTB){ gSTB.Stop(); gSTB.Play(c.url); info.textContent=c.name+' (gSTB)'; }
  else { 
   if(Hls.isSupported()){ const hls=new Hls(); hls.loadSource(c.url); hls.attachMedia(video); }
   else video.src=c.url; video.play();
  }
 }catch(e){ video.src=c.url; video.play(); }
 render();
}
document.addEventListener('keydown',e=>{
 if(e.key==='ArrowDown'){ idx=Math.min(CHS.length-1,idx+1); render(); e.preventDefault();}
 if(e.key==='ArrowUp'){ idx=Math.max(0,idx-1); render(); e.preventDefault();}
 if(e.key==='Enter'){ play(idx); }
});
render();
</script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.7/dist/hls.min.js"></script>
</body></html>`;
    return new Response(html,{headers:{"Content-Type":"text/html","Access-Control-Allow-Origin":"*"}});
  }
}
