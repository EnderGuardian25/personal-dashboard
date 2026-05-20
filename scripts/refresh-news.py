"""
refresh-news.py
================
Rewrites the news section of index.html using fresh items from a curated
list of AI-focused RSS feeds, with a Claude-Haiku-written digest at the top.

- Stdlib + feedparser. Optionally anthropic for the digest paragraph.
- Touches ONLY the news block (#news-feed, .news-summary, #news-meta).
- Silent fallback to a deterministic summary when ANTHROPIC_API_KEY is unset
  or the API call fails for any reason.

Run locally:   python refresh-news.py
In CI:         called by .github/workflows/refresh-news.yml
"""
from __future__ import annotations

import datetime as dt
import html
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import feedparser  # pip install feedparser

# Optional: Anthropic Claude for the top-story summary paragraph.
# When ANTHROPIC_API_KEY is set in the environment we generate a real summary;
# otherwise we silently fall back to a deterministic concatenation of titles.
try:
    import anthropic  # pip install anthropic
except ImportError:
    anthropic = None

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
HTML_PATH = Path(__file__).resolve().parent.parent / "index.html"
TARGET_COUNT = 6                       # number of news items to show
LOOKBACK_HOURS = 72                    # only consider items newer than this
TIMEZONE_OFFSET_HOURS = 5.5            # Sri Lanka (UTC+5:30) for the "Updated" date

# Claude Haiku is the cheapest Claude model and plenty for a 6-sentence summary.
LLM_MODEL = "claude-haiku-4-5-20251001"
LLM_MAX_TOKENS = 700                   # hard cap — comfortably fits a 6-sentence digest
LLM_TIMEOUT_SECONDS = 30               # never block CI longer than this

# RSS sources — public, no auth. Order matters: earlier feeds get higher priority
# when we de-dup by source.
FEEDS = [
    # Primary sources
    ("Anthropic",      "https://www.anthropic.com/news/rss.xml"),
    ("OpenAI",         "https://openai.com/news/rss.xml"),
    ("Google AI Blog", "https://blog.google/technology/ai/rss/"),
    ("DeepMind",       "https://deepmind.google/blog/rss.xml"),
    # Tech press (AI-tagged)
    ("TechCrunch AI",  "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI",   "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"),
    ("Ars Technica AI","https://arstechnica.com/ai/feed/"),
    # Independent / cybersecurity-adjacent
    ("Simon Willison", "https://simonwillison.net/atom/everything/"),
    ("HF Papers",      "https://huggingface.co/papers/feed"),
    # HN — broad, useful as a fallback
    ("Hacker News AI", "https://hnrss.org/newest?q=AI+OR+LLM+OR+%22machine+learning%22"),
]

# Keywords that bias toward cybersecurity/UI-UX flavour stories (Damian's tracks)
PRIORITY_KEYWORDS = (
    "security", "vulnerab", "prompt injection", "jailbreak", "owasp",
    "agent", "claude", "gpt", "gemini", "anthropic", "openai", "deepmind",
    "figma", "design", "ux", "ui", "copilot",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def html_escape_attr(value: str) -> str:
    """Escape a string for use inside an HTML attribute (double-quoted)."""
    return html.escape(value, quote=True)


def domain_of(url: str) -> str:
    """e.g. https://www.anthropic.com/news/foo -> anthropic.com"""
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def parse_entry_dt(entry):
    for key in ("published_parsed", "updated_parsed"):
        struct = getattr(entry, key, None) or (entry.get(key) if hasattr(entry, "get") else None)
        if struct:
            try:
                return dt.datetime(*struct[:6], tzinfo=dt.timezone.utc)
            except Exception:
                continue
    return None


def fetch_candidates():
    """Pull recent entries from every feed and normalise them."""
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=LOOKBACK_HOURS)
    candidates = []
    for source_name, url in FEEDS:
        try:
            parsed = feedparser.parse(url)
        except Exception as e:
            print(f"  [warn] {source_name}: {e}", file=sys.stderr)
            continue
        for entry in parsed.entries[:15]:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue
            pub = parse_entry_dt(entry)
            if pub and pub < cutoff:
                continue
            text = title.lower()
            score = sum(1 for kw in PRIORITY_KEYWORDS if kw in text)
            candidates.append({
                "title":  title,
                "url":    link,
                "src":    source_name,
                "domain": domain_of(link),
                "pub":    pub or now,
                "score":  score,
            })
    return candidates


def pick_top(candidates, n):
    """Rank by (priority score, recency); dedupe per domain so the list feels varied."""
    candidates.sort(key=lambda c: (-c["score"], -c["pub"].timestamp()))
    picked = []
    seen_domains = set()
    seen_titles = set()
    for c in candidates:
        title_key = re.sub(r"[^a-z0-9]+", " ", c["title"].lower()).strip()
        if title_key in seen_titles:
            continue
        if c["domain"] in seen_domains and len(picked) < n - 1:
            continue
        picked.append(c)
        seen_domains.add(c["domain"])
        seen_titles.add(title_key)
        if len(picked) >= n:
            break
    if len(picked) < n:
        for c in candidates:
            title_key = re.sub(r"[^a-z0-9]+", " ", c["title"].lower()).strip()
            if title_key in seen_titles:
                continue
            picked.append(c)
            seen_titles.add(title_key)
            if len(picked) >= n:
                break
    return picked[:n]


