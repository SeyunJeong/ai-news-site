export interface Article {
  id: string;
  title: string;
  title_ko: string | null;
  summary_ko: string | null;
  content_ko: string | null;
  url: string;
  source: string;
  source_type: "news" | "community" | "paper" | "blog";
  content_type: "news" | "paper" | "knowhow" | "usecase" | "tool" | "discussion";
  score: number;
  social_score: number;
  published_at: string;
  collected_at: string;
  tags: string[];
  author: string | null;
  thumbnail_url: string | null;
}

export type ContentFilter = "all" | Article["content_type"];

export interface FeedResponse {
  articles: Article[];
  total: number;
  page: number;
  per_page: number;
}
