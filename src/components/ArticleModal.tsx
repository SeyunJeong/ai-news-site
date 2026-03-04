"use client";

import { Article } from "@/lib/types";
import { useEffect } from "react";

const TYPE_LABELS: Record<string, string> = {
  news: "News",
  paper: "Paper",
  knowhow: "Know-how",
  usecase: "Use Case",
  tool: "Tool",
  discussion: "Discussion",
};

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diff < 60) return "방금 전";
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}일 전`;
  return date.toLocaleDateString("ko-KR");
}

function getDomain(url: string): string {
  try {
    return new URL(url).hostname.replace("www.", "");
  } catch {
    return "";
  }
}

interface ArticleModalProps {
  article: Article;
  onClose: () => void;
}

export default function ArticleModal({ article, onClose }: ArticleModalProps) {
  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 transition-colors z-10"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="p-6">
          {/* Meta row */}
          <div className="flex items-center gap-2 mb-4 text-xs">
            <span className="px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 font-medium">
              {article.source}
            </span>
            <span className="px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-300">
              {TYPE_LABELS[article.content_type] || article.content_type}
            </span>
            <span className="text-zinc-400 dark:text-zinc-300 ml-auto">
              {timeAgo(article.published_at)}
            </span>
          </div>

          {/* Korean title */}
          <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 leading-snug mb-2">
            {article.title_ko || article.title}
          </h2>

          {/* Original title */}
          <p className="text-sm text-zinc-400 dark:text-zinc-300 mb-5">
            {article.title}
          </p>

          {/* Divider */}
          <div className="border-t border-zinc-100 dark:border-zinc-800 mb-5" />

          {/* Korean content (full interpretation) */}
          {article.content_ko ? (
            <div className="mb-6">
              <h3 className="text-xs font-semibold text-zinc-500 dark:text-zinc-300 uppercase tracking-wider mb-2">
                전문 해석
              </h3>
              <div className="text-[15px] text-zinc-700 dark:text-zinc-300 leading-relaxed whitespace-pre-line space-y-3">
                {article.content_ko.split("\n\n").map((paragraph, i) => (
                  <p key={i}>{paragraph}</p>
                ))}
              </div>
            </div>
          ) : article.summary_ko ? (
            <div className="mb-6">
              <h3 className="text-xs font-semibold text-zinc-500 dark:text-zinc-300 uppercase tracking-wider mb-2">
                요약
              </h3>
              <p className="text-base text-zinc-700 dark:text-zinc-300 leading-relaxed">
                {article.summary_ko}
              </p>
            </div>
          ) : (
            <div className="mb-6 text-sm text-zinc-400 dark:text-zinc-300">
              한국어 해석이 아직 생성되지 않았습니다.
            </div>
          )}

          {/* Stats row */}
          <div className="flex items-center gap-4 mb-6 text-sm text-zinc-500 dark:text-zinc-300">
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
              {article.score} points
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              {article.social_score} comments
            </span>
            {article.author && (
              <span className="flex items-center gap-1.5">
                by {article.author}
              </span>
            )}
            <span className="ml-auto text-zinc-400">
              {getDomain(article.url)}
            </span>
          </div>

          {/* Tags */}
          {article.tags && article.tags.length > 0 && (
            <div className="flex gap-2 mb-6 flex-wrap">
              {article.tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-1 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-300"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}

          {/* Action button */}
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-[var(--accent)] hover:opacity-90 text-white dark:text-zinc-900 font-medium transition-colors"
          >
            원문 보기
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  );
}
