const SRC="https://raw.githubusercontent.com/wpgx/Motel/main/dctv.m3u8";
let CHS=null;
async function getCHS(){if(CHS) return CHS; const t=await fetch(SRC).then(r=>r.text()); let a=[],cur=null,id=1; t.split('\n').forEach(l=>{l=l.trim(); if(l.startsWith('#EXTINF:')) cur=l.split(',').pop().trim(); else if(l&&!l.startsWith('#')&&cur&&l.startsWith('http')){a.push({id:id+"",name:cur,number:id+"",cmd:l,tv_genre_id:"1"}); id++; cur=null;}}); CHS=a; return a;}
export default{
  async fetch(req){
    const url=new URL(req.url); const act=url.searchParams.get('action')||"";
    const J={"Content-Type":"application/json","Access-Control-Allow-Origin":"*"};
    const H={"Content-Type":"text/html","Access-Control-Allow-Origin":"*"};
    if(!act) return new Response("<html><body style=background:#000></body></html>",{headers:H});
    const chs=await getCHS();
    if(act.includes('handshake')) return new Response(JSON.stringify({js:{token:"1",id:"1"}}),{headers:J});
    if(act.includes('get_profile')) return new Response(JSON.stringify({js:{id:"1",name:"Motel"}}),{headers:J});
    if(act.includes('get_genres')) return new Response(JSON.stringify({js:[{id:"1",title:"Live"}]}),{headers:J});
    if(act.includes('get_ordered_list')||act.includes('get_all_channels')){
      return new Response(JSON.stringify({js:{total_items:chs.length,max_page_items:500,data:chs}}),{headers:J});
    }
    if(act.includes('create_link')){
      const id=url.searchParams.get('id')||"1"; const c=chs.find(x=>x.id===id)||chs[0];
      return new Response(JSON.stringify({js:{id,cmd:c.cmd,storage:"0"}}),{headers:J});
    }
    return new Response(JSON.stringify({js:{}}),{headers:J});
  }
}
