export default {
  async fetch(request, env) {
    if (!env.PROXY_SECRET || request.headers.get("X-ClutchUp-Proxy-Secret") !== env.PROXY_SECRET) {
      return new Response("Forbidden", { status: 403 });
    }

    const incoming = new URL(request.url);
    let target;
    if (incoming.pathname.startsWith("/data/")) {
      target = new URL(`https://open.faceit.com${incoming.pathname}${incoming.search}`);
    } else if (incoming.pathname.startsWith("/auth/")) {
      target = new URL(`https://api.faceit.com${incoming.pathname}${incoming.search}`);
    } else {
      return new Response("Not found", { status: 404 });
    }

    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.delete("x-clutchup-proxy-secret");
    headers.delete("cf-connecting-ip");
    headers.set("User-Agent", "ClutchUp/1.0");

    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
      redirect: "manual",
    });
    const responseHeaders = new Headers(upstream.headers);
    responseHeaders.delete("content-length");
    responseHeaders.delete("content-encoding");
    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  },
};
