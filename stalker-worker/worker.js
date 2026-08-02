export default {
 async fetch(req){
  const u=new URL(req.url);
  const action=u.searchParams.get('action');
  const h={"Access-Control-Allow-Origin":"*","Content-Type":"application/json"};
  if(action==='handshake'||action==='do_handshake'||u.pathname.endsWith('/c/')||u.pathname.endsWith('/c')) {
   return new Response(JSON.stringify({js:{token:"1",id:"1"}}),{headers:h});
  }
  if(action==='get_profile') return new Response(JSON.stringify({js:{id:"1",name:"Motel"}}),{headers:h});
  if(action==='get_genres') return new Response(JSON.stringify({js:[{id:"1",title:"All Channels"}]}),{headers:h});
  if(!action){
   const PLAYLIST_URL="https://raw.githubusercontent.com/wpgx/Motel/main/motel.m3u8";
   function parseM3U(t){let l=t.split('\n'),c=[],id=1,cur=null;for(let x of l){x=x.trim();if(x.startsWith('#EXTINF:')){let n=x.split(',').pop().trim();let lo=(x.match(/tvg-logo="([^"]+)"/)||[])[1]||"";cur={name:n,logo:lo}}else if(x&&!x.startsWith('#')&&cur){c.push({id,name:cur.name,cmd:x,logo:cur.logo});id++;cur=null}}return c}
   const txt=await fetch(PLAYLIST_URL).then(r=>r.text());
   const chs=parseM3U(txt);
   // for ordered list without action param still handled
  }
  // playlist fetch
  const PLAYLIST_URL="https://raw.githubusercontent.com/wpgx/Motel/main/motel.m3u8";
  function parseM3U(t){let l=t.split('\n'),c=[],id=1,cur=null;for(let x of l){x=x.trim();if(x.startsWith('#EXTINF:')){let n=x.split(',').pop().trim()||`Ch ${id}`;cur={name:n}}else if(x&&!x.startsWith('#')&&cur){c.push({id,name:cur.name,cmd:x});id++;cur=null}}return c}
  const txt=await fetch(PLAYLIST_URL).then(r=>r.text());
  const chs=parseM3U(txt);
  if(action && (action.includes('ordered')||action.includes('get_all'))){
   const data=chs.map(c=>({id:c.id+"",name:c.name,number:c.id+"",cmd:c.cmd,tv_genre_id:"1"}));
   return new Response(JSON.stringify({js:{total_items:data.length,max_page_items:500,data}}),{headers:h});
  }
  if(action && action.includes('create_link')){
   const id=u.searchParams.get('id')||"1";
   const ch=chs.find(x=>x.id+""===id)||chs[0];
   return new Response(JSON.stringify({js:{cmd:ch.cmd}}),{headers:h});
  }
  return new Response(JSON.stringify({js:{token:"1"}}),{headers:h});
 }
}
