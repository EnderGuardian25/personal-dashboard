/**
 * Dashboard Sync Worker
 * =====================
 * Tiny Cloudflare Worker that backs the dashboard's reading queue,
 * learning-path progress, and track filter so they sync across devices.
 *
 * Storage: one KV namespace, one key ("state"), one JSON blob.
 * Auth:    single static bearer token (set via `wrangler secret put SYNC_TOKEN`).
 * CORS:    locked to ALLOWED_ORIGINS (set via wrangler.toml `[vars]`).
 *
 * Endpoints
 * ---------
 *   GET  /api/health  → liveness check, no auth
 *   GET  /api/state   → returns the saved state JSON (auth required)
 *   PUT  /api/state   → replaces the saved state (auth required)
 *
 * Everything else returns 404.
 */

const STATE_KEY = "state";

const DEFAULT_STATE = {
  queue: [],
  learning: {},
  track: "all",
  updatedAt: null,
};

// ---------- Helpers ----------

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = (env.ALLOWED_ORIGINS || "*")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  let allowOrigin = "*";
  if (!allowed.includes("*")) {
    allowOrigin = allowed.includes(origin) ? origin : allowed[0] || "*";
  }

  return {
    "Access-Control-Allow-Origin": allowOrigin,
    "Access-Control-Allow-Methods": "GET, PUT, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

function json(body, { status = 200, headers = {} } = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

function timingSafeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

function authorized(request, env) {
  if (!env.SYNC_TOKEN) return false;
  const header = request.headers.get("Authorization") || "";
  const token = header.replace(/^Bearer\s+/i, "").trim();
  if (!token) return false;
  return timingSafeEqual(token, env.SYNC_TOKEN);
}

function normaliseState(raw) {
  const queue = Array.isArray(raw.queue)
    ? raw.queue
        .filter((q) => q && typeof q === "object" && q.url && q.title)
        .slice(0, 500)
        .map((q) => ({
          title: String(q.title).slice(0, 500),
          url: String(q.url).slice(0, 2000),
          src: String(q.src || "").slice(0, 200),
          done: !!q.done,
        }))
    : [];

  const learning =
    raw.learning && typeof raw.learning === "object"
      ? Object.fromEntries(
          Object.entries(raw.learning)
            .filter(([k]) => typeof k === "string" && k.length <= 64)
            .slice(0, 100)
            .map(([k, v]) => [k, !!v])
        )
      : {};

  const allowedTracks = ["all", "cyber", "design"];
  const track =
    typeof raw.track === "string" && allowedTracks.includes(raw.track)
      ? raw.track
      : "all";

  return {
    queue,
    learning,
    track,
    updatedAt: new Date().toISOString(),
  };
}

export function mergeState(existing, incoming) {
  const queueByUrl = new Map();

  for (const item of existing.queue || []) {
    queueByUrl.set(item.url, { ...item });
  }
  for (const item of incoming.queue || []) {
    const prev = queueByUrl.get(item.url);
    if (prev) {
      queueByUrl.set(item.url, {
        ...prev,
        title: item.title ?? prev.title,
        src: item.src ?? prev.src,
        done: prev.done || item.done,
      });
    } else {
      queueByUrl.set(item.url, { ...item });
    }
  }

  const learning = { ...(existing.learning || {}) };
  for (const [key, value] of Object.entries(incoming.learning || {})) {
    learning[key] = Boolean(learning[key]) || Boolean(value);
  }

  return {
    queue: Array.from(queueByUrl.values()),
    learning,
    track: incoming.track,
    updatedAt: new Date().toISOString(),
  };
}

// ---------- Handlers ----------

async function handleHealth(request, env) {
  return json(
    { ok: true, time: new Date().toISOString() },
    { headers: corsHeaders(request, env) }
  );
}

async function handleGetState(request, env) {
  const raw = await env.DASHBOARD_KV.get(STATE_KEY);
  const data = raw ? JSON.parse(raw) : DEFAULT_STATE;
  return json(data, { headers: corsHeaders(request, env) });
}

async function handlePutState(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json(
      { error: "invalid_json" },
      { status: 400, headers: corsHeaders(request, env) }
    );
  }

  const rawExisting = await env.DASHBOARD_KV.get(STATE_KEY);
  let existingParsed = DEFAULT_STATE;
  if (rawExisting) {
    try {
      existingParsed = JSON.parse(rawExisting);
    } catch {
      existingParsed = DEFAULT_STATE;
    }
  }

  const incoming = normaliseState(body);
  const state = mergeState(existingParsed, incoming);
  await env.DASHBOARD_KV.put(STATE_KEY, JSON.stringify(state));

  return json(
    {
      ok: true,
      updatedAt: state.updatedAt,
      sizes: {
        queue: state.queue.length,
        learning: Object.keys(state.learning).length,
      },
    },
    { headers: corsHeaders(request, env) }
  );
}

// ---------- Entrypoint ----------

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = corsHeaders(request, env);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    if (url.pathname === "/api/health" && request.method === "GET") {
      return handleHealth(request, env);
    }

    if (!authorized(request, env)) {
      return json(
        { error: "unauthorized" },
        { status: 401, headers: cors }
      );
    }

    if (url.pathname === "/api/state") {
      if (request.method === "GET") return handleGetState(request, env);
      if (request.method === "PUT") return handlePutState(request, env);
      return json(
        { error: "method_not_allowed" },
        { status: 405, headers: cors }
      );
    }

    return json({ error: "not_found" }, { status: 404, headers: cors });
  },
};
