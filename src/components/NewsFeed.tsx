"use client";

import { useState } from "react";
import { Article, ContentFilter } from "@/lib/types";
import FilterTabs from "./FilterTabs";
import NewsCard from "./NewsCard";
import ArticleModal from "./ArticleModal";

interface NewsFeedProps {
  initialArticles: Article[];
  total: number;
}

export default function NewsFeed({ initialArticles, total }: NewsFeedProps) {
  const [filter, setFilter] = useState<ContentFilter>("all");
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

  const filtered =
    filter === "all"
      ? initialArticles
      : initialArticles.filter((a) => a.content_type === filter);

  // Count per type
  const counts: Record<string, number> = { all: initialArticles.length };
  for (const a of initialArticles) {
    counts[a.content_type] = (counts[a.content_type] || 0) + 1;
  }

  return (
    <div>
      <div className="mb-4">
        <FilterTabs active={filter} onChange={setFilter} counts={counts} />
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-20 text-zinc-400 dark:text-zinc-500">
          <p className="text-lg mb-2">아직 뉴스가 없습니다</p>
          <p className="text-sm">파이프라인이 실행되면 여기에 AI 뉴스가 표시됩니다.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {filtered.map((article) => (
            <NewsCard
              key={article.id}
              article={article}
              onClick={setSelectedArticle}
            />
          ))}
        </div>
      )}

      {filtered.length > 0 && (
        <div className="text-center py-6 text-sm text-zinc-400 dark:text-zinc-500">
          {filtered.length}개의 뉴스 표시 중 (전체 {total}개)
        </div>
      )}

      {selectedArticle && (
        <ArticleModal
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
        />
      )}
    </div>
  );
}
