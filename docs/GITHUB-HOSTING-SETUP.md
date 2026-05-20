# Host Your Dashboard on GitHub — Setup Guide

What you'll have when you're done:

- The dashboard lives at a URL like `https://<your-username>.github.io/ai-dashboard/`
- GitHub's servers refresh the news section **every day at 7am Sri Lanka time** — completely independent of your PC being on or off.
- You can open the dashboard from your phone, laptop, college PC, anywhere, just by bookmarking the URL.
- Totally free. No credit card, no server to maintain.

Estimated setup time: **15–20 minutes** the first time. After that, zero maintenance.

---

## What you need before you start

1. A GitHub account → sign up at [github.com](https://github.com) (free).
2. A **GitHub Student Developer Pack** — you already have this in your dashboard's Learning Path. Apply at [education.github.com/pack](https://education.github.com/pack) if you haven't yet. With student status you get **GitHub Pro free**, which lets you host private repos on Pages.
3. **Git** is optional — everything in this guide can be done in the GitHub web UI by drag-and-drop. If you'd rather use the command line, install Git from [git-scm.com](https://git-scm.com).

---

## Step 1 — Create the repo

1. Sign in to GitHub and click the **+** in the top-right → **New repository**.
2. Settings:
   - Repository name: `ai-dashboard` (or anything you like — this becomes part of your URL)
   - Description: *Personal AI news + cybersecurity + UI/UX dashboard*
   - Visibility: **Private** (recommended) or **Public** — both work for Pages with the Student Pack
   - Tick **Add a README file**
3. Click **Create repository**.

You'll land on the repo's main page.

---

## Step 2 — Upload your three files

You're going to push three files into the repo:

| File | Goes at this path in the repo |
|---|---|
| `ai-student-dashboard.html` | `ai-student-dashboard.html` (root) |
| `refresh-news.py`           | `scripts/refresh-news.py` |
| `refresh-news.yml`          | `.github/workflows/refresh-news.yml` |

All three files are already in your `Personal Dashboard\github-hosting\` folder. Plus the dashboard HTML is in `Personal Dashboard\`.

**Easiest way (web UI):**

1. On the repo page, click **Add file → Upload files**.
2. Drag `ai-student-dashboard.html` (from `Personal Dashboard\`) into the upload area.
3. Scroll to the bottom and click **Commit changes**.

Now add the script:

4. Click **Add file → Create new file** (NOT upload — we want to specify a folder).
5. In the filename box, type `scripts/refresh-news.py` — the `/` makes GitHub create the folder automatically.
6. Open `Personal Dashboard\github-hosting\refresh-news.py` on your PC, copy all its contents, paste into the GitHub editor.
7. Click **Commit changes**.

Now add the workflow:

8. Click **Add file → Create new file** again.
9. Filename: `.github/workflows/refresh-news.yml` — the dots and slashes matter, copy exactly.
10. Paste the contents of `refresh-news.yml` from your local folder.
11. Click **Commit changes**.

Your repo should now look like:

```
ai-dashboard/
├─ .github/
│  └─ workflows/
│     └─ refresh-news.yml
├─ scripts/
│  └─ refresh-news.py
├─ ai-student-dashboard.html
└─ README.md
```

---

## Step 3 — Enable GitHub Pages

This is the "make it a website" step.

1. On the repo, click **Settings** (top tabs).
2. In the left sidebar, click **Pages**.
3. Under **Build and deployment**:
   - Source: **Deploy from a branch**
   - Branch: **main** / **/(root)** → click **Save**.
4. GitHub takes about 30–60 seconds to publish. Refresh the page; you'll see:

   > Your site is live at `https://<username>.github.io/ai-dashboard/`

5. Click that URL. You should see your dashboard — but at `ai-student-dashboard.html`, not at the root. So your real URL will be one of:

   - `https://<username>.github.io/ai-dashboard/ai-student-dashboard.html`

   To make it work at the root URL directly, rename the file in the repo from `ai-student-dashboard.html` to `index.html`. Either:
   - In the web UI: click the file → ✏️ (edit) → in the filename box at the top, change to `index.html` → commit.
   - **Important**: also update `refresh-news.py` so it edits the right filename. Open `scripts/refresh-news.py`, find the line `HTML_PATH = …`, change `"ai-student-dashboard.html"` to `"index.html"`, commit.

Now your dashboard lives at the clean URL.

---

## Step 4 — Trigger the first refresh

You don't want to wait until tomorrow morning to see if the workflow works.

1. On the repo, click the **Actions** tab.
2. In the left sidebar, click **Refresh AI dashboard news**.
3. Click **Run workflow** (top-right) → **Run workflow** (green button).
4. Wait ~30 seconds, then refresh the page. You'll see a new run appear with a spinning yellow icon, then green ✓.

If it goes green, your dashboard's news section now has the latest items pulled from RSS, and a new commit appeared on the repo. Open the Pages URL again — fresh news.

If it goes red ✗, click into the run to see what failed. Common causes are at the bottom of this guide.

---

## Step 5 — Bookmark on every device

This is the whole point. On each device:

- **iPhone / Android**: open the URL in Safari/Chrome → tap the share button → **Add to Home Screen**. Now you have a dashboard icon next to your apps.
- **Laptop / desktop browser**: open the URL → bookmark it. Drop it on your bookmarks bar or pin it as a startup tab.
- **Windows**: in Edge or Chrome, **Install as app** (the small "install" icon in the address bar). This gives you a standalone window with no browser chrome.

The reading queue and learning-path progress use `localStorage`, so they persist **per-device** — they won't sync across devices automatically. (That's a bigger project; if you want it, ask later.)

