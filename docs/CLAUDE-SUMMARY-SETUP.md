# Smart Top-Story Summary — Claude Haiku Setup

The daily news refresh can use **Claude Haiku** to write a real 3-4 sentence digest of the day's headlines instead of the default deterministic "Top stories: A; B; C." line.

The code and workflow are already wired up. You just need to:

1. Get an Anthropic API key.
2. Add it to your GitHub repo as an Actions secret.
3. Trigger one workflow run to verify.

Estimated time: **5–10 minutes**.

---

## What you'll see when it's on

**Before (deterministic fallback):**

> **Top stories:** *Anthropic releases Claude Sonnet 4.6* (Anthropic); *Google adds Gemini Spark to Android* (The Verge AI); *OWASP updates LLM Top 10 for 2026* (Simon Willison).

**After (Haiku summary):**

> **Top stories:** Anthropic shipped <em>Claude Sonnet 4.6</em> with stronger agentic-coding scores, while Google rolled <em>Gemini Spark</em> deeper into Android with on-device task automation. On the security side, <em>OWASP</em> refreshed its LLM Top 10 list, with prompt injection still the top concern and a new entry for agent-action abuse. Worth a closer read if you're brushing up your cyber-track notes today.

The model is told to use your dashboard's voice — warm, direct, no jargon, no emojis. It synthesises themes across the six picked headlines rather than listing them.

---

## How it works (one paragraph)

When the Actions workflow runs each morning, the `refresh-news.py` script picks the day's six top stories from RSS, then tries to call Claude Haiku to produce the summary paragraph. If the API key is set and the call succeeds, you get the LLM digest. If the key is missing, the call times out, or anything else goes wrong, the script silently falls back to the deterministic line and the workflow still succeeds — **the dashboard never breaks because of a flaky API call**.

The fallback path means it's safe to leave the workflow running even when the API key isn't set yet. You'll just keep getting the old-style summary until you add it.

---

## Part 1 — Get an Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com).
2. Sign up or log in. Anthropic gives you a small amount of free credit on signup — enough to run this for many months.
3. Click your avatar (top-right) → **Settings** → **API keys** (or visit directly at [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)).
4. Click **Create Key**.
   - Name: `dashboard-news-refresh` (or anything memorable).
   - Workspace: Default is fine.
   - Permissions: **Read & write** (the default).
5. Click **Create Key**. A modal shows your key — it starts with `sk-ant-…`.
6. **Copy the key now.** Anthropic only shows it once. Paste it into a password manager.

Done with this part. Close the console.

---

## Part 2 — Add the key to GitHub as a secret

The key goes into the GitHub repo as an **Actions secret**, where the workflow can read it but nothing else can. It's encrypted at rest and never exposed in logs.

