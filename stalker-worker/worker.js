export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // CORS
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    // Only handle portal paths, otherwise show info
    if (!url.pathname.includes("/stalker_portal/")) {
      return new Response("Motel Portal OK - Use: /stalker_portal/c/ - " + new Date().toISOString(), { headers: corsHeaders() });
    }

    // --- PARSE PARAMS FROM BOTH GET + POST ---
    // STB Emu Pro sends POST with x-www-form-urlencoded body
    let params = {};
    url.searchParams.forEach((v,k) => params[k] = v);

    if (request.method === "POST") {
      try {
        const bodyText = await request.text();
        if (bodyText) {
          // try as form
          try {
            const bodyParams = new URLSearchParams(bodyText);
            bodyParams.forEach((v,k) => params[k] = v);
          } catch(e){}
          // try as json
          try {
            const json = JSON.parse(bodyText);
            params = {...params,...json };
          } catch(e){}
        }
      } catch(e){}
    }

    const action = (params.action || params.p1 || "").toLowerCase();
    const jsCallback = params.JsHttpRequest || "";

    // Test channels - KNOWN GOOD HLS
    const CHANNELS = [
      { id: "1", name: "Bunny Test", number: "1", cmd_id: "ch1", url: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", logo: "" },
      { id: "2", name: "Sintel Test", number: "2", cmd_id: "ch2", url: "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8", logo: "" },
    ];
    const channelMap = Object.fromEntries(CHANNELS.map(c => [c.cmd_id, c]));

    let jsData = {};

    switch (action) {
      case "handshake":
        // STB Emu Pro REQUIRES this to pass loading portal
        jsData = {
          token: "4f3d8c8e8a8e8a8e8a8e",
          random: Math.random().toString(36).substring(2),
          not_valid: 0
        };
        break;

      case "get_profile":
        jsData = {
          stb_type: "MAG250",
          sn: "0000000000000",
          ver: "ImageDescription: 0.2.18-r14-pub-250; ImageDate: Fri Jan 18 17:14:05 EET 2019; PORTAL version: 5.6.0; API Version: JS API version: 328; STB API version: 134; Player Engine version: 0x200",
          mac: params.mac || "00:1A:79:00:00:00",
          account: { name: "Don" },
          auth: 1
        };
        break;

      case "get_genres":
        jsData = [
          { id: "1", alias: "all", title: "All Channels" }
        ];
        break;

      case "get_ordered_list":
      case "get_all_channels":
        // This is what draws the BLUE BOX
        const listData = CHANNELS.map(c => ({
          id: c.id,
          name: c.name,
          number: c.number,
          tv_genre_id: "1",
          cmd: c.cmd_id, // <- create_link will be called with this
          logo: c.logo,
          use_http_tmp_link: 0,
          wow: 0
        }));
        jsData = {
          total_items: listData.length,
          max_page_items: 100,
          selected_item: 0,
          cur_page: 1,
          total_pages: 1,
          data: listData
        };
        break;

      case "create_link":
        // STB calls this when you press OK on a channel
        const cmdParam = params.cmd || "";
        // cmdParam will be "ch1" or "ch2"
        let realUrl = "";
        if (channelMap[cmdParam]) {
          realUrl = channelMap[cmdParam].url;
        } else {
          // fallback if it passes full cmd
          realUrl = CHANNELS[0].url;
        }
        jsData = {
          id: cmdParam,
          cmd: `ffmpeg ${realUrl}`,
          storage_name: "",
          error: ""
        };
        break;

      default:
        // For any other action, return empty ok to avoid black screen
        jsData = {};
        break;
    }

    // STB Emu expects format: {"js": {...}}
    // Some versions wrap with JsHttpRequest
    let responseObj;
    if (jsCallback) {
      responseObj = { js: jsData };
      // Original Ministra format: { "js": {...} } is actually what it wants
      // But keep simple
    } else {
      responseObj = { js: jsData };
    }

    return new Response(JSON.stringify(responseObj), {
      headers: {
       ...corsHeaders(),
        "Content-Type": "application/json; charset=utf-8"
      }
    });
  }
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
  };
}
