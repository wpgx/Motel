export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const action = url.searchParams.get('action') || url.searchParams.get('type') || '';

    // Load your m3u from the same repo deployment
    const m3uUrl = new URL('/motel.m3u8', url.origin).href;
    const m3uText = await fetch(m3uUrl).then(r=>r.text()).catch(()=>'');

    function parseM3U(text){
      let channels=[], id=1, cur={};
      text.split('\n').forEach(line=>{
        line=line.trim();
        if(line.startsWith('#EXTINF:')){
          let name = line.split(',').pop().trim();
          let logo = (line.match(/tvg-logo="([^"]+)"/)||[])[1]||'';
          let group = (line.match(/group-title="([^"]+)"/)||[])[1]||'Motel TV';
          cur={name, logo, group};
        } else if(line &&!line.startsWith('#')){
          channels.push({
            id: String(id),
            name: cur.name || `Channel ${id}`,
            number: String(id),
            tv_genre_id: '1',
            logo: cur.logo || '',
            group: cur.group,
            cmd: line,
            use_http_tmp_link: 0,
            genres_str: cur.group
          });
          id++;
        }
      });
      return channels;
    }

    const channels = parseM3U(m3uText);
    const cors = { 'Access-Control-Allow-Origin':'*', 'Content-Type':'application/json' };

    if(action==='handshake' || url.pathname.includes('handshake')){
      return new Response(JSON.stringify({js:{token:'12345', random:'1234'}}), {headers:cors});
    }
    if(action==='get_profile'){
      return new Response(JSON.stringify({js:{
        stb_type:'MAG250', version:'Motel 1.0', fname:'Guest',
        account: 'Motel Guest'
      }}), {headers:cors});
    }
    if(action==='get_genres'){
      let groups=[...new Set(channels.map(c=>c.group))];
      let genres=groups.map((g,i)=>({id:String(i+1), title:g, alias:g.toLowerCase()}));
      return new Response(JSON.stringify({js:genres}), {headers:cors});
    }
    if(action.includes('channel') || action==='get_ordered_list' || action==='get_all_channels' || action==='get_channels'){
      return new Response(JSON.stringify({js:{data:channels, total_items:channels.length, max_page_items:500}}), {headers:cors});
    }
    // default empty
    return new Response(JSON.stringify({js:[]}), {headers:cors});
  }
}
