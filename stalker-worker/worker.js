export default{
  async fetch(req){
    const url=new URL(req.url);
    const act=url.searchParams.get('action')||"";
    const J={"Content-Type":"application/json","Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*"};
    if(req.method==="OPTIONS") return new Response("",{headers:J});
    if(!act) return new Response("<html><body style=background:#000></body></html>",{headers:{"Content-Type":"text/html"}});

    const CHS=[
      {id:"1",name:"BUNNY HD",number:"1",cmd:"https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",tv_genre_id:"1",logo:"",use_http_tmp_link:0},
      {id:"2",name:"SINTEL HD",number:"2",cmd:"https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8",tv_genre_id:"1",logo:"",use_http_tmp_link:0}
    ];

    if(act.includes('handshake')){
      return new Response(JSON.stringify({js:{token:"1234", id:"1", ip:"127.0.0.1"}}),{headers:J});
    }
    if(act.includes('get_profile')){
      return new Response(JSON.stringify({js:{id:"1", name:"Motel", stb_type:"MAG250", version:"ImageDescription: 0.2.18-r11-pub-250"}}),{headers:J});
    }
    if(act.includes('get_genres')){
      return new Response(JSON.stringify({js:[{id:"1", title:"Live", alias:"live"}]}),{headers:J});
    }
    if(act.includes('get_ordered_list')||act.includes('get_all_channels')){
      return new Response(JSON.stringify({js:{total_items:CHS.length, max_page_items:14, selected_item:1, cur_page:1, data:CHS}}),{headers:J});
    }
    if(act.includes('create_link')||act.includes('get_link')){
      const id=url.searchParams.get('id')||"1";
      const c=CHS.find(x=>x.id===id)||CHS[0];
      const cmd=c.cmd;
      return new Response(JSON.stringify({js:{id:id, cmd:cmd, storage:"0", cmds:[{id:"1", ch_id:id, cmd:cmd, storage:"0"}]}}),{headers:J});
    }
    if(act.includes('get_events')){
      const now=Math.floor(Date.now()/1000);
      return new Response(JSON.stringify({js:{events:[{id:"1", name:"Live", start_timestamp:now-3600, stop_timestamp:now+7200}]}}),{headers:J});
    }
    return new Response(JSON.stringify({js:{}}),{headers:J});
  }
}
