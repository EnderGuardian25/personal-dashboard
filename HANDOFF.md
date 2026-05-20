# Handoff — Damian's AI Student Dashboard

**Owner:** Damian De Cruz (damian@bisteccare.lk)
**Created:** 20 May 2026
**Last updated:** 20 May 2026 (v2)
**Status:** v2 shipped — live as Cowork artifact `ai-student-dashboard`, auto-refreshed daily by `ai-dashboard-daily-refresh` scheduled task.

---

## 1. Purpose

A personal dashboard for Damian — a CS student focused on **cybersecurity** and **UI/UX design** — to:

- Catch up on daily AI news in one glance (auto-refreshed)
- Discover AI tools relevant to his two tracks, with a one-click filter to focus on just one
- Save articles for later in a persistent reading queue
- Follow a curated learning path with checkboxes and a progress ring
- Reach for ready-made prompts during study/coding/design work
- Browse a "deeper reads" library of long-form material

The artifact is intentionally light, calm, and scannable.

---

## 2. Files in this handoff

| File | Role | Notes |
|---|---|---|
| `ai-student-dashboard.html` | The dashboard itself | Self-contained HTML with inline CSS + JS. Renders as Cowork artifact id `ai-student-dashboard`. |
| `HANDOFF.md` | This file | Context, design decisions, how to extend. |

---

## 3. What's in the dashboard (v2)

**Header**
- Title + today's date
- **Track filter tabs**: All tracks / 🔒 Cyber only / 🎨 Design only. Selection persists in `localStorage` (`dashboard.track`).

**Left column**
1. **Today in AI** — top-story paragraph + 6 headline links + sources. Each headline has a `＋ Save` button that adds it to the reading queue. Footer note explains the daily auto-refresh.
2. **AI for Cybersecurity** (`.track-cyber`) — Snyk, Huntr, TryHackMe AI rooms, OWASP LLM Top 10, NVIDIA garak, Cybrary. Hidden when filter is set to Design.
3. **AI for UI/UX Design** (`.track-design`) — UX Pilot, Relume, Magician, Stark, Clueify, Adobe Firefly. Hidden when filter is set to Cyber.

**Right column**
4. **Reading Queue** (NEW) — `localStorage`-backed (`dashboard.queue`). Shows saved items with checkboxes to mark read, an × to remove, and a "Clear all" button. Empty-state copy when nothing is saved.
5. **Learning Path** — six resources, each with a persistent checkbox (`dashboard.learning`). An SVG progress ring in the section header shows X/6 complete and animates as items are ticked.
6. **Quick Prompts** (5, copy-to-clipboard) — unchanged from v1.
7. **Deeper Reads** — OWASP LLM Top 10, Figma UX AI guide, HF trending papers, Anthropic Research, OpenAI Research, Lenny's Newsletter, Simon Willison's weblog. Each also has a `＋ Save` button feeding the reading queue. Cyber/design-flavoured reads are tagged with `.track-cyber` / `.track-design` so they also respect the track filter.

---

## 4. New JS modules (in the inline `<script>`)

- **Track filter** — `applyTrack(track)` sets `body[data-track]`. CSS hides `.track-cyber` / `.track-design` accordingly. Persisted under key `dashboard.track`.
- **Reading queue** — `loadQueue() / saveQueue(q) / renderQueue() / refreshSaveButtons()`. Each item is `{ title, url, src, done }`. Save buttons identify items by `data-url`. Persisted under key `dashboard.queue`.
- **Learning progress** — `loadProgress() / saveProgress(p) / updateProgressRing() / initProgress()`. Each resource has a `data-key` (`learn-1` … `learn-6`); state is `{ [key]: bool }`. Persisted under key `dashboard.learning`.
- **SVG progress ring** — `r=15`, circumference `2π·15 ≈ 94.25`. `stroke-dashoffset` is animated to reveal proportion done.

All `localStorage` keys are namespaced under `dashboard.*` to keep things tidy if more widgets are added later.

---

## 5. Daily auto-refresh — `ai-dashboard-daily-refresh`

A scheduled task runs **every morning at 7am local time** (cron `0 7 * * *`). It:

1. Runs `WebSearch` for the day's AI news.
2. Reads `ai-student-dashboard.html`.
3. Uses `Edit` to swap only:
   - The `#news-meta` "Updated …" date.
   - The `.news-summary` top-story block.
   - The six `.news-item` blocks inside `#news-feed`.
4. Re-registers the artifact via `mcp__cowork__update_artifact` (same id → updates in place).

