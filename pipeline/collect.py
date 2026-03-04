"""
AI News Data Pipeline - Collector v2
Sources: HN, Reddit, and official AI company blogs (Anthropic, OpenAI, Google AI, etc.)

Usage:
  pip install -r requirements.txt
  python collect.py
"""

import os
import re
import hashlib
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Load .env from pipeline dir or parent
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

# ─── Recency ───────────────────────────────────────────────
MAX_AGE_HOURS = 168  # 7 days — articles older than this are skipped

# ─── AI Keyword Matching ──────────────────────────────────
# Short keywords (<=3 chars) use exact word-boundary matching
# Longer keywords use substring matching
AI_KEYWORDS_STRONG = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "claude", "gemini", "openai",
    "anthropic", "transformer", "neural network", "diffusion model",
    "stable diffusion", "midjourney", "chatgpt", "copilot",
    "rag", "fine-tuning", "finetuning", "embedding", "vector database",
    "langchain", "llamaindex", "hugging face", "huggingface", "ollama", "vllm",
    "agentic", "mcp", "model context protocol",
    "deepseek", "mistral", "llama", "qwen", "phi-",
    "foundation model", "generative ai", "gen ai",
    "text-to-image", "text-to-video", "text-to-speech",
    "computer vision", "nlp", "natural language",
    "reinforcement learning", "rlhf", "grpo", "rlvr",
    "inference", "quantization", "lora", "qlora",
    "benchmark", "leaderboard", "swe-bench",
    "multimodal", "context window",
    "arxiv", "cs.ai", "cs.cl", "cs.lg", "cs.cv",
    "perplexity", "cursor", "windsurf",
    "google deepmind", "meta ai", "xai", "grok",
]

WEAK_KEYWORDS = ["agent", "model", "training", "data", "tool", "api", "token"]

BLACKLIST_PATTERNS = [
    # Consumer products
    "air con", "aircon", "air purifier", "paper airplane", "paper plane",
    "airpod", "airfoil", "airline", "airport", "amazon prime air",
    "air quality", "hvac", "drone delivery",
    # Non-tech
    "real estate", "stock market", "cryptocurrency", "bitcoin",
    "sports", "recipe", "cooking", "fashion", "celebrity",
    # Conflict/violence (not about AI tech)
    "massacre", "bombing in gaza", "killed aid", "point blank range",
    "ground invasion", "troops deployed",
]


def is_ai_related(title: str) -> bool:
    """Strict check with word-boundary matching for short keywords."""
    title_lower = title.lower()

    # Blacklist check
    if any(bl in title_lower for bl in BLACKLIST_PATTERNS):
        return False

    # Extract words for boundary matching
    words = set(re.findall(r'\b\w+\b', title_lower))

    for kw in AI_KEYWORDS_STRONG:
        if ' ' in kw:
            # Multi-word phrase: substring match
            if kw in title_lower:
                return True
        elif len(kw) <= 3:
            # Short keyword: exact word match only (prevents "ai" matching "aid")
            if kw in words:
                return True
        else:
            # Longer keyword: substring is fine
            if kw in title_lower:
                return True

    # Weak keywords need 2+ matches
    weak_count = sum(1 for kw in WEAK_KEYWORDS if kw in words)
    if weak_count >= 2:
        return True

    return False


def classify_content_type(title: str, source: str, subreddit: str = "") -> str:
    """Classify article content type by title heuristics."""
    title_lower = title.lower()

    if any(x in title_lower for x in [
        "arxiv", "[r]", "paper:", "research:", "cs.ai", "cs.cl", "cs.lg", "cs.cv",
        "nips", "icml", "iclr", "cvpr", "neurips", "aaai", "acl ",
        "we propose", "we introduce", "we present", "benchmark",
    ]):
        return "paper"

    if any(x in title_lower for x in [
        "how to", "how i", "tutorial", "guide", "tip", "trick",
        "step by step", "walkthrough", "lesson", "learned",
        "my experience", "i built", "i trained", "i made",
        "best practice", "production", "deploy",
    ]):
        return "knowhow"

    if any(x in title_lower for x in [
        "use case", "case study", "we built", "we shipped", "we replaced",
        "at scale", "in production", "our stack", "our experience",
    ]):
        return "usecase"

    if any(x in title_lower for x in [
        "release", "launch", "announcing", "introducing",
        "v1", "v2", "v3", "v4", "v0.",
        "open source", "open-source", "library", "framework", "sdk",
        "show hn", "[p]", "playground",
    ]):
        return "tool"

    if any(x in title_lower for x in [
        "[d]", "discuss", "opinion", "thought", "debate",
        "ask hn", "ask reddit", "what do you think",
        "is it just me", "anyone else", "hot take",
        "why ", "should we", "rant", "unpopular opinion",
    ]):
        return "discussion"

    # Subreddit prefix hints
    if title_lower.startswith("[r]"):
        return "paper"
    if title_lower.startswith("[p]"):
        return "tool"
    if title_lower.startswith("[d]"):
        return "discussion"

    return "news"


