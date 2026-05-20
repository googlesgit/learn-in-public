# HTTP caching headers and CDN behavior

**Date:** 2026-05-19  
**Track:** Day A — Learn in public  
**Status:** Published

---

## What I learned

HTTP caching is a contract between **browser**, **CDN edge**, and **origin server**. Response headers tell each layer *whether* to store a response, *for how long*, and *when* to revalidate instead of fetching again.

### Core headers

| Header | Role |
|--------|------|
| `Cache-Control` | Main control knob: `max-age=3600` (fresh for 1 hour), `no-store` (never cache), `no-cache` (may store but must revalidate before use), `private` (browser only, not shared caches), `public` (CDN may cache). |
| `ETag` | Opaque version token for the representation (e.g. `"a1b2c3"`). On later requests the client sends `If-None-Match: "a1b2c3"`; if unchanged, the server returns **304 Not Modified** with no body. |
| `Last-Modified` | Weaker time-based validator. Client sends `If-Modified-Since`; server compares and may return 304. |
| `Vary` | Tells caches the response depends on listed request headers (often `Accept-Encoding`, `Accept-Language`). Without it, a CDN might serve the wrong variant to another user. |

### Fresh vs stale vs revalidation

1. **Fresh** — Within `max-age`, the cache serves the stored copy with no origin round-trip.
2. **Stale** — Past `max-age` but still stored; behavior depends on `stale-while-revalidate`, `must-revalidate`, etc.
3. **Revalidation** — Cache asks origin: “Still valid?” via `If-None-Match` / `If-Modified-Since`. 304 saves bandwidth; 200 means send the new body.

### How a CDN fits in

A CDN (Cloudflare, Fastly, CloudFront, etc.) is a **shared cache** in front of your origin:

```
Browser → CDN edge (PoP) → Origin (your API/server)
```

- First request for a URL at an edge location: **cache miss** → CDN fetches from origin, stores response (if headers allow).
- Later requests from nearby users: **cache hit** → served from edge until TTL expires or cache is purged.
- **Cache key** is usually method + URL + parts of headers listed in `Vary`. Two users with different `Accept-Language` may get different cached objects for the same URL.
- **Purging** invalidates edge copies before TTL ends (deployments, fixing bad content). Don’t rely only on short TTLs if you need instant updates.

CDNs respect `Cache-Control` on the response they receive from origin. If you send `Cache-Control: private` or `no-store`, the edge should not treat it as publicly cacheable.

---

## Why it matters

- **Latency & cost** — Static assets and cacheable API responses at the edge cut round-trips to your origin and reduce load.
- **Correctness** — Wrong caching breaks auth (session cookies on “public” pages), leaks one user’s data to another, or shows stale prices after a deploy.
- **Debugging** — “Works on my machine” often means `Cache-Control` differs in prod, or a CDN still has an old object. Knowing 304 vs 200 and `Age` / `X-Cache` headers speeds triage.

Backend and frontend both set and consume these headers: APIs define policy; browsers and CDNs enforce it.

---

## Minimal example

See `examples/2026-05-19-cache-headers-demo.js` — a tiny Node server that returns cacheable JSON with `ETag` and honors `If-None-Match` (304 when unchanged).

```javascript
// Run: node examples/2026-05-19-cache-headers-demo.js
// Then: curl -i http://localhost:3456/data
//       curl -i http://localhost:3456/data -H 'If-None-Match: "..."'  # use ETag from first response
```

---

## Gotcha / common mistake

**Caching personalized responses as if they were public static files.**

Example: `/api/me` returns JSON with `Cache-Control: public, max-age=3600` but no `Vary` and no `private`. A CDN may cache one user’s profile and serve it to the next visitor on the same edge.

Fix: use `Cache-Control: private, no-store` for auth/session data, or ensure the cache key includes what makes the response unique (cookies are generally **not** part of the default cache key — don’t cache per-user bodies at the CDN without explicit design).

Another common mistake: treating `no-cache` as “do not cache.” It usually means **“cache, but revalidate with origin before each use.”** Use `no-store` when nothing should be persisted.

---

## Further reading

- [HTTP caching (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching)
- [Cache-Control (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)
- [RFC 9111 — HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)
- [Cloudflare: How caching works](https://developers.cloudflare.com/cache/concepts/how-cache-works/)

---

## My review notes

**2-minute summary for a friend:** Browsers and CDNs save copies of responses when headers allow. `max-age` says how long they can use it without asking again. `ETag` / `If-None-Match` let them check “anything new?” with a cheap 304 instead of re-downloading. CDNs sit in the middle — great for static assets and carefully chosen public API responses, dangerous for anything tied to a logged-in user unless you use `private` / `no-store` or design cache keys on purpose.
