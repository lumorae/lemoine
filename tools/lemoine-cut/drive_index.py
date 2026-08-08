#!/usr/bin/env python3
"""Build a searchable index of every lemoine cut, and show what's still raw.

Day folders are great for "what did I ship today" and useless for "where's
that Spanish cedar clip from a few weeks ago". This walks the Drive tree and
writes one INDEX.md at the top of Cut/ that answers both, plus a To cut list
built by diffing Inbox against the cuts that already exist.

  python3 drive_index.py            # rebuild and upload Cut/INDEX.md
  python3 drive_index.py --dry-run  # print it, upload nothing
"""
import argparse
import json
import os
import re
import urllib.parse
import urllib.request

from drive_upload import CUT_FOLDER_ID, DEFAULT_KEY, get_token, upload

INBOX_FOLDER_ID = "12kmLXP1WCXCw7qFOeR2GtjqzYb9uMcpn"
FOLDER_MIME = "application/vnd.google-apps.folder"

# YYYY-MM-DD[_HHMM]_slug[-takeNN]_platform.mp4
CUT_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?:_(?P<time>\d{4}))?"
    r"_(?P<slug>.+?)"
    r"(?:-take(?P<take>\d{2}))?"
    r"_(?P<platform>reels|shorts)\.mp4$")


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
                  fields="nextPageToken,files(id,name,mimeType,size)",
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
    """Walk Cut/YYYY-MM/YYYY-MM-DD/ and return one record per finished cut."""
    cuts, strays = [], []
    for month in children(CUT_FOLDER_ID, token):
        if month["mimeType"] != FOLDER_MIME:
            strays.append(month)
            continue
        for day in children(month["id"], token):
            if day["mimeType"] != FOLDER_MIME:
                strays.append(day)
                continue
            for f in children(day["id"], token):
                m = CUT_RE.match(f["name"])
                if not m:
                    strays.append(f)
                    continue
                cuts.append(dict(
                    **m.groupdict(), id=f["id"], name=f["name"],
                    mb=int(f.get("size") or 0) / 1e6,
                    month=month["name"], day=day["name"]))
    return cuts, strays


def render(cuts, strays, uncut):
    """The index itself: newest first, one row per clip, links included."""
    lines = ["# lemoine cuts — index", ""]
    lines += [f"{len(cuts)} cuts across {len({c['day'] for c in cuts})} shoot days. "
              "Rebuild with `python3 drive_index.py`.", ""]

    if uncut:
        lines += ["## To cut", "",
                  "Raw clips in Inbox with no matching cut yet.", ""]
        lines += [f"- {name}" for name in uncut] + [""]

    # one section per day, newest first; clips grouped so takes sit together
    lines += ["## Cuts", ""]
    for day in sorted({c["day"] for c in cuts}, reverse=True):
        lines += [f"### {day}", ""]
        lines += ["| clip | take | platform | size | link |",
                  "|---|---|---|---|---|"]
        rows = sorted((c for c in cuts if c["day"] == day),
                      key=lambda c: (c["slug"], c["take"] or "", c["platform"]))
        for c in rows:
            title = c["slug"].replace("-", " ")
            link = f"https://drive.google.com/file/d/{c['id']}/view"
            lines.append(f"| {title} | {c['take'] or '—'} | {c['platform']} "
                         f"| {c['mb']:.0f} MB | [open]({link}) |")
        lines.append("")

    if strays:
        lines += ["## Not filed", "",
                  "Files that don't match the naming scheme or sit outside a "
                  "day folder — worth a look.", ""]
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
        # replace the previous index rather than piling up copies
        from drive_upload import trash_exact
        trash_exact(os.path.basename(args.out), CUT_FOLDER_ID, token)
        upload(args.out, CUT_FOLDER_ID, token)


if __name__ == "__main__":
    main()
