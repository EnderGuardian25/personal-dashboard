# Dashboard Sync — Backend

Tiny Cloudflare Worker that backs the dashboard's reading queue, learning-path progress, and track-filter so they sync across devices.

- **Runtime:** Cloudflare Workers (free tier — 100k requests/day)
- **Storage:** Cloudflare KV (free tier — 100k reads/day, 1k writes/day, 1 GB)
- **Auth:** single static bearer token
- **Code size:** one ~180-line file (`src/worker.js`)

See [`../docs/BACKEND-SETUP.md`](../docs/BACKEND-SETUP.md) for the step-by-step deploy guide. This README is for someone who already has it deployed and just needs a reference.

---

## API

All endpoints under `https://<your-worker>.workers.dev`.

| Method  | Path           | Auth | Notes |
|---------|----------------|------|-------|
| GET     | `/api/health`  | no   | Liveness check. Returns `{ ok: true, time: ISO }` |
| GET     | `/api/state`   | yes  | Returns the saved state JSON. |
| PUT     | `/api/state`   | yes  | Replaces the saved state. Body: `{ queue, learning, track }` |
| OPTIONS | any            | no   | CORS preflight. |

Auth is `Authorization: Bearer <SYNC_TOKEN>`.

The PUT handler validates and clamps the payload — bad shapes are silently coerced to safe defaults rather than 500ing. Limits: queue <= 500 items, learning <= 100 keys, individual string fields capped.

## State shape

```jsonc
{
  "queue":    [{ "title": "...", "url": "...", "src": "...", "done": false }],
  "learning": { "learn-1": true, "learn-2": false },
  "track":    "all" | "cyber" | "design",
  "updatedAt": "2026-05-20T08:30:00.000Z"
}
```

## Config (`wrangler.toml`)

- `[vars] ALLOWED_ORIGINS` — comma-separated CORS allow-list. Set to your Pages URL in production. `"*"` is fine while developing.
- `[[kv_namespaces]] DASHBOARD_KV` — paste the id from `wrangler kv namespace create DASHBOARD_KV`.

## Secrets (not in source)

- `SYNC_TOKEN` — the shared bearer token. Set with `wrangler secret put SYNC_TOKEN`.

## Local dev

```bash
cd backend
npm install
npm run dev    # http://localhost:8787
```

## Deploy

```bash
npm run deploy
```

Prints the live URL. Use it as `dashboard.syncUrl` in the dashboard.

## Smoke test

```bash
BASE_URL=https://dashboard-sync.<you>.workers.dev \
SYNC_TOKEN=<token> \
npm run smoke
```

Exits 0 if everything's wired correctly.

## Cost / quotas

For a single user with a few writes per session:

- ~30 writes/day, ~50 reads/day → 0.05% of the KV free tier
- Well inside Workers' 100k-requests/day allowance

You will not pay a cent.

## What this deliberately does NOT do

- Multi-user — there's one KV key, one user. Adding users means keying by token / user-id.
- Realtime push — clients poll on page focus + after writes. WebSocket / Durable Object would be overkill.
- Conflict resolution — last-write-wins. Fine for one user; sloppy for two.
- Migrations — schema lives in the client. If you change shape, bump a `version` field both sides.
