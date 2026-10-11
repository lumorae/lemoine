#!/usr/bin/env python3
"""Download every clip in Drive Inbox/ into a work folder, proving each arrived whole.

    python3 fetch_inbox.py --out /home/user/work/<day>/src
    python3 fetch_inbox.py --out ... --expect 5     # wait until 5 clips are in Inbox

Why this exists. A plain download through the session proxy can be cut off
partway: the file lands short, and an iPhone .MOV truncated before its
trailing moov atom will not open, yet looks like an ordinary file. On
2026-09-27 three of six downloads arrived short, one by a full megabyte. So
every file is checked against the size Drive reports and a short read is
retried, never trusted.

Johnny often asks for a cut while his phone is still uploading. --expect N
polls Inbox until N clips are there (or --wait-min runs out) before
downloading, rather than cutting whatever happened to have landed.

Safe to re-run after a container restart: clips already on disk at the right
size are skipped.
"""
import argparse
import os
import shutil
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_index as d  # noqa: E402
from drive_upload import DEFAULT_KEY, get_token  # noqa: E402


def inbox(token):
    return [c for c in d.children(d.INBOX_FOLDER_ID, token) if c.get("size")]


def fetch(clip, out, tries=4):
    want = int(clip["size"])
    if os.path.exists(out) and os.path.getsize(out) == want:
        print(f"  have  {want:>11}  {clip['name']}")
        return True
    for attempt in range(1, tries + 1):
        url = (f"https://www.googleapis.com/drive/v3/files/{clip['id']}"
               "?alt=media&supportsAllDrives=true")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {get_token(DEFAULT_KEY)}"})
        try:
            with urllib.request.urlopen(req) as r, open(out, "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
        except Exception as e:  # network drop: retry, it is not the file's fault
            print(f"  attempt {attempt}: {e}")
            time.sleep(2 * attempt)
            continue
        got = os.path.getsize(out)
        if got == want:
            print(f"  ok    {want:>11}  {clip['name']}")
            return True
        print(f"  attempt {attempt}: short by {want - got} bytes")
        time.sleep(2 * attempt)
    print(f"  FAILED {clip['name']}: never arrived whole", file=sys.stderr)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="folder to download into")
    ap.add_argument("--expect", type=int, default=0, help="wait until this many clips are in Inbox")
    ap.add_argument("--wait-min", type=float, default=20, help="how long --expect may wait")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    token = get_token(DEFAULT_KEY)
    clips = inbox(token)
    deadline = time.time() + a.wait_min * 60
    while a.expect and len(clips) < a.expect and time.time() < deadline:
        print(f"  Inbox has {len(clips)} of {a.expect}; waiting for the rest to finish uploading")
        time.sleep(30)
        clips = inbox(get_token(DEFAULT_KEY))
    if a.expect and len(clips) < a.expect:
        print(f"  only {len(clips)} of {a.expect} arrived within {a.wait_min} min; fetching those")

    ok = all([fetch(c, os.path.join(a.out, c["name"])) for c in clips])
    print(f"{len(clips)} clip(s) in Inbox, {'all' if ok else 'NOT all'} downloaded whole")
    if not ok:
        sys.exit(1)
    # fewer than expected is not success: the rest may still be uploading
    sys.exit(2 if a.expect and len(clips) < a.expect else 0)


if __name__ == "__main__":
    main()
