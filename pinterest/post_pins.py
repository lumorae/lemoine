"""
Post pending pins to Pinterest.

Runs daily via GitHub Action. Reads pins from etsy-audit/pins.json,
tracks posted state in pinterest/posted.json, posts up to PINS_PER_RUN
new pins per run. Refreshes access token on expiry.

Required env vars:
  PINTEREST_APP_ID
  PINTEREST_APP_SECRET
  PINTEREST_ACCESS_TOKEN
  PINTEREST_REFRESH_TOKEN

State file (pinterest/posted.json) is committed to the repo so runs
across days don't repost the same pin.
"""
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
PINS_FILE = ROOT / "etsy-audit" / "pins.json"
STATE_FILE = ROOT / "pinterest" / "posted.json"
TOKEN_FILE = ROOT / "pinterest" / "tokens.json"  # only used locally; CI reads env

PINS_PER_RUN = int(os.environ.get("PINS_PER_RUN", "3"))
API_ROOT = "https://api.pinterest.com/v5"

APP_ID = os.environ["PINTEREST_APP_ID"]
APP_SECRET = os.environ["PINTEREST_APP_SECRET"]
access_token = os.environ["PINTEREST_ACCESS_TOKEN"]
refresh_token = os.environ["PINTEREST_REFRESH_TOKEN"]


def api(method: str, path: str, body: dict | None = None, retry_on_401: bool = True):
    global access_token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=data,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 401 and retry_on_401:
            refresh_access_token()
            return api(method, path, body, retry_on_401=False)
        sys.stderr.write(f"HTTP {e.code} on {method} {path}: {e.read().decode()}\n")
        raise


def refresh_access_token():
    global access_token, refresh_token
    basic = base64.b64encode(f"{APP_ID}:{APP_SECRET}".encode()).decode()
    body = urllib.parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": refresh_token}
    ).encode()
    req = urllib.request.Request(
        f"{API_ROOT}/oauth/token",
        data=body,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        tokens = json.load(r)
    access_token = tokens["access_token"]
    if tokens.get("refresh_token"):
        refresh_token = tokens["refresh_token"]
    print(f"::notice::Refreshed access token (expires_in={tokens.get('expires_in')})")
    # Emit new tokens for CI to store back as secrets
    print(f"::add-mask::{access_token}")
    print(f"NEW_ACCESS_TOKEN={access_token}")
    if tokens.get("refresh_token"):
        print(f"::add-mask::{refresh_token}")
        print(f"NEW_REFRESH_TOKEN={refresh_token}")


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"posted_pin_ids": [], "board_id_by_name": {}}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def ensure_board(name: str, state: dict) -> str:
    """Return board_id for a board name, creating it if missing."""
    if name in state["board_id_by_name"]:
        return state["board_id_by_name"][name]
    # Search existing boards first
    boards = api("GET", "/boards?page_size=100")
    for b in boards.get("items", []):
        if b["name"].strip().lower() == name.strip().lower():
            state["board_id_by_name"][name] = b["id"]
            return b["id"]
    # Create it
    created = api(
        "POST",
        "/boards",
        {
            "name": name,
            "description": f"Original art prints by Johnny Lemoine — {name.lower()}.",
        },
    )
    state["board_id_by_name"][name] = created["id"]
    print(f"::notice::Created board '{name}' → {created['id']}")
    return created["id"]


def post_pin(pin: dict, state: dict) -> str:
    board_id = ensure_board(pin["board_name"], state)
    body = {
        "board_id": board_id,
        "title": pin["pin_title"][:100],
        "description": pin["pin_description"][:500],
        "link": pin["listing_url"],
        "alt_text": pin["pin_title"][:500],
        "media_source": {"source_type": "image_url", "url": pin["image_url"]},
    }
    result = api("POST", "/pins", body)
    return result["id"]


def main():
    pins = json.loads(PINS_FILE.read_text())
    state = load_state()
    posted_ids = set(state["posted_pin_ids"])
    queue = [p for p in pins if p["pin_id"] not in posted_ids and p.get("image_url")]

    if not queue:
        print("Nothing to post — all pins already published.")
        return

    to_post = queue[:PINS_PER_RUN]
    print(f"Posting {len(to_post)} of {len(queue)} pending pins.")

    for pin in to_post:
        try:
            pinterest_pin_id = post_pin(pin, state)
            state["posted_pin_ids"].append(pin["pin_id"])
            print(f"  ✓ {pin['pin_title']} → {pinterest_pin_id}")
        except Exception as e:
            print(f"  ✗ {pin['pin_title']}: {e}")
        finally:
            save_state(state)


if __name__ == "__main__":
    main()
