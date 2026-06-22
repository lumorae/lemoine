-- Lemoine social system — core data model
-- Lives in a dedicated `social` schema so it stays separate from the
-- proposals data already in this project. Apply with:
--   supabase db push   (or the Supabase MCP apply_migration tool)
--
-- NOTE ON SECRETS: API tokens are NOT stored in these tables. They live in
-- Supabase Vault / project secrets and are referenced by name only.

create schema if not exists social;

-- ---------------------------------------------------------------------------
-- Connected accounts (one row per platform identity we publish to)
-- ---------------------------------------------------------------------------
create table if not exists social.accounts (
  id            uuid primary key default gen_random_uuid(),
  platform      text not null check (platform in ('instagram', 'linkedin')),
  display_name  text not null,                 -- e.g. "Lemoine" / "@lemoine"
  external_id   text not null,                 -- IG Business Account ID / LinkedIn Org URN
  token_secret  text not null,                 -- name of the Vault secret holding the token
  is_active     boolean not null default true,
  created_at    timestamptz not null default now(),
  unique (platform, external_id)
);

-- ---------------------------------------------------------------------------
-- Posts (mirrors the Airtable "cockpit"; Airtable is the place you compose,
-- this is the system of record for what actually shipped)
-- ---------------------------------------------------------------------------
create table if not exists social.posts (
  id                 uuid primary key default gen_random_uuid(),
  airtable_record_id text unique,              -- link back to the Airtable row
  caption            text,
  media_url          text,                     -- public URL (Supabase Storage) for IG publishing
  media_type         text default 'image' check (media_type in ('image','carousel','video','text')),
  platforms          text[] not null default '{}',  -- {'instagram','linkedin'}
  scheduled_for      timestamptz,
  status             text not null default 'draft'
                       check (status in ('draft','approved','scheduled','published','failed')),
  published_at       timestamptz,
  error_detail       text,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

-- Per-platform publish result for a post (a post can go to >1 platform)
create table if not exists social.post_targets (
  id               uuid primary key default gen_random_uuid(),
  post_id          uuid not null references social.posts(id) on delete cascade,
  platform         text not null check (platform in ('instagram','linkedin')),
  external_post_id text,                        -- IG media id / LinkedIn URN of the live post
  permalink        text,
  status           text not null default 'pending'
                     check (status in ('pending','published','failed')),
  published_at     timestamptz,
  error_detail     text,
  unique (post_id, platform)
);

-- ---------------------------------------------------------------------------
-- Per-post metrics, captured repeatedly over time (so we see how a post matures)
-- ---------------------------------------------------------------------------
create table if not exists social.post_metrics (
  id               uuid primary key default gen_random_uuid(),
  post_id          uuid not null references social.posts(id) on delete cascade,
  platform         text not null check (platform in ('instagram','linkedin')),
  captured_at      timestamptz not null default now(),
  impressions      bigint,
  reach            bigint,
  likes            bigint,
  comments         bigint,
  shares           bigint,
  saves            bigint,                      -- IG
  profile_visits   bigint,                      -- IG
  follows          bigint,                      -- IG: follows attributed to the post
  video_views      bigint,
  clicks           bigint,                      -- LinkedIn
  engagement_rate  numeric,                     -- computed: engagements / reach
  raw              jsonb                        -- full API payload, for anything we didn't model
);
create index if not exists post_metrics_post_idx on social.post_metrics (post_id, captured_at desc);

-- ---------------------------------------------------------------------------
-- Account-level snapshots (follower growth over time — the "are we growing?" table)
-- ---------------------------------------------------------------------------
create table if not exists social.account_metrics (
  id              uuid primary key default gen_random_uuid(),
  account_id      uuid not null references social.accounts(id) on delete cascade,
  captured_at     timestamptz not null default now(),
  followers       bigint,
  following       bigint,
  reach_28d       bigint,
  profile_visits  bigint,
  raw             jsonb
);
create index if not exists account_metrics_acct_idx on social.account_metrics (account_id, captured_at desc);

-- ---------------------------------------------------------------------------
-- My analysis write-ups (so growth insights are saved, not just chatted)
-- ---------------------------------------------------------------------------
create table if not exists social.insights (
  id           uuid primary key default gen_random_uuid(),
  created_at   timestamptz not null default now(),
  period_start date,
  period_end   date,
  summary      text not null,
  recommendations jsonb        -- structured next-step suggestions
);
