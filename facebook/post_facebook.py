"""
Post Etsy listings to the Lemoine Facebook Page.

Runs daily via GitHub Action. Reads listings from etsy-audit/pins.json
(written by generate_pins.py), posts the product photo with a caption and
the Etsy link, and tracks what went out in facebook/posted.json.

Rotation: listings never posted go first, best-viewed first. Once every
listing has been posted, it starts round again with the least recently
posted, using the next caption variant, so the Page never runs dry.

Required env vars:
  FB_PAGE_ID
  FB_PAGE_TOKEN     long-lived Page token from get_page_token.py

Optional:
  FB_POSTS_PER_RUN  default 1
  FB_GRAPH_VERSION  default v23.0
  DRY_RUN=1         print what would post, touch nothing

  python3 facebook/post_facebook.py --preview 7   shows the next 7 posts
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from captions import TEMPLATES, caption_for, load_custom

ROOT = Path(__file__).parent.parent
PINS_FILE = ROOT / "etsy-audit" / "pins.json"
STATE_FILE = ROOT / "facebook" / "posted.json"
SEED_FILE = ROOT / "facebook" / "posted_seed.json"

POSTS_PER_RUN = int(os.environ.get("FB_POSTS_PER_RUN", "1"))
GRAPH_VERSION = os.environ.get("FB_GRAPH_VERSION", "v23.0")
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

# Fan art of other people's characters stays off Facebook: a trademark
# report gets the post removed, and repeat reports can restrict the Page.
SKIP_WORDS = ("lightning", "mater", "pixar", "disney", "cars ")

# How many recent posts to keep apart: no repeated caption wording among them.
RECENT = 6

NO_LINK_LINE ="\n\nPrints on Etsy. The shop link is on the Lemoine Page."


def load_listings() -> list[dict]:
    """One entry per listing; pins.json has three pins per listing."""
    seen = {}
    for pin in json.loads(PINS_FILE.read_text()):
        lid = str(pin["listing_id"])
        if lid in seen or not pin.get("image_url"):
            continue
        if any(w in f"{pin['listing_title']} {pin['listing_url']}".lower() for w in SKIP_WORDS):
            continue
        seen[lid] = {
            "listing_id": lid,
            "title": pin["listing_title"],
            "url": pin["listing_url"].split("?")[0],
            "image_url": pin["image_url"],
            "views": pin.get("listing_views", 0),
            "category": pin["category"],
        }
    return list(seen.values())


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    # No cached state yet (first run on a branch): start from the posts
    # already made by hand, so they don't go out again.
    if SEED_FILE.exists():
        return json.loads(SEED_FILE.read_text())
    return {"listings": {}}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def queue(listings: list[dict], state: dict) -> list[dict]:
    """Fewest posts first, then longest since last post, then most views."""
    def key(l):
        s = state["listings"].get(l["listing_id"], {})
        return (s.get("count", 0), s.get("last_posted", ""), -l["views"])
    return sorted(listings, key=key)


def recent_posts(state: dict, listings: list[dict]) -> list[dict]:
    """The last few posts, oldest first: category and caption template.

    State written before this was tracked has no "recent", so rebuild it
    from the posting history and the templates those posts would have used.
    """
    if "recent" in state:
        return state["recent"]
    by_id = {l["listing_id"]: l for l in listings}
    posted = sorted((s["last_posted"], lid) for lid, s in state["listings"].items()
                    if s.get("last_posted") and lid in by_id)
    recent = []
    for _, lid in posted[-RECENT:]:
        l, n = by_id[lid], state["listings"][lid]["count"]
        variants = TEMPLATES.get(l["category"], TEMPLATES["art_general"])
        recent.append({"listing_id": lid, "category": l["category"],
                       "template": variants[(n - 1) % len(variants)]})
    return recent


def next_listing(listings: list[dict], state: dict, recent: list[dict]) -> dict:
    """Next in the queue, skipping ahead past pieces from the same category
    as the last post, so similar pieces don't go out back to back."""
    ordered = queue(listings, state)
    last = recent[-1]["category"] if recent else None
    return next((l for l in ordered if l["category"] != last), ordered[0])


def remember(state: dict, recent: list[dict], listing: dict, template: str, when: str):
    s = state["listings"].setdefault(listing["listing_id"], {"count": 0, "post_ids": []})
    s["count"] += 1
    s["last_posted"] = when
    recent.append({"listing_id": listing["listing_id"], "category": listing["category"],
                   "template": template})
    state["recent"] = recent[-RECENT:]


def post_photo(listing: dict, caption: str) -> str:
    body = urllib.parse.urlencode({
        "url": listing["image_url"],
        "caption": caption,
        "access_token": os.environ["FB_PAGE_TOKEN"],
    }).encode()
    req = urllib.request.Request(
        f"https://graph.facebook.com/{GRAPH_VERSION}/{os.environ['FB_PAGE_ID']}/photos",
        data=body,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        if '"code":190' in detail.replace(" ", ""):
            detail += ("\nThe Page token is no longer valid (a password change or a"
                       " removed permission does this). Run facebook/get_page_token.py"
                       " again to issue a new one.")
        raise RuntimeError(f"HTTP {e.code}: {detail}") from None
    return result.get("post_id") or result["id"]


def main():
    preview = None
    if len(sys.argv) == 3 and sys.argv[1] == "--preview":
        preview = int(sys.argv[2])

    listings = load_listings()
    if not listings:
        print("No listings with images in pins.json. Run pull_etsy.py and generate_pins.py first.")
        return

    state = load_state()
    custom = load_custom()
    recent = recent_posts(state, listings)

    def pick(st: dict) -> tuple[dict, str, str]:
        listing = next_listing(listings, st, recent)
        count = st["listings"].get(listing["listing_id"], {}).get("count", 0)
        caption, template = caption_for(listing, count, custom,
                                        [r["template"] for r in recent])
        return listing, caption, template

    if preview:
        # Simulate the rotation without saving, so a 7-day preview is honest.
        sim = json.loads(json.dumps(state))
        for day in range(1, preview + 1):
            listing, caption, template = pick(sim)
            print(f"--- Post {day}: {listing['title'][:70]}\n{listing['image_url']}\n")
            print(caption + "\n")
            remember(sim, recent, listing, template, f"preview-{day:04d}")
        return

    for _ in range(POSTS_PER_RUN):
        listing, caption, template = pick(state)
        if DRY_RUN:
            print(f"[dry run] would post {listing['image_url']}\n{caption}\n")
            remember(state, recent, listing, template, "dry-run")
            continue
        try:
            try:
                post_id = post_photo(listing, caption)
            except RuntimeError as e:
                # Pages without Meta One get a few link posts a month. Once
                # they're used up, post anyway and point to the Page's shop link.
                if "link" not in str(e).lower():
                    raise
                print(f"  ! link refused, posting without it: {e}")
                caption = caption.rsplit("\n\nOn Etsy:", 1)[0] + NO_LINK_LINE
                post_id = post_photo(listing, caption)
        except Exception as e:
            print(f"  ✗ {listing['title'][:70]}: {e}")
            sys.exit(1)
        remember(state, recent, listing, template,
                 datetime.now(timezone.utc).isoformat(timespec="seconds"))
        state["listings"][listing["listing_id"]].setdefault("post_ids", []).append(post_id)
        save_state(state)
        print(f"  ✓ {listing['title'][:70]} → https://www.facebook.com/{post_id}")


if __name__ == "__main__":
    main()
