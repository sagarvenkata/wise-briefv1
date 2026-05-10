-- Drop existing tables cleanly
drop table if exists posts cascade;
drop table if exists theme_accounts cascade;
drop table if exists themes cascade;

-- 1. Themes
create table themes (
  id            bigint generated always as identity primary key,
  slot          int unique not null,
  name          text not null,
  emoji         text not null,
  prompt        text not null default '',
  post_hour_utc int not null,
  post_min_utc  int not null default 30,
  active        boolean not null default true
);

-- 2. Accounts per theme
create table theme_accounts (
  id              bigint generated always as identity primary key,
  theme_id        bigint not null references themes(id) on delete cascade,
  twitter_handle  text not null,
  unique(theme_id, twitter_handle)
);

-- 3. Post log
create table posts (
  id                bigint generated always as identity primary key,
  theme_id          bigint not null references themes(id),
  source_tweet_url  text,
  source_tweet_text text,
  source_likes      int,
  source_views      int,
  tweet_id          text,
  run_date          date not null,
  status            text not null,
  error_message     text,
  created_at        timestamptz default now()
);

-- Seed: 12 themes (IST = UTC+5:30)
insert into themes (slot, name, emoji, post_hour_utc, post_min_utc) values
  (1,  'AI & Tech Disruption',        '🤖', 0,  30),
  (2,  'Business Model Decoded',       '💡', 2,  30),
  (3,  'Sports',                       '🏆', 4,  30),
  (4,  'Movies & Pop Culture',         '🎬', 6,  30),
  (5,  'History & Science',            '🏛️', 8,  30),
  (6,  'War & Geopolitics',            '⚔️', 10, 30),
  (7,  'Human Psychology & Behaviour', '🧠', 12, 30),
  (8,  'Stock Market & Wealth',        '📈', 14, 30),
  (9,  'Climate & Energy',             '🌱', 16, 30),
  (10, 'Consumer & Corporate',         '😤', 18, 30),
  (11, 'Cities & Infrastructure',      '🏙️', 20, 30),
  (12, 'Food & Health',                '🍔', 22, 30);