# ---------------------------------------------------------------------------
# HTML rewriting
# ---------------------------------------------------------------------------
def build_news_items_html(items):
    """Six <div class="news-item">...</div> blocks."""
    blocks = []
    for it in items:
        title = html.escape(it["title"])
        url = html_escape_attr(it["url"])
        src = html.escape(f"{it['src']} · {it['domain']}")
        src_attr = html_escape_attr(f"{it['src']} · {it['domain']}")
        title_attr = html_escape_attr(it["title"])
        blocks.append(f"""\
          <div class="news-item">
            <div class="body">
              <a class="title-link" href="{url}" target="_blank" rel="noopener">{title}</a>
              <div class="src">{src}</div>
            </div>
            <button class="save-btn" data-save data-title="{title_attr}" data-url="{url}" data-src="{src_attr}">＋ Save</button>
          </div>""")
    return "\n".join(blocks)


def build_summary_html_fallback(items):
    """Deterministic top-story line — used when the LLM is unavailable."""
    top = items[:3]
    parts = []
    for it in top:
        parts.append(f"<em>{html.escape(it['title'])}</em> ({html.escape(it['src'])})")
    body = "; ".join(parts) if parts else "No fresh items today — check back tomorrow."
    return (
        '<div class="news-summary">\n'
        f'  <strong>Top stories:</strong> {body}.\n'
        '</div>'
    )


