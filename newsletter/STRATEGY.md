# Lemoine Newsletter — Growth Strategy

> Goal for this cycle: **grow the list.**
> Brand: Johnny Lemoine / Lemoine — premium brand & web design for founders who
> "weren't made to blend in." Tone: confident, artistic, strategically grounded, warm.

---

## 0. How to actually connect Flodesk (do this first)

Flodesk ships an **official MCP connector** — this is the right way to let Claude
read your account. It beats a custom-built API integration for your goal because
it exposes the *analytics the public REST API does not* (opens, clicks, send-time
insights, form conversion), it's OAuth (no API keys to store), and it's read-only
(it can't change your account).

**Connect it in the Claude app → Customize → Connectors → Add custom connector:**

- Name: `Flodesk MCP`
- MCP Server URL: `https://mcp.flodesk.com/mcp`
- Authentication: OAuth (sign into your Flodesk account)

Once connected, you can ask plain-language questions and Claude pulls live answers.
What the connector can see today:

| Area | Tool | Use it to answer |
|---|---|---|
| Account | `get_me` | plan / profile |
| Email perf | `get_email_totals`, `get_email_trends` | "How's open rate trending over 6 months?" |
| Best emails | `rank_emails` | "Which emails performed best last quarter, by clicks?" |
| Timing | `get_send_time_insights` | "Best day/time/device to send?" |
| Audience | `get_subscriber_totals`, `get_subscriber_trends` | "How has my list grown? What's my churn?" |
| Segments | `rank_segments` | "Which segments are biggest / most engaged?" |
| **Forms** | `rank_forms` | **"Which signup forms convert best?" ← growth lever #1** |
| Automations | `rank_workflows` | "Which automation converts best?" |
| Sales | `get_checkout_totals` | "Revenue / orders / conversion this month" |

> ⚠️ Note on safety: Flodesk's own docs flag prompt-injection and hallucination
> risk for AI connectors. Treat AI-surfaced numbers as a starting point and
> sanity-check anything you'd act on financially.

### Diagnostic questions to run once connected (the "what's worked" audit)
1. `get_subscriber_trends` — monthly net growth + churn for the last 12 months. Are we net-growing?
2. `rank_forms` — which form/placement converts visitors best? Pour traffic there.
3. `rank_emails` by open rate **and** by click rate — what *topics & subject styles* win?
4. `get_send_time_insights` — lock the send window.
5. `rank_segments` by engagement — who actually reads us? Write more for them.

---

## 1. The growth model (a newsletter doesn't grow itself)

Sending to your existing list doesn't add subscribers. Growth = **Acquisition ×
Activation × Amplification.** The monthly issue is the amplification engine; the
real net-new comes from acquisition surfaces.

### A. Acquisition — get the email in the first place
- **Lead magnet matched to the audience.** Founders who want to stand out don't
  want "10 tips." Offer something they'd pay for: e.g. *"The Stand-Out Brand
  Audit — the 12-point checklist I run on every client before we design a thing."*
  High perceived value, directly demonstrates expertise, pre-qualifies buyers.
- **Forms everywhere, measured.** Homepage, blog/case-study pages, exit-intent,
  and link-in-bio. Use `rank_forms` monthly to kill losers and clone winners.
  (Your site currently has **no signup** — that's the single biggest fix.)
- **Content-to-capture loop.** Every case study / Behance / IG post ends with one
  line: "I break down how I do this in my newsletter → [link]."

### B. Activation — turn a signup into a reader
- **Welcome sequence (Flodesk Workflow).** 3 emails: deliver the magnet → the
  Lemoine origin/POV → one signature piece of design thinking + soft "here's what
  I do." Check `rank_workflows` to see completion/conversion.
- **Double opt-in on** so the list stays clean (protects deliverability = protects
  open rate = protects everything).

### C. Amplification — make the list grow the list
- **Forward-ability.** Each issue carries one genuinely useful idea worth sending
  to a peer. Add a light "Know a founder who needs this? Forward it →" line.
- **Referral / share line + a public web version** of each issue to post on socials.
- **Repurpose:** every issue = 1 LinkedIn post + 2–3 IG slides → drives back to the form.

---

## 2. The monthly system (so it's never a blank page)

| When | Action |
|---|---|
| Day 1 | Run the 5 diagnostic questions above. Note the winning topic/subject style. |
| Day 2 | Draft from `TEMPLATE.md`. One idea, one CTA. |
| Day 3 | Write 3 subject-line variants; pick send window from `get_send_time_insights`. |
| Send day | Send. Plain-text-feeling, single column, one button. |
| +3 days | Repurpose to LinkedIn + IG, each linking to the signup form. |
| Month end | Log open/click/net-growth into `metrics-log.md`. Compare to last month. |

---

## 3. What "good" looks like (benchmarks to beat)
- Open rate: 30%+ is solid for a design audience; aim to beat *your own* trailing average.
- Click rate: 2–4% baseline; a strong single-CTA issue can hit 5%+.
- **Net list growth: the number that matters this cycle.** Target a positive,
  compounding month-over-month curve via the acquisition surfaces, not the send.
- Unsubscribe rate: keep < 0.5%. Spikes = wrong audience or wrong promise.

---

## 4. Honest scope note
- Flodesk's MCP connector is **read-only** today. For *automated writes* (e.g.
  auto-tagging subscribers, scheduled CSV growth reports, syncing signups from
  another tool), you'd need the **REST API** (`https://api.flodesk.com/v1`, Basic
  auth, paid plans only). I can build that integration in this repo if/when you
  want automation the connector can't do — just say the word and we'll handle the
  key as a secret, never committed.
