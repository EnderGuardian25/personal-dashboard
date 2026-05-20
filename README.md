# AI Dashboard

A personal dashboard for tracking AI news, cybersecurity tools, UI/UX tools, learning resources, and a curated reading queue. Single-page, single-file, hosted on GitHub Pages, auto-refreshed daily.

**Live site:** `https://<your-username>.github.io/<repo-name>/`

---

## What's in here

```
.
├── .github/workflows/
│   └── refresh-news.yml      ← daily Actions workflow (07:00 Asia/Colombo)
├── scripts/
│   └── refresh-news.py       ← Python news-refresh script (RSS, no API keys)
├── docs/
│   ├── GITHUB-HOSTING-SETUP.md   ← how this was wired up
│   └── HANDOFF.md            ← design notes + state-of-the-dashboard
├── index.html                ← the dashboard itself (open in any browser)
├── README.md                 ← this file
└── .gitignore
```

The dashboard is intentionally a **single HTML file** with inline CSS and JavaScript — no build step, no framework, no dependencies. Drop it on any static host and it works.

---

## How the daily refresh works

1. GitHub Actions fires at **01:30 UTC** every day (= 07:00 in Asia/Colombo).
2. The workflow checks out the repo, installs `feedparser`, and runs `scripts/refresh-news.py`.
3. The script:
   - Reads `index.html`
   - Pulls items from ~10 public AI RSS feeds (Anthropic, OpenAI, Google AI, DeepMind, TechCrunch AI, The Verge AI, Ars Technica AI, Simon Willison, Hugging Face Papers, Hacker News AI search)
   - Ranks by keyword priority (security, agents, design, etc.) + recency, dedupes per domain
   - Picks the top 6 and rewrites the news section in place
   - Updates the "Updated DD Month YYYY" date label
4. The workflow commits the new HTML and pushes it.
5. GitHub Pages republishes within ~1 minute.

**Total cost:** free. **Total compute used per month:** about 15 minutes of Actions time.

---

## Local maintenance

**Refresh the news manually (without waiting for cron):**

```bash
pip install feedparser
python scripts/refresh-news.py
```

…or open the GitHub repo's Actions tab → *Refresh AI dashboard news* → *Run workflow*.

**Add or remove RSS sources:** edit the `FEEDS` list at the top of `scripts/refresh-news.py`.

**Bias the picker toward different topics:** edit `PRIORITY_KEYWORDS` in the same file.

**Change the refresh time:** edit the `cron:` line in `.github/workflows/refresh-news.yml`. The schedule is in UTC — use [crontab.guru](https://crontab.guru) for translations.

**Pause refreshes:** Actions tab → *Refresh AI dashboard news* → "…" menu → *Disable workflow*.

---

## Features at a glance

- **Today in AI** — top-story summary + 6 headline links, refreshed daily.
- **Track filter tabs** — *All / Cyber / Design* — hides the off-track sections. Persists via `localStorage`.
- **AI for Cybersecurity** — Snyk, Huntr, TryHackMe AI rooms, OWASP LLM Top 10, NVIDIA garak, Cybrary.
- **AI for UI/UX Design** — UX Pilot, Relume, Magician, Stark, Clueify, Adobe Firefly.
- **Reading Queue** — save-for-later button on every news item and deeper read, persists via `localStorage`.
- **Learning Path** — six curated resources with persistent checkboxes and an SVG progress ring.
- **Quick Prompts** — five copy-to-clipboard prompts tailored to coding, security, design, learning.
- **Deeper Reads** — long-form references on AI, security, design.

All persistent state lives in `localStorage` under the `dashboard.*` namespace. State is **per-device** — it doesn't sync across phone/laptop.

---

## Tech notes

- Single HTML file with `:root { color-scheme: light }` and CSS variables for the palette — easy to re-skin.
- Monospace font stack (Courier New + fallbacks) — works without webfonts.
- Color palette: navy/blue accents on a baby-blue tinted off-white background.
- No external scripts. No analytics. No tracking. No cookies.
- The Python script is stdlib + `feedparser` only — runs anywhere with Python 3.10+.

---

## See also

- `docs/GITHUB-HOSTING-SETUP.md` — the original step-by-step that created this repo.
- `docs/HANDOFF.md` — design decisions, palette tokens, JS module layout, future ideas.
