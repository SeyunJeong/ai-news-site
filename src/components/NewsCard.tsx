import { Article } from "@/lib/types";

const SOURCE_COLORS: Record<string, string> = {
  "Hacker News": "bg-orange-500/10 text-orange-600 dark:text-orange-400",
  Reddit: "bg-red-500/10 text-red-600 dark:text-red-400",
  "arXiv": "bg-purple-500/10 text-purple-600 dark:text-purple-400",
  "TechCrunch": "bg-green-500/10 text-green-600 dark:text-green-400",
  "The Verge": "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400",
  X: "bg-zinc-500/10 text-zinc-600 dark:text-zinc-400",
  Bluesky: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  "Dev.to": "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400",
};

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

export default function NewsCard({ article }: { article: Article }) {
  const sourceColor = SOURCE_COLORS[article.source] || "bg-zinc-500/10 text-zinc-600 dark:text-zinc-400";

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block group"
    >
      <article className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:border-blue-300 dark:hover:border-blue-700 transition-all hover:shadow-md">
        {/* Top meta row */}
        <div className="flex items-center gap-2 mb-2 text-xs">
          <span className={`px-2 py-0.5 rounded-full font-medium ${sourceColor}`}>
            {article.source}
          </span>
          <span className="px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400">
            {TYPE_LABELS[article.content_type] || article.content_type}
          </span>
          <span className="text-zinc-400 dark:text-zinc-500 ml-auto">
            {timeAgo(article.published_at)}
          </span>
        </div>

        {/* Title */}
        <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100 group-hover:text-blue-500 transition-colors leading-snug mb-1">
          {article.title_ko || article.title}
        </h2>

        {/* Original title if translated */}
        {article.title_ko && (
          <p className="text-xs text-zinc-400 dark:text-zinc-500 mb-2 line-clamp-1">
            {article.title}
          </p>
        )}

        {/* Summary */}
        {article.summary_ko && (
          <p className="text-sm text-zinc-600 dark:text-zinc-400 line-clamp-2 mb-3 leading-relaxed">
            {article.summary_ko}
          </p>
        )}

        {/* Bottom row */}
        <div className="flex items-center gap-3 text-xs text-zinc-400 dark:text-zinc-500">
          <span className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
            {article.score}
          </span>
          {article.author && <span>{article.author}</span>}
          <span className="ml-auto">{getDomain(article.url)}</span>
        </div>

        {/* Tags */}
        {article.tags && article.tags.length > 0 && (
          <div className="flex gap-1.5 mt-2 flex-wrap">
            {article.tags.slice(0, 4).map((tag) => (
              <span
                key={tag}
                className="text-xs px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </article>
    </a>
  );
}
