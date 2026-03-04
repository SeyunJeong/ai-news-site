"use client";

import { ContentFilter } from "@/lib/types";

const FILTERS: { key: ContentFilter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "news", label: "News" },
  { key: "paper", label: "Papers" },
  { key: "knowhow", label: "Know-how" },
  { key: "usecase", label: "Use Cases" },
  { key: "tool", label: "Tools" },
  { key: "discussion", label: "Discussion" },
];

interface FilterTabsProps {
  active: ContentFilter;
  onChange: (filter: ContentFilter) => void;
  counts?: Record<string, number>;
}

export default function FilterTabs({ active, onChange, counts }: FilterTabsProps) {
  return (
    <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-hide">
      {FILTERS.map((f) => (
        <button
          key={f.key}
          onClick={() => onChange(f.key)}
          className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
            active === f.key
              ? "bg-[var(--accent)] text-white dark:text-zinc-900"
              : "bg-[var(--accent-soft)] text-[var(--muted)] hover:bg-[var(--accent-soft)] hover:text-[var(--foreground)]"
          }`}
        >
          {f.label}
          {counts && counts[f.key] !== undefined && (
            <span className="ml-1 text-xs opacity-70">{counts[f.key]}</span>
          )}
        </button>
      ))}
    </div>
  );
}
