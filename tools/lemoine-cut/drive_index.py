#!/usr/bin/env python3
"""Build a searchable index of every lemoine cut, and show what's still raw.

Cuts are filed one folder per flute, so Drive already answers "every take of
the Spanish cedar". This adds the view a folder tree cannot: one page listing
every cut with its date and a direct link, plus a To cut list built by diffing
Inbox against the cuts that already exist.

  python3 drive_index.py            # rebuild and upload Cut/INDEX.md
  python3 drive_index.py --dry-run  # print it, upload nothing
"""
import argparse
import json
import os
import re
import urllib.parse
import urllib.request

from drive_upload import CUT_FOLDER_ID, DEFAULT_KEY, get_token, replace_in_place, trash_id, upload

INBOX_FOLDER_ID = "12kmLXP1WCXCw7qFOeR2GtjqzYb9uMcpn"
FOLDER_MIME = "application/vnd.google-apps.folder"

# YYYY-MM-DD[_HHMM]_slug[-takeNN]_platform.mp4
#
# "youtube" is the long-form landscape cut: a full 20-minute take at 1920x1080
# rather than one of the vertical clips. It is listed here so a long-form
# render counts as a cut instead of falling through to "Not filed" — the index
# reports what is in Cut/, and a piece that took an hour to render should not
# read as a stray file someone left lying around.
CUT_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?:_(?P<time>\d{4}))?"
    r"_(?P<slug>.+?)"
    r"(?:-take(?P<take>\d{2}))?"
    r"_(?P<platform>reels|shorts|youtube)\.mp4$")


def api(path, token, **params):
    params.setdefault("supportsAllDrives", "true")
    params.setdefault("includeItemsFromAllDrives", "true")
    url = f"https://www.googleapis.com/drive/v3/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    return json.load(urllib.request.urlopen(req))


def children(folder_id, token):
    """Every non-trashed child of a folder, following pagination."""
    out, page = [], None
    while True:
        kw = dict(q=f"'{folder_id}' in parents and trashed=false",
                  fields="nextPageToken,files(id,name,mimeType,size,createdTime)",
                  pageSize=200, orderBy="name")
        if page:
            kw["pageToken"] = page
        res = api("files", token, **kw)
        out += res.get("files", [])
        page = res.get("nextPageToken")
        if not page:
            return out


def norm(text):
    """Loose key for matching a raw source against an already-cut slug.

    "F#" survives as "f" in some slugs and "f-sharp" in others depending on
    how the clip was named, so sharps are dropped in both spellings — the key
    only has to be stable, not readable.
    """
    text = re.sub(r"\.(mov|mp4|m4v)$", "", text, flags=re.I)
    text = re.sub(r"[\s_-]*\(?\[?(?:take[\s_-]*)?#?\d{1,2}\)?\]?\s*$", "", text)
    text = re.sub(r"#|\bsharp\b", "", text.lower())
    return re.sub(r"[^a-z0-9]+", "", text)


def collect(token):
    """Walk Cut/<Flute>/ and return one record per finished cut.

    A cut's thumbnail (same name, _thumb.jpg in place of _shorts.mp4) is its
    companion, shown on the cut's row, not a stray: once every short had one,
    the "Not filed" list was mostly thumbnails and stopped being worth reading.
    A short without one shows "none", which is the thing to look for."""
    cuts, strays = [], []
    for flute in children(CUT_FOLDER_ID, token):
        if flute["mimeType"] != FOLDER_MIME:
            if flute["name"] != "INDEX.md":
                strays.append(flute)
            continue
        files = children(flute["id"], token)
        thumbs = {f["name"]: f for f in files if f["name"].endswith("_thumb.jpg")}
        used = set()
        for f in files:
            if f["name"] in thumbs:
                continue
            m = CUT_RE.match(f["name"])
            if not m:
                strays.append(f)
                continue
            t = thumbs.get(f["name"].rsplit("_", 1)[0] + "_thumb.jpg")
            if t:
                used.add(t["name"])
            cuts.append(dict(
                **m.groupdict(), id=f["id"], name=f["name"], thumb=t and t["id"],
                mb=int(f.get("size") or 0) / 1e6, flute=flute["name"]))
        strays += [t for n, t in thumbs.items() if n not in used]
    return cuts, strays


def render(cuts, strays, uncut):
    """The index itself: newest first, one row per clip, links included."""
    lines = ["# lemoine cuts — index", ""]
    lines += [f"{len(cuts)} cuts across {len({c['flute'] for c in cuts})} flutes. "
              "Rebuild with `python3 drive_index.py`.", ""]

    if uncut:
        lines += ["## To cut", "",
                  "Raw clips in Inbox with no matching cut yet.", ""]
        lines += [f"- {name}" for name in uncut] + [""]

    # one section per flute, newest take first inside each
    lines += ["## Cuts", ""]
    for flute in sorted({c["flute"] for c in cuts}):
        rows = sorted((c for c in cuts if c["flute"] == flute),
                      key=lambda c: (c["date"], c["time"] or "", c["platform"]),
                      reverse=True)
        lines += [f"### {flute}  ({len(rows)})", ""]
        lines += ["| date | title | take | platform | size | link | thumbnail |",
                  "|---|---|---|---|---|---|---|"]
        for c in rows:
            when = c["date"] + (f" {c['time'][:2]}:{c['time'][2:]}" if c["time"] else "")
            link = f"https://drive.google.com/file/d/{c['id']}/view"
            # Shorts thumbnails began 2026-09-21 and were never back-filled
            # (Johnny: the template applies going forward), so "none" flags
            # only the shorts that should have one.
            thumb = (f"[open](https://drive.google.com/file/d/{c['thumb']}/view)" if c["thumb"]
                     else ("none" if c["platform"] == "shorts" and c["date"] >= "2026-09-21" else ""))
            lines.append(f"| {when} | {c['slug'].replace('-', ' ')} | {c['take'] or ''} "
                         f"| {c['platform']} | {c['mb']:.0f} MB | [open]({link}) | {thumb} |")
        lines.append("")

    if strays:
        lines += ["## Not filed", "",
                  "Files that don't match the naming scheme or sit loose at "
                  "the top of Cut/ — worth a look.", ""]
        lines += [f"- {f['name']}" for f in strays] + [""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=os.environ.get("GDRIVE_SA_JSON", DEFAULT_KEY))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="INDEX.md")
    args = ap.parse_args()

    token = get_token(args.key)
    cuts, strays = collect(token)

    cut_keys = {norm(c["slug"]) for c in cuts}
    uncut = [f["name"] for f in children(INBOX_FOLDER_ID, token)
             if f["mimeType"] != FOLDER_MIME and norm(f["name"]) not in cut_keys]

    text = render(cuts, strays, uncut)
    with open(args.out, "w") as fh:
        fh.write(text)
    print(text if args.dry_run else
          f"{len(cuts)} cuts, {len(uncut)} still to cut, {len(strays)} unfiled")

    if not args.dry_run:
        # Overwrite the index in place, so its link never changes and there is
        # never a moment with no index (this used to trash it, then upload a
        # new file: a new link every rebuild, and none at all if the container
        # died in between). Duplicates left by the old way are trashed.
        name = os.path.basename(args.out)
        same = [f for f in children(CUT_FOLDER_ID, token) if f["name"] == name]
        if same:
            replace_in_place(same[0]["id"], args.out, token)
            for extra in same[1:]:
                trash_id(extra["id"], token)
        else:
            upload(args.out, CUT_FOLDER_ID, token)


if __name__ == "__main__":
    main()
