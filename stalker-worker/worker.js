const PLAYLIST_URL="https://raw.githubusercontent.com/wpgx/Motel/main/motel.m3u8";
function parseM3U(t){let l=t.split('\n'),c=[],id=1,cur=null;for(let x of l){x=x.trim();if(x.startsWith('#EXTINF:')){let n=x.split(',').pop().trim()||`Ch ${id}`;let lo=(x.match(/tvg-logo="([^"]+)"/)||[])[1]||"";let gr=(x.match(/group-title="([^"]+)"/)||[])[1]||"All";cur={name:n,logo:lo,group:gr}}else if(x&&!x.startsWith('#')&&cur){c.push({id,name:cur.name,cmd:x,logo:cur.logo,group:cur.group});id++;cur=null}}return c}
export default{
 async fetch(req){
  const url=new URL(req.url);
  let action=url.searchParams.get('action');
  // STB Emu also sends type=stb and action in different case
  if(!action){
    // Try to get from path like /server/load.php?type=stb&action=...
    action=url.searchParams.get('JsHttpRequest')?url.searchParams.get('action'):null;
  }
  const txt=await fetch(PLAYLIST_URL).then(r=>r.text()).catch(()=>"#EXTINF:-1,Test\nhttp://test");
  const chs=parseM3U(txt);
  const h={"Access-Control-Allow-Origin":"*","Content-Type":"application/json","Cache-Control":"no-cache"};

  // ALWAYS return JSON for STB, never HTML for portal paths
  if(url.pathname.includes('load.php') || action){
    if(!action) action="handshake";
    if(action==='handshake'||action==='do_handshake'){
      return new Response(JSON.stringify({js:{token:"123456",id:"1",profile:{id:"1"}}}),{headers:h});
    }
    if(action==='get_profile'){
      return new Response(JSON.stringify({js:{id:"1",name:"Motel",stb_type:"MAG250",version:"2.18-r14-pub-250",api_version:"1.0"}}),{headers:h});
    }
    if(action==='get_genres'){
      return new Response(JSON.stringify({js:[{id:"1",title:"All Channels",alias:"all"}]}),{headers:h});
    }
    if(action.includes('ordered_list')||action.includes('get_all')||action==='get_ordered_list'||action==='get_ordered_list'){
      let page=parseInt(url.searchParams.get('p')||"1");
      let data=chs.map(c=>({id:c.id+"",name:c.name,number:c.id+"",cmd:c.cmd,logo:c.logo,tv_genre_id:"1",cmds:[c.cmd]}));
      return new Response(JSON.stringify({js:{total_items:data.length,max_page_items:5000,cur_page:page,data}}),{headers:h});
    }
    if(action.includes('create_link')||action.includes('get_link')||action==='get_short_epg'){
      let id=url.searchParams.get('id')||"1";
      let ch=chs.find(x=>x.id+""===id)||chs[0];
      return new Response(JSON.stringify({js:{id:id,cmd:ch.cmd,error:"" }}),{headers:h});
    }
    // default for any other action
    return new Response(JSON.stringify({js:{}}),{headers:h});
  }
  // Only for root browser visit, show info
  return new Response("Portal OK - use in STB Emu as: https://motel-portal.donxman.workers.dev/stalker_portal/c/",{headers:{"Content-Type":"text/plain"}});
 }
}
