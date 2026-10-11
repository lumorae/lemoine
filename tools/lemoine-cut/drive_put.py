#!/usr/bin/env python3
"""Put finished files into Cut/<flute>/ on Drive: replace in place, never duplicate.

    python3 drive_put.py --flute "Stellar Flute D" thumb1.jpg thumb2.jpg
    python3 drive_put.py --flute "Quena Jayras" --trash 2026-10-07_1654_ ...

The local file's name is its Drive name. If Cut/<flute>/ already holds a file
of that name, its CONTENT is replaced, so the Drive link Johnny may already
have pasted somewhere keeps working. Otherwise it is uploaded new. Every
replace is checked: the size Drive reports must equal the bytes sent.

This is how a hand-made thumbnail replaces the one lemoine_publish.sh files
automatically. Do it only after that publish run has FINISHED: replacing
while the run is still going lets the run's own upload land afterwards as a
second file with the same name.

--trash PREFIX moves every file in the folder whose name starts with PREFIX
to Drive's trash (recoverable for 30 days), for superseded first versions.

Safe to repeat: running it twice changes nothing the second time.
"""
import argparse
import json
import mimetypes
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_index as d  # noqa: E402
from drive_upload import CUT_FOLDER_ID, DEFAULT_KEY, get_token, upload  # noqa: E402


def api(url, token, data=None, method="GET", ctype="application/json"):
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": ctype})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flute", required=True, help="folder under Cut/, as categories.py names it")
    ap.add_argument("--trash", action="append", default=[], help="trash files starting with this")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()

    token = get_token(DEFAULT_KEY)
    folder = next((f for f in d.children(CUT_FOLDER_ID, token) if f["name"] == a.flute), None)
    if not folder:
        sys.exit(f"Cut/{a.flute}/ does not exist on Drive; check the flute name in categories.py")
    have = {}
    for g in d.children(folder["id"], token):
        have.setdefault(g["name"], []).append(g)

    bad = 0
    for path in a.files:
        name = os.path.basename(path)
        data = open(path, "rb").read()
        existing = have.get(name, [])
        if len(existing) > 1:
            print(f"  WARNING {name}: {len(existing)} files share this name; replacing the first, check the rest")
        if existing:
            mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
            r = api(f"https://www.googleapis.com/upload/drive/v3/files/{existing[0]['id']}"
                    "?uploadType=media&supportsAllDrives=true&fields=id,size",
                    token, data=data, method="PATCH", ctype=mime)
            ok = int(r["size"]) == len(data)
            bad += not ok
            print(f"  {'replaced' if ok else 'SIZE MISMATCH'}  {name}  "
                  f"https://drive.google.com/file/d/{r['id']}/view")
        else:
            upload(path, folder["id"], token)

    for prefix in a.trash:
        for name, gs in have.items():
            if name.startswith(prefix):
                for g in gs:
                    api(f"https://www.googleapis.com/drive/v3/files/{g['id']}?supportsAllDrives=true",
                        token, data=json.dumps({"trashed": True}).encode(), method="PATCH")
                    print(f"  trashed   {name}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
