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
The prefix must be at least a full YYYY-MM-DD_HHMM_ stamp; a file this same
call just replaced or uploaded is never trashed (an empty prefix once meant
"the whole folder", and a replaced thumbnail could be trashed straight after
its replacement); and nothing is trashed if any replace came back wrong.

Cut/INDEX.md is rebuilt afterwards whenever anything changed.

Safe to repeat: running it twice changes nothing the second time.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_index as d  # noqa: E402
from drive_upload import CUT_FOLDER_ID, DEFAULT_KEY, get_token, replace_in_place, trash_id, upload  # noqa: E402

STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{4}_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flute", required=True, help="folder under Cut/, as categories.py names it")
    ap.add_argument("--trash", action="append", default=[], help="trash files starting with this")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    for p in a.trash:
        if not STAMP.match(p):
            sys.exit(f"--trash {p!r}: give at least a full YYYY-MM-DD_HHMM_ stamp")

    token = get_token(DEFAULT_KEY)
    folder = next((f for f in d.children(CUT_FOLDER_ID, token) if f["name"] == a.flute), None)
    if not folder:
        sys.exit(f"Cut/{a.flute}/ does not exist on Drive; check the flute name in categories.py")
    have = {}
    for g in d.children(folder["id"], token):
        have.setdefault(g["name"], []).append(g)

    bad, changed, mine = 0, False, set()
    for path in a.files:
        name = os.path.basename(path)
        mine.add(name)
        existing = have.get(name, [])
        if len(existing) > 1:
            print(f"  WARNING {name}: {len(existing)} files share this name; replacing the first, check the rest")
        if existing:
            fid, ok = replace_in_place(existing[0]["id"], path, token)
            bad += not ok
            print(f"  {'replaced' if ok else 'SIZE MISMATCH'}  {name}  "
                  f"https://drive.google.com/file/d/{fid}/view")
        else:
            # new on Drive: fine when the run's own thumbnail never got made
            # or filed, but check the name against the log's stamp and slug
            upload(path, folder["id"], token)
        changed = True

    if a.trash and bad:
        print("  NOT trashing anything: a replace above came back the wrong size")
    elif a.trash:
        for prefix in a.trash:
            for name, gs in have.items():
                if not name.startswith(prefix):
                    continue
                if name in mine:
                    print(f"  kept      {name}  (just put there by this call)")
                    continue
                for g in gs:
                    trash_id(g["id"], token)
                    print(f"  trashed   {name}")
                    changed = True

    if changed:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, os.path.join(HERE, "drive_index.py"),
                            "--out", os.path.join(tmp, "INDEX.md")], check=False)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