# ─── Date Helpers ──────────────────────────────────────────

def parse_rss_date(date_str: str) -> str:
    """Parse RFC 2822 (RSS) or ISO 8601 (Atom) date strings."""
    if not date_str:
        return datetime.now(timezone.utc).isoformat()
    try:
        return parsedate_to_datetime(date_str).isoformat()
    except Exception:
        pass
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).isoformat()
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat()


def is_recent(published_at: str, max_hours: int = MAX_AGE_HOURS) -> bool:
    """Check if article is within the allowed age."""
    try:
        pub = datetime.fromisoformat(published_at)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        return pub > datetime.now(timezone.utc) - timedelta(hours=max_hours)
    except Exception:
        return True


# ─── Source: Hacker News ───────────────────────────────────

def fetch_hn_top_ai(limit: int = 30) -> list[dict[str, Any]]:
    """Fetch recent AI stories from HN (last 48h, sorted by date)."""
    print("[HN] Fetching recent AI stories...")
    articles: list[dict[str, Any]] = []

    cutoff_ts = int((datetime.now(timezone.utc) - timedelta(hours=48)).timestamp())
    url = "https://hn.algolia.com/api/v1/search_by_date"
    queries = ["AI", "LLM", "GPT", "Claude", "OpenAI", "deep learning",
               "machine learning", "Anthropic", "transformer"]

    seen_urls: set[str] = set()

    for query in queries:
        try:
            resp = httpx.get(url, params={
                "query": query,
                "tags": "story",
                "numericFilters": f"points>20,created_at_i>{cutoff_ts}",
                "hitsPerPage": 20,
            }, timeout=15)
            resp.raise_for_status()

            for hit in resp.json().get("hits", []):
                story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
                if story_url in seen_urls:
                    continue
                seen_urls.add(story_url)

                title = hit.get("title", "")
                if not is_ai_related(title):
                    continue

                articles.append({
                    "title": title,
                    "url": story_url,
                    "source": "Hacker News",
                    "source_type": "community",
                    "content_type": classify_content_type(title, "Hacker News"),
                    "score": hit.get("points", 0),
                    "social_score": hit.get("num_comments", 0),
                    "author": hit.get("author"),
                    "published_at": hit.get("created_at", datetime.now(timezone.utc).isoformat()),
                    "tags": ["hn"],
                })
        except Exception as e:
            print(f"  [HN] Error querying '{query}': {e}")

    print(f"  [HN] Found {len(articles)} recent AI stories")
    return articles[:limit]


# ─── Source: Reddit ────────────────────────────────────────

