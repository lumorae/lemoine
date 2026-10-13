#!/usr/bin/env python3
"""Move already-cut originals out of Inbox, so Inbox means "still to cut".

  python3 drive_tidy_inbox.py --dry-run   # show what would move
  python3 drive_tidy_inbox.py             # do it

Inbox fills up with every clip ever filmed, cut and uncut alike, so the one
question it should answer — what still needs cutting — is the one it cannot.
Anything with a finished cut moves to Source/<Flute>/, filed the same way the
cuts are, and what stays behind is the to-do list.

A source is matched to its cut by normalising both to the same loose key, so
"High Spirits — High Kestrel in D (01)" finds the cut it produced. Where a
source has no cut, it stays put — that is the whole point. Moves only ever
change a file's parent, so shared links keep working.
"""
import argparse
import json
import os
import re
import urllib.parse
import urllib.request

from drive_index import CUT_RE, INBOX_FOLDER_ID, children, norm
from drive_upload import CUT_FOLDER_ID, DEFAULT_KEY, get_token

FOLDER = "application/vnd.google-apps.folder"
SOURCE_DIR = "Source"


def api(path, token, method="GET", body=None, **params):
    params.setdefault("supportsAllDrives", "true")
    url = f"https://www.googleapis.com/drive/v3/{path}?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=os.environ.get("GDRIVE_SA_JSON", DEFAULT_KEY))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    token, dry = get_token(args.key), args.dry_run

    # where the finished cuts live tells us where each source belongs — this is
    # ground truth, rather than re-deriving the flute from the source name
    cut_home = {}
    for flute in children(CUT_FOLDER_ID, token):
        if flute["mimeType"] != FOLDER:
            continue
        for f in children(flute["id"], token):
            m = CUT_RE.match(f["name"])
            if m:
                cut_home[norm(m.group("slug"))] = flute["name"]

    kit = api(f"files/{INBOX_FOLDER_ID}", token, fields="parents")["parents"][0]
    existing = {f["name"]: f["id"] for f in children(kit, token) if f["mimeType"] == FOLDER}
    source_root = existing.get(SOURCE_DIR)
    if source_root is None:
        if dry:
            source_root = f"<new:{SOURCE_DIR}>"
        else:
            source_root = api("files", token, method="POST", fields="id",
                              body={"name": SOURCE_DIR, "mimeType": FOLDER,
                                    "parents": [kit]})["id"]
        print(f"  + {SOURCE_DIR}/")

    sub = {f["name"]: f["id"] for f in
           ([] if isinstance(source_root, str) and source_root.startswith("<new")
            else children(source_root, token)) if f["mimeType"] == FOLDER}

    def flute_dir(name):
        if name not in sub:
            if dry:
                sub[name] = f"<new:{name}>"
            else:
                sub[name] = api("files", token, method="POST", fields="id",
                                body={"name": name, "mimeType": FOLDER,
                                      "parents": [source_root]})["id"]
            print(f"  + {SOURCE_DIR}/{name}/")
        return sub[name]

    moved, staying = 0, []
    for f in children(INBOX_FOLDER_ID, token):
        if f["mimeType"] == FOLDER:
            continue
        home = cut_home.get(norm(f["name"]))
        if not home:
            staying.append(f["name"])
            continue
        dest = flute_dir(home)
        print(f"  {f['name']}\n      -> {SOURCE_DIR}/{home}/")
        if not dry:
            api(f"files/{f['id']}", token, method="PATCH", body={},
                addParents=dest, removeParents=INBOX_FOLDER_ID, fields="id")
        moved += 1

    print(f"\n{moved} original(s) {'would move' if dry else 'moved'} to {SOURCE_DIR}/")
    if staying:
        print(f"Inbox keeps {len(staying)} clip(s) with no cut yet — the to-do list:")
        for n in staying:
            print(f"  - {n}")
    else:
        print("Inbox is empty: everything filmed has been cut.")


if __name__ == "__main__":
    main()
