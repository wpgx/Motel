const PLAYLIST_URL="https://raw.githubusercontent.com/wpgx/Motel/main/motel.m3u8";
function parseM3U(t){let l=t.split('\n'),c=[],id=1,cur=null;for(let x of l){x=x.trim();if(x.startsWith('#EXTINF:')){let n=x.split(',').pop().trim()||`Ch ${id}`;let lo=(x.match(/tvg-logo="([^"]+)"/)||[])[1]||"";let gr=(x.match(/group-title="([^"]+)"/)||[])[1]||"General";cur={name:n,logo:lo,group:gr}}else if(x&&!x.startsWith('#')&&cur){c.push({id,name:cur.name,cmd:x,logo:cur.logo,group:cur.group});id++;cur=null}}return c}
export default{
 async fetch(req){
  const u=new URL(req.url); const a=u.searchParams.get('action');
  const txt=await fetch(PLAYLIST_URL).then(r=>r.text());
  const chs=parseM3U(txt);
  const h={"Access-Control-Allow-Origin":"*","Content-Type":"application/json"};
  if(!a){return new Response("<html><body style=background:#000;color:#fff><h2>STB Portal Active - Open in STB Emu as portal, not browser</h2></body></html>",{headers:{"Content-Type":"text/html"}})}
  if(a==='handshake'||a==='do_handshake') return new Response(JSON.stringify({js:{token:"1",id:"1"}}),{headers:h});
  if(a==='get_profile') return new Response(JSON.stringify({js:{id:"1",name:"Motel"}}),{headers:h});
  if(a==='get_genres'){
   // ONLY 1 CATEGORY - NO STUCK
   return new Response(JSON.stringify({js:[{id:"1",title:"All Channels",alias:"all"}]}),{headers:h});
  }
  if(a.includes('ordered_list')||a.includes('get_all')||a.includes('get_ordered')){
   const data=chs.map(c=>({id:c.id+"",name:c.name,number:c.id+"",cmd:c.cmd,logo:c.logo,tv_genre_id:"1"}));
   return new Response(JSON.stringify({js:{total_items:data.length,max_page_items:500,data}}),{headers:h});
  }
  if(a.includes('create_link')||a.includes('get_link')){
   const id=u.searchParams.get('id')||"1";
   const ch=chs.find(x=>x.id+""===id)||chs[0];
   return new Response(JSON.stringify({js:{cmd:ch.cmd}}),{headers:h});
  }
  return new Response(JSON.stringify({js:[]}),{headers:h});
 }
}
