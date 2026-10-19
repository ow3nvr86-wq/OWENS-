# Trend Scout

Trend Scout finds what is trending, decides which topics fit your account, researches them from their
sources, writes posts for each platform, has an independent reviewer check every draft, and publishes
only what you approve. It starts with Bluesky; X, Threads, Instagram, LinkedIn and TikTok adapters are
included for when you have access to their APIs.

```
collectors ──► dedupe + cluster ──► score 0-100 ──► safety filter ──► classify (1 cheap batched call)
 HN, RSS,          (database:           (per-source      (keyword rules     relevance, originality,
 Google Trends,     covered topics)      percentiles)     + policy)          safety flags
 Reddit, YouTube,                                                                │
 X (optional)                                                                    ▼
 published ◄── publish queue ◄── YOU APPROVE ◄── reviewer ◄── writers ◄── research
 + metrics      (lock, claim,     (dashboard)     (checks +    (one per     (fetch sources,
 + learning      idempotency)                      model)       platform,    verify each claim)
                                                                parallel)
```

## Status: what has and has not been verified

Be clear about this before you rely on it.

| Part | How it was verified |
|---|---|
| Hacker News, RSS/Atom feeds, Google Trends collectors | Live: collected real trends (152 items in one run) |
| Article fetching and text extraction | Live, on BBC, Ars Technica and The Verge pages |
| Bluesky publisher | Live: reached bsky.social, and an invalid login was correctly reported. **A real post has not been made**, because no account credentials were available. Posting, threads, reconciliation and metrics were tested against a local fake of the AT Protocol API |
| Claude calls (classify, research, write, review, web search) | **Not run against the real API**: no API key was available. Request shape, refusal handling, usage/cost tracking and the budget guard were tested through the Anthropic SDK with a mocked HTTP layer |
| Reddit, YouTube, X trends collectors | Parsing tested on recorded-format fixtures; not run live (needs your keys) |
| X, Threads, Instagram, LinkedIn, TikTok publishers | Tested against fakes of each API. X's OAuth 1.0a signing matches X's published test vector. None has been run against the real platform |
| Workflow, approval rules, idempotency, scheduling, analytics, dashboard | 107 automated tests, plus a full offline run from discovery to simulated publication |

Every optional integration shows as *unconfigured* on the dashboard until its credentials are present, and
as *verified* only after `python -m app doctor` has successfully authenticated against the real service.

## Quick start (five minutes, no API keys)

Requires Python 3.12+ (developed on 3.13).

```bash
cd trendscout
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Dashboard login: put a password and a session secret in .env
python -m app hash-password          # paste the output into DASHBOARD_PASSWORD_HASH
python -c "import secrets; print(secrets.token_urlsafe(48))"   # paste into SESSION_SECRET

python -m app discover --offline     # sample trends + simulated AI: produces drafts
python -m app serve --offline        # open http://127.0.0.1:8000
```

Offline mode uses the sample data in `fixtures/` (fictional companies on example.com) and a rule-based
stand-in for the model, so you can try the whole workflow: browse trends and rejection reasons, read the
research, approve or edit drafts, and watch them "publish" in dry-run mode. Offline mode can never publish.

## Going live

1. **Describe your account** in `config/trendscout.toml`: name, niche, audience, voice, categories,
   keywords, topics to avoid, platforms, schedule and time zone. Run `python -m app check-config`.
2. **Add an Anthropic API key** (`ANTHROPIC_API_KEY` in `.env`). Without it, discovery still collects and ranks
   trends, but nothing is researched or written.
3. **Run discovery for real**: `python -m app discover`, then review the results in the dashboard (`python -m app serve`).
4. **Connect Bluesky** (below), then run `python -m app doctor` to check the login without posting anything.
5. **Optionally make one test post**: `python -m app test-post bluesky --text "Testing my new setup"`
   (this asks you to confirm, and the post is public).
6. **Turn off dry run**: set `publishing.dry_run = false`. From then on, approved posts are really published.
   Posts that were only simulated while dry run was on can be sent for real from the Queue page.

Human approval stays on unless you set `publishing.require_human_approval = false` *and*
`publishing.auto_publish = true`. Even then, the dashboard has a switch that turns automatic publishing
off, and drafts on sensitive subjects always wait for a person.

## Credentials

Everything goes in `.env` (see `.env.example`). Never commit `.env`; it is in `.gitignore`.

