-- AI News Community - Supabase Schema
-- Run this in Supabase SQL Editor

-- Articles table
CREATE TABLE IF NOT EXISTS articles (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  title_ko TEXT,
  summary_ko TEXT,
  url TEXT NOT NULL UNIQUE,
  source TEXT NOT NULL,
  source_type TEXT NOT NULL DEFAULT 'news',
  content_type TEXT NOT NULL DEFAULT 'news',
  score INTEGER DEFAULT 0,
  social_score INTEGER DEFAULT 0,
  published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  tags TEXT[] DEFAULT '{}',
  author TEXT,
  thumbnail_url TEXT,
  raw_data JSONB,
  is_duplicate BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_content_type ON articles(content_type);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_score ON articles(score DESC);
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);

-- Enable Row Level Security
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;

-- Public read access (anyone can read articles)
CREATE POLICY "Public read access" ON articles
  FOR SELECT USING (true);

-- Service role can insert/update (for pipeline)
CREATE POLICY "Service role insert" ON articles
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role update" ON articles
  FOR UPDATE USING (true);

-- Optional: sources metadata table
CREATE TABLE IF NOT EXISTS sources (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  source_type TEXT NOT NULL,
  url TEXT,
  reliability_score FLOAT DEFAULT 0.8,
  is_active BOOLEAN DEFAULT TRUE,
  last_fetched_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed sources
INSERT INTO sources (name, source_type, url, reliability_score) VALUES
  ('Hacker News', 'community', 'https://news.ycombinator.com', 0.9),
  ('Reddit r/MachineLearning', 'community', 'https://reddit.com/r/MachineLearning', 0.85),
  ('Reddit r/artificial', 'community', 'https://reddit.com/r/artificial', 0.8),
  ('Reddit r/LocalLLaMA', 'community', 'https://reddit.com/r/LocalLLaMA', 0.85),
  ('arXiv cs.AI', 'paper', 'https://arxiv.org/list/cs.AI/recent', 0.95),
  ('TechCrunch AI', 'news', 'https://techcrunch.com/category/artificial-intelligence/', 0.85),
  ('The Verge AI', 'news', 'https://theverge.com/ai-artificial-intelligence', 0.8),
  ('VentureBeat AI', 'news', 'https://venturebeat.com/ai/', 0.8),
  ('Dev.to #ai', 'blog', 'https://dev.to/t/ai', 0.75)
ON CONFLICT (name) DO NOTHING;
