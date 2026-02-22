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
  });

  return (
    <div className="min-h-screen">
      <Header />
      <main className="max-w-3xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h2 className="text-sm text-zinc-500 dark:text-zinc-400 mb-1">
            {today}
          </h2>
          <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            Today&apos;s AI News
          </p>
        </div>
        <NewsFeed initialArticles={articles} total={total} />
      </main>
      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-6 text-center text-xs text-zinc-400 dark:text-zinc-500">
        <p>AI News &mdash; Curated daily for AI engineers</p>
      </footer>
    </div>
  );
}