| Service | What you need | Notes |
|---|---|---|
| Claude | `ANTHROPIC_API_KEY` from console.anthropic.com | Used for classification, research, writing and review |
| **Bluesky** | `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD` | Create an **app password** under Settings → Privacy and security → App passwords. Never use your main password. Self-hosted PDS: set `BLUESKY_PDS` |
| Reddit | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` | Create a "script" app at reddit.com/prefs/apps. The user agent must identify you, e.g. `script:trendscout:1.0 (by /u/yourname)`. Follow Reddit's API terms |
| YouTube | `YOUTUBE_API_KEY` | Google Cloud console → enable YouTube Data API v3 → API key. Default quota is 10,000 units/day; the trending chart costs 1 unit per call, each search costs 100 |
| X trends (optional) | `X_BEARER_TOKEN` | Only on an X API tier that includes the trends endpoint. Turn on `collectors.x_trends.enabled` |
| X posting | `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` | Developer account on a tier that allows posting; app permission "Read and write"; generate the access token *after* setting that permission. Reconciliation and metrics need read access |
| Threads | `THREADS_USER_ID`, `THREADS_ACCESS_TOKEN` | Meta app with the Threads API use case and `threads_content_publish` (app review for use beyond your own test accounts). Long-lived tokens last 60 days: refresh them |
| Instagram | `INSTAGRAM_USER_ID`, `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_GRAPH_VERSION` | Professional (Business or Creator) account, Meta app with `instagram_content_publish` (app review). **Every post needs an image**: add a public HTTPS image URL to the draft on the dashboard |
| LinkedIn | `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_AUTHOR_URN`, `LINKEDIN_VERSION` | "Share on LinkedIn" product (`w_member_social`) for a personal profile, or Community Management API for a page. Tokens last about 60 days. Keep `LINKEDIN_VERSION` (YYYYMM) current |
| TikTok | `TIKTOK_ACCESS_TOKEN`, `TIKTOK_PRIVACY_LEVEL` | Content Posting API with `video.publish`. **Needs a recorded video** at a public URL on a domain verified with TikTok. Until your app passes TikTok's audit, posts can only be private (`SELF_ONLY`) |

Turn a platform on with `[platforms.<name>] enabled = true`. This makes Trend Scout write drafts for it. Publishing
to it also needs the credentials above; until then its jobs are held with a clear reason.

## Using the dashboard

- **Overview:** pause all publishing (the kill switch), switch automatic publishing off, start a discovery,
  publishing or metrics run, see platform status, recent runs and errors, and AI spend for the month.
- **Trends:** every topic from each run with its score breakdown, sources and discovery times, and the reason
  each rejected topic was dropped.
- **Topic page:** the source items, the research summary, each claim with its evidence links and whether it
  was verified, conflicts, missing information, and every source (including whether its text was retrieved).
- **Drafts:** filter by status and platform. Approve (optionally at a set time), edit (optionally re-running
  the reviewer), request a rewrite with instructions, reject, or approve several at once. Each draft shows
  its character count, sources, claims, the writer's rationale and the reviewer's decision and checks.
- **Queue:** scheduled, held, failed and *uncertain* posts. You can reschedule, retry, cancel, or resolve an
  uncertain post after checking the account.
- **Published, Analytics, Logs:** links to live posts, metrics at 1h/24h/72h/7d, performance by
  category/platform/hour/format, learned scoring adjustments with their reasons, AI cost, run history,
  errors and the audit log.

## Scheduling

Choose **one** of these (running both is safe, because every run takes a database lock, but it is pointless).

**On the server (recommended).** `python -m app scheduler` runs discovery at `schedule.discovery_times` in
`schedule.timezone`, checks for due posts every `publish_check_minutes`, and collects metrics every
`metrics_check_minutes`. The `docker-compose.yml` here runs it alongside the dashboard.

**GitHub Actions as the clock.** `.github/workflows/trend_scout.yml` (at the repository root) calls your hosted
instance's `POST /api/trigger` endpoint. The work and the database stay on the server. To set it up:

1. Set `TRIGGER_TOKEN` (24+ random characters) in the server's `.env`.
2. In the repository, open Settings → Secrets and variables → Actions:
   - Add the secrets `TRENDSCOUT_URL` (for example `https://trendscout.example.com`) and `TRENDSCOUT_TRIGGER_TOKEN`
     (the same value as `TRIGGER_TOKEN`).
   - Add the variable `TRENDSCOUT_ENABLED` = `true`.
3. **Start or stop:** set `TRENDSCOUT_ENABLED` to `true` or `false`, or disable the workflow in the Actions tab.
4. **Run by hand:** Actions → Trend Scout → Run workflow, then pick `discover`, `publish`, `metrics`, `all`
   or `test`.
