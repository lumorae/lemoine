#!/usr/bin/env python3
"""Which flute a cut belongs to — the folder it gets filed under.

Cuts used to be filed by shoot date, which answers "what shipped today" and
nothing else. There are only so many flutes, so the same instrument comes back
week after week under slightly different names: "High Spirits — Ebonized Walnut
in A" one day, "Ebonized Walnut Flute in A [San Diego]" the next. Filing by
flute puts every take of one instrument in one place.

MAP is the authority, because only Johnny knows which names are the same
physical flute — "Drone in F#" and "Double Drone in F#" look like a typo apart
and are two different instruments. Anything not in MAP falls back to a derived
name, which is a reasonable guess and easy to correct: add the slug to MAP and
re-run the migration.
"""
import re

# cut slug -> flute folder
MAP = {
    "double-drone-flute-in-f-san-diego":     "Double Drone F#",
    "high-spirits-double-drone-in-f":        "Double Drone F#",
    "double-flute-in-f-san-diego":           "Double Flute F#",
    # "Drone in F#" is a different instrument from "Double Drone in F#"
    "high-spirits-drone-in-f":               "Drone F#",
    "high-spirits-double-nova-drone-in-g":   "Double Nova Drone G",
    # the untitled Mexico City drone measured G minor, same flute as the titled one
    "drone-flute-in-gm-mexico-city":         "Drone Flute Gm",
    "drone-in-mexico-city":                  "Drone Flute Gm",
    "ebonized-walnut-flute-in-a-san-diego":  "Ebonized Walnut A",
    "high-spirits-ebonized-walnut-in-a":     "Ebonized Walnut A",
    "high-spirits-432hz-in-spanish-cedar":   "Spanish Cedar 432Hz",
    "high-spirits-432hz-spanish-cedar":      "Spanish Cedar 432Hz",
    "high-spirits-high-kestrel-in-d":        "High Kestrel D",
    "high-spirits-spirit-flute-in-f":        "Spirit Flute F#",
    "high-spirits-spirit-flute-in-f-sharp":  "Spirit Flute F#",
    "stellar-flutes-shaker-and-flute-in-d":  "Shaker and Flute D",
    "shakuhachi-in-san-diego":               "Shakuhachi",
    "learning-the-shakuhachi":               "Shakuhachi",
    "learning-shakuhachi-with-my-cat-sammy": "Shakuhachi",
}

MAKERS = ("high-spirits", "stellar-flutes")
PLACES = ("san-diego", "mexico-city", "cdmx", "oaxaca")
NOTE = re.compile(r"^(?:[a-g](?:-sharp|-flat|b|#)?|\d+hz)$", re.I)


def derive(slug):
    """Best guess at a flute name for a slug that is not in MAP."""
    parts = [p for p in slug.split("-") if p]
    for maker in MAKERS:                       # drop the maker prefix
        m = maker.split("-")
        if parts[:len(m)] == m:
            parts = parts[len(m):]
    for place in PLACES:                       # drop a trailing location
        p = place.split("-")
        if parts[-len(p):] == p:
            parts = parts[:-len(p)]
    if parts and parts[0] == "learning":       # "learning the shakuhachi"
        parts = parts[1:]
        if parts and parts[0] == "the":
            parts = parts[1:]
    parts = [p for p in parts if p != "in"]    # "... in D" -> "... D"
    # slugify splits "F#" into either "f" or "f-sharp"; rejoin the latter
    merged = []
    for p in parts:
        if p in ("sharp", "flat") and merged and len(merged[-1]) == 1:
            merged[-1] += "#" if p == "sharp" else "b"
        else:
            merged.append(p)
    parts = merged
    out = []
    for p in parts:
        # a key or a tuning keeps musical casing: F#, Bb, 432Hz — never BB
        if NOTE.match(p):
            if p.lower().endswith("hz"):
                out.append(p[:-2] + "Hz")
            else:
                n = p.replace("-sharp", "#").replace("-flat", "b")
                out.append(n[0].upper() + n[1:].lower())
        else:
            out.append(p.capitalize())
    return " ".join(out) or slug


def folder_for(slug):
    return MAP.get(slug) or derive(slug)


if __name__ == "__main__":
    import sys
    for s in sys.argv[1:]:
        print(f"{s}  ->  {folder_for(s)}")
