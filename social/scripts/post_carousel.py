#!/usr/bin/env python3
"""Publish a mixed photo+video carousel to Instagram (Instagram Login / graph.instagram.com).

Usage:
    python3 post_carousel.py manifest.json

manifest.json:
{
  "caption": "…",
  "items": [
    {"url": "https://raw.githubusercontent.com/.../01.png", "type": "image"},
    {"url": "https://raw.githubusercontent.com/.../02.mp4", "type": "video"},
    ...
  ]
}

Token is read from tok.txt in the same dir. Order of items == order in the carousel.
"""
import json, sys, time, urllib.parse, urllib.request

IGID = "17841401720504053"
BASE = "https://graph.instagram.com/v21.0"
TOKEN = open("tok.txt").read().strip()

def api(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        url = f"{BASE}/{path}?{data.decode()}"
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(f"{BASE}/{path}", data=data, method="POST")
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{path} -> {e.code}: {e.read().decode()}")

def make_child(item):
    p = {"is_carousel_item": "true"}
    if item["type"] == "video":
        p["media_type"] = "VIDEO"; p["video_url"] = item["url"]
    else:
        p["image_url"] = item["url"]
    cid = api("POST", f"{IGID}/media", **p)["id"]
    print(f"  child created: {cid} ({item['type']})")
    return cid, item["type"]

def wait_ready(cid):
    for _ in range(40):  # up to ~6.5 min
        st = api("GET", cid, fields="status_code")["status_code"]
        if st == "FINISHED": return
        if st == "ERROR": raise RuntimeError(f"container {cid} processing ERROR")
        time.sleep(10)
    raise RuntimeError(f"container {cid} not FINISHED in time")

def main(manifest_path):
    m = json.load(open(manifest_path))
    children = []
    for i, item in enumerate(m["items"], 1):
        print(f"[{i}/{len(m['items'])}] {item['type']}: {item['url']}")
        cid, typ = make_child(item)
        children.append((cid, typ))
    # videos need to finish processing before the parent is created
    for cid, typ in children:
        if typ == "video":
            print(f"  waiting for video {cid} to finish…"); wait_ready(cid)
    parent = api("POST", f"{IGID}/media", media_type="CAROUSEL",
                 children=",".join(c for c, _ in children), caption=m["caption"])["id"]
    print(f"carousel container: {parent}")
    wait_ready(parent)
    pub = api("POST", f"{IGID}/media_publish", creation_id=parent)
    print(f"PUBLISHED: {json.dumps(pub)}")
    live = api("GET", pub["id"], fields="permalink")
    print(f"LIVE AT: {live.get('permalink')}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "manifest.json")
