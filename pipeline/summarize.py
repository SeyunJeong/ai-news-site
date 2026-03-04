"""
AI News Pipeline - Korean Summarizer (with article body extraction)
Fetches articles without Korean summaries, scrapes content, generates:
  - title_ko: Korean title
  - summary_ko: 3-4 line summary (for card)
  - content_ko: Full Korean interpretation (for modal)

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

MAX_CONTENT_CHARS = 3000

SYSTEM_PROMPT_FULL = """너는 AI/ML 뉴스 전문 편집자야. 기사 본문을 읽고 아래 3가지를 만들어:

1. title_ko: 한국어 제목 (간결하고 핵심적으로)
2. summary_ko: 카드용 요약 (3-4문장, AI 엔지니어가 훑어보고 가치를 판단할 수 있게)
3. content_ko: 전문 해석 (본문의 전체 맥락과 인사이트를 한국어로 재구성. 핵심 논점, 기술적 디테일, 의미/시사점을 빠뜨리지 않되 불필요한 반복이나 광고성 문구는 제거. 문단 나눠서 읽기 쉽게. 길어도 됨.)

반드시 아래 JSON 형식으로만 응답해:
{"title_ko": "...", "summary_ko": "...", "content_ko": "..."}"""

SYSTEM_PROMPT_TITLE_ONLY = """너는 AI/ML 뉴스 전문 번역가야. 제목만 보고:
1. title_ko: 한국어 제목
2. summary_ko: 한국어 요약 (2문장)
3. content_ko: 제목에서 유추 가능한 배경 설명 (3-4문장)

반드시 아래 JSON 형식으로만 응답해:
{"title_ko": "...", "summary_ko": "...", "content_ko": "..."}"""


def fetch_unsummarized(limit: int = 20) -> list[dict]:
    """Fetch articles without Korean content."""
    url = f"{SUPABASE_URL}/rest/v1/articles"
    params = {
        "select": "id,title,url,source,content_type",
        "or": "(title_ko.is.null,content_ko.is.null)",
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
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            no_fallback=True,
        )
        if not text or len(text) < 100:
            return None
        if len(text) > MAX_CONTENT_CHARS:
            text = text[:MAX_CONTENT_CHARS] + "..."
        return text
    except Exception as e:
        print(f"    [Scrape] Failed: {e}")
        return None


def summarize_article(title: str, url: str, content: str | None) -> dict | None:
    """Generate Korean title, summary, and full content using GPT-4o-mini."""
    if content:
        system = SYSTEM_PROMPT_FULL
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
        "max_tokens": 2000,
    }

    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
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


def update_article(article_id: str, data: dict) -> bool:
    """Update article with Korean fields."""
    url = f"{SUPABASE_URL}/rest/v1/articles"
    params = {"id": f"eq.{article_id}"}
    resp = httpx.patch(url, headers=HEADERS, params=params, json=data, timeout=15)
    return resp.status_code in (200, 204)


def main():
    print("=" * 50)
    print("AI News Summarizer - Korean Translation")
    print("=" * 50)

    articles = fetch_unsummarized(20)
    print(f"[Found] {len(articles)} articles to process\n")

    if not articles:
        print("[Done] All articles already processed.")
        return

    success = 0
    scraped = 0
    for i, article in enumerate(articles):
        print(f"[{i+1}/{len(articles)}] {article['title'][:60]}...")

        content = extract_content(article["url"])
        if content:
            scraped += 1
            print(f"    [Scrape] OK ({len(content)} chars)")
        else:
            print(f"    [Scrape] Failed, using title-only")

        result = summarize_article(article["title"], article["url"], content)
        if result and "title_ko" in result and "summary_ko" in result:
            update_data = {
                "title_ko": result["title_ko"],
                "summary_ko": result["summary_ko"],
                "content_ko": result.get("content_ko", ""),
            }
            if update_article(article["id"], update_data):
                print(f"  -> {result['title_ko']}")
                content_len = len(result.get("content_ko", ""))
                print(f"     content_ko: {content_len} chars")
                success += 1
            else:
                print("  -> DB update failed")
        else:
            print("  -> Summarization failed")

        time.sleep(1)

    print(f"\n[Done] {success}/{len(articles)} processed ({scraped} with full content)")


if __name__ == "__main__":
    main()