def fetch_reddit_ai(limit: int = 30) -> list[dict[str, Any]]:
    """Fetch AI posts from Reddit subreddits."""
    print("[Reddit] Fetching AI posts...")
    articles: list[dict[str, Any]] = []
    subreddits = ["MachineLearning", "artificial", "LocalLLaMA", "ChatGPT", "singularity"]

    seen_urls: set[str] = set()

    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json"
            resp = httpx.get(url, params={"limit": 25},
                             headers={"User-Agent": "AINewsPipeline/1.0"},
                             timeout=15, follow_redirects=True)
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])

            for post in posts:
                data = post.get("data", {})
                if data.get("stickied"):
                    continue

                post_url = data.get("url", "")
                if not post_url or post_url in seen_urls:
                    continue
                if data.get("is_self"):
                    post_url = f"https://reddit.com{data.get('permalink', '')}"
                seen_urls.add(post_url)

                title = data.get("title", "")
                score = data.get("score", 0)
                if score < 10:
                    continue

                # Blacklist check
                if any(bl in title.lower() for bl in BLACKLIST_PATTERNS):
                    continue

                published_at = datetime.fromtimestamp(
                    data.get("created_utc", 0), tz=timezone.utc
                ).isoformat()

                if not is_recent(published_at):
                    continue

                articles.append({
                    "title": title,
                    "url": post_url,
                    "source": "Reddit",
                    "source_type": "community",
                    "content_type": classify_content_type(title, "Reddit", sub),
                    "score": score,
                    "social_score": data.get("num_comments", 0),
                    "author": data.get("author"),
                    "published_at": published_at,
                    "tags": [f"r/{sub}"],
                })
        except Exception as e:
            print(f"  [Reddit] Error fetching r/{sub}: {e}")

    print(f"  [Reddit] Found {len(articles)} posts")
    return articles[:limit]


# ─── Source: Official AI Company Blogs (RSS) ───────────────

RSS_FEEDS = [
    ("https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml", "Anthropic"),
    ("https://openai.com/news/rss.xml", "OpenAI"),
    ("https://blog.google/technology/ai/rss/", "Google AI"),
    ("https://huggingface.co/blog/feed.xml", "Hugging Face"),
    ("https://deepmind.google/blog/rss.xml", "DeepMind"),
    ("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch"),
]


def fetch_rss_feed(feed_url: str, source_name: str, limit: int = 10) -> list[dict[str, Any]]:
    """Fetch articles from a single RSS/Atom feed."""
    try:
        resp = httpx.get(feed_url, timeout=15, follow_redirects=True,
                         headers={"User-Agent": "AINewsPipeline/1.0"})
        if resp.status_code != 200:
            print(f"  [{source_name}] HTTP {resp.status_code}")
            return []

        root = ET.fromstring(resp.text)
        articles: list[dict[str, Any]] = []

        # Try RSS format first (channel/item)
        items = root.findall('.//item')
        if items:
            for item in items[:limit]:
                title = (item.findtext('title') or '').strip()
                link = (item.findtext('link') or '').strip()
                pub_date = item.findtext('pubDate') or ''

                if not title or not link:
                    continue

                published_at = parse_rss_date(pub_date)
                if not is_recent(published_at):
                    continue

                articles.append({
                    "title": title,
                    "url": link,
                    "source": source_name,
                    "source_type": "blog",
                    "content_type": classify_content_type(title, source_name),
                    "score": 0,
                    "social_score": 0,
                    "author": None,
                    "published_at": published_at,
                    "tags": [source_name.lower().replace(" ", "-")],
                })
        else:
            # Try Atom format (entry)
            atom_ns = "http://www.w3.org/2005/Atom"
            entries = root.findall(f'.//{{{atom_ns}}}entry')

            for entry in entries[:limit]:
                title_el = entry.find(f'{{{atom_ns}}}title')
                title = title_el.text.strip() if title_el is not None and title_el.text else ''

                link_el = entry.find(f'{{{atom_ns}}}link')
                link = link_el.get('href', '') if link_el is not None else ''

                pub_el = entry.find(f'{{{atom_ns}}}published') or entry.find(f'{{{atom_ns}}}updated')
                pub_date = pub_el.text if pub_el is not None else ''

                if not title or not link:
                    continue

                published_at = parse_rss_date(pub_date)
                if not is_recent(published_at):
                    continue

                articles.append({
                    "title": title,
                    "url": link,
                    "source": source_name,
                    "source_type": "blog",
                    "content_type": classify_content_type(title, source_name),
                    "score": 0,
                    "social_score": 0,
                    "author": None,
                    "published_at": published_at,
                    "tags": [source_name.lower().replace(" ", "-")],
                })

        print(f"  [{source_name}] {len(articles)} recent articles")
        return articles
    except Exception as e:
        print(f"  [{source_name}] Error: {e}")
        return []


