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
size are skipped. A download in progress is written to <name>.part and only
renamed once it is whole, so a kill mid-download never leaves a short file
under the real name for a cut to pick up.

Two Inbox files with the same name (two devices, a re-upload) would land on
one local path, so the second is saved as <stem>_<first 6 of its Drive id>.
Clips that have sat in Inbox more than 12 hours are named as leftovers, since
--expect counts everything in Inbox, not only today's uploads.
"""
import argparse
import datetime
import errno
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
    clips = [c for c in d.children(d.INBOX_FOLDER_ID, token) if c.get("size")]
    seen = set()
    for c in clips:   # Drive allows duplicate names; disk does not
        c["local"] = c["name"]
        if c["name"] in seen:
            stem, ext = os.path.splitext(c["name"])
            c["local"] = f"{stem}_{c['id'][:6]}{ext}"
            print(f"  NOTE two Inbox files are named {c['name']}; this one saves as {c['local']}")
        seen.add(c["name"])
    return clips


def listing(tries=4):
    """Inbox, retried: the token request goes through the same proxy that
    cuts downloads off, and one reset must not end the whole run."""
    for attempt in range(1, tries + 1):
        try:
            return inbox(get_token(DEFAULT_KEY))
        except Exception as e:
            print(f"  listing attempt {attempt}: {e}")
            time.sleep(2 * attempt)
    sys.exit("could not list Inbox")


def leftovers(clips, hours=12):
    """Clips uploaded well before today's batch: still to cut, or forgotten."""
    now = datetime.datetime.now(datetime.timezone.utc)
    old = []
    for c in clips:
        t = c.get("createdTime")
        if t and (now - datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))).total_seconds() > hours * 3600:
            old.append(c)
    return old


def fetch(clip, out, tries=4):
    want = int(clip["size"])
    if os.path.exists(out) and os.path.getsize(out) == want:
        print(f"  have  {want:>11}  {clip['name']}")
        return True
    part = out + ".part"
    for attempt in range(1, tries + 1):
        url = (f"https://www.googleapis.com/drive/v3/files/{clip['id']}"
               "?alt=media&supportsAllDrives=true")
        try:
            # the token request is inside the try: it can be reset too
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {get_token(DEFAULT_KEY)}"})
            with urllib.request.urlopen(req) as r, open(part, "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
        except OSError as e:
            if e.errno == errno.ENOSPC:   # a full disk is not a network drop
                if os.path.exists(part):
                    os.remove(part)
                sys.exit(f"  disk full while fetching {clip['name']}: free space (old src/ and cuts already on Drive), then re-run")
            print(f"  attempt {attempt}: {e}")
            time.sleep(2 * attempt)
            continue
        except Exception as e:  # network drop: retry, it is not the file's fault
            print(f"  attempt {attempt}: {e}")
            time.sleep(2 * attempt)
            continue
        got = os.path.getsize(part)
        if got == want:
            os.replace(part, out)
            print(f"  ok    {want:>11}  {clip['name']}")
            return True
        print(f"  attempt {attempt}: short by {want - got} bytes")
        time.sleep(2 * attempt)
    if os.path.exists(part):
        os.remove(part)
    print(f"  FAILED {clip['name']}: never arrived whole", file=sys.stderr)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="folder to download into")
    ap.add_argument("--expect", type=int, default=0, help="wait until this many clips are in Inbox")
    ap.add_argument("--wait-min", type=float, default=20, help="how long --expect may wait")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    clips = listing()
    deadline = time.time() + a.wait_min * 60
    while a.expect and len(clips) < a.expect and time.time() < deadline:
        print(f"  Inbox has {len(clips)} of {a.expect}; waiting for the rest to finish uploading")
        time.sleep(30)
        clips = listing()
    if a.expect and len(clips) < a.expect:
        print(f"  only {len(clips)} of {a.expect} arrived within {a.wait_min} min; fetching those")
    if not clips:
        print("Inbox is empty: nothing to fetch")
        sys.exit(3)
    for c in leftovers(clips):
        print(f"  LEFTOVER {c['name']} has been in Inbox since {c['createdTime'][:16]}Z; "
              "it counts toward --expect but may not be one of today's clips")

    ok = all([fetch(c, os.path.join(a.out, c["local"])) for c in clips])
    print(f"{len(clips)} clip(s) in Inbox, {'all' if ok else 'NOT all'} downloaded whole")
    for c in clips:
        print(f"  {c['local']}")
    if not ok:
        sys.exit(1)
    # fewer than expected is not success: the rest may still be uploading
    sys.exit(2 if a.expect and len(clips) < a.expect else 0)


if __name__ == "__main__":
    main()
