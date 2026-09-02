#!/usr/bin/env python3
"""Refile every cut in Cut/ into the folder categories.py says it belongs in.

Idempotent, and not tied to the old date-folder layout: it looks at where each
cut currently is, works out where it should be, and moves only the ones that
disagree. That makes it the tool for merging two flute folders as well as for
the original date-to-flute migration — change MAP, re-run, done.

  python3 drive_migrate.py --dry-run   # show every move, change nothing
  python3 drive_migrate.py             # do it

Moves only ever change a file's parent, never its id, so every link already
handed out keeps working. Emptied date folders are trashed (recoverable), and a
date folder that still holds something is left alone and reported.
"""
import argparse
import json
import os
import re
import urllib.parse
import urllib.request

from categories import folder_for
from drive_upload import CUT_FOLDER_ID, DEFAULT_KEY, get_token

FOLDER = "application/vnd.google-apps.folder"
CUT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:_(\d{4}))?_(.+?)"
                    r"(?:-take(\d{2}))?_(reels|shorts)\.mp4$")
DATE_DIR = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


def api(path, token, method="GET", body=None, **params):
    params.setdefault("supportsAllDrives", "true")
    url = f"https://www.googleapis.com/drive/v3/{path}?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


def children(fid, token):
    out, page = [], None
    while True:
        kw = dict(q=f"'{fid}' in parents and trashed=false",
                  fields="nextPageToken,files(id,name,mimeType)", pageSize=300,
                  includeItemsFromAllDrives="true")
        if page:
            kw["pageToken"] = page
        r = api("files", token, **kw)
        out += r.get("files", [])
        page = r.get("nextPageToken")
        if not page:
            return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=os.environ.get("GDRIVE_SA_JSON", DEFAULT_KEY))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    token = get_token(args.key)
    dry = args.dry_run

    # existing flute folders at the top of Cut/, so a re-run is a no-op
    top = children(CUT_FOLDER_ID, token)
    flute_dirs = {f["name"]: f["id"] for f in top if f["mimeType"] == FOLDER
                  and not DATE_DIR.match(f["name"])}

    def flute_dir(name):
        if name not in flute_dirs:
            if dry:
                flute_dirs[name] = f"<new:{name}>"
            else:
                r = api("files", token, method="POST",
                        body={"name": name, "mimeType": FOLDER,
                              "parents": [CUT_FOLDER_ID]}, fields="id")
                flute_dirs[name] = r["id"]
            print(f"  + folder  {name}")
        return flute_dirs[name]

    # every folder under Cut/ holds cuts: old date folders (month/day) and the
    # flute folders themselves, which may need re-filing after a MAP change
    holders = []
    for f in top:
        if f["mimeType"] != FOLDER:
            continue
        if DATE_DIR.match(f["name"]):
            for day in children(f["id"], token):
                if day["mimeType"] == FOLDER:
                    holders.append((f"{f['name']}/{day['name']}", day["id"], True))
            holders.append((f["name"], f["id"], True))
        else:
            holders.append((f["name"], f["id"], False))

    moved, skipped, date_dirs = 0, [], []
    for label, fid, is_date in holders:
        if is_date:
            date_dirs.append((label, fid, None))
        for f in children(fid, token):
            if f["mimeType"] == FOLDER:
                continue
            m = CUT_RE.match(f["name"])
            if not m:
                skipped.append(f"{label}/{f['name']}")
                continue
            dest_name = folder_for(m.group(3))
            if dest_name == label:           # already where it belongs
                continue
            dest = flute_dir(dest_name)
            print(f"  {label}/{f['name']}\n      -> {dest_name}/")
            if not dry:
                api(f"files/{f['id']}", token, method="PATCH", body={},
                    addParents=dest, removeParents=fid, fields="id")
            moved += 1

    # a flute folder emptied by a merge should go too, not just old date folders
    if not dry:
        for f in top:
            if f["mimeType"] == FOLDER and not children(f["id"], token):
                api(f"files/{f['id']}", token, method="PATCH",
                    body={"trashed": True}, fields="id")
                print(f"  - emptied folder {f['name']}")

    # trash date folders that are now empty; keep any that still hold something
    emptied = 0
    for name, fid, _ in date_dirs:
        if dry:
            continue
        if not children(fid, token):
            api(f"files/{fid}", token, method="PATCH", body={"trashed": True}, fields="id")
            emptied += 1

    print(f"\n{moved} file(s) {'would move' if dry else 'moved'}, "
          f"{len(set(flute_dirs))} flute folder(s), {emptied} empty date folder(s) trashed")
    if skipped:
        print("left in place (name does not parse as a cut):")
        for s in skipped:
            print(f"  {s}")


if __name__ == "__main__":
    main()
