# Northline Athletic marketing agent

Posts three slideshows a day to Instagram, Facebook and TikTok for Northline Athletic.
You approve every post from your phone before it goes out.

## How a day works

1. **7:00 AM**: the agent asks Claude to write three slideshow posts (hook, 3–6 content slides,
   a closing slide with the store link, caption, hashtags) and draws the slides.
2. **Telegram**: it sends you each slideshow with three buttons: **Approve for 11:30 AM**,
   **Post now**, **Skip**. There's also an **Approve all 3** button.
3. **11:30 AM, 4:30 PM, 8:00 PM**: each approved post goes out on all three platforms, and
   Telegram sends you links to the live posts. If a platform fails, only that platform is retried,
   up to 3 times.
4. If you haven't answered by post time, you get one reminder. A post still unapproved 4 hours after
   its slot is skipped.

Telegram commands: `/status`, `/pause`, `/resume`.

Change the brand voice, products, colours and post times in [`config.yaml`](config.yaml).
Put product or lifestyle photos in `assets/photos/` and they'll be used behind cover slides.

## What you need to set up

Each piece works on its own: once Claude + Telegram are set up you get daily previews, and each
platform starts posting as soon as its credentials are added.

All secrets go in **GitHub → repo Settings → Secrets and variables → Actions → New repository secret**.
Never paste them into files, because this repo is public.

### 1. Claude (writes the posts), ~2 min
- Create a key at console.anthropic.com → API Keys and add billing.
  Three posts a day costs a few cents.
- Secret: `ANTHROPIC_API_KEY`

### 2. Telegram (your approval buttons), ~3 min
- In Telegram, message **@BotFather**, send `/newbot`, and name it (e.g. "Northline Poster").
  It gives you a token. Secret: `TELEGRAM_BOT_TOKEN`
- Send your new bot any message, then message **@userinfobot** to get your numeric ID.
  Secret: `TELEGRAM_CHAT_ID`
- Only this chat ID can approve posts.

### 3. Instagram + Facebook (one Meta setup covers both), ~20 min
1. Your Instagram must be a **Business** or **Creator** account, **linked to the Northline Facebook Page**
   (Instagram app → Settings → Account type and tools; then link the Page).
2. Go to developers.facebook.com → **Create app** → type **Business**. Add the
   **Instagram Graph API** / "Manage messaging & content on Instagram" and **Facebook Login for Business** use cases.
3. Get a token that doesn't expire: business.facebook.com → Settings → **System users** → add an admin
   system user → **Assign assets** (your Page and Instagram account) → **Generate token** for your app with
   these permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`, `pages_manage_posts`, `business_management`.
   Secret: `META_ACCESS_TOKEN`
4. Run the **check** command (see "Running it" below). It lists your Page and Instagram IDs.
   Secrets: `FB_PAGE_ID`, `IG_USER_ID`

Because you own the app and the accounts, Meta doesn't need to review the app to post to your own accounts.

### 4. TikTok, ~30 min plus TikTok's review
1. developers.tiktok.com → **Manage apps** → **Connect an app**. Add the **Login Kit** and
   **Content Posting API** products, and turn on **Direct Post**.
2. Add a redirect URI. Any https page you control works; the default is
   `https://ow3nvr86-wq.github.io/OWENS-/`. If you use a different one, also add it as a GitHub
   *variable* (not secret) named `TIKTOK_REDIRECT_URI`.
3. **Verify the URL prefix** the slides are served from: in the app's URL properties add
   `https://raw.githubusercontent.com/ow3nvr86-wq/OWENS-/northline-agent-data/media/`. TikTok gives you a
   signature file. Run the **tiktok-verify-file** command with the file name and its contents, then click Verify.
4. Secrets: `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` (from the app page).
5. Run **tiktok-login-url**, open the link it prints, and log in as Northline. You land on your redirect page
   with `?code=...` in the address bar. Copy that code and run **tiktok-exchange** with it. The agent sends
   the refresh token to your Telegram. Secret: `TIKTOK_REFRESH_TOKEN`
6. **Important:** until TikTok **audits** your app, everything it posts is **private** (only you can see it).
   Submit the app for review in the developer portal to go public. Telegram tells you when a post went out private.

## Running it

The agent is built to run on GitHub Actions: a scheduled workflow runs `python -m northline_agent tick`
every 10 minutes with the secrets above. That plans the day after `plan_at`, reads your Telegram taps
and publishes whatever is due. A manual run of `check` tests every connection.
Slides and the post queue are kept on a separate branch, `northline-agent-data`. Platforms download images
from that branch's public URL, and keeping them off the main branch stops its history from growing.

To run it on your own computer instead:

```bash
cd northline-agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY=... TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=...   # plus any platform secrets
python -m northline_agent check      # test connections
python -m northline_agent sample     # send a sample post to Telegram (no Claude call)
python -m northline_agent plan       # write today's 3 posts now
python -m northline_agent tick       # read approvals and post what's due
```

For posts to go out, the slides must be at a public URL the platforms can download from. Set
`MEDIA_BASE_URL` if you host `data/media/` somewhere other than the data branch.
