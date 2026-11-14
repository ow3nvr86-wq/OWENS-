-- Trend Scout initial schema.
-- Portable SQL: timestamps are ISO-8601 UTC strings ("2026-10-19T20:27:48.707000Z"),
-- JSON is stored as TEXT. For PostgreSQL, change "INTEGER PRIMARY KEY" to
-- "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY" and TEXT JSON columns to JSONB.

CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,                 -- discovery | publish | metrics | rewrite
    status TEXT NOT NULL,               -- running | succeeded | failed | skipped
    trigger TEXT NOT NULL,              -- schedule | manual | dashboard | api | cli
    dry_run INTEGER NOT NULL DEFAULT 1,
    offline INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    stats_json TEXT NOT NULL DEFAULT '{}',
    error TEXT
);

CREATE TABLE trends (
    id TEXT PRIMARY KEY,                -- stable hash of source + external id
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    url TEXT,
    summary TEXT NOT NULL DEFAULT '',
    keywords_json TEXT NOT NULL DEFAULT '[]',
    metrics_json TEXT NOT NULL DEFAULT '{}',
    confidence REAL NOT NULL DEFAULT 0.5,
    raw_json TEXT NOT NULL DEFAULT '{}',
    published_at TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_run_id INTEGER REFERENCES runs(id)
);
CREATE INDEX idx_trends_last_seen ON trends(last_seen_at);

