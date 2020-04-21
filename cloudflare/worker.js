const regex = /Spotify.Entity = (.*);/;

addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
    let psk = request.headers.get(PRESHARED_AUTH_HEADER_KEY)
    if (psk !== PRESHARED_AUTH_HEADER_VALUE) {
        return new Response('Sorry, you have supplied an invalid key.', {
            status: 403,
        })
    }

    let url = new URL(request.url);
    let params = new URLSearchParams(url.search.slice(1));
    let path = url.pathname.slice(1)
    if (path === 'artist-meta') {
        let artistId = params.get('artistId');
        if (artistId == null) {
            return new Response('You need to supply an "artistId"', { status: 400 })
        }
        let response = await fetch(`https://open.spotify.com/artist/${artistId}/about`, {
            headers: {
                'User-Agent': 'python-requests/2.23.0',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
            }
        });
        if (response.status == 404) {
            return new Response(`Artist "${artistId} not found`, { status: 404 })
        }
        if (response.status !== 200) {
            console.log(response.status)
            return new Response('Gateway error', { status: 502 })
        }
        let html = await response.text();
        let result = html.match(regex);
        if (result == null) {
            return new Response('You need to supply an "artistId"', { status: 400 })
        }
        let [, json_string] = result;
        return new Response(json_string, { status: 200, headers: { 'content-type': 'application/json;charset=UTF-8' } })
    } else {
        return new Response("path not supported, supported paths: ['artist-meta']", { status: 404 })
    }
}