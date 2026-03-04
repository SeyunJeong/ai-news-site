"use client";

import { useState, useEffect } from "react";

export default function Header() {
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem("theme");
    const isDark = saved ? saved === "dark" : true;
    setDarkMode(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  const toggleTheme = () => {
    const next = !darkMode;
    setDarkMode(next);
    localStorage.setItem("theme", next ? "dark" : "light");
    document.documentElement.classList.toggle("dark", next);
  };

  return (
    <>
      <div className="greek-border" />
      <header className="sticky top-0 z-50 border-b border-[var(--card-border)] bg-[var(--card-bg)]/80 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-[var(--foreground)]">
              <span className="text-[var(--accent)]">Morgen</span>AI
            </h1>
            <span className="hidden sm:inline text-xs text-[var(--muted)]">
              AI 엔지니어를 위한 아고라
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-[var(--accent-soft)] text-[var(--muted)] transition-colors"
              aria-label="테마 전환"
            >
              {darkMode ? (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>
    </>
  );
}
