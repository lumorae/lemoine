"""
Weekly marketing report: Etsy views and favorites, and how the Lemoine
Facebook Page did, compared with last week.

Runs Mondays via .github/workflows/weekly-report.yml, which opens the
result as a GitHub issue (GitHub emails it). Reads etsy-audit/listings.json
(from pull_etsy.py) and the Page through FB_PAGE_ID / FB_PAGE_TOKEN.

Etsy's public API gives views and favorites, not orders, so sales stay in
Etsy Stats; the report links there.

Last week's numbers live in report/snapshot.json, carried between runs by
the Actions cache. The first run has no baseline, so it shows totals only.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
LISTINGS_FILE = ROOT / "etsy-audit" / "listings.json"
SNAPSHOT_FILE = ROOT / "report" / "snapshot.json"
REPORT_FILE = ROOT / "report" / "report.md"
POSTED_FILE = ROOT / "facebook" / "posted.json"
POSTED_SEED = ROOT / "facebook" / "posted_seed.json"
GRAPH = f"https://graph.facebook.com/{os.environ.get('FB_GRAPH_VERSION', 'v23.0')}"


def graph(path: str, **params) -> dict:
    params["access_token"] = os.environ["FB_PAGE_TOKEN"]
    url = f"{GRAPH}{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        message = json.loads(e.read() or b"{}").get("error", {}).get("message", "")
        raise RuntimeError(f"{path}: HTTP {e.code} {message}") from None


def etsy_numbers() -> dict:
    listings = json.loads(LISTINGS_FILE.read_text())["results"]
    return {str(l["listing_id"]): {"title": l["title"], "url": l["url"].split("?")[0],
                                   "views": l["views"], "favs": l["num_favorers"]}
            for l in listings}


# Richest first. Reactions and comments need pages_read_user_content, which
# the app may not have; fall back to what the Page token can read.
POST_FIELDS = [
    "created_time,message,permalink_url,shares,"
    "reactions.summary(true).limit(0),comments.summary(true).limit(0)",
    "created_time,message,permalink_url,shares,reactions.summary(true).limit(0)",
    "created_time,message,permalink_url,shares",
    "created_time,permalink_url",
]


def read_post(pid: str) -> dict:
    for fields in POST_FIELDS:
        try:
            return graph(f"/{pid}", fields=fields)
        except RuntimeError as e:
            print(f"  {fields.split(',')[-1]}: {e}")
    raise RuntimeError(f"couldn't read post {pid}")


def facebook_numbers() -> dict:
    """Followers, plus engagement on this week's posts.

    Listing every Page post needs pages_read_user_content, which the app
    doesn't have, so it looks up the posts the auto-poster recorded in
    facebook/posted.json (or the seed file before the first run).
    """
    page = graph(f"/{os.environ['FB_PAGE_ID']}", fields="followers_count")
    state_file = POSTED_FILE if POSTED_FILE.exists() else POSTED_SEED
    state = json.loads(state_file.read_text()) if state_file.exists() else {"listings": {}}
    post_ids = [pid for s in state["listings"].values() for pid in s.get("post_ids", [])]
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    posts = []
    for pid in post_ids:
        p = read_post(pid)
        if p["created_time"] < week_ago[:19]:
            continue
        posts.append({
            "when": p["created_time"][:10],
            "text": (p.get("message") or "").split("\n")[0][:70],
            "url": p.get("permalink_url", ""),
            "reactions": p.get("reactions", {}).get("summary", {}).get("total_count", "–"),
            "comments": p.get("comments", {}).get("summary", {}).get("total_count", "–"),
            "shares": p.get("shares", {}).get("count", 0),
        })
    return {"followers": page.get("followers_count"),
            "posts": sorted(posts, key=lambda p: p["when"])}


def delta(now: int, before: int | None) -> str:
    if before is None:
        return ""
    d = now - before
    return f" ({'+' if d >= 0 else ''}{d})"


def main():
    etsy = etsy_numbers()
    try:
        fb = facebook_numbers()
    except (urllib.error.URLError, KeyError, RuntimeError) as e:
        fb = {"error": str(e)}
    last = json.loads(SNAPSHOT_FILE.read_text()) if SNAPSHOT_FILE.exists() else {}
    last_etsy = last.get("etsy", {})

    views = sum(l["views"] for l in etsy.values())
    favs = sum(l["favs"] for l in etsy.values())
    last_views = sum(l["views"] for l in last_etsy.values()) if last_etsy else None
    last_favs = sum(l["favs"] for l in last_etsy.values()) if last_etsy else None

    lines = [f"Week ending {datetime.now(timezone.utc):%b %d, %Y}.", ""]

    lines += ["## Etsy", "",
              f"- **Views, all listings:** {views:,}{delta(views, last_views)}",
              f"- **Favorites:** {favs:,}{delta(favs, last_favs)}",
              f"- **Active listings:** {len(etsy)}", ""]
    if last_etsy:
        gains = sorted(((l["views"] - last_etsy.get(lid, {}).get("views", l["views"]), lid)
                        for lid, l in etsy.items()), reverse=True)[:5]
        lines += ["**Most new views this week**", ""]
        lines += [f"{i}. [{etsy[lid]['title'][:60]}]({etsy[lid]['url']}): +{g} views"
                  for i, (g, lid) in enumerate(gains, 1) if g > 0] or ["No new views recorded."]
    else:
        top = sorted(etsy.values(), key=lambda l: -l["views"])[:5]
        lines += ["**Most viewed, all time** (week-on-week changes start next Monday)", ""]
        lines += [f"{i}. [{l['title'][:60]}]({l['url']}): {l['views']:,} views"
                  for i, l in enumerate(top, 1)]
    lines += ["", "Orders and where shoppers came from (including Facebook) are in "
              "[Etsy Stats](https://www.etsy.com/your/shops/me/stats).", ""]

    lines += ["## Facebook Page", ""]
    if "error" in fb:
        lines += [f"Couldn't read the Page this week: {fb['error']}", ""]
    else:
        lines += [f"- **Followers:** {fb['followers']:,}"
                  f"{delta(fb['followers'], last.get('followers'))}",
                  f"- **Auto-posts this week:** {len(fb['posts'])} (Reels and posts made by hand aren't counted)", ""]
        if fb["posts"]:
            lines += ["| Date | Post | Reactions | Comments | Shares |", "|---|---|---|---|---|"]
            lines += [f"| {p['when']} | [{p['text'] or 'post'}]({p['url']}) | {p['reactions']} "
                      f"| {p['comments']} | {p['shares']} |" for p in fb["posts"]]
            lines.append("")

    REPORT_FILE.write_text("\n".join(lines))
    SNAPSHOT_FILE.write_text(json.dumps({"etsy": etsy, "followers": fb.get("followers")}))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
