"""
Pull active Etsy listings for johnnylemoine and write listings.json.
Reads ETSY_API_KEY (keystring) and ETSY_SHARED_SECRET from env.
Etsy v3 auth requires x-api-key: <keystring>:<shared_secret>.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SHOP_NAME = "johnnylemoine"
OUT = Path(__file__).parent / "listings.json"

api_key = os.environ.get("ETSY_API_KEY")
shared_secret = os.environ.get("ETSY_SHARED_SECRET")
if not api_key or not shared_secret:
    sys.exit("Missing ETSY_API_KEY and/or ETSY_SHARED_SECRET env vars.")

auth_header = f"{api_key}:{shared_secret}"


def etsy_get(path: str) -> dict:
    """GET from Etsy, paced under its per-second limit, retrying on 429."""
    req = urllib.request.Request(
        f"https://api.etsy.com/v3/application{path}",
        headers={"x-api-key": auth_header},
    )
    for attempt in range(5):
        time.sleep(0.25)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4:
                raise
            time.sleep(int(e.headers.get("Retry-After") or 2 ** attempt))


shop = etsy_get(f"/shops?shop_name={SHOP_NAME}")
if not shop.get("results"):
    sys.exit(f"Shop {SHOP_NAME} not found.")
shop_id = shop["results"][0]["shop_id"]

listings = etsy_get(f"/shops/{shop_id}/listings/active?limit=100")

# Fetch images per listing (Etsy v3's `includes=Images` param is unreliable).
for l in listings["results"]:
    imgs = etsy_get(f"/listings/{l['listing_id']}/images")
    l["images"] = imgs.get("results", [])

OUT.write_text(json.dumps(listings, indent=2))
print(f"Pulled {listings['count']} listings + images from shop {shop_id} → {OUT}")
