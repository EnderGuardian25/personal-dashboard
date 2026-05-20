# Cross-Device Sync — Deploy & Connect Guide

You're deploying a tiny Cloudflare Worker that stores your dashboard's reading queue, learning progress, and selected track in Cloudflare KV. Every device that opens the dashboard pulls fresh state on load and pushes changes back automatically.

**The dashboard code is already wired up.** The HTML, CSS, and JavaScript for the sync feature have been applied to `index.html` — a "SYNC OFF" badge will appear in the page header the next time you open it. You don't need to edit any files. This guide is purely about standing up the backend and connecting your devices.

- **Free.** Cloudflare's free tier covers single-user usage 100× over. No credit card needed.
- **Single user.** One bearer token = one user = you.
- **180 lines of Worker code** in `backend/src/worker.js`. Already written, ready to deploy.

Estimated time once you start: **20–25 minutes**.

---

## Quick sanity check — what's already in place

```
personal-dashboard/
├── backend/
│   ├── src/worker.js          ← Worker code (deployed in Part 4)
│   ├── wrangler.toml          ← Worker config (edited in Parts 2 & 6)
│   ├── package.json
│   ├── scripts/smoke-test.sh
│   └── README.md
└── index.html                 ← already patched with sync UI + JS
```

You'll touch `backend/wrangler.toml` once (to paste a KV namespace id), run a handful of `wrangler` CLI commands, and copy the resulting Worker URL + token into each device. That's the whole job.

---

## Part 0 — Prerequisites (install once)

