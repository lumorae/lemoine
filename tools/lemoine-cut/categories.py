#!/usr/bin/env python3
"""Which flute a cut belongs to.

The first version derived a folder name from each file name. That reliably
drifts, because the same instrument gets typed differently every week —
"Drone in F#", "Double Drone in F#" and "Double Flute in F#" turned out to be
one flute, and so did "Drone Flute Gm", "Drone Flute G" and "Double Nova Drone
G". Deriving a name per clip meant every new phrasing silently invented a
folder, and the mess had to be merged by hand afterwards.

So the flutes are listed here instead. There are only a handful of them, they
change rarely, and Johnny is the only one who knows which name means which
instrument. A clip is matched against the list; anything the list cannot
place goes to UNSORTED and says so, rather than inventing a folder. A wrong
guess is worse than an obvious question.

Matching is by key first, since each flute has one, then by a distinguishing
word where a key is shared — F# covers both the Spirit Flute and the double,
and D covers both the High Kestrel and the Stellar shaker.

    python3 categories.py "slug::title"     # what would this be filed as
    python3 categories.py --audit           # check the list against Drive
"""
import re

UNSORTED = "Unsorted"

# key       — the key(s) this flute sounds in; mode is ignored, so G covers Gm
# needs     — at least one of these words must appear (only where a key is shared)
# not_      — any of these words rules it out
FLUTES = [
    {
        "folder": "High Spirits Double F#",
        "key": {"F#", "F"},   # a slug loses the "#", and there is no F natural
        "not_": ["spirit flute"],
        "note": "the crossbow-shaped traditional double — drone + melody chambers",
    },
    {
        "folder": "Spirit Flute F#",
        "key": {"F#", "F"},
        "needs": ["spirit flute"],   # "spirit" alone also matches the maker
        "note": "the other F#; not the double",
    },
    {
        "folder": "High Spirits Nova G",
        "key": {"G"},
        "note": "Nova double — the only G flute, so every G and Gm lands here",
    },
    {
        "folder": "Ebonized Walnut A",
        "key": {"A"},
        "note": "the only A flute",
    },
    {
        "folder": "High Kestrel D",
        "key": {"D"},
        "needs": ["kestrel"],
    },
    {
        "folder": "Shaker and Flute D",
        "key": {"D"},
        "needs": ["shaker", "stellar"],
        "note": "Stellar Flutes, not High Spirits",
    },
    {
        "folder": "Spanish Cedar 432Hz",
        "keyless": ["spanish cedar", "432"],
        "note": "tuned to 432Hz, so it carries no letter key",
    },
    {
        "folder": "Shakuhachi",
        "keyless": ["shakuhachi"],
    },
]

# Last-resort overrides, for a clip whose file name simply lacks the
# information a rule would need. "Drone in Mexico City" names no key; it was
# identified as G minor by measuring the recording, and Johnny confirmed the
# Gm clips are the Nova.
MAP = {
    "drone-in-mexico-city": "High Spirits Nova G",
}

# The publish script capitalises the key and nothing else, so an uppercase
# letter in a finished title IS the key — no guessing needed.
KEY_IN_TITLE = re.compile(r"\b([A-G])(#|b)?")
# Falling back to the slug, where "#" has been stripped: "...-in-f-sharp-..."
KEY_IN_SLUG = re.compile(r"(?:^|-)(?:in-)?([a-g])(?:-(sharp|flat))?(?:m)?(?=-|$)")


def _has(hay, phrase):
    """Whole-word phrase test.

    A plain substring test is not enough: the maker is "High Spirits", so
    looking for "spirit" finds it in every title and would file the whole
    catalogue as the Spirit Flute.
    """
    return re.search(rf"\b{re.escape(phrase)}\b", hay) is not None


def key_of(slug, title=None):
    """The flute's key, normalised — mode dropped, so Gm reads as G."""
    if title:
        m = KEY_IN_TITLE.search(title)
        if m:
            return m.group(1) + (m.group(2) or "")
    m = KEY_IN_SLUG.search(slug)
    if m:
        acc = {"sharp": "#", "flat": "b"}.get(m.group(2) or "", "")
        return m.group(1).upper() + acc
    return None


def folder_for(slug, title=None):
    """The folder this cut belongs in, or UNSORTED if the list can't place it."""
    if slug in MAP:
        return MAP[slug]
    hay = f"{slug} {title or ''}".lower().replace("-", " ")

    # a flute with no key is identified by name alone
    for f in FLUTES:
        if any(_has(hay, w) for w in f.get("keyless", [])):
            return f["folder"]

    key = key_of(slug, title)
    if not key:
        return UNSORTED

    candidates = []
    for f in FLUTES:
        if key not in f.get("key", ()):
            continue
        if any(_has(hay, w) for w in f.get("not_", [])):
            continue
        needs = f.get("needs")
        if needs and not any(_has(hay, w) for w in needs):
            continue
        candidates.append(f["folder"])

    # exactly one flute fits, or we don't guess
    return candidates[0] if len(candidates) == 1 else UNSORTED


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if args and args[0] == "--audit":
        for f in FLUTES:
            k = "/".join(sorted(f.get("key", ()))) or "no key"
            print(f"  {f['folder']:<26} {k:<8} {f.get('note','')}")
        raise SystemExit
    for a in args:
        slug, _, title = a.partition("::")
        print(f"{a}\n    -> {folder_for(slug, title or None)}")