The prompt is intentionally narrow — it must NOT touch styles, layout, the track filter, the queue, the learning path, or anything else. The news items must keep their exact shape (`.news-item > .body > a.title-link + .src` plus the `.save-btn` with matching `data-title / data-url / data-src`) or the Save buttons will desync from the queue.

To change the schedule or prompt:
```
mcp__scheduled-tasks__update_scheduled_task(taskId="ai-dashboard-daily-refresh", ...)
```

Note: scheduled tasks only run while Cowork is open. If the app was closed when 7am hit, it runs on next launch.

---

## 6. Design decisions worth keeping

- **Light theme, neutral cream background** (`#fafaf7`) — reads well in long sessions.
- **Sub-brand accent colors** — blue (live/news), magenta (cyber), purple (design), green (learning), amber (queue). Each section tag is keyed off these so the eye finds the right block fast.
- **System font stack** — no webfonts → fast load, no FOUT.
- **Hover affordances are subtle** — borders darken, cards lift 1px.
- **Mobile-first grid** — collapses cleanly at 900px and 600px.
- **State persistence over network calls** — every dynamic behaviour uses `localStorage`. The artifact sandbox blocks arbitrary network, so this is the safest pattern.

---

## 7. How to extend

### Common updates Damian will ask for

- **"Refresh my AI news now"** → run the steps from §5 manually (or trigger the scheduled task).
- **"Add a tool"** → drop a new `<div class="tool">…</div>` into the relevant `.tool-grid`. Use the existing `<span class="tag free|freemium|paid">` convention.
- **"Add a prompt"** → new `<div class="prompt">` with `data-copy` button. Wiring is automatic.
- **"Add an item to the reading queue from chat"** → not yet wired. Easiest path: append to `localStorage.dashboard.queue` JSON from a one-off script injected into the artifact, or extend the dashboard with an input box.
- **"Reset my progress"** → clear `localStorage.dashboard.learning` (or `dashboard.queue`).
- **"Switch to a dark theme"** → flip the CSS variables in `:root`. The whole palette is tokenised.

### Track filter — adding more tracks

If Damian picks up a third focus (e.g. AI-for-music), add:
- A new tab button `<button class="track-tab newtrack" data-track-btn="newtrack">…</button>`
- A new CSS rule `body[data-track="newtrack"] .track-cyber, body[data-track="newtrack"] .track-design { display: none; }`
- A `.track-newtrack` class on the new section card
- Include `"newtrack"` in the allow-list inside the `applyTrack` init code

---

## 8. Known constraints / open items

### Live news fetch is still NOT inside the artifact
Same as v1 — the artifact sandbox only exposes MCP tools via `window.cowork.callMcpTool()`, and `WebSearch` isn't an MCP tool. The daily scheduled task is the workaround.

Future option: if Damian connects a Brave-Search-style MCP, the in-page Refresh button could be wired to call it directly.

### Potential further improvements
- **Trending models widget** — Hugging Face has a trending API; if exposed via an MCP, render with Chart.js (already CDN-allowed).
- **"What's new this week" digest** — generate via Haiku with `window.cowork.askClaude()` summarising the news section into 3 bullets.
- **Cross-device sync** — `localStorage` is per-machine. If Damian uses the artifact on multiple devices and wants the queue to follow him, this needs a backing store (out of scope for the sandbox).

---

## 9. Tech notes (for the next agent)

- The artifact uses **no external libraries**. Chart.js, Grid.js, and Mermaid are CDN-allowed but unused.
- **`localStorage` is available** and used by all three new features. Keys: `dashboard.track`, `dashboard.queue`, `dashboard.learning`.
- **Clipboard API** works in the sandbox; the prompt-copy buttons use `navigator.clipboard.writeText`.
- The artifact must remain **self-contained**: all CSS/JS inline, no external font/image URLs.
- Color scheme is locked to `light` via `:root { color-scheme: light }`.

---

## 10. Quick-start for a fresh session

> Damian is a CS student studying cybersecurity and UI/UX design. He has a personal AI dashboard (`ai-student-dashboard.html`) registered as a Cowork artifact with the same id. Single-file static HTML page with: track filter tabs, daily AI news (6 items + top-story summary), AI-for-cyber tools, AI-for-design tools, a persistent reading queue (`dashboard.queue`), learning path with checkbox progress + SVG ring (`dashboard.learning`), quick prompts, and deeper reads. News is refreshed automatically each morning at 7am by the scheduled task `ai-dashboard-daily-refresh` — it WebSearches, Edits only the news section, and re-registers the artifact. To update content manually, edit the HTML and call `mcp__cowork__update_artifact`. Design system: clean light theme, accent colors per section, tokenised CSS variables in `:root`, voice warm/direct/no jargon.

---

*End of handoff.*