1. Open your repo on github.com.
2. Click **Settings** (top tabs, not your user settings — the repo's settings).
3. In the left sidebar: **Secrets and variables** → **Actions**.
4. Click **New repository secret** (green button, top right).
5. Fill in:
   - **Name:** `ANTHROPIC_API_KEY` — must be this exact name.
   - **Secret:** paste the `sk-ant-…` key from Part 1.
6. Click **Add secret**.

You'll land back on the secrets page with a row showing `ANTHROPIC_API_KEY · Updated now`. The value itself is no longer viewable — only editable.

---

## Part 3 — Pull the workflow changes (one-time)

Your local repo has the workflow + script changes that enable this; the live repo on GitHub needs them too.

```bash
cd C:\Users\DamianDeCruzBISTECCa\Documents\personal-dashboard
git add scripts/refresh-news.py .github/workflows/refresh-news.yml docs/CLAUDE-SUMMARY-SETUP.md
git commit -m "feat(news): summarise headlines with Claude Haiku"
git push
```

After the push, the next scheduled run will use the new code.

---

## Part 4 — Trigger a run to verify

You don't have to wait until 7am tomorrow.

1. Repo → **Actions** tab.
2. Left sidebar → **Refresh AI dashboard news**.
3. Top-right → **Run workflow** → **Run workflow** (green button).
4. Wait ~30 seconds. A new run with a yellow spinner appears, then turns green.
5. Click into the run → click the **refresh** job → expand the **Refresh the news section** step.

Look in the step logs for a line like:

```
  [llm] ok — in=412 out=187 model=claude-haiku-4-5-20251001
```

That's confirmation Claude Haiku ran. If you see that, the dashboard's news summary on the next page load will be the LLM-written version.

If instead you see:

```
  [llm] anthropic package not installed — falling back
```

then `pip install anthropic` didn't run for some reason — check that your push from Part 3 actually included the `.github/workflows/refresh-news.yml` change.

If you see:

```
  [llm] Claude call failed: <error> — falling back
```

then the API call itself errored. The most common reasons:
- **AuthenticationError** — the secret name is misspelled or the key is wrong/expired. Re-check Part 2.
- **RateLimitError** — extremely unlikely at one call per day; usually means the key isn't valid.
- **APITimeoutError** — Anthropic was slow that morning. The next day's run will retry automatically.

Either way the news section still updates with the fallback summary, so nothing breaks.

---

## Cost

Claude Haiku is the cheapest Claude model. At roughly:

- **400 input tokens** (system prompt + 6 headlines)
- **200 output tokens** (a 4-sentence paragraph)

…per daily run, that's about **0.1 cents per day**, or roughly **30 cents a year**.

Your signup credit will more than cover the first year. After that, top up $5 once and you're set for a decade.

---

## Local testing (optional)

If you want to see what the LLM summary looks like before triggering an Actions run:

```bash
cd C:\Users\DamianDeCruzBISTECCa\Documents\personal-dashboard
pip install feedparser anthropic

# PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
python scripts/refresh-news.py

# bash / git bash
ANTHROPIC_API_KEY="sk-ant-..." python scripts/refresh-news.py
```

The script reads `index.html`, fetches feeds, picks 6 stories, calls Claude, and **rewrites your local `index.html`**. So:

- If you just want to test without modifying your file, **stash first**:
  ```bash
  git stash
  python scripts/refresh-news.py
  git diff index.html       # inspect what changed
  git checkout -- index.html # discard the test changes
  git stash pop             # bring back any other local edits
  ```

Don't paste the API key into any committed file. Use the environment variable.

---

## Turning it off

If you want to disable the LLM summary later — e.g. you used up your credit, or you prefer the deterministic version:

- **Easiest:** GitHub → Settings → Secrets and variables → Actions → click the row → **Remove secret**. Next run will see no key and silently fall back.
- **Alternative:** keep the secret but rename it (e.g. `ANTHROPIC_API_KEY_DISABLED`). Same effect.

No code change needed either way.

---

## Tuning the prompt

The system prompt is in `scripts/refresh-news.py` inside `build_summary_html_llm()`. It says, in essence:

> Warm, direct, no jargon, no emojis. 3-4 sentences. Synthesise themes, don't list one-by-one. `<em>` for product/company names only. Start with `Top stories:`. Don't invent facts.

If you want a different voice — chattier, more terse, focused only on cyber, in Sinhala, whatever — that's the string to edit. After editing, commit + push and the next run uses the new prompt.

Useful tweaks I'd suggest later:
- Add `"Mention at least one cybersecurity angle if any of the headlines touch on it."` — biases output toward your track.
- Change `"3-4 sentences"` to `"2-3 sentences"` to keep the dashboard denser.
- Switch model to `claude-sonnet-4-6` (constant `LLM_MODEL` in the script) for higher quality at ~5x the cost — still pennies.

---

## Security notes

- API keys grant access to your Anthropic account. Treat like a password.
- The key only lives in GitHub Actions secrets — never in the repo or in logs.
- If you suspect a leak: console.anthropic.com → API keys → **Revoke**. Then create a fresh key, update the GitHub secret. Total recovery time: 60 seconds.
- The key is per-user, not per-repo. The same key could be added to multiple repo secrets if you have other projects calling Claude.

---

*Once the green check shows up on the workflow run with the `[llm] ok` log line, you're done. Tomorrow's 7am refresh will use the Haiku summary.*
