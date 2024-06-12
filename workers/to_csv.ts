const ASSET_CACHE = caches.default;

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const pathname = url.pathname;
    const baseUrl = process.env.PAGES_BASE_URL; // Get the base URL from environment variable

    // Check if the file is in the cache
    const cacheKey = new Request(`${baseUrl}/data/${url.searchParams.get('file') || pathname.substring('/data/'.length)}`, request);
    let cachedResponse = await ASSET_CACHE.match(cacheKey);

    if (cachedResponse) {
      console.log('Cache hit:', cacheKey.url); // log when using cache
      return cachedResponse;
    }

    console.log('Cache miss:', cacheKey.url); // log when not using cache
    // TODO: implement
  },
};
