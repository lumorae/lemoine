#!/usr/bin/env python3
"""Read the channel's own YouTube analytics — no third-party service, no fee.

Studio shows all of this in a browser. This is the same data over Google's
API so it can be pulled here, diffed between videos, and kept next to the
cuts that produced it.

WHAT THIS CANNOT TELL YOU: impressions and impression click-through rate.
Those two live only in the Studio UI; Google has never exposed them through
the Analytics API. So "how many people were shown this" stays a screenshot
job. What you get instead is where the views that DID happen came from,
which answers the same question from the other side: if the Shorts feed
delivered ~0 views, the video was never fed, whatever the impressions say.

Numbers also settle over 2-3 days. A video a few hours old will read low
and climb; don't diff a fresh upload against a settled one and call the gap
a result.

Setup, once (see SETUP-yt-stats.md in this folder for the console clicks):

    python3 yt_stats.py --init <client_id> <client_secret>
    python3 yt_stats.py --auth-url        # open it, approve, copy the code
    python3 yt_stats.py --auth-code <code>

Then:

    python3 yt_stats.py --video nISGlilj1Ho     # one video, in detail
    python3 yt_stats.py --recent --days 28      # every video, ranked
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TOKENS = os.environ.get("YT_OAUTH_JSON", os.path.join(HERE, "yt-oauth.json"))

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"
DATA_API = "https://www.googleapis.com/youtube/v3"

# Read-only throughout: this tool reports, it never edits the channel.
SCOPES = ("https://www.googleapis.com/auth/yt-analytics.readonly "
          "https://www.googleapis.com/auth/youtube.readonly")
# Google dropped the out-of-band flow in 2022, so the code comes back on a
# localhost redirect that will not resolve. That is fine and expected: the
# browser shows a connection error and the code sits in the address bar.
REDIRECT = "http://localhost:8080"


# --------------------------------------------------------------- credentials

def load():
    if not os.path.exists(TOKENS):
        sys.exit(f"no credentials at {TOKENS} — run --init first (see the docstring)")
    with open(TOKENS) as fh:
        return json.load(fh)


def save(data):
    with open(TOKENS, "w") as fh:
        json.dump(data, fh, indent=2)
    os.chmod(TOKENS, 0o600)   # same handling as the Drive key: owner-only


def post_form(url, fields):
    body = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        sys.exit(f"{url} -> {e.code}\n{e.read().decode()}")


def access_token():
    """Trade the stored refresh token for a short-lived access token."""
    c = load()
    if not c.get("refresh_token"):
        sys.exit("no refresh_token yet — run --auth-url, then --auth-code")
    return post_form(TOKEN_URL, {
        "client_id": c["client_id"], "client_secret": c["client_secret"],
        "refresh_token": c["refresh_token"], "grant_type": "refresh_token",
    })["access_token"]


def get(url, token, **params):
    full = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(full, headers={"Authorization": f"Bearer {token}"})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        sys.exit(f"{url} -> {e.code}\n{e.read().decode()}")


# ------------------------------------------------------------------ reporting

def report(token, metrics, start, end, dimensions=None, filters=None, sort=None,
           max_results=None):
    kw = dict(ids="channel==MINE", startDate=start, endDate=end, metrics=metrics)
    if dimensions:
        kw["dimensions"] = dimensions
    if filters:
        kw["filters"] = filters
    if sort:
        kw["sort"] = sort
    if max_results:
        kw["maxResults"] = max_results
    res = get(ANALYTICS, token, **kw)
    cols = [c["name"] for c in res.get("columnHeaders", [])]
    return [dict(zip(cols, row)) for row in res.get("rows", [])]


def titles_for(token, video_ids):
    """Resolve ids to titles and durations via the Data API, 50 at a time."""
    out = {}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        res = get(f"{DATA_API}/videos", token, part="snippet,contentDetails",
                  id=",".join(chunk), maxResults=50)
        for item in res.get("items", []):
            out[item["id"]] = {
                "title": item["snippet"]["title"],
                "published": item["snippet"]["publishedAt"][:10],
                "duration": item["contentDetails"]["duration"].lower()
                            .replace("pt", "").replace("m", "m ").strip(),
            }
    return out


def pct(row, key):
    v = row.get(key)
    return "—" if v is None else f"{v:.1f}%"


def show_video(token, vid, start, end):
    meta = titles_for(token, [vid]).get(vid, {})
    print(f"\n{meta.get('title', vid)}")
    print(f"  {vid}   published {meta.get('published', '?')}"
          f"   length {meta.get('duration', '?')}   window {start} .. {end}\n")

    totals = report(token, "views,likes,comments,shares,subscribersGained,"
                           "estimatedMinutesWatched,averageViewDuration,"
                           "averageViewPercentage", start, end,
                    filters=f"video=={vid}")
    if not totals:
        print("  no data yet for this window")
        return
    t = totals[0]
    print(f"  views {t['views']}    likes {t['likes']}    comments {t['comments']}"
          f"    shares {t['shares']}    subs +{t['subscribersGained']}")
    print(f"  avg view {t['averageViewDuration']}s"
          f"    avg watched {pct(t, 'averageViewPercentage')}"
          f"    total {t['estimatedMinutesWatched']} min\n")

    # The point of the whole exercise: did the Shorts feed carry it or not.
    rows = report(token, "views,estimatedMinutesWatched,averageViewDuration",
                  start, end, dimensions="insightTrafficSourceType",
                  filters=f"video=={vid}", sort="-views")
    print("  traffic source            views    avg view")
    print("  " + "-" * 42)
    if not rows:
        print("  (none recorded — nothing has been delivered to a feed yet)")
    for r in rows:
        print(f"  {r['insightTrafficSourceType']:<24} {r['views']:>6}"
              f"    {r['averageViewDuration']:>5}s")

    days = report(token, "views", start, end, dimensions="day",
                  filters=f"video=={vid}", sort="day")
    if days:
        print("\n  day          views")
        for d in days:
            bar = "#" * min(40, int(d["views"] ** 0.5))
            print(f"  {d['day']}  {d['views']:>6}  {bar}")


def show_recent(token, start, end, limit):
    rows = report(token, "views,likes,averageViewPercentage,averageViewDuration",
                  start, end, dimensions="video", sort="-views",
                  max_results=limit)
    if not rows:
        print("no video data in this window")
        return
    meta = titles_for(token, [r["video"] for r in rows])
    print(f"\ntop {len(rows)} videos, {start} .. {end}\n")
    print(f"  {'views':>7}  {'likes':>5}  {'watched':>7}  {'avg':>5}  title")
    print("  " + "-" * 74)
    for r in rows:
        m = meta.get(r["video"], {})
        title = m.get("title", r["video"])[:44]
        print(f"  {r['views']:>7}  {r['likes']:>5}  "
              f"{pct(r, 'averageViewPercentage'):>7}  "
              f"{r['averageViewDuration']:>4}s  {title}")


# ----------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--init", nargs=2, metavar=("CLIENT_ID", "CLIENT_SECRET"),
                    help="store the OAuth client from the Cloud console")
    ap.add_argument("--auth-url", action="store_true",
                    help="print the consent URL to open in a browser")
    ap.add_argument("--auth-code", metavar="CODE",
                    help="exchange the pasted code for a refresh token")
    ap.add_argument("--video", metavar="ID", help="detail for one video")
    ap.add_argument("--recent", action="store_true", help="rank every video")
    ap.add_argument("--days", type=int, default=28, help="window, default 28")
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()

    if args.init:
        save({"client_id": args.init[0], "client_secret": args.init[1]})
        print(f"saved client to {TOKENS} — now run --auth-url")
        return

    if args.auth_url:
        c = load()
        url = AUTH_URL + "?" + urllib.parse.urlencode({
            "client_id": c["client_id"], "redirect_uri": REDIRECT,
            "response_type": "code", "scope": SCOPES,
            "access_type": "offline", "prompt": "consent",
        })
        print("\nOpen this, sign in as the channel owner, and approve:\n")
        print(url)
        print("\nThe browser will then fail to load a localhost page. That is "
              "expected.\nCopy the code= value out of the address bar (stop at "
              "the & if there is one)\nand run:\n\n"
              "  python3 yt_stats.py --auth-code <code>\n")
        return

    if args.auth_code:
        c = load()
        tok = post_form(TOKEN_URL, {
            "code": urllib.parse.unquote(args.auth_code),
            "client_id": c["client_id"], "client_secret": c["client_secret"],
            "redirect_uri": REDIRECT, "grant_type": "authorization_code",
        })
        if "refresh_token" not in tok:
            sys.exit("Google returned no refresh_token. Re-run --auth-url "
                     "(it forces the consent screen, which is what issues one).")
        c["refresh_token"] = tok["refresh_token"]
        save(c)
        print("authorised — refresh token stored. Try:\n"
              "  python3 yt_stats.py --recent")
        return

    end = dt.date.today()
    start = end - dt.timedelta(days=args.days)
    token = access_token()
    if args.video:
        show_video(token, args.video, start.isoformat(), end.isoformat())
    else:
        show_recent(token, start.isoformat(), end.isoformat(), args.limit)


if __name__ == "__main__":
    main()