---

## How the daily refresh actually works

1. At 01:30 UTC (07:00 Sri Lanka time) every day, GitHub's scheduler triggers your workflow.
2. The workflow:
   - Checks out the repo
   - Installs `feedparser` (a small Python library)
   - Runs `scripts/refresh-news.py`
3. The script:
   - Reads your HTML file
   - Pulls items from ~10 AI RSS feeds (Anthropic, OpenAI, Google AI, TechCrunch, The Verge, Ars Technica, Simon Willison, HF Papers, Hacker News AI search)
   - Ranks them by keyword relevance (security, agents, design, etc.) and recency, dedupes by domain
   - Picks 6 and rewrites the news section
   - Updates the "Updated DD Month YYYY" date label
4. The workflow commits the new HTML and pushes it.
5. GitHub Pages sees the commit and republishes the site within ~1 minute.

Cost: $0. GitHub Actions gives you 2,000 free minutes per month on private repos (more on public) — your workflow uses about 30 seconds per day, or **15 minutes a month**.

---

## Maintenance — how to make changes

**Edit the dashboard design.** Pull the latest HTML from the repo, edit on your machine, commit it back. The next morning's refresh only touches the news section, so your edits to layout/colors/sections survive.

**Add/remove RSS sources.** Edit `scripts/refresh-news.py` → the `FEEDS` list near the top. Add a tuple `("Name", "https://example.com/rss")`. Commit. The next run uses the new list.

**Change the refresh time.** Edit `.github/workflows/refresh-news.yml` → the `cron:` line. Format is UTC: `"30 1 * * *"` = 01:30 UTC daily. Use [crontab.guru](https://crontab.guru) to translate human times.

**Trigger an immediate refresh.** Actions tab → Refresh AI dashboard news → Run workflow. Useful when something big happens during the day.

**Pause the daily refresh.** Actions tab → Refresh AI dashboard news → "..." menu → Disable workflow. Re-enable the same way.

---

## Troubleshooting

**The workflow fails with "Permission denied" on git push.**
Repo → Settings → Actions → General → scroll to "Workflow permissions" → choose **Read and write permissions** → Save.

**The workflow runs but the dashboard URL still shows old news.**
GitHub Pages caches aggressively. Open in incognito, or wait a few minutes, or hard-refresh (Ctrl+Shift+R).

**One of the RSS feeds in `FEEDS` is dead.**
The script just skips dead feeds with a warning — you don't need to remove them. But if you want to clean up, edit the list and commit.

**The script picked items that aren't actually about AI.**
Edit `PRIORITY_KEYWORDS` in the script — these bias the ranking toward what matters to you. The more matches a title has, the higher it ranks. You can also remove low-quality feeds from `FEEDS`.

**I want the news section to use AI for a smarter top-story summary.**
The current script writes a deterministic "Top stories: A; B; C" sentence with no LLM. To upgrade: get an Anthropic API key (free tier exists, link in Anthropic Console), add it as a repo secret named `ANTHROPIC_API_KEY`, and we can extend `refresh-news.py` to call Claude Haiku for a real summary paragraph. Ask me when you're ready.

**Private repo: Pages says "404 not found".**
Pages on private repos needs Pro (Student Pack gives this free). Confirm in Settings → Pages → "Visibility" is set correctly. If still stuck, switch the repo to Public — nothing in this dashboard is sensitive.

---

## What about the Cowork artifact?

Two options once the GitHub version is live:

1. **Keep both.** Use the Cowork artifact for in-app convenience and the GitHub site for cross-device access. Just remember to copy structural changes (new sections, design tweaks) from one to the other periodically.
2. **Retire the Cowork version.** Delete the `ai-dashboard-daily-refresh` scheduled task in Cowork to stop the daily refresh attempting from there. The Cowork artifact will still exist but go stale.

If you stop using Cowork as the source of truth, you can also tell me "drop the Cowork artifact" and I'll remove it cleanly.

---

## Quick reference — files you'll need

All three are already saved in `Personal Dashboard\github-hosting\` and ready to upload:

- `refresh-news.py` — copy contents into `scripts/refresh-news.py` in the repo
- `refresh-news.yml` — copy contents into `.github/workflows/refresh-news.yml` in the repo
- Your existing `ai-student-dashboard.html` (one folder up) — upload to the repo root (and rename to `index.html` if you want the clean URL)

---

*That's it. Once the first manual workflow run goes green, the dashboard is officially "in production" and self-maintaining.*
