"""
The Page access token to post and read with.

FB_PAGE_TOKEN may be a Page token, or a token for the "Lemoine Poster"
system user in Business settings. System user tokens never expire and
aren't tied to anyone's Facebook login, so password changes and session
resets don't break posting; Facebook still wants a Page token for Page
calls, so it's looked up here each run. A Page token answers the same
lookup with itself.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from functools import cache

GRAPH = f"https://graph.facebook.com/{os.environ.get('FB_GRAPH_VERSION', 'v23.0')}"


@cache
def page_token() -> str:
    token = os.environ["FB_PAGE_TOKEN"]
    url = f"{GRAPH}/{os.environ['FB_PAGE_ID']}?" + urllib.parse.urlencode(
        {"fields": "access_token", "access_token": token})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r).get("access_token") or token
    except urllib.error.HTTPError:
        # Let the real call fail with Facebook's own message.
        return token
