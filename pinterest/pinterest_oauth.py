"""
One-shot local Pinterest OAuth flow.

Run: python3 pinterest/pinterest_oauth.py

Requires env vars:
  PINTEREST_APP_ID       — App ID (numeric)
  PINTEREST_APP_SECRET   — App secret key

Steps:
  1. Opens the Pinterest authorize URL in your browser.
  2. Log into the Pinterest account you want the API to post as (@Lemoineart).
  3. Click Approve.
  4. This script catches the redirect on localhost:8080 and exchanges the code
     for an access token + refresh token.
  5. Tokens are printed. Save both as GitHub Secrets:
       PINTEREST_ACCESS_TOKEN
       PINTEREST_REFRESH_TOKEN
"""
import base64
import http.server
import json
import os
import secrets
import socketserver
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

APP_ID = os.environ.get("PINTEREST_APP_ID")
APP_SECRET = os.environ.get("PINTEREST_APP_SECRET")
if not APP_ID or not APP_SECRET:
    sys.exit("Set PINTEREST_APP_ID and PINTEREST_APP_SECRET env vars first.")

REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"
STATE = secrets.token_urlsafe(16)

AUTH_URL = (
    "https://www.pinterest.com/oauth/?"
    + urllib.parse.urlencode(
        {
            "client_id": APP_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "state": STATE,
        }
    )
)

_captured = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        params = urllib.parse.parse_qs(parsed.query)
        _captured["code"] = params.get("code", [None])[0]
        _captured["state"] = params.get("state", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<h1>You can close this tab.</h1>"
            b"<p>Return to your terminal — tokens are printing there.</p>"
        )

    def log_message(self, *args, **kwargs):
        pass  # silence noisy default logging


def exchange_code_for_tokens(code: str) -> dict:
    basic = base64.b64encode(f"{APP_ID}:{APP_SECRET}".encode()).decode()
    body = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.pinterest.com/v5/oauth/token",
        data=body,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    print(f"Opening authorize URL in your browser…")
    print(f"  {AUTH_URL}\n")
    print("Make sure you're logged into @Lemoineart in that browser before approving.\n")

    server = socketserver.TCPServer(("localhost", 8080), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    webbrowser.open(AUTH_URL)

    while "code" not in _captured:
        pass  # wait for callback
    server.shutdown()

    if _captured.get("state") != STATE:
        sys.exit("State mismatch — possible CSRF. Aborting.")
    if not _captured.get("code"):
        sys.exit("No auth code received.")

    tokens = exchange_code_for_tokens(_captured["code"])
    print("=" * 60)
    print("Save these as GitHub repository secrets:")
    print("=" * 60)
    print(f"PINTEREST_ACCESS_TOKEN   = {tokens['access_token']}")
    print(f"PINTEREST_REFRESH_TOKEN  = {tokens.get('refresh_token', '(none returned)')}")
    print(f"Expires in: {tokens.get('expires_in')} seconds")
    print("=" * 60)
    print("\nAlso: regenerate PINTEREST_APP_SECRET on Pinterest since it was")
    print("shared in chat. Update the GitHub Secret with the new value.")


if __name__ == "__main__":
    main()
