# Audit: soniq-proxy (CORS proxy for SONIQ)

**Date:** 2026-05-21  
**Track:** Day C — Quality / security audit (authorized scope only)  
**Target:** soniq-proxy ([googlesgit/soniq-proxy](https://github.com/googlesgit/soniq-proxy))  
**Status:** Published

---

## Scope

Static review of the **public** `main` branch on GitHub (May 21, 2026): five Vercel serverless handlers under `api/`, `package.json`, and `vercel.json`. No live penetration testing. Findings are tied to files visible in the repo.

**In scope:** error handling, CORS, input validation, dependency surface, maintainability, operational abuse risk.  
**Out of scope:** JioSaavn / LRCLIB terms of service (noted as product risk only).

---

## Method

- Listed repo tree via GitHub API (`api/search.js`, `stream.js`, `lyrics.js`, `suggestions.js`, `jukebox.js`)
- Read handler source from `raw.githubusercontent.com/googlesgit/soniq-proxy/main/...`
- Checklist from `REVIEW.md`: secrets, validation, logging, tests, README

---

## Findings

| ID | Severity | Area | Finding | Suggested fix |
|----|----------|------|---------|---------------|
| F1 | **High** | Correctness | `api/stream.js` decrypts with **XOR** loop; `api/search.js` and `api/jukebox.js` use full **DES-ECB** with the same public key. If both paths serve stream URLs, behavior may diverge and `stream.js` may return broken URLs. | Extract one shared `decryptUrl()` module; delete XOR implementation; add a smoke test with a known fixture. |
| F2 | **High** | Operations | Public serverless proxy with **no rate limiting** and open CORS. Any site can drive JioSaavn/LRCLIB traffic through your Vercel bill. | Vercel firewall / rate limits, optional API key for non-local callers, or restrict `Access-Control-Allow-Origin` to your player origin(s). |
| F3 | **Medium** | Security | `Access-Control-Allow-Origin: *` and `Allow-Headers: *` on all routes (`vercel.json` + per-handler headers). Convenient for a demo; increases **browser-based abuse** from arbitrary origins. | Allowlist `https://googlesgit.github.io` (and localhost in dev). |
| F4 | **Medium** | Maintainability | DES tables + `decryptUrl` duplicated in **`search.js` and `jukebox.js`** (~150+ lines each). Future key/algorithm fixes must be edited twice. | `api/_lib/des.js` (or similar) imported by handlers. |
| F5 | **Medium** | Reliability | Search/suggestions forward user `q` with **no max length**; large queries still hit upstream APIs and your function duration. | Reject `q` over e.g. 200 chars with `400`; trim whitespace. |
| F6 | **Low** | Security | `500` responses return `err.message` to clients (`stream.js`), which can leak upstream error text. | Log server-side; return generic `{ error: 'Upstream unavailable' }`. |
| F7 | **Low** | DX | Repo has `package.json` but **no README**, license, or tests in tree. Hard for future-you (or contributors) to run/deploy safely. | README: env, routes, deploy, legal disclaimer; add one Vitest test for `decryptUrl`. |

---

## What’s working well

- **No npm dependencies** for crypto in search path — small cold-start footprint on Vercel.
- **Query encoding:** `encodeURIComponent(q)` before JioSaavn URLs (verified in `search.js`, `suggestions.js`).
- **Lyrics path:** `Promise.race` with 6s timeout reduces hung serverless invocations (`lyrics.js`).
- **Suggestions:** `Promise.allSettled` so one upstream failure does not kill the other (`suggestions.js`).
- **OPTIONS** preflight handled consistently; **400** when required params missing (`q`, `id`).

---

## Recommended next PRs

1. **`refactor: shared decrypt module + fix stream.js`** — single DES implementation, remove duplication (F1, F4).
2. **`ops: CORS allowlist + rate limit`** — tighten `vercel.json` and document Vercel protection (F2, F3).
3. **`docs: README + input limits`** — max `q` length, route table, disclaimer (F5, F7).

---

## My review notes

**2-minute summary:** Your proxy is lean and works well for a personal music player, but it is **wide open on the internet** (CORS + no rate limits). The biggest technical red flag is **two different decrypt implementations** in `stream.js` vs `search.js` — worth fixing before adding features.
