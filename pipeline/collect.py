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

# Strong AI keywords — title MUST contain at least one
AI_KEYWORDS_STRONG = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "claude", "gemini", "openai",
    "anthropic", "transformer", "neural network", "diffusion model",
    "stable diffusion", "midjourney", "chatgpt", "copilot",
    "rag", "fine-tuning", "finetuning", "embedding", "vector database",
    "langchain", "llamaindex", "hugging face", "ollama", "vllm",
    "agentic", "mcp", "model context protocol",
    "deepseek", "mistral", "llama", "qwen", "phi-",
    "foundation model", "generative ai", "gen ai",
    "text-to-image", "text-to-video", "text-to-speech",
    "computer vision", "nlp", "natural language",
    "reinforcement learning", "rlhf", "grpo",
    "inference", "quantization", "lora", "qlora",
    "benchmark", "leaderboard", "swe-bench",
    "token", "context window", "multimodal",
    "arxiv", "cs.ai", "cs.cl", "cs.lg", "cs.cv",
]

# Ambiguous words that need a second AI keyword to qualify
WEAK_KEYWORDS = ["agent", "model", "training", "data", "tool", "api"]

# Blacklist — definitely NOT AI news even if keywords match
BLACKLIST_PATTERNS = [
    "air con", "aircon", "air purifier", "paper airplane", "paper plane",
    "airpod", "airfoil", "airline", "airport", "amazon prime air",
    "air quality", "hvac", "weather", "flight", "drone delivery",
    "real estate", "stock market", "cryptocurrency", "bitcoin",
    "sports", "recipe", "cooking", "fashion", "celebrity",
]


def is_ai_related(title: str) -> bool:
    """Strict check: title must be genuinely about AI/ML."""
    title_lower = title.lower()

    # Blacklist check first
    if any(bl in title_lower for bl in BLACKLIST_PATTERNS):
        return False

    # Strong keyword match
    if any(kw in title_lower for kw in AI_KEYWORDS_STRONG):
        return True

    # Weak keyword needs at least 2 matches or 1 weak + context
    weak_count = sum(1 for kw in WEAK_KEYWORDS if kw in title_lower)
    if weak_count >= 2:
        return True

    return False


def classify_content_type(title: str, source: str, subreddit: str = "") -> str:
    """Improved heuristic to classify content type."""
    title_lower = title.lower()
    sub_lower = subreddit.lower()

    # Paper detection
    if any(x in title_lower for x in [
        "arxiv", "[r]", "paper", "research", "cs.ai", "cs.cl", "cs.lg", "cs.cv",
        "nips", "icml", "iclr", "cvpr", "neurips", "aaai", "acl ",
        "we propose", "we introduce", "we present", "benchmark",
    ]):
        return "paper"

    # Know-how / Tutorial
    if any(x in title_lower for x in [
        "how to", "how i", "tutorial", "guide", "tip", "trick", "howto",
        "step by step", "walkthrough", "lesson", "learned",
        "my experience", "i built", "i trained", "i made",
        "best practice", "production", "deploy",
    ]):
        return "knowhow"

    # Use case / Case study
    if any(x in title_lower for x in [
        "use case", "case study", "we built", "we shipped", "we replaced",
        "at scale", "in production", "our stack", "our experience",
        "startup", "company", "enterprise",
    ]):
        return "usecase"

    # Tool / Release
    if any(x in title_lower for x in [
        "release", "launch", "announcing", "introducing",
        "v1", "v2", "v3", "v4", "v0.",
        "open source", "open-source", "library", "framework", "sdk",
        "show hn", "[p]", "cli", "playground",
    ]):
        return "tool"

    # Discussion
    if any(x in title_lower for x in [
        "[d]", "discuss", "opinion", "thought", "debate",
        "ask hn", "ask reddit", "what do you think",
        "is it just me", "anyone else", "hot take",
        "why ", "should we", "will ", "can ",
        "rant", "unpopular opinion",
    ]):
        return "discussion"

    # Subreddit-based hints
    if sub_lower in ["machinelearning"]:
        if title_lower.startswith("[r]"):
            return "paper"
        if title_lower.startswith("[p]"):
            return "tool"
        if title_lower.startswith("[d]"):
            return "discussion"

    return "news"


def fetch_hn_top_ai(limit: int = 30) -> list[dict[str, Any]]:
    """Fetch AI-related stories from Hacker News using Algolia API."""
    print("[HN] Fetching AI stories...")
    articles = []

    url = "https://hn.algolia.com/api/v1/search"
    queries = ["AI", "LLM", "machine learning", "GPT", "Claude", "OpenAI",
               "deep learning", "neural network", "transformer"]

    seen_urls: set[str] = set()

    for query in queries:
        try:
            resp = httpx.get(
                url,
                params={
                    "query": query,
                    "tags": "story",
                    "numericFilters": "points>10",
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

                # Strict AI relevance check
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

                # Reddit AI subreddits are already filtered by topic,
                # but still check for obviously off-topic posts
                if any(bl in title.lower() for bl in BLACKLIST_PATTERNS):
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

    now = datetime.now(timezone.utc).isoformat()
    for a in articles:
        a["collected_at"] = now
        a.setdefault("title_ko", None)
        a.setdefault("summary_ko", None)
        a.setdefault("thumbnail_url", None)
        a.pop("raw_data", None)

    url = f"{SUPABASE_URL}/rest/v1/articles"
    headers = {**HEADERS, "Prefer": "return=minimal,resolution=merge-duplicates"}

    inserted = 0
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
