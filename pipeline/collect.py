"""
AI News Data Pipeline - Collector
Fetches AI-related content from HN and Reddit, inserts into Supabase.

Usage:
  pip install -r requirements.txt
  cp ../.env.example .env  (fill in SUPABASE_URL + SUPABASE_SERVICE_KEY)
  python collect.py
"""

import os
import json
import hashlib
from datetime import datetime, timezone
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

# Supabase REST API headers
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "claude", "gemini", "openai",
    "anthropic", "transformer", "neural network", "diffusion",
    "stable diffusion", "midjourney", "chatgpt", "copilot",
    "rag", "fine-tuning", "finetuning", "embedding", "vector",
    "langchain", "llamaindex", "hugging face", "ollama",
    "agent", "agentic", "mcp", "tool use",
]


def is_ai_related(title: str, score_threshold: int = 0) -> bool:
    """Check if a title is AI-related based on keywords."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in AI_KEYWORDS)


def classify_content_type(title: str, source: str) -> str:
    """Simple heuristic to classify content type."""
    title_lower = title.lower()
    if "arxiv" in source.lower() or "paper" in title_lower or "research" in title_lower:
        return "paper"
    if any(w in title_lower for w in ["how to", "tutorial", "guide", "tip", "trick", "howto"]):
        return "knowhow"
    if any(w in title_lower for w in ["use case", "case study", "built", "building", "shipped"]):
        return "usecase"
    if any(w in title_lower for w in ["tool", "library", "framework", "release", "launch", "v2", "v3"]):
        return "tool"
    if any(w in title_lower for w in ["discuss", "opinion", "thought", "debate", "ask hn", "ask reddit"]):
        return "discussion"
    return "news"


def fetch_hn_top_ai(limit: int = 30) -> list[dict[str, Any]]:
    """Fetch AI-related stories from Hacker News using Algolia API."""
    print("[HN] Fetching AI stories...")
    articles = []

    # Search HN for AI-related stories from last 24h
    url = "https://hn.algolia.com/api/v1/search"
    queries = ["AI", "LLM", "machine learning", "GPT", "Claude", "OpenAI"]

    seen_urls: set[str] = set()

    for query in queries:
        try:
            resp = httpx.get(
                url,
                params={
                    "query": query,
                    "tags": "story",
                    "numericFilters": "points>5",
                    "hitsPerPage": 20,
                },
                timeout=15,
            )
            resp.raise_for_status()
            hits = resp.json().get("hits", [])

            for hit in hits:
                story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
                if story_url in seen_urls:
                    continue
                seen_urls.add(story_url)

                title = hit.get("title", "")
                if not is_ai_related(title) and query.lower() not in title.lower():
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

    print(f"  [HN] Found {len(articles)} AI stories")
    return articles[:limit]


def fetch_reddit_ai(limit: int = 30) -> list[dict[str, Any]]:
    """Fetch AI-related posts from Reddit subreddits."""
    print("[Reddit] Fetching AI posts...")
    articles = []
    subreddits = ["MachineLearning", "artificial", "LocalLLaMA", "ChatGPT", "singularity"]

    seen_urls: set[str] = set()

    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json"
            resp = httpx.get(
                url,
                params={"limit": 25},
                headers={"User-Agent": "AINewsPipeline/1.0"},
                timeout=15,
                follow_redirects=True,
            )
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])

            for post in posts:
                data = post.get("data", {})
                if data.get("stickied"):
                    continue

                post_url = data.get("url", "")
                if not post_url or post_url in seen_urls:
                    continue

                # Use reddit permalink for self posts
                if data.get("is_self"):
                    post_url = f"https://reddit.com{data.get('permalink', '')}"

                seen_urls.add(post_url)
                title = data.get("title", "")
                score = data.get("score", 0)

                if score < 10:
                    continue

                articles.append({
                    "title": title,
                    "url": post_url,
                    "source": f"Reddit",
                    "source_type": "community",
                    "content_type": classify_content_type(title, f"Reddit r/{sub}"),
                    "score": score,
                    "social_score": data.get("num_comments", 0),
                    "author": data.get("author"),
                    "published_at": datetime.fromtimestamp(
                        data.get("created_utc", 0), tz=timezone.utc
                    ).isoformat(),
                    "tags": [f"r/{sub}"],
                })
        except Exception as e:
            print(f"  [Reddit] Error fetching r/{sub}: {e}")

    print(f"  [Reddit] Found {len(articles)} posts")
    return articles[:limit]


def upsert_articles(articles: list[dict[str, Any]]) -> int:
    """Insert articles into Supabase, skip duplicates by URL."""
    if not articles:
        return 0

    print(f"[DB] Upserting {len(articles)} articles...")

    # Add collected_at and ensure required fields
    now = datetime.now(timezone.utc).isoformat()
    for a in articles:
        a["collected_at"] = now
        a.setdefault("title_ko", None)
        a.setdefault("summary_ko", None)
        a.setdefault("thumbnail_url", None)
        # Remove raw_data to keep payload small
        a.pop("raw_data", None)

    # Supabase REST upsert (on conflict url)
    url = f"{SUPABASE_URL}/rest/v1/articles"
    headers = {**HEADERS, "Prefer": "return=minimal,resolution=merge-duplicates"}

    inserted = 0
    # Batch in chunks of 50
    for i in range(0, len(articles), 50):
        batch = articles[i : i + 50]
        try:
            resp = httpx.post(url, headers=headers, json=batch, timeout=30)
            if resp.status_code in (200, 201):
                inserted += len(batch)
            else:
                print(f"  [DB] Batch error: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            print(f"  [DB] Batch exception: {e}")

    print(f"  [DB] Upserted {inserted} articles")
    return inserted


def main():
    print("=" * 50)
    print(f"AI News Pipeline - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    all_articles: list[dict[str, Any]] = []

    # Collect from sources
    all_articles.extend(fetch_hn_top_ai(30))
    all_articles.extend(fetch_reddit_ai(30))

    print(f"\n[Total] Collected {len(all_articles)} articles")

    # Deduplicate by URL
    seen: set[str] = set()
    unique = []
    for a in all_articles:
        url_hash = hashlib.md5(a["url"].encode()).hexdigest()
        if url_hash not in seen:
            seen.add(url_hash)
            unique.append(a)

    print(f"[Dedup] {len(unique)} unique articles")

    # Insert to DB
    count = upsert_articles(unique)
    print(f"\n[Done] {count} articles saved to database")


if __name__ == "__main__":
    main()
