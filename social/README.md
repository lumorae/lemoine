# Lemoine Social — desktop-only posting & data-driven growth

A custom system to write/design posts on **desktop only**, publish them to
**Instagram** (Business) and **LinkedIn** (Company Page), pull the **real
performance data** back in, and use that data to decide what to post next.
No phone, no Instagram app.

## How it works

```
  You compose in        Supabase publishes &        Claude reads the
  Airtable (cockpit)  →  measures (engine)        →  metrics & advises
        ▲                       │                          │
        └───────────────────────┴── next posts drafted ────┘
```

- **Airtable** — where you write. One record per post (caption, image,
  platforms, schedule, status). Also your calendar + a performance view.
- **Supabase** (`lemoine-proposals` project, `social` schema) — publishes
  approved posts via the platform APIs, pulls analytics on a schedule, hosts
  post images publicly, and warehouses every metric over time.
- **Vercel** — hosts the one-time OAuth login pages + any webhooks.
- **Claude** — drafts/refines posts into Airtable, reads metrics from
  Supabase, and tells you what's working.

## Status / build order

- [x] Data model (`supabase/migrations/0001_social_schema.sql`)
- [x] **Meta app + Instagram credentials** — DONE, token verified live
- [x] Instagram **read + insights** — working (proved against the real account)
- [x] Real data snapshot + audit (`data/`, `scripts/analyze.py`)
- [x] Automation written (`functions/instagram-sync`, `migrations/0002_automation.sql`)
- [ ] **Deploy to Supabase** — blocked: Supabase MCP access errored in the web
      session. Apply 0001 + 0002, deposit the token in Vault, deploy the function.
- [ ] Confirm Instagram **publishing** (first real post)
- [ ] **You:** LinkedIn Community Management API approval (pending)
- [ ] Airtable "Content" cockpit
- [ ] Growth analysis loop

### Connected Instagram account (non-secret)
- Username: **@lemoinedesign**  ·  Type: **BUSINESS**
- IG user id (for publishing): **17841401720504053**
- Secrets (token, app secret) are held outside the repo — to be deposited in
  Supabase Vault as `ig_lemoinedesign_token`. **Never commit them.**

### Finish-line deploy (when Supabase access is restored)
1. `apply_migration` 0001 then 0002.
2. `select vault.create_secret('<IGA token>', 'ig_lemoinedesign_token', ...);`
3. Deploy `functions/instagram-sync`; enable the daily cron in 0002.
4. The token is reusable — **the Meta/Instagram setup never needs redoing.**

---

## Setup you must do (desktop, one-time)

These are tied to *your* identity as account/page admin — Claude can't do them
for you. Start them early; the LinkedIn approval is the slowest part.

### 1. Meta / Instagram — https://developers.facebook.com

1. **Create app** → type **Business**.
2. Add product **Instagram Graph API**; connect your Facebook Page + the
   Instagram **Business/Creator** account.
3. From Graph API Explorer, generate a **long-lived Page access token**.
4. Note your **Instagram Business Account ID** (numeric) and **App ID/Secret**.
5. While the app is in **Development mode** you can already publish to and read
   insights from **your own** connected account — so we can start without the
   full App Review. (App Review is only needed to go public / manage other
   people's accounts.)

Permissions in play: `instagram_content_publish`, `instagram_manage_insights`,
`pages_read_engagement`, `pages_show_list`.

### 2. LinkedIn — https://www.linkedin.com/developers

1. **Create app**, and **associate it with the Lemoine Company Page** (you must
   be a Page admin).
2. Request the **Community Management API** product (needed to post to the Page
   and read Page analytics). This requires approval — apply early.
3. Also add **Sign In with LinkedIn using OpenID Connect**.
4. Note your **Organization URN** (`urn:li:organization:########`) and
   **Client ID/Secret**.

Scopes: `w_organization_social`, `r_organization_social`, `rw_organization_admin`.

> Personal-profile posting via API is effectively closed — that's why posts go
> to the **Company Page**.

### 3. Hand credentials to Claude

Paste them in chat (or add them yourself). They get stored as **Supabase/Vercel
secrets** — never committed. See `.env.example` for the full list.

---

## Repo layout

```
social/
  README.md                         this file (runbook)
  .env.example                      every credential the system needs
  supabase/migrations/              database schema
  functions/                        publish + analytics-sync code (built post-credentials)
```
