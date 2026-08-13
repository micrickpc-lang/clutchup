const DATA_PATH = /^\/data\/v4\/(players(?:\/[^/]+(?:\/(?:stats\/cs2|history))?)?)$/;
const AUTH_PATH = /^\/auth\/v1\/(?:oauth\/token|resources\/userinfo)$/;

export default {
  async fetch(request, env) {
    if (!env.PROXY_SECRET || request.headers.get("X-ClutchUp-Proxy-Secret") !== env.PROXY_SECRET) return new Response("Forbidden", { status: 403 });
    const incoming = new URL(request.url);
    const dataMatch = DATA_PATH.test(incoming.pathname);
    const authMatch = AUTH_PATH.test(incoming.pathname);
    if (!dataMatch && !authMatch) return new Response("Not found", { status: 404 });
    const allowed = authMatch && incoming.pathname.endsWith("oauth/token") ? ["POST"] : ["GET"];
    if (!allowed.includes(request.method)) return new Response("Method not allowed", { status: 405, headers: { Allow: allowed.join(", ") } });
    const target = new URL(`${dataMatch ? "https://open.faceit.com" : "https://api.faceit.com"}${incoming.pathname}${incoming.search}`);
    const headers = new Headers({ Accept: "application/json", "User-Agent": "ClutchUp/2.0" });
    const authorization = request.headers.get("Authorization");
    const contentType = request.headers.get("Content-Type");
    if (authorization) headers.set("Authorization", authorization);
    if (contentType === "application/x-www-form-urlencoded") headers.set("Content-Type", contentType);
    const upstream = await fetch(target, { method: request.method, headers, body: request.method === "POST" ? request.body : undefined, redirect: "manual" });
    const responseHeaders = new Headers({ "Content-Type": upstream.headers.get("Content-Type") || "application/json", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" });
    return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
  },
};
