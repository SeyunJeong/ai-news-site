"""Remove non-AI articles from DB and re-classify content types."""
import os
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

AI_STRONG = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "claude", "gemini", "openai",
    "anthropic", "transformer", "neural network", "diffusion",
    "chatgpt", "copilot", "rag", "fine-tuning", "embedding",
    "langchain", "llamaindex", "hugging face", "ollama",
    "deepseek", "mistral", "llama", "qwen", "phi-",
    "generative ai", "nlp", "natural language",
    "reinforcement learning", "rlhf", "grpo",
    "inference", "quantization", "lora", "benchmark",
    "multimodal", "arxiv", "cs.ai", "cs.cl", "cs.lg", "cs.cv",
    "agentic", "mcp", "swe-bench", "context window",
    "foundation model", "gen ai", "text-to-",
    "computer vision", "token",
]

BLACKLIST = [
    "air con", "aircon", "air purifier", "paper airplane", "paper plane",
    "airpod", "airfoil", "airline", "airport", "amazon prime air",
    "airmash", "ikea", "recipe", "cooking", "weather", "flight",
]


def classify(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ["arxiv", "[r]", "paper", "research", "cs.ai", "cs.cl", "cs.lg", "cs.cv",
                              "nips", "icml", "iclr", "cvpr", "neurips", "aaai",
                              "we propose", "we introduce", "benchmark"]):
        return "paper"
    if any(x in t for x in ["how to", "how i", "tutorial", "guide", "tip", "trick",
                              "step by step", "lesson", "learned", "my experience",
                              "i built", "i trained", "i made", "best practice", "production", "deploy"]):
        return "knowhow"
    if any(x in t for x in ["use case", "case study", "we built", "we shipped", "we replaced",
                              "at scale", "in production", "our stack", "startup", "company"]):
        return "usecase"
    if any(x in t for x in ["release", "launch", "announcing", "introducing",
                              "v1", "v2", "v3", "v0.", "open source", "open-source",
                              "library", "framework", "sdk", "show hn", "[p]", "cli"]):
        return "tool"
    if any(x in t for x in ["[d]", "discuss", "opinion", "thought", "debate",
                              "ask hn", "anyone else", "hot take", "why ", "should we", "rant"]):
        return "discussion"
    return "news"


resp = httpx.get(
    f"{SUPABASE_URL}/rest/v1/articles",
    headers=HEADERS,
    params={"select": "id,title,content_type", "limit": "200"},
    timeout=15,
)
articles = resp.json()
print(f"Total articles in DB: {len(articles)}")

to_delete = []
to_reclassify = []

for a in articles:
    t = a["title"].lower()

    # Blacklist
    if any(bl in t for bl in BLACKLIST):
        to_delete.append(a)
        continue

    # Not AI related
    has_strong = any(kw in t for kw in AI_STRONG)
    weak = ["agent", "model", "training", "data", "tool", "api"]
    weak_count = sum(1 for w in weak if w in t)

    if not has_strong and weak_count < 2:
        to_delete.append(a)
        continue

    # Reclassify
    new_type = classify(a["title"])
    if new_type != a["content_type"]:
        to_reclassify.append((a, new_type))

print(f"\n--- DELETE ({len(to_delete)} articles) ---")
for a in to_delete:
    print(f"  X {a['title'][:80]}")
    httpx.delete(f"{SUPABASE_URL}/rest/v1/articles", headers=HEADERS,
                 params={"id": f"eq.{a['id']}"}, timeout=10)

print(f"\n--- RECLASSIFY ({len(to_reclassify)} articles) ---")
for a, new_type in to_reclassify:
    print(f"  {a['content_type']:>10} -> {new_type:<10} | {a['title'][:60]}")
    httpx.patch(f"{SUPABASE_URL}/rest/v1/articles", headers=HEADERS,
                params={"id": f"eq.{a['id']}"}, json={"content_type": new_type}, timeout=10)

print(f"\nDone. Deleted {len(to_delete)}, reclassified {len(to_reclassify)}")