1. **Node.js 18+.** Check with `node --version`. If missing, install from [nodejs.org](https://nodejs.org).
2. **A Cloudflare account.** Sign up at [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up). Free, no credit card.

Everything else is installed automatically by `npm install` in Part 1.

---

## Part 1 — Install wrangler and log in

`wrangler` is Cloudflare's CLI for managing Workers. Open PowerShell or Command Prompt in the repo root:

```bash
cd backend
npm install
npx wrangler login
```

`npx wrangler login` pops a browser tab — click **Allow** to link the CLI to your Cloudflare account.

Sanity check:

```bash
npx wrangler whoami
```

Should print your Cloudflare email.

---

## Part 2 — Create the KV namespace

KV is Cloudflare's key-value store. Create one namespace:

```bash
npx wrangler kv namespace create DASHBOARD_KV
```

It prints something like:

```toml
[[kv_namespaces]]
binding = "DASHBOARD_KV"
id = "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d"
```

Copy the `id` value (the hex string after `id =`).

Now open `backend/wrangler.toml` in any editor. Find this block:

```toml
[[kv_namespaces]]
binding = "DASHBOARD_KV"
id = "REPLACE_WITH_KV_NAMESPACE_ID"
```

Replace `REPLACE_WITH_KV_NAMESPACE_ID` with the id you just copied. Save the file.

---

## Part 3 — Set the auth token

Generate a strong random token. Easiest options:

**PowerShell:**

```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object {[char]$_})
```

**Any browser console:**

```js
crypto.randomUUID() + crypto.randomUUID()
```

Either way, copy the output. **Save it somewhere safe** — a password manager is ideal. You'll paste it into each device once.

Now register the token as a Cloudflare secret (it's encrypted on their side, never in your repo):

```bash
npx wrangler secret put SYNC_TOKEN
```

It prompts: `Enter a secret value:` — paste the token, hit Enter.

---

## Part 4 — Deploy

```bash
npm run deploy
```

After a few seconds it prints the live URL, e.g.:

```
Published dashboard-sync
https://dashboard-sync.<your-cf-subdomain>.workers.dev
```

Copy that URL. You'll paste it into your dashboard in Part 7.

---

## Part 5 — Smoke test

Quick verification that auth, storage and CORS are all wired correctly:

```bash
BASE_URL=https://dashboard-sync.<your-cf-subdomain>.workers.dev \
SYNC_TOKEN=<the-token-from-part-3> \
npm run smoke
```

You should see four `OK` ticks: health endpoint returns 200, state without auth returns 401, PUT succeeds, GET returns what you PUT. If any step fails, fix it before continuing — it's easier to debug when only one piece is wired up.

**On Windows without bash?** Skip the smoke test and instead open `https://dashboard-sync.<your-subdomain>.workers.dev/api/health` in your browser. It should return `{"ok":true,"time":"..."}`. That's enough to confirm the deploy worked.

---

## Part 6 — Tighten CORS (do this once your Pages URL is live)

While testing, `wrangler.toml` allows any origin (`"*"`). Once your GitHub Pages site is live, lock it down:

1. Open `backend/wrangler.toml`.
2. Change:

   ```toml
   [vars]
   ALLOWED_ORIGINS = "*"
   ```

   to your real Pages URL — for example:

   ```toml
   [vars]
   ALLOWED_ORIGINS = "https://<your-username>.github.io"
   ```

3. Redeploy:

   ```bash
   npm run deploy
   ```

Multiple origins are supported as a comma-separated list. Add `http://localhost:5500` or wherever you preview locally if you also open the HTML directly during development.

**You can defer this step** while you're still testing — the only thing it does is reject API calls from unrelated origins. Just don't forget to come back to it once everything's working.

---

## Part 7 — Connect each device

For every device you want synced:

1. Open the dashboard URL (`https://<your-username>.github.io/<repo>/` or wherever you've hosted it).
2. In the header you'll see a small **SYNC OFF** badge with a grey dot.
3. **Click the badge.** A prompt asks for the **Worker URL** — paste the one from Part 4 (e.g. `https://dashboard-sync.<you>.workers.dev`). Click OK.
4. A second prompt asks for the **Sync token** — paste the one from Part 3. Click OK.
5. The badge turns blue (configured), then amber (syncing), then green (**SYNCED**). That device is now syncing.

**Important — the order you connect devices matters.** Whatever's currently on the server overwrites this device's local state on first connect. So:

- If you have stuff in your reading queue you don't want to lose, **connect that device first**. It pushes its local state up.
- Then connect the next device — it pulls down and inherits the data.

Subsequent edits push back automatically, debounced 600ms.

---

## Day-to-day usage

- **Add an article to the queue on your phone.** ~1 second later it's pushed to Cloudflare.
- **Open your laptop later.** On page load (or window focus), the dashboard pulls and re-renders.
- **No internet?** Edits still work — they're written to localStorage. The badge shows red. Push retries on next focus / reconnect.
- **Manual pull.** Click the SYNC badge → type `pull` → Enter.
- **Disconnect a device.** Click the SYNC badge → type `disconnect` → Enter. Token is wiped from that device's localStorage.

Status colours on the badge:

| Colour | Meaning |
|---|---|
| Grey | Sync off / not configured |
| Blue | Configured, idle |
| Amber (pulsing) | Pushing or pulling |
| Green | Last sync OK |
| Red | Error (network, bad token, etc.) |

---

## Troubleshooting

**Badge stays red / says "OFFLINE?".** Network issue or wrong Worker URL. Open `<your-worker-url>/api/health` in the browser — should return `{"ok":true,...}`. If it doesn't, the URL you pasted is wrong.

**Badge says "BAD TOKEN".** The token on the device doesn't match the one Cloudflare has. Either re-paste the correct token (click badge → it'll re-prompt if you `disconnect` first) or rotate the secret with `npx wrangler secret put SYNC_TOKEN` and re-connect every device.

**Sync works but data isn't appearing.** Open browser devtools → Application → Local Storage. Check that `dashboard.queue`, `dashboard.learning`, `dashboard.track` exist. Also check the Network tab for `/api/state` calls — look at status and body.

**CORS error in the console** (e.g. *"No 'Access-Control-Allow-Origin' header..."*). Your Pages URL isn't in `ALLOWED_ORIGINS`. Open `backend/wrangler.toml`, add the exact origin (include `https://`, no trailing slash), redeploy.

**Two devices "fighting" / data flapping.** Last-write-wins is the design. If you genuinely edit the queue on two devices in the same second, one write loses. In practice, wait for the green SYNCED badge before switching devices.

**`npx wrangler login` hangs forever.** Use `npx wrangler login --browser=false` and follow the URL it prints manually.

**`npm run deploy` says "Account ID required".** Run `npx wrangler whoami` to confirm you're logged in. If you have multiple Cloudflare accounts, set `account_id = "..."` in `wrangler.toml` under the `name = "dashboard-sync"` line.

---

## Updating the backend later

To change anything in `worker.js`:

```bash
cd backend
# ...edit src/worker.js...
npm run deploy
```

To rotate the auth token:

```bash
npx wrangler secret put SYNC_TOKEN   # paste new token
# Then re-connect each device with the new token.
```

To see real-time logs from your devices' calls:

```bash
npx wrangler tail
```

To roll back to a previous version, use the Cloudflare dashboard → Workers & Pages → dashboard-sync → Deployments tab.

---

## Security notes

- The bearer token is the **only** thing protecting your data. Treat it like a password.
- Anyone who has the token can read and overwrite your dashboard state. Not catastrophic (it's a reading queue), but worth knowing.
- The token lives in localStorage on each connected device. If you lose a device, rotate the token (Part 3 again, then re-connect every remaining device).
- HTTPS is enforced by Cloudflare — no plaintext traffic.
- Cloudflare doesn't see the content of your queue beyond the JSON blob. Don't paste secrets into article titles and you'll be fine.

---

## What this deliberately doesn't solve

- **Selective sync.** All-or-nothing per device. A "private notes" channel that doesn't sync would be a bigger change.
- **History / undo.** Last-write-wins means no version history. Could be added with a daily KV snapshot — ask later if you want it.
- **Multi-user.** One token = one user. Multi-user would mean scoping each KV key by user-id and adding a real auth flow.

---

## TL;DR — for when you come back to this in six months

```bash
cd backend
npm install
npx wrangler login
npx wrangler kv namespace create DASHBOARD_KV   # paste the id into wrangler.toml
npx wrangler secret put SYNC_TOKEN              # paste a long random token
npm run deploy                                  # note the URL it prints
```

Then in the dashboard: click the SYNC badge in the header → paste URL → paste token → done.

---

*Once the badge turns green on two devices, you're done. Your dashboard now follows you across machines.*