5. **Change times:** edit the `cron` lines (they are in UTC) and the matching `case` in the trigger step.

The same workflow's `test` job runs the test suite and an offline dry run on every change to `trendscout/`.

GitHub Actions is not a host for the dashboard: runners are short-lived and have no persistent disk.

## Deployment

The dashboard and scheduler need a small always-on machine with persistent disk for the SQLite file:
a $5-10/month VPS, Fly.io or Railway with a volume, or a home server.

```bash
cp .env.example .env    # fill it in; set COOKIE_SECURE=true
docker compose up -d --build
```

This serves the dashboard on `127.0.0.1:8000`. Put a TLS-terminating reverse proxy in front of it (Caddy is the
simplest: `trendscout.example.com { reverse_proxy 127.0.0.1:8000 }`). Do not expose the dashboard over plain HTTP.
Back up the `trendscout-data` volume; it holds every trend, draft, approval and publication record.

Without Docker: `python -m app serve --host 127.0.0.1 --port 8000` and `python -m app scheduler`, under systemd
or similar.

## How it stays safe

- **Nothing publishes without approval.** Only `approve` creates a publishing job, and only for drafts awaiting
  approval: drafts the reviewer passed, or drafts you edited yourself (marked "edited, not re-reviewed" until you
  run the reviewer on them). Editing an approved draft cancels its job and sends it back for approval.
- **An independent reviewer gates every draft.** Deterministic checks run first: length; URLs must come from
  the research; numbers must appear in the sources; bait phrasing; invented first-hand experience; hashtags;
  repetition; near-duplicates; and the safety rules. Then a separate model review runs. Writers only ever
  receive revision instructions, and a draft that keeps failing is rejected after `ai.max_revisions`.
- **Editorial policy.** Tragedies, unverified allegations, personal information, medical and political
  misinformation, hate, dangerous challenges, engagement bait and off-niche topics are excluded by default.
  Financial claims and copyright concerns are kept but flagged for a person. Every exclusion is recorded with
  its reason. Edit the policy and keyword lists under `[safety]`.
- **Claims need evidence.** A claim is verified only if text the system actually retrieved supports it.
  A headline, a social post or a search term alone is never enough. Claims citing unknown URLs are stripped.
  Source links are stored with every draft, so any post can be audited.
- **Collected content is treated as untrusted data.** It is sanitised, sentences that read like instructions
  to an AI are removed (and counted in the research record), and it is wrapped in delimiters the prompts tell
  the model never to obey. The models are given no tools that act on anything; research may use Anthropic's
  web search only.
- **No duplicate posts.** There is one job per draft, and a database lease lock allows one publishing run at a
  time. Each job is claimed with an atomic `queued → publishing` update before any network call. A job that
  dies mid-request becomes *uncertain*, never *queued*. Uncertain jobs are reconciled with the platform before
  any retry. Bluesky posts use a record key fixed at approval time, so even a retry cannot create a second copy.
  For platforms that cannot confirm, a person resolves the job on the Queue page.
- **Limits.** Per-platform daily limits, minimum spacing, a publishing window, near-duplicate holds, honouring
  each platform's rate-limit headers, and an automatic pause after `publishing.error_pause_threshold` failures
  within `error_window_minutes`.
- **Kill switch:** "Pause all publishing now" on the dashboard, or `python -m app pause`. It is checked before
  every single post.
- **Dashboard security:** login with a PBKDF2 password hash, signed HttpOnly SameSite session cookies (Secure
  with `COOKIE_SECURE=true`), CSRF tokens on every form, lockout after 5 failed logins, a strict
  Content-Security-Policy, and only http(s) links rendered from collected data. API keys are never sent to
  the browser and are redacted from logs.

## Costs

These are estimates, not measurements: no real Claude call has been made yet. The Analytics page records actual
token use and cost for every call, so check it after the first few days.

- **Claude**, per run: one batched classification call on Claude Haiku 5.5 (well under a cent). Then, for each
  selected topic, on Claude Opus 5.5: an optional web search (up to 3 searches at $0.01 each plus the result
  tokens), one research call that reads up to five source articles, and one writing call and one review per
  platform. Reviews only call the model when the free checks pass. Thinking tokens are billed as output.
  Expect roughly **$0.25-0.60 per selected topic for one platform**, plus about $0.10-0.20 for each extra platform.
  At the defaults (3 runs a day, up to 2 topics each, Bluesky only) that is about **$45-110 a month**.
  `ai.monthly_budget_usd` (default $50) stops AI calls for the rest of the month once the estimate passes it,
  so you never pay more than you set.
