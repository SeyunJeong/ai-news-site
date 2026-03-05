"use client";

import { Article } from "@/lib/types";
import { useEffect, useRef, useState, useCallback } from "react";

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

interface ArticleModalProps {
  article: Article;
  articles: Article[];
  onClose: () => void;
  onNavigate: (article: Article) => void;
}

export default function ArticleModal({
  article,
  articles,
  onClose,
  onNavigate,
}: ArticleModalProps) {
  const [dragY, setDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef<{ y: number; time: number } | null>(null);
  const swipeStart = useRef<{ x: number; y: number } | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const currentIndex = articles.findIndex((a) => a.id === article.id);
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex < articles.length - 1;

  // Reset scroll on article change
  useEffect(() => {
    contentRef.current?.scrollTo(0, 0);
  }, [article.id]);

  // Keyboard: Escape, Arrow keys
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft" && hasPrev) onNavigate(articles[currentIndex - 1]);
      if (e.key === "ArrowRight" && hasNext)
        onNavigate(articles[currentIndex + 1]);
    };
    document.addEventListener("keydown", handler);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
    };
  }, [onClose, onNavigate, articles, currentIndex, hasPrev, hasNext]);

  // ─── Drag handle: swipe down to dismiss ───
  const handleDragStart = useCallback((e: React.TouchEvent) => {
    dragStart.current = { y: e.touches[0].clientY, time: Date.now() };
    setIsDragging(true);
  }, []);

  const handleDragMove = useCallback((e: React.TouchEvent) => {
    if (!dragStart.current) return;
    const dy = e.touches[0].clientY - dragStart.current.y;
    setDragY(Math.max(0, dy));
  }, []);

  const handleDragEnd = useCallback(
    (e: React.TouchEvent) => {
      if (!dragStart.current) return;
      const dy = e.changedTouches[0].clientY - dragStart.current.y;
      const velocity = dy / (Date.now() - dragStart.current.time);

      if (dy > 80 || velocity > 0.3) {
        onClose();
      } else {
        setDragY(0);
      }
      setIsDragging(false);
      dragStart.current = null;
    },
    [onClose]
  );

  // ─── Content: horizontal swipe for prev/next ───
  const handleSwipeStart = useCallback((e: React.TouchEvent) => {
    swipeStart.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
    };
  }, []);

  const handleSwipeEnd = useCallback(
    (e: React.TouchEvent) => {
      if (!swipeStart.current) return;
      const dx = e.changedTouches[0].clientX - swipeStart.current.x;
      const dy = e.changedTouches[0].clientY - swipeStart.current.y;

      if (Math.abs(dx) > 80 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        if (dx > 0 && hasPrev) onNavigate(articles[currentIndex - 1]);
        else if (dx < 0 && hasNext) onNavigate(articles[currentIndex + 1]);
      }
      swipeStart.current = null;
    },
    [hasPrev, hasNext, articles, currentIndex, onNavigate]
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        style={{
          opacity: isDragging ? Math.max(0.2, 1 - dragY / 400) : 1,
          transition: isDragging ? "none" : "opacity 0.3s",
        }}
      />

      {/* Modal */}
      <div
        className="relative w-full sm:max-w-2xl max-h-[92vh] sm:max-h-[85vh] rounded-t-2xl sm:rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] shadow-2xl flex flex-col"
        style={{
          transform: `translateY(${dragY}px)`,
          transition: isDragging ? "none" : "transform 0.3s ease-out",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drag handle — mobile */}
        <div
          className="flex justify-center pt-3 pb-2 cursor-grab active:cursor-grabbing sm:hidden"
          style={{ touchAction: "none" }}
          onTouchStart={handleDragStart}
          onTouchMove={handleDragMove}
          onTouchEnd={handleDragEnd}
        >
          <div className="w-10 h-1.5 rounded-full bg-zinc-300 dark:bg-zinc-600 drag-handle-hint" />
        </div>

        {/* Close button — desktop */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 transition-colors z-10 hidden sm:block"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {/* Scrollable content */}
        <div
          ref={contentRef}
          className="overflow-y-auto flex-1 px-6 pb-6 pt-2 sm:pt-6"
          onTouchStart={handleSwipeStart}
          onTouchEnd={handleSwipeEnd}
        >
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

          {/* Original title + 원문 link */}
          <div className="flex items-start gap-2 mb-5">
            <p className="text-sm text-zinc-400 dark:text-zinc-300 flex-1 line-clamp-2">
              {article.title}
            </p>
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-[var(--accent)] hover:underline whitespace-nowrap flex items-center gap-0.5 shrink-0 mt-0.5"
            >
              원문
              <svg
                className="w-3 h-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
            </a>
          </div>

          {/* Divider */}
          <div className="border-t border-zinc-100 dark:border-zinc-800 mb-5" />

          {/* Full Korean content */}
          {article.content_ko ? (
            <div className="mb-6">
              <h3 className="text-xs font-semibold text-zinc-500 dark:text-zinc-300 uppercase tracking-wider mb-2">
                전문 해석
              </h3>
              <div className="text-[15px] text-zinc-700 dark:text-zinc-300 leading-relaxed space-y-3">
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

          {/* Stats */}
          <div className="flex items-center gap-4 text-sm text-zinc-500 dark:text-zinc-300">
            <span className="flex items-center gap-1.5">
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 15l7-7 7 7"
                />
              </svg>
              {article.score}
            </span>
            <span className="flex items-center gap-1.5">
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              {article.social_score}
            </span>
            {article.author && <span>by {article.author}</span>}
          </div>

          {/* Tags */}
          {article.tags && article.tags.length > 0 && (
            <div className="flex gap-2 mt-4 flex-wrap">
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

          {/* Swipe hint — mobile */}
          {(hasPrev || hasNext) && (
            <div className="text-center text-xs text-[var(--muted)] pt-6 pb-2 sm:hidden">
              ← 스와이프로 이전/다음 뉴스 →
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
