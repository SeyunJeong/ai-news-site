"""
AI News Pipeline - Korean Summarizer (with article body extraction)
Fetches articles without Korean summaries, scrapes content, summarizes via GPT-4o-mini.

Usage:
  pip install -r requirements.txt
  python summarize.py
"""

import os
import json
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

try:
    import trafilatura
except ImportError:
    trafilatura = None
    print("[Warn] trafilatura not installed, falling back to title-only summary")

env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    print("[Skip] OPENAI_API_KEY not set. Skipping summarization.")
    exit(0)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# Max chars to send to LLM (≈750 tokens) — keeps cost low
MAX_CONTENT_CHARS = 3000

SYSTEM_PROMPT = """너는 AI/ML 뉴스 전문 편집자야. 기사 본문을 읽고:
1. 한국어 제목 (자연스럽고 간결하게, 핵심을 살려서)
2. 한국어 요약 (3-4문장, AI 엔지니어가 읽고 핵심 내용과 의미를 파악할 수 있게)

반드시 아래 JSON 형식으로만 응답해:
{"title_ko": "한국어 제목", "summary_ko": "한국어 요약 3-4문장"}"""

SYSTEM_PROMPT_TITLE_ONLY = """너는 AI/ML 뉴스 전문 번역가야. 제목만 보고:
1. 한국어 제목
2. 한국어 요약 (2문장, 제목에서 추론 가능한 내용)

반드시 아래 JSON 형식으로만 응답해:
{"title_ko": "한국어 제목", "summary_ko": "한국어 요약"}"""


def fetch_unsummarized(limit: int = 20) -> list[dict]:
    """Fetch articles that don't have Korean summaries yet."""
    url = f"{SUPABASE_URL}/rest/v1/articles"
    params = {
        "select": "id,title,url,source,content_type",
        "title_ko": "is.null",
        "order": "published_at.desc",
        "limit": str(limit),
    }
    resp = httpx.get(url, headers=HEADERS, params=params, timeout=15)
    if resp.status_code == 200:
        return resp.json()
    print(f"  [DB] Error fetching: {resp.status_code} - {resp.text[:200]}")
    return []


def extract_content(url: str) -> str | None:
    """Scrape article URL and extract main text content."""
    if not trafilatura:
        return None

    try:
        # Download with timeout
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None

        # Extract main content (no comments, no boilerplate)
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            no_fallback=True,
        )

        if not text or len(text) < 100:
            return None

        # Truncate to save tokens
        if len(text) > MAX_CONTENT_CHARS:
            text = text[:MAX_CONTENT_CHARS] + "..."

        return text
    except Exception as e:
        print(f"    [Scrape] Failed: {e}")
        return None


def summarize_article(title: str, url: str, content: str | None) -> dict | None:
    """Generate Korean title and summary using GPT-4o-mini."""
    if content:
        system = SYSTEM_PROMPT
        user_msg = f"제목: {title}\n\n본문:\n{content}"
    else:
        system = SYSTEM_PROMPT_TITLE_ONLY
        user_msg = f"제목: {title}\nURL: {url}"

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.3,
        "max_tokens": 400,
    }

    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        if resp.status_code != 200:
            print(f"  [OpenAI] Error: {resp.status_code} - {resp.text[:200]}")
            return None

        text = resp.json()["choices"][0]["message"]["content"]
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        return json.loads(text)
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"  [OpenAI] Parse error: {e}")
        return None


def update_article(article_id: str, title_ko: str, summary_ko: str) -> bool:
    """Update article with Korean title and summary."""
    url = f"{SUPABASE_URL}/rest/v1/articles"
    params = {"id": f"eq.{article_id}"}
    data = {"title_ko": title_ko, "summary_ko": summary_ko}

    resp = httpx.patch(url, headers=HEADERS, params=params, json=data, timeout=15)
    return resp.status_code in (200, 204)


def main():
    print("=" * 50)
    print("AI News Summarizer - Korean Translation")
    print("=" * 50)

    articles = fetch_unsummarized(20)
    print(f"[Found] {len(articles)} articles without Korean summary\n")

    if not articles:
        print("[Done] All articles already summarized.")
        return

    success = 0
    scraped = 0
    for i, article in enumerate(articles):
        print(f"[{i+1}/{len(articles)}] {article['title'][:60]}...")

        # Try to scrape article content
        content = extract_content(article["url"])
        if content:
            scraped += 1
            print(f"    [Scrape] OK ({len(content)} chars)")
        else:
            print(f"    [Scrape] Failed, using title-only")

        result = summarize_article(article["title"], article["url"], content)
        if result and "title_ko" in result and "summary_ko" in result:
            if update_article(article["id"], result["title_ko"], result["summary_ko"]):
                print(f"  -> {result['title_ko']}")
                success += 1
            else:
                print("  -> DB update failed")
        else:
            print("  -> Summarization failed")

        time.sleep(1)

    print(f"\n[Done] {success}/{len(articles)} summarized ({scraped} with full content)")


if __name__ == "__main__":
    main()