- **Levers to spend less:**
  - `selection.topics_per_run`, and fewer `schedule.discovery_times`;
  - `ai.use_web_search = false`, which researches from the trend's own sources only;
  - a lower `ai.max_source_chars`, and `ai.effort_research` / `ai.effort_review` set to `low`;
  - `ai.model = "claude-sonnet-5-5"` (about half the price per token).
- **Bluesky, Hacker News, RSS, Google Trends:** free. **Reddit:** free for non-commercial use within its
  rate limits. **YouTube:** free within quota.
- **X:** posting needs a paid API tier. **Meta, LinkedIn and TikTok:** free, but they require app review.
- **Hosting:** about $5-10/month for a small VPS.

Model prices used for estimates are in `app/llm.py` (`PRICES`). Check current pricing before relying on them.

## Testing

```bash
python -m pytest              # 107 tests, about 15 seconds, no network, nothing is published
python -m app discover --offline && python -m app publish --offline   # manual end-to-end dry run
```

The tests cover:
- each collector and failure isolation, retries and rate limits;
- scoring and normalisation, clustering, covered topics and meaningful updates, and safety rules;
- research validation, prompt-injection stripping, every platform writer, and reviewer decisions;
- approval rules, the dry run, daily limits and spacing, near-duplicates, the kill switch and the circuit breaker;
- definite, uncertain and crashed publishes, reconciliation, and two simultaneous runs publishing a job exactly once;
- each publisher against a fake API, the Claude client through a mocked SDK transport;
- dashboard auth, CSRF and lockout, scheduling, metrics buckets and bounded learning.

## Database

SQLite (WAL mode) in `data/trendscout.db`, or wherever `DATABASE_PATH` points. Migrations are numbered SQL files
in `migrations/`, applied automatically on start (`python -m app init-db` applies them by hand). All timestamps are
ISO-8601 UTC strings. Duplicate prevention and all workflow state live in the database, so restarts and separate
scheduled processes are safe.

**Moving to PostgreSQL:** the SQL is portable apart from the notes at the top of
`migrations/0001_initial.sql` (identity columns, JSONB). Replace `Database._connect` with a psycopg connection,
translate `?` placeholders to `%s`, and use `SELECT ... FOR UPDATE SKIP LOCKED` for the job claim if you run
several publishers.

## Limitations

- Google Trends has no official API. The RSS feed is public but undocumented and may change; when it does,
  that one source fails and the others carry on.
- Bluesky character limits are counted in code points, which can only over-count graphemes. A post with
  complex emoji may be flagged as long when it would actually fit.
- Some sites block automated fetching or render articles with JavaScript. Those sources count as
  "headline only" and cannot verify claims on their own.
- Metrics are only what each API provides. Bluesky reports no views or clicks; LinkedIn personal-post
  analytics are not available to most apps, so those fields stay empty rather than estimated.
- Image and video creation is not automated. Instagram and TikTok drafts include a media brief, and you
  attach the finished asset's URL before publishing.
- Learning adjusts topic ranking within ±20% by category and source, and adds format and timing notes to the
  writer prompts. It never relaxes safety, relevance or evidence checks.

## Project layout

```
app/
  __main__.py        CLI (python -m app ...)
  main.py            FastAPI app factory
  config.py          settings (TOML) + environment
  database.py        SQLite + migrations
  models.py          trend object, schemas for model outputs, records
  pipeline.py        discover -> research -> write -> review; publish; metrics
  llm.py             Claude client, cost tracking, budget guard, offline simulator
  collectors/        hacker_news, news_rss, google_trends, reddit, youtube, x_trends
  agents/            trend_ranker, safety, researcher, writer_base, reviewer, prompts
  writers/           bluesky, x_writer, instagram, threads, linkedin, tiktok
  publishers/        bluesky, x, instagram, threads, linkedin, tiktok
  services/          deduplication, approval, publishing, analytics, scheduler, controls
  dashboard/         routes, auth, templates, static
config/trendscout.toml
migrations/          numbered SQL
fixtures/            offline sample data
tests/
```

## CLI

```
python -m app discover [--offline]     collect, rank, research, write, review
python -m app publish [--offline]      publish approved posts that are due
python -m app metrics                  collect metrics, update learning
python -m app run-all [--offline]      all three
python -m app scheduler [--offline]    long-running scheduler
python -m app serve [--offline]        dashboard
python -m app doctor                   check config and credentials (posts nothing)
python -m app test-post <platform> --text "..."   one real post, after confirmation
python -m app pause [--reason ...] | resume        kill switch
python -m app check-config | init-db | hash-password
```