def build_summary_html_llm(items):
    """Ask Claude Haiku to write a 5-7 sentence digest of today's headlines.

    Returns the full <div class="news-summary">...</div> block, or None on any
    failure. The caller is expected to fall back to the deterministic version.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    if anthropic is None:
        print("  [llm] anthropic package not installed — falling back", file=sys.stderr)
        return None
    if not items:
        return None

    headlines = "\n".join(
        f"- {it['title']} ({it['src']})" for it in items[:TARGET_COUNT]
    )

    system_prompt = (
        "You write a one-paragraph top-stories digest for a personal AI "
        "dashboard. The reader is a CS student into cybersecurity and UI/UX. "
        "Voice: warm, direct, no jargon, no emojis, no hype words like "
        "'groundbreaking' or 'revolutionary' or 'game-changing'. "
        "Length: 5 to 7 sentences. Long enough to be substantive, short "
        "enough to skim with morning coffee. "
        "Content rules: "
        "(a) Name the specific products, companies, models, and tools the "
        "headlines reference — not vague phrases like 'a major lab' or 'a "
        "leading model'. If a headline mentions Claude Sonnet 4.6, say "
        "<em>Claude Sonnet 4.6</em>, not 'a new Anthropic model'. "
        "(b) Briefly say what each one actually is or does — one short "
        "clause is enough — so a reader who hasn't seen the headlines still "
        "understands. "
        "(c) Group related items together (e.g. all the new model releases, "
        "all the security stories, all the design-tool news) rather than "
        "stepping through them headline-by-headline. "
        "(d) Where it's natural, end with one sentence on the so-what for "
        "Damian's cybersecurity or UI/UX work. If nothing in today's batch "
        "is relevant to those tracks, skip it rather than forcing a tie-in. "
        "Formatting: use <em>...</em> ONLY around very short noun phrases "
        "— specific product names ('Gemini 3.5 Flash'), model names "
        "('Claude Sonnet 4.6'), or company names ('Figma', 'OpenAI'). "
        "NEVER wrap entire clauses, sentences, descriptions, or anything "
        "longer than about three words inside <em>. Examples of correct "
        "use: <em>Gemini 3.5 Flash</em>, <em>Figma</em>, <em>Claude</em>. "
        "Examples of WRONG use (do not do this): "
        "<em>Google is shifting focus to agentic systems</em>, "
        "<em>an upcoming agentic overhaul to search coming in 2026</em>. "
        "If a sentence has no specific name worth emphasising, use no "
        "<em> tags in it. Better to under-emphasise than to over-emphasise. "
        "EVERY opening <em> tag must have a matching closing </em> tag — "
        "never leave one unclosed. "
        "No other HTML tags. No markdown. No line breaks. "
        "Start the paragraph with the literal phrase 'Top stories:' "
        "followed by a space (this exact prefix will be wrapped in a "
        "<strong> tag by the caller — write 'Top stories:' once and only "
        "once at the very start). "
        "Never invent facts beyond what the headlines literally say. "
        "If you're unsure what a headline means, describe only what the "
        "title and source make verifiable."
    )

    user_prompt = (
        "Write today's top-stories digest from these headlines:\n\n"
        f"{headlines}\n\n"
        "Remember: name the specific products and companies, briefly "
        "explain what each one is, group related items, 5 to 7 sentences. "
        "Reply with ONLY the paragraph — no preamble, no markdown, no "
        "newlines. Plain text plus optional <em>...</em> tags."
    )

    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=LLM_TIMEOUT_SECONDS)
        resp = client.messages.create(
            model=LLM_MODEL,
            max_tokens=LLM_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as e:
        print(f"  [llm] Claude call failed: {e!r} — falling back", file=sys.stderr)
        return None

    try:
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        ).strip()
    except Exception:
        text = ""

    if not text:
        print("  [llm] empty response — falling back", file=sys.stderr)
        return None

    # Strip the literal "Top stories:" the model was told to prepend, since we
    # wrap it in <strong> ourselves.
    body = re.sub(r"^\s*top\s+stories\s*:\s*", "", text, count=1, flags=re.IGNORECASE)

    # Defensive: allow only a tiny whitelist of inline tags. Strip anything else.
    body = re.sub(r"</?(?!em\b)[^>]+>", "", body)

    # Defensive: unwrap any <em> that wraps too much content. If the model
    # over-applied emphasis (e.g. wrapping a whole clause), we'd rather lose
    # the emphasis than have it dominate the paragraph visually.
    MAX_EM_CHARS = 30
    MAX_EM_WORDS = 4

    def _maybe_unwrap_em(match):
        inner = match.group(1)
        if len(inner) > MAX_EM_CHARS or len(inner.split()) > MAX_EM_WORDS:
            return inner
        return f"<em>{inner}</em>"

    body = re.sub(r"<em>([^<]*)</em>", _maybe_unwrap_em, body)

    # Defensive: if the model emitted unbalanced <em> tags (i.e. opened one
    # without closing it), the browser will implicitly extend the emphasis
    # to the end of the paragraph, turning the whole summary bold+blue.
    # When in doubt, drop ALL em tags.
    open_count  = len(re.findall(r"<em\b[^>]*>", body))
    close_count = len(re.findall(r"</em>", body))
    if open_count != close_count:
        print(
            f"  [llm] unbalanced em tags ({open_count} open / {close_count} close) "
            f"— stripping all emphasis",
            file=sys.stderr,
        )
        body = re.sub(r"</?em\b[^>]*>", "", body)

    usage = getattr(resp, "usage", None)
    if usage:
        print(
            f"  [llm] ok — in={usage.input_tokens} out={usage.output_tokens} "
            f"model={LLM_MODEL}",
            file=sys.stderr,
        )

    return (
        '<div class="news-summary">\n'
        f'  <strong>Top stories:</strong> {body}\n'
        '</div>'
    )


def build_summary_html(items):
    """Top-story paragraph. Tries Claude Haiku, falls back to deterministic."""
    llm = build_summary_html_llm(items)
    if llm is not None:
        return llm
    return build_summary_html_fallback(items)


def today_label():
    """Label like 'Updated 21 May 2026 · 07:14 SLT' in Sri Lanka time.

    Includes the time-of-day so the dashboard surfaces when the last
    refresh ran, not just which day — useful since GitHub Actions cron
    can drift 5-15 minutes around the scheduled minute.
    """
    now = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=TIMEZONE_OFFSET_HOURS)
    return (
        f"Updated {now.day} {now.strftime('%B %Y')} "
        f"· {now.strftime('%H:%M')} SLT"
    )


def rewrite_html(src, items):
    # 1. Replace the news-meta date label
    src = re.sub(
        r'(<p class="section-sub" id="news-meta">)[^<]*(</p>)',
        lambda m: f'{m.group(1)}{today_label()}{m.group(2)}',
        src,
        count=1,
    )

    # 2. Replace the .news-summary block
    src = re.sub(
        r'<div class="news-summary">[\s\S]*?</div>',
        lambda m: build_summary_html(items),
        src,
        count=1,
    )

    # 3. Replace the 6 news-item blocks inside #news-feed
    new_items = build_news_items_html(items)
    src = re.sub(
        r'(<div id="news-feed" class="news-list">)[\s\S]*?(</div>\s*<p style="margin-top:14px)',
        lambda m: f'{m.group(1)}\n{new_items}\n        {m.group(2)}',
        src,
        count=1,
    )

    return src


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not HTML_PATH.exists():
        print(f"ERROR: {HTML_PATH} not found", file=sys.stderr)
        return 1

    print(f"Reading {HTML_PATH}")
    original = HTML_PATH.read_text(encoding="utf-8")

    print("Fetching feeds…")
    candidates = fetch_candidates()
    print(f"  {len(candidates)} recent entries from {len(FEEDS)} feeds")

    if not candidates:
        print("WARN: No fresh entries found — leaving HTML unchanged.")
        return 0

    items = pick_top(candidates, TARGET_COUNT)
    if len(items) < TARGET_COUNT:
        print(f"WARN: only found {len(items)}/{TARGET_COUNT} items")

    print("Picked:")
    for i, it in enumerate(items, 1):
        print(f"  {i}. [{it['src']}] {it['title']}")

    new_html = rewrite_html(original, items)

    if new_html == original:
        print("No changes detected (regex may not have matched). Aborting write.")
        return 2

    HTML_PATH.write_text(new_html, encoding="utf-8")
    print(f"Wrote {HTML_PATH} ({len(new_html)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
