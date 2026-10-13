"""
One-time setup, run on your laptop: turn a short-lived Facebook login
into a Page token that doesn't expire, and save it to GitHub.

  python3 facebook/get_page_token.py

It asks for three things (input is hidden, nothing is printed back):
  App ID, App Secret   developers.facebook.com > your app > App settings > Basic
  User token           Graph API Explorer > Get User Access Token, with
                       pages_show_list, pages_manage_posts, pages_read_engagement

Then it exchanges the token, finds the Lemoine Page, and stores
FB_PAGE_ID and FB_PAGE_TOKEN as GitHub Actions secrets on lumorae/lemoine
(needs the gh CLI, logged in). Without gh, it writes them to
facebook/tokens.json (gitignored) so you can add them by hand.
"""
import getpass
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

GRAPH = f"https://graph.facebook.com/{os.environ.get('FB_GRAPH_VERSION', 'v23.0')}"
REPO = "lumorae/lemoine"
TOKEN_FILE = Path(__file__).parent / "tokens.json"
NEEDED = {"pages_show_list", "pages_manage_posts", "pages_read_engagement"}


def get(path: str, **params) -> dict:
    url = f"{GRAPH}{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Facebook said no ({e.code}): {e.read().decode()}")


def ask(label: str, env: str) -> str:
    return os.environ.get(env) or getpass.getpass(f"{label}: ").strip()


def main():
    app_id = ask("App ID", "FB_APP_ID")
    app_secret = ask("App Secret", "FB_APP_SECRET")
    short_token = ask("User token from Graph API Explorer", "FB_USER_TOKEN")

    long_user = get(
        "/oauth/access_token",
        grant_type="fb_exchange_token",
        client_id=app_id,
        client_secret=app_secret,
        fb_exchange_token=short_token,
    )["access_token"]

    granted = {p["permission"] for p in get("/me/permissions", access_token=long_user)["data"]
               if p["status"] == "granted"}
    missing = NEEDED - granted
    if missing:
        sys.exit(f"The token is missing {', '.join(sorted(missing))}. "
                 "Add them in Graph API Explorer, generate a new token and run this again.")

    pages = get("/me/accounts", access_token=long_user, fields="id,name,access_token")["data"]
    if not pages and os.environ.get("FB_PAGE_ID"):
        # Pages owned by a business portfolio can be missing from /me/accounts
        # but still answer when asked for by id.
        pages = [get(f"/{os.environ['FB_PAGE_ID']}", access_token=long_user,
                     fields="id,name,access_token")]
    if not pages:
        sys.exit("No Pages came back. In the Facebook login dialog, make sure the Lemoine Page is ticked.")
    matches = [p for p in pages if "lemoine" in p["name"].lower()]
    if len(matches) == 1:
        page = matches[0]
    else:
        for i, p in enumerate(pages, 1):
            print(f"  {i}. {p['name']}")
        page = pages[int(input("Which Page? ")) - 1]
    print(f"Using Page: {page['name']} ({page['id']})")

    # A Page token issued from a long-lived user token has no expiry.
    expires = get("/debug_token", input_token=page["access_token"],
                  access_token=f"{app_id}|{app_secret}")["data"].get("expires_at")
    print("Page token expires: never" if not expires else f"Page token expires at {expires}")

    # Only use gh if it's logged in, so a missing login can't lose the token.
    gh_ready = shutil.which("gh") and subprocess.run(
        ["gh", "auth", "status"], capture_output=True).returncode == 0
    if gh_ready:
        for name, value in (("FB_PAGE_ID", page["id"]), ("FB_PAGE_TOKEN", page["access_token"])):
            subprocess.run(["gh", "secret", "set", name, "-R", REPO], input=value.encode(), check=True)
        print(f"Saved FB_PAGE_ID and FB_PAGE_TOKEN as secrets on {REPO}.")
    else:
        TOKEN_FILE.write_text(json.dumps({"FB_PAGE_ID": page["id"], "FB_PAGE_TOKEN": page["access_token"]}, indent=2))
        TOKEN_FILE.chmod(0o600)
        print(f"gh isn't installed or logged in, so the values are in {TOKEN_FILE}.")
        print(f"Add both as secrets at https://github.com/{REPO}/settings/secrets/actions, then delete the file.")


if __name__ == "__main__":
    main()