CREATE TABLE trend_observations (
    id INTEGER PRIMARY KEY,
    trend_id TEXT NOT NULL REFERENCES trends(id),
    run_id INTEGER REFERENCES runs(id),
    observed_at TEXT NOT NULL,
    metric REAL,
    metrics_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_obs_trend ON trend_observations(trend_id, observed_at);

CREATE TABLE clusters (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    cluster_key TEXT NOT NULL,
    title TEXT NOT NULL,
    keywords_json TEXT NOT NULL DEFAULT '[]',
    trend_ids_json TEXT NOT NULL DEFAULT '[]',
    sources_json TEXT NOT NULL DEFAULT '[]',
    score REAL NOT NULL DEFAULT 0,
    score_breakdown_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL,               -- candidate | selected | rejected
    rejection_reason TEXT,
    safety_json TEXT NOT NULL DEFAULT '{}',
    classification_json TEXT NOT NULL DEFAULT '{}',
    category TEXT,
    needs_human_review INTEGER NOT NULL DEFAULT 0,
    covered_topic_id INTEGER REFERENCES covered_topics(id),
    created_at TEXT NOT NULL
);
CREATE INDEX idx_clusters_run ON clusters(run_id);

CREATE TABLE covered_topics (
    id INTEGER PRIMARY KEY,
    cluster_key TEXT NOT NULL,
    title TEXT NOT NULL,
    keywords_json TEXT NOT NULL DEFAULT '[]',
    cluster_id INTEGER REFERENCES clusters(id),
    first_covered_at TEXT NOT NULL,
    last_covered_at TEXT NOT NULL,
    update_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE research (
    id INTEGER PRIMARY KEY,
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    cache_key TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    data_json TEXT NOT NULL,
    confidence TEXT NOT NULL,           -- high | medium | low
    sufficient INTEGER NOT NULL,
    generated_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE drafts (
    id INTEGER PRIMARY KEY,
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    research_id INTEGER NOT NULL REFERENCES research(id),
    platform TEXT NOT NULL,
    status TEXT NOT NULL,               -- drafting | pending_approval | approved | rejected | rejected_by_human | published
    post_text TEXT NOT NULL,
    structure_json TEXT NOT NULL DEFAULT '{}',
    media_brief TEXT NOT NULL DEFAULT '',
    source_urls_json TEXT NOT NULL DEFAULT '[]',
    hashtags_json TEXT NOT NULL DEFAULT '[]',
    claims_json TEXT NOT NULL DEFAULT '[]',
    rationale TEXT NOT NULL DEFAULT '',
    char_count INTEGER NOT NULL DEFAULT 0,
    char_limit INTEGER NOT NULL DEFAULT 0,
    revision_count INTEGER NOT NULL DEFAULT 0,
    review_decision TEXT,
    needs_human_review INTEGER NOT NULL DEFAULT 0,
    human_edited INTEGER NOT NULL DEFAULT 0,
    generated_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX idx_drafts_status ON drafts(status, platform);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    draft_id INTEGER NOT NULL REFERENCES drafts(id),
    attempt INTEGER NOT NULL,
    decision TEXT NOT NULL,             -- APPROVED_FOR_HUMAN_REVIEW | NEEDS_REVISION | REJECTED
    reasons_json TEXT NOT NULL DEFAULT '[]',
    instructions TEXT NOT NULL DEFAULT '',
    checks_json TEXT NOT NULL DEFAULT '{}',
    reviewer TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE approvals (
    id INTEGER PRIMARY KEY,
    draft_id INTEGER NOT NULL REFERENCES drafts(id),
    action TEXT NOT NULL,               -- approve | reject | edit | rewrite | schedule | auto_approve
    actor TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE publish_jobs (
    id INTEGER PRIMARY KEY,
    draft_id INTEGER NOT NULL UNIQUE REFERENCES drafts(id),
    platform TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    client_ref TEXT NOT NULL,           -- platform-side idempotency handle (e.g. Bluesky record key)
    platform_ref TEXT,                  -- id the platform returned for an unfinished publish (e.g. TikTok publish_id)
    status TEXT NOT NULL,               -- queued | publishing | published | failed | uncertain | held | cancelled
    scheduled_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    claimed_by TEXT,
    lease_expires_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX idx_jobs_status ON publish_jobs(status, scheduled_at);

CREATE TABLE published_posts (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL UNIQUE REFERENCES publish_jobs(id),
    draft_id INTEGER NOT NULL REFERENCES drafts(id),
    platform TEXT NOT NULL,
    platform_post_id TEXT,
    url TEXT,
    post_text TEXT NOT NULL,
    category TEXT,
    source TEXT,
    dry_run INTEGER NOT NULL,
    published_at TEXT NOT NULL
);

CREATE TABLE platform_accounts (
    platform TEXT PRIMARY KEY,
    handle TEXT,
    status TEXT NOT NULL,               -- unconfigured | configured | verified | error
    detail TEXT NOT NULL DEFAULT '',
    last_checked_at TEXT
);

CREATE TABLE metrics (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES published_posts(id),
    collected_at TEXT NOT NULL,
    post_age_minutes INTEGER NOT NULL,
    age_bucket TEXT NOT NULL,           -- 1h | 24h | 72h | 7d | adhoc
    impressions INTEGER,
    likes INTEGER,
    comments INTEGER,
    reposts INTEGER,
    clicks INTEGER,
    engagement_rate REAL,
    raw_json TEXT NOT NULL DEFAULT '{}'
);
CREATE UNIQUE INDEX idx_metrics_bucket ON metrics(post_id, age_bucket);

CREATE TABLE scoring_adjustments (
    id INTEGER PRIMARY KEY,
    dimension TEXT NOT NULL,            -- category | source | hour | platform
    key TEXT NOT NULL,
    multiplier REAL NOT NULL,
    previous REAL,
    sample_size INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_adj_key ON scoring_adjustments(dimension, key, created_at);

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL
);

CREATE TABLE locks (
    name TEXT PRIMARY KEY,
    holder TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT,
    detail_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_audit_ts ON audit_log(ts);

CREATE TABLE error_log (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    run_id INTEGER,
    component TEXT NOT NULL,
    message TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_errors_ts ON error_log(ts);

CREATE TABLE llm_usage (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    run_id INTEGER,
    task TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens INTEGER NOT NULL DEFAULT 0,
    web_searches INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0
);
CREATE INDEX idx_usage_ts ON llm_usage(ts);
