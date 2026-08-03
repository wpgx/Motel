export default{
  async fetch(req){
    const J={"Content-Type":"application/json","Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"*"};
    if(req.method==="OPTIONS") return new Response("",{headers:J});

    let url=new URL(req.url);
    let params=url.searchParams;
    if(req.method==="POST"){
      const b=await req.text();
      const p=new URLSearchParams(b);
      for(const [k,v] of p) params.set(k,v);
    }
    const act=params.get('action')||"";
    const id=params.get('id')||"1";

    if(!act){
      return new Response("<html><body style=background:#000></body></html>",{headers:{"Content-Type":"text/html"}});
    }

    const CHS=[
      {id:"1",name:"BUNNY TEST",number:"1",cmd:"https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",tv_genre_id:"1",use_http_tmp_link:0,genre_id:"1"},
      {id:"2",name:"SINTEL TEST",number:"2",cmd:"https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8",tv_genre_id:"1",use_http_tmp_link:0,genre_id:"1"}
    ];

    if(act.includes('handshake')){
      return new Response(JSON.stringify({js:{token:"12345",id:"1",result:0}}),{headers:J});
    }
    if(act.includes('get_profile')){
      return new Response(JSON.stringify({js:{id:"1",stb_type:"MAG250",version:"0.2.18-r22",api_version:"349"}}),{headers:J});
    }
    if(act.includes('get_genres')){
      return new Response(JSON.stringify({js:[{id:"1",title:"Live TV",alias:"live"}]}),{headers:J});
    }
    if(act.includes('get_ordered_list')||act.includes('get_all_channels')||act.includes('get_order')){
      return new Response(JSON.stringify({js:{total_items:CHS.length,max_page_items:14,cur_page:1,selected_item:1,data:CHS}}),{headers:J});
    }
    if(act.includes('create_link')||act.includes('get_link')||act.includes('do_order')){
      const c=CHS.find(x=>x.id===id)||CHS[0];
      return new Response(JSON.stringify({js:{id:id,info:{name:c.name},cmd:c.cmd,cmds:[{id:"1",ch_id:id,cmd:c.cmd}]}}),{headers:J});
    }
    if(act.includes('get_events')){
      const now=Math.floor(Date.now()/1000);
      return new Response(JSON.stringify({js:{events:[{id:"1",name:"Live",start_timestamp:now-3600,stop_timestamp:now+3600}]}}),{headers:J});
    }
    return new Response(JSON.stringify({js:{}}),{headers:J});
  }
}
