import { supabase } from "./supabase";
import { Article, ContentFilter } from "./types";

// Demo data for when Supabase is not connected
const DEMO_ARTICLES: Article[] = [
  {
    id: "demo-1",
    title: "Claude 4 Opus Released with Enhanced Reasoning",
    title_ko: "Claude 4 Opus 출시 — 향상된 추론 능력",
    summary_ko:
      "Anthropic이 Claude 4 Opus를 출시했습니다. 이번 버전은 복잡한 추론, 코드 생성, 멀티스텝 태스크에서 크게 개선되었으며, 새로운 도구 사용 패러다임을 도입했습니다.",
    url: "https://example.com/claude-4",
    source: "Hacker News",
    source_type: "community",
    content_type: "news",
    score: 342,
    social_score: 189,
    published_at: new Date().toISOString(),
    collected_at: new Date().toISOString(),
    tags: ["anthropic", "llm", "claude"],
    author: "dang",
    thumbnail_url: null,
  },
  {
    id: "demo-2",
    title: "Building Production RAG Systems: Lessons from 100+ Deployments",
    title_ko: "프로덕션 RAG 시스템 구축: 100건 이상의 배포에서 얻은 교훈",
    summary_ko:
      "RAG 시스템을 프로덕션에 배포할 때 흔히 겪는 문제와 해결법을 정리했습니다. 청킹 전략, 임베딩 모델 선택, 리랭킹, 하이브리드 검색 등 실전 노하우를 공유합니다.",
    url: "https://example.com/rag-production",
    source: "Reddit",
    source_type: "community",
    content_type: "knowhow",
    score: 156,
    social_score: 78,
    published_at: new Date(Date.now() - 3600000).toISOString(),
    collected_at: new Date().toISOString(),
    tags: ["rag", "production", "embedding"],
    author: "ml_engineer_42",
    thumbnail_url: null,
  },
  {
    id: "demo-3",
    title: "Attention Is All You Need... Again? Mamba-2 Architecture Deep Dive",
    title_ko: "Attention이 전부인가? Mamba-2 아키텍처 심층 분석",
    summary_ko:
      "State Space Model 기반의 Mamba-2 아키텍처가 Transformer와 비교해 어떤 장단점이 있는지 분석합니다. 긴 컨텍스트 처리와 추론 효율성에서 주목할 만한 결과를 보여줍니다.",
    url: "https://example.com/mamba-2",
    source: "Hacker News",
    source_type: "community",
    content_type: "paper",
    score: 89,
    social_score: 45,
    published_at: new Date(Date.now() - 7200000).toISOString(),
    collected_at: new Date().toISOString(),
    tags: ["mamba", "ssm", "transformer", "architecture"],
    author: null,
    thumbnail_url: null,
  },
  {
    id: "demo-4",
    title: "How We Replaced 5 Microservices with a Single AI Agent",
    title_ko: "AI 에이전트 하나로 마이크로서비스 5개를 대체한 방법",
    summary_ko:
      "스타트업에서 고객 지원, 주문 처리, FAQ 응답 등 5개 마이크로서비스를 Claude 기반 에이전트 하나로 통합한 사례입니다. 비용 70% 절감, 응답 시간 3배 개선을 달성했습니다.",
    url: "https://example.com/agent-microservices",
    source: "Reddit",
    source_type: "community",
    content_type: "usecase",
    score: 234,
    social_score: 112,
    published_at: new Date(Date.now() - 10800000).toISOString(),
    collected_at: new Date().toISOString(),
    tags: ["agent", "microservices", "claude", "startup"],
    author: "startup_cto",
    thumbnail_url: null,
  },
  {
    id: "demo-5",
    title: "Introducing MCP Toolkit: Open-Source Model Context Protocol SDK",
    title_ko: "MCP Toolkit 출시: 오픈소스 Model Context Protocol SDK",
    summary_ko:
      "MCP(Model Context Protocol)를 쉽게 구현할 수 있는 오픈소스 SDK가 출시되었습니다. Python/TypeScript 지원, 10줄 코드로 커스텀 MCP 서버를 만들 수 있습니다.",
    url: "https://example.com/mcp-toolkit",
    source: "Hacker News",
    source_type: "community",
    content_type: "tool",
    score: 178,
    social_score: 67,
    published_at: new Date(Date.now() - 14400000).toISOString(),
    collected_at: new Date().toISOString(),
    tags: ["mcp", "sdk", "opensource", "tool"],
    author: "dev_tools",
    thumbnail_url: null,
  },
  {
    id: "demo-6",
    title: "Is AGI Really 2-3 Years Away? A Technical Perspective",
    title_ko: "AGI가 정말 2~3년 안에 올까? 기술적 관점에서의 분석",
    summary_ko:
      "최근 AGI 타임라인 예측이 점점 앞당겨지고 있습니다. 현재 기술의 한계, 스케일링 법칙의 벽, 그리고 새로운 아키텍처 접근법을 통해 현실적인 타임라인을 논의합니다.",
    url: "https://example.com/agi-timeline",
    source: "Reddit",
    source_type: "community",
    content_type: "discussion",
    score: 412,
    social_score: 298,
    published_at: new Date(Date.now() - 18000000).toISOString(),
    collected_at: new Date().toISOString(),
    tags: ["agi", "scaling", "discussion"],
    author: "ai_researcher",
    thumbnail_url: null,
  },
];

export async function getArticles(
  filter: ContentFilter = "all",
  page: number = 1,
  perPage: number = 30
): Promise<{ articles: Article[]; total: number }> {
  // If Supabase is not connected, return demo data
  if (!supabase) {
    const filtered =
      filter === "all"
        ? DEMO_ARTICLES
        : DEMO_ARTICLES.filter((a) => a.content_type === filter);
    return { articles: filtered, total: filtered.length };
  }

  let query = supabase
    .from("articles")
    .select("*", { count: "exact" })
    .order("published_at", { ascending: false })
    .range((page - 1) * perPage, page * perPage - 1);

  if (filter !== "all") {
    query = query.eq("content_type", filter);
  }

  const { data, count, error } = await query;

  if (error) {
    console.error("Error fetching articles:", error);
    return { articles: DEMO_ARTICLES, total: DEMO_ARTICLES.length };
  }

  return {
    articles: (data as Article[]) || [],
    total: count || 0,
  };
}
