import Header from "@/components/Header";
import NewsFeed from "@/components/NewsFeed";
import { getArticles } from "@/lib/articles";

// ISR: revalidate every 5 minutes
export const revalidate = 300;

export default async function Home() {
  const { articles, total } = await getArticles("all", 1, 50);

  const today = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
    timeZone: "Asia/Seoul",
  });

  return (
    <div className="min-h-screen relative">
      {/* Stone grain texture overlay */}
      <div className="agora-bg" />

      <div className="relative z-10">
        <Header />
        <main className="max-w-3xl mx-auto px-4 py-6">
          <div className="mb-6">
            <h2 className="text-sm text-[var(--muted)] mb-1">
              {today}
            </h2>
            <p className="text-2xl font-bold text-[var(--foreground)]">
              Today&apos;s <span className="text-[var(--accent)]">Discourse</span>
            </p>
          </div>
          <NewsFeed initialArticles={articles} total={total} />
        </main>
        <footer className="border-t border-[var(--card-border)] py-6 text-center text-xs text-[var(--muted)]">
          <p>MorgenAI &mdash; Where AI engineers gather to discuss</p>
        </footer>
      </div>
    </div>
  );
}