def fetch_ai_blogs(limit: int = 20) -> list[dict[str, Any]]:
    """Fetch from all official AI company blog RSS feeds."""
    print("[Blogs] Fetching official AI company blogs...")
    all_articles: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for feed_url, name in RSS_FEEDS:
        articles = fetch_rss_feed(feed_url, name)
        for a in articles:
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                all_articles.append(a)
        time.sleep(0.5)

    print(f"  [Blogs] Total: {len(all_articles)} articles")
    return all_articles[:limit]


# ─── Topic Dedup ───────────────────────────────────────────

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "about", "but",
    "not", "or", "and", "if", "so", "that", "this", "it", "its",
    "you", "your", "i", "my", "me", "we", "our", "they", "their",
    "just", "how", "what", "who", "why", "when", "where", "which",
    "all", "any", "each", "every", "both", "few", "more", "most",
    "than", "too", "very", "really", "also", "now", "new", "first",
}


def dedup_by_topic(articles: list[dict[str, Any]], max_overlap: float = 0.5) -> list[dict[str, Any]]:
    """Remove near-duplicate articles about the same topic. Keeps highest-scored."""
    articles.sort(key=lambda a: a.get("score", 0), reverse=True)

    result: list[dict[str, Any]] = []
    kept_word_sets: list[set[str]] = []

    for article in articles:
        title_words = {
            w.lower() for w in re.findall(r'\b\w+\b', article["title"])
            if len(w) > 2 and w.lower() not in STOP_WORDS
        }

        if not title_words:
            result.append(article)
            continue

        is_dup = False
        for existing_words in kept_word_sets:
            shared = len(title_words & existing_words)
            smaller = min(len(title_words), len(existing_words))
            if smaller > 0 and shared / smaller > max_overlap:
                is_dup = True
                break

        if not is_dup:
            result.append(article)
            kept_word_sets.append(title_words)

    removed = len(articles) - len(result)
    if removed:
        print(f"[Dedup] Removed {removed} near-duplicate articles")
    return result


# ─── DB Operations ─────────────────────────────────────────

def upsert_articles(articles: list[dict[str, Any]]) -> int:
    """Insert articles into Supabase, skip duplicates by URL."""
    if not articles:
        return 0

    print(f"[DB] Upserting {len(articles)} articles...")

    now = datetime.now(timezone.utc).isoformat()
    for a in articles:
        a["collected_at"] = now
        a.setdefault("title_ko", None)
        a.setdefault("summary_ko", None)
        a.setdefault("content_ko", None)
        a.setdefault("thumbnail_url", None)
        a.pop("raw_data", None)

    url = f"{SUPABASE_URL}/rest/v1/articles"
    headers = {**HEADERS, "Prefer": "return=headers-only,resolution=ignore-duplicates"}

    inserted = 0
    for i in range(0, len(articles), 50):
        batch = articles[i : i + 50]
        try:
            resp = httpx.post(url, headers=headers, json=batch, timeout=30,
                              params={"on_conflict": "url"})
            if resp.status_code in (200, 201):
                inserted += len(batch)
            else:
                print(f"  [DB] Batch error: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            print(f"  [DB] Batch exception: {e}")

    print(f"  [DB] Upserted {inserted} articles")
    return inserted


# ─── Main ──────────────────────────────────────────────────

def main():
    print("=" * 50)
    print(f"AI News Pipeline v2 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    all_articles: list[dict[str, Any]] = []

    # 1) Community sources
    all_articles.extend(fetch_hn_top_ai(30))
    all_articles.extend(fetch_reddit_ai(30))

    # 2) Official AI company blogs
    all_articles.extend(fetch_ai_blogs(20))

    print(f"\n[Total] Collected {len(all_articles)} articles")

    # 3) Deduplicate by URL
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for a in all_articles:
        url_hash = hashlib.md5(a["url"].encode()).hexdigest()
        if url_hash not in seen:
            seen.add(url_hash)
            unique.append(a)

    print(f"[URL Dedup] {len(unique)} unique articles")

    # 4) Topic dedup (remove near-duplicate titles)
    unique = dedup_by_topic(unique)

    print(f"[Final] {len(unique)} articles to save")

    # 5) Insert to DB
    count = upsert_articles(unique)
    print(f"\n[Done] {count} articles saved to database")


if __name__ == "__main__":
    main()
