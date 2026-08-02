const PLAYLIST_URL = "https://raw.githubusercontent.com/wpgx/Motel/main/motel.m3u8";
function parseM3U(t){let l=t.split('\n'),c=[],id=1,cur=null;for(let x of l){x=x.trim();if(x.startsWith('#EXTINF:')){let n=x.split(',').pop().trim()||`Ch ${id}`;let lo=(x.match(/tvg-logo="([^"]+)"/)||[])[1]||"";let gr=(x.match(/group-title="([^"]+)"/)||[])[1]||"General";cur={name:n,logo:lo,group:gr}}else if(x&&!x.startsWith('#')&&cur){c.push({id,name:cur.name,cmd:x,logo:cur.logo,group:cur.group});id++;cur=null}}return c}
export default{
 async fetch(req){
  const u=new URL(req.url); const a=u.searchParams.get('action');
  const h={"Access-Control-Allow-Origin":"*","Content-Type":"application/json"};
  const txt=await fetch(PLAYLIST_URL).then(r=>r.text()); const chs=parseM3U(txt);
  if(a==='handshake'||a==='do_handshake'||!a&&u.pathname.includes('stalker')){return new Response(JSON.stringify({js:{token:"1234",id:"1",status:"OK"}}),{headers:h})}
  if(a==='get_profile'){return new Response(JSON.stringify({js:{id:"1",name:"Motel"}}),{headers:h})}
  if(a==='get_genres'){const g=[...new Set(chs.map(c=>c.group))].map((gg,i)=>({id:(i+1)+"",title:gg}));return new Response(JSON.stringify({js:g}),{headers:h})}
  if(a==='get_ordered_list'||a==='get_all_channels'||a==='get_ordered_list_genre'||a==='get_ordered_list_genre_and_search'){
    const data=chs.map(c=>({id:c.id+"",name:c.name,number:c.id+"",cmd:c.cmd,logo:c.logo,tv_genre_id:"1"}));
    return new Response(JSON.stringify({js:{total_items:data.length,max_page_items:500,data}}),{headers:h})
  }
  if(a==='itv_create_link'||a==='create_link'||a==='get_link'||a==='itv_get_ordered_list'){
    const id=u.searchParams.get('id')||"1"; const ch=chs.find(x=>x.id+""===id)||chs[0];
    return new Response(JSON.stringify({js:{cmd:ch.cmd}}),{headers:h})
  }
  const data=chs.map(c=>({id:c.id+"",name:c.name,number:c.id+"",cmd:c.cmd,logo:c.logo}));
  return new Response(JSON.stringify({js:{total_items:data.length,max_page_items:500,data}}),{headers:h})
 }
}
