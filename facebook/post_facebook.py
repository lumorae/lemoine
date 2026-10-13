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

from captions import caption_for, load_custom

ROOT = Path(__file__).parent.parent
PINS_FILE = ROOT / "etsy-audit" / "pins.json"
STATE_FILE = ROOT / "facebook" / "posted.json"

POSTS_PER_RUN = int(os.environ.get("FB_POSTS_PER_RUN", "1"))
GRAPH_VERSION = os.environ.get("FB_GRAPH_VERSION", "v23.0")
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")


def load_listings() -> list[dict]:
    """One entry per listing; pins.json has three pins per listing."""
    seen = {}
    for pin in json.loads(PINS_FILE.read_text()):
        lid = str(pin["listing_id"])
        if lid in seen or not pin.get("image_url"):
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

    if preview:
        # Simulate the rotation without saving, so a 7-day preview is honest.
        sim = json.loads(json.dumps(state))
        for day in range(1, preview + 1):
            listing = queue(listings, sim)[0]
            s = sim["listings"].setdefault(listing["listing_id"], {"count": 0})
            print(f"--- Post {day}: {listing['title'][:70]}\n{listing['image_url']}\n")
            print(caption_for(listing, s["count"], custom) + "\n")
            s["count"] += 1
            s["last_posted"] = f"preview-{day:04d}"
        return

    for listing in queue(listings, state)[:POSTS_PER_RUN]:
        s = state["listings"].get(listing["listing_id"], {"count": 0, "post_ids": []})
        caption = caption_for(listing, s["count"], custom)
        if DRY_RUN:
            print(f"[dry run] would post {listing['image_url']}\n{caption}\n")
            continue
        try:
            post_id = post_photo(listing, caption)
        except Exception as e:
            print(f"  ✗ {listing['title'][:70]}: {e}")
            sys.exit(1)
        s["count"] += 1
        s["last_posted"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        s["post_ids"].append(post_id)
        state["listings"][listing["listing_id"]] = s
        save_state(state)
        print(f"  ✓ {listing['title'][:70]} → https://www.facebook.com/{post_id}")


if __name__ == "__main__":
    main()
