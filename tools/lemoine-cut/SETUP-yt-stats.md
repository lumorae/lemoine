# yt_stats.py — reading the channel's analytics directly

One-time setup. Reuses the existing Google Cloud project `analytics-501817`
(the one behind the Drive service account), so there is no new project to
create and nothing to pay for.

The Drive service account cannot be reused for this. YouTube Analytics only
answers for a human who owns the channel, so this needs a normal OAuth
sign-in — done once, then a stored refresh token keeps it working.

## 1. Turn on the two APIs

Open each and press **Enable**:

- https://console.cloud.google.com/apis/library/youtubeanalytics.googleapis.com?project=analytics-501817
- https://console.cloud.google.com/apis/library/youtube.googleapis.com?project=analytics-501817

The first serves the numbers; the second turns video ids into titles.

## 2. Set up the consent screen

https://console.cloud.google.com/auth/overview?project=analytics-501817

- User type: **External**
- App name: anything (`lemoine stats`), support email: your own
- On the **Audience** step, while it is in Testing, add your own Google
  account under **Test users** — the account that owns @lemoinemusic

Leave it in Testing. It is only ever you signing in. The one consequence is
that the refresh token expires every 7 days in Testing mode; if you would
rather not redo step 5 weekly, press **Publish app** on that screen. It asks
for no review, because the scopes here are read-only.

## 3. Create the OAuth client

https://console.cloud.google.com/apis/credentials?project=analytics-501817

**Create credentials → OAuth client ID → Application type: Desktop app.**
Name it anything. Copy the **client ID** and **client secret**.

Desktop app is the right type because it permits `http://localhost` redirects
without registering them, which is what step 5 leans on.

## 4. Store the client

```bash
cd tools/lemoine-cut
python3 yt_stats.py --init <client_id> <client_secret>
```

Writes `yt-oauth.json`, owner-read-only and gitignored — same handling as
`gdrive-sa.json`. It never gets committed.

## 5. Authorise once

```bash
python3 yt_stats.py --auth-url
```

Open the printed URL, sign in as the channel owner, approve. Google will
warn that the app is unverified — that is your own app; continue past it.

The browser then fails to load a `localhost:8080` page. **That is expected
and means it worked.** The address bar now reads something like:

```
http://localhost:8080/?code=4/0AX4XfWh...&scope=https://...
```

Copy the value between `code=` and `&`, then:

```bash
python3 yt_stats.py --auth-code 4/0AX4XfWh...
```

That is the last manual step. From here it refreshes itself.

## Using it

```bash
python3 yt_stats.py --recent --days 28      # every video, ranked by views
python3 yt_stats.py --video nISGlilj1Ho     # one video, in detail
```

The per-video view is the useful one. It prints totals, then a breakdown by
traffic source, then a day-by-day curve. The traffic-source table is what
distinguishes a distribution problem from a content problem: if the Shorts
feed row is missing or near zero, YouTube never put the video in front of
anyone, and no amount of editing the title would have changed that.

## What it deliberately does not do

- **Impressions and click-through rate are not available.** Google has never
  exposed them through the Analytics API; they exist only in the Studio UI.
  For those, screenshot Studio.
- **Nothing is written.** Both scopes are `.readonly`. This tool cannot edit,
  publish, delete, or comment.
- **Fresh numbers are provisional.** Analytics settle over 2-3 days. A video
  a few hours old reads low and climbs, so don't compare a same-day upload
  against a settled one and treat the gap as a finding.
