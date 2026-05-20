"""
refresh-news.py
================
Rewrites the news section of ai-student-dashboard.html using fresh items
from a curated list of AI-focused RSS feeds.

- No API keys required.
- Stdlib + feedparser only.
- Touches ONLY the news block (#news-feed, .news-summary, #news-meta).
  All other dashboard sections, styles, scripts are left untouched.

Run locally:   python refresh-news.py
In CI:         called by .github/workflows/refresh-news.yml
"""
from __future__ import annotations

import datetime as dt
import html
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import feedparser  # pip install feedparser

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
HTML_PATH = Path(__file__).resolve().parent.parent / "index.html"
TARGET_COUNT = 6                       # number of news items to show
LOOKBACK_HOURS = 72                    # only consider items newer than this
TIMEZONE_OFFSET_HOURS = 5.5            # Sri Lanka (UTC+5:30) for the "Updated" date

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


def parse_entry_dt(entry) -> dt.datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        struct = getattr(entry, key, None) or entry.get(key) if hasattr(entry, "get") else None
        if struct:
            try:
                return dt.datetime(*struct[:6], tzinfo=dt.timezone.utc)
            except Exception:
                continue
    return None


def fetch_candidates() -> list[dict]:
    """Pull recent entries from every feed and normalise them."""
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=LOOKBACK_HOURS)
    candidates: list[dict] = []

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


def pick_top(candidates: list[dict], n: int) -> list[dict]:
    """Rank by (priority score, recency); dedupe per domain so the list feels varied."""
    candidates.sort(key=lambda c: (-c["score"], -c["pub"].timestamp()))
    picked: list[dict] = []
    seen_domains: set[str] = set()
    seen_titles: set[str] = set()

    for c in candidates:
        title_key = re.sub(r"[^a-z0-9]+", " ", c["title"].lower()).strip()
        if title_key in seen_titles:
            continue
        if c["domain"] in seen_domains and len(picked) < n - 1:
            # Allow second pass to fill remaining slots if needed
            continue
        picked.append(c)
        seen_domains.add(c["domain"])
        seen_titles.add(title_key)
        if len(picked) >= n:
            break

    # If we still don't have enough, relax the per-domain dedupe.
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
def build_news_items_html(items: list[dict]) -> str:
    """Six <div class="news-item">…</div> blocks."""
    blocks: list[str] = []
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


def build_summary_html(items: list[dict]) -> str:
    """Top-story paragraph synthesised from the day's headlines.

    Without an LLM we stick to a deterministic summary: the top 3 titles inline.
    """
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


def today_label() -> str:
    """Date string like 'Updated 21 May 2026' in Sri Lanka time."""
    now = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=TIMEZONE_OFFSET_HOURS)
    return f"Updated {now.day} {now.strftime('%B %Y')}"


def rewrite_html(src: str, items: list[dict]) -> str:
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
def main() -> int:
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
