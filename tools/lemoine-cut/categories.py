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
and D covers three: the High Kestrel, the Stellar shaker and the sacral
chakra flute. A shared key is therefore never enough on its own; a clip whose
name carries no distinguishing word goes to UNSORTED rather than to whichever
flute happens to be listed first.

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
        # Measured: the drone chamber sits at 370.1 Hz, F#4 within half a cent
        # of A440, with clean partials at 740 and 1110 Hz. An older note had
        # it at 184 Hz, an octave low; verify against a recording, not notes.
        #
        # 2026-10-14: two San Diego garden takes agree. The drone peaks at
        # 366 Hz in both, and the spectrum at 185 Hz sits 37-40 dB under it:
        # there is no F#3. measure.py still reported "lowest 182-184 Hz",
        # because the drone and a C# melody note a fifth above it repeat
        # together every 1/185 s and the pitch tracker reads that shared
        # period as a note. That is where the old 184 Hz came from too. With
        # three takes putting the lowest real sound at 366-370 Hz, the low cut
        # below sits an octave under the drone and only removes the ~95 Hz
        # garden rumble those takes carry.
        "note": "the crossbow-shaped traditional double — drone + melody chambers",
        "lowcut": 180,   # an octave under the 366-370Hz drone; three takes
    },
    {
        "folder": "Spirit Flute F#",
        "key": {"F#", "F"},
        "needs": ["spirit flute"],   # "spirit" alone also matches the maker
        # Single chamber, reddish wood, carved spiral/flame marks down the body.
        # Measured 2026-10-12 on three takes (two September garden cuts and the
        # October "after a storm" take): best fit A4 436.9-440.8, notes F#, A,
        # B, C#, E (F# minor pentatonic), lowest sustained 366-369 Hz, F#4.
        # An older transcript figure of 360.7 Hz was never tied to this flute.
        "note": "the other F#; not the double; F# minor pentatonic near A440",
        "lowcut": 180,   # an octave under the 366-369Hz bottom note, three takes
    },
    {
        "folder": "High Spirits Nova G",
        "key": {"G"},
        # The quenas are G too, but they are matched by name ("quena",
        # "jayras") before keys are looked at, so any G title without a quena
        # word still lands here, including theme-led Jayras titles: those
        # need LEMOINE_FLUTE.
        "note": "Nova double; every G and Gm title without a quena word lands here",
    },
    {
        "folder": "Tulum Bamboo Double C",
        "key": {"C"},
        # A gift from Johnny's friend Albert, who found it in Tulum (2026-10).
        # Made by Omar La Rosa Sánchez, "La Rosa de Bambú" (Instagram
        # @larosadebambu: "Flautas del mundo, bambú y madera", Urubamba, Peru);
        # Johnny identified him, and the burned cursive mark near one end is
        # his signature, "La Rosa". So it was bought in Tulum but made in Peru.
        # One long bamboo tube with the mouthpiece in the MIDDLE: two flutes
        # joined at the centre, held sideways like a transverse flute, one
        # hand on each half. Two leather-wrapped blocks with red/brown cord
        # ties, cane bindings.
        #
        # Measured 2026-10-19 on its first take (San Diego garden): one half
        # holds a drone on C5, ~533 Hz, sounding in 87% of quarter-second
        # slices; the other moves over it through G4 (~398 Hz), A4, B4, C5, D5,
        # with D#5 now and then. Named against A447 every note lands within a
        # few cents, so like the D flutes it sits ~30 cents sharp of concert.
        # measure.py alone reads it badly (two voices at once): it gave a
        # semitone-ambiguous fit and "lowest 176 Hz", which was handling and
        # wind in the first seconds, before he played. The only C flute, so
        # any title in C files here.
        "note": "bamboo centre-blown double by Omar La Rosa (Peru), from Tulum; C drone ~A447",
        "lowcut": 170,   # under the melody's lowest note (G4 ~398, an F4 ~355 now and then)
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
        "folder": "Stellar Flute D",
        "key": {"D"},
        "needs": ["shaker", "stellar"],
        # Was "Shaker and Flute D". Johnny confirmed the August shaker clips are
        # this same flute with a shaker added, not a second instrument, so the
        # two folders became one. "shaker" stays in `needs`: it is how those
        # clips name themselves and it now points here.
        #
        # 2026-09-10: measured from the indoor take. Lowest sustained note D4,
        # and the scale played is root, minor third, fourth, fifth with a light
        # major sixth. The whole instrument sounds about 30 cents sharp of
        # concert D, near an A=447 reference, so it is neither a 440 nor a 432
        # flute. One recording cannot separate the instrument from breath
        # pressure; a second take would, as it did for the quena.
        #
        # 2026-09-23: two takes of the Sacral Chakra D, identified visually,
        # measure the same way — D dorian, ~30c sharp, A=447. So this reading
        # may belong to that flute instead; the indoor take it came from was
        # never identified by sight. Treat the tuning above as unconfirmed
        # until a clip showing this instrument is measured.
        #
        # 2026-10-11: RESOLVED. Four indoor takes identified by sight as this
        # flute (plain reddish body with no burned chakra symbols, black block
        # tie, red/white/grey woven band) all measure best fit A4 445.3-447.1,
        # centred on D with C, F, G, A: D dorian, lowest sustained ~291 Hz (D4
        # bent flat). The September reading was this flute after all, and the
        # sacral chakra flute independently sits near 447 too. Nothing was
        # misattributed; both D flutes are simply ~30c sharp of concert.
        "note": "Stellar Flutes, not High Spirits; the shaker clips are this flute too; D dorian ~A447",
        "lowcut": 140,   # lowest note D4 ~291-296Hz, measured on four takes
    },
    {
        "folder": "Sacral Chakra D",
        "key": {"D"},
        # "svadhisthana" is the sacral chakra's Sanskrit name, which Johnny has
        # started using interchangeably with "sacral" in titles. Without it, a
        # title that names only the Sanskrit term matches no D flute at all and
        # the clip goes to UNSORTED.
        "needs": ["sacral", "chakra", "svadhisthana"],
        # Named by its chakra rather than its maker or model, which is how
        # Johnny refers to it. Single chamber, reddish wood, branded medallion
        # near the foot. Confirmed by Johnny as a separate instrument, not the
        # Kestrel or the Stellar under another name — so D now needs a
        # distinguishing word for all three.
        #
        # 2026-09-23: measured from two garden takes, and identified visually
        # from the frames rather than the file name — the svadhisthana
        # medallion is branded near the foot. Both takes give the same absolute
        # note peaks: 296, 354, 398.5, 449, 506, 532 Hz. Against concert pitch
        # that is D +14c, F +23c, G +28c, A +35c, B +42c, C +29c, so the scale
        # is D dorian (minor third, major sixth) and the instrument sits about
        # 30 cents sharp, near an A=447 reference. Neither a 440 nor a 432
        # flute.
        #
        # That reading is the same as the one recorded on the Stellar below,
        # which was taken from a single indoor take. Either that take was this
        # flute, or both D flutes sit near 447. One of the two notes is
        # probably misattributed, and nothing here can say which, so both
        # stand until a take of the Stellar is identified visually the way
        # these were.
        #
        # 2026-10-11: resolved by four visually identified Stellar takes, which
        # also measure ~A447 D dorian. Both readings stand; neither was
        # misattributed. Seen side by side, the sacral flute is the one with
        # burned chakra medallions; the Stellar's body is plain.
        "note": "third D flute; measures D dorian ~30c sharp, near A=447",
        "lowcut": 140,   # lowest note D4 ~296Hz, measured on two takes
    },
    {
        "folder": "Spanish Cedar 432Hz",
        # "432hz" as well as "432": the match is whole-word, so the bare number
        # does not match inside "432hz", which is how Johnny writes it. A title
        # like "solar plexus flute in E, 432hz" went to Unsorted until this.
        "keyless": ["spanish cedar", "432", "432hz"],
        # 2026-09-16: measured at last, and it does have a letter key — E minor.
        # Best-fit reference A4=433.0 Hz, four cents off A432 and 27 cents flat
        # of A440, so the 432 label is real rather than marketing. The scale is
        # E minor pentatonic: root, 315c, 520c, 725c, 995c above E. The folder
        # stays keyless because "432" and "spanish cedar" already identify it
        # and renaming would move every existing cut for no gain.
        #
        # Identified against the August cut rather than assumed: same honey
        # wood, same block and leather binding, same concentric-arc maker's
        # mark on the body.
        #
        # 2026-10-10: San Diego garden take reproduces it independently: best
        # fit A4=430.6 Hz, E 51%, A 28%, G 13%, B 7% (E minor pentatonic), the
        # lowest sustained notes ~312-322 Hz, i.e. E4 bent slightly flat. Two
        # takes agree, so the low cut below is set from a measured low end.
        "note": "tuned to 432Hz; measures E minor pentatonic at A433",
        "lowcut": 150,   # lowest note E4 ~320Hz; an octave clear of it
    },
    {
        "folder": "Shakuhachi",
        "keyless": ["shakuhachi"],
    },
    {
        # Must sit BEFORE "Quena": keyless rules are tried in order, and the
        # bamboo flute's rule matches the bare word "quena".
        "folder": "Quena Jayras",
        "keyless": ["jayras"],
        # Bought at a market in Mexico City, October 2026. Branded "QUENAS
        # JAYRAS" with a burned stamp and an underline flourish; a pale chakana
        # (stepped Andean cross) inlaid near the top, black cloth wrap with a
        # tab over two woven blue-and-white bands, pale U-notch mouthpiece,
        # dark wood Johnny reads as walnut. Centred on G like the bamboo quena,
        # sitting flat of concert (best fit A4 ~428-434 across four takes), so
        # neither key nor the word "quena" tells the two apart.
        #
        # What the name is, as researched 2026-10-08: no maker, workshop or
        # shop called "Jayras" turned up anywhere. "Los Jayras" is a real,
        # published spelling of Los Jairas, the 1960s La Paz folk group whose
        # quena player was Gilbert Favre (Los Tiempos, 19 Nov 2016, which also
        # translates it "the lazy ones", from Aymara "jayra", lazy). That the
        # flute is named after them is a guess, not a finding.
        #
        # Under warm indoor light the bands do NOT look as they do outdoors:
        # the brown beaded band reads as a red-and-black diamond weave and the
        # blue-and-white bands go grey. On 2026-10-10 that misread filed an
        # indoor Jayras take into a new "Quena Red Band" folder as if it were
        # the second market quena; Johnny caught it and it was moved back. The
        # chakana inlay and the pitch (G, lowest ~383 Hz, ~A430) matched all
        # along. When Johnny names the flute, file it as named; a band colour
        # seen through a lamp is not grounds to overrule him.
        #
        # The OTHER quena from that market is "Black Quena", below: an F#
        # instrument, not this one.
        #
        # Titles usually lead with the theme and never say "jayras", so cuts
        # are filed with LEMOINE_FLUTE="Quena Jayras" on the publish run.
        "note": "dark wood, chakana inlay, stamped QUENAS JAYRAS; G, ~A430",
        "sounds_in": {"G"},
        "lowcut": 200,   # lowest note G4 ~385Hz; see LOWCUT below
    },
    {
        "folder": "Quena",
        "keyless": ["quena"],
        # Measured, not yet confirmed by Johnny, so the folder stays keyless:
        # pitch-tracking the three Massachusetts takes puts every sustained note
        # ~33 cents flat of A440, which is A432 (-31.8 cents) almost exactly.
        # Read against 432 they land on A -5c, B -1c, C -8c, with the lowest
        # sustained note a G — G major pentatonic on a quena in G. Against 440
        # nothing fits, which is why a first pass looked like "B something".
        #
        # 2026-09-04: the San Diego garden take reproduces this independently —
        # different day, different continent, best-fit reference A4=431.4 Hz and
        # the lowest sustained note a G again (382.6 Hz, -7.9c). A quena's pitch
        # bends a long way with embouchure, so one recording sitting flat could
        # have been the player; two, weeks and a hemisphere apart, landing on the
        # same reference is the instrument.
        "note": "Andean notched flute; measures as G tuned to A432",
        "sounds_in": {"G"},
        "lowcut": 200,   # lowest sustained note G4 ~383Hz, measured three times
    },
    {
        # Must sit AFTER "Quena": a quena title with no key goes to the bamboo
        # quena, as it always has. This one is reached by a quena title in F#,
        # or by LEMOINE_FLUTE="Black Quena".
        "folder": "Black Quena",
        "keyless": ["quena"],
        # The second quena Johnny bought at the Mexico City market with the
        # Jayras, October 2026: "just a black wood type", no maker's mark.
        # Two side-by-side clips (2026-10-11), each flute played in turn, gave
        # note sets that do not overlap. Black: 370, 412, 466, 500, 562, 619,
        # 679 Hz. Jayras: 387, 428, 477, 504, 622, 690 Hz. The black quena's
        # home note, held for seven seconds at full breath, is 368-372 Hz:
        # F#4 at A440 almost exactly. So it is an F# quena, not a flat G one.
        # The two are ~75 cents apart at the bottom and nearly meet by the top
        # (C and E within ~10 cents), so they clash played together, low notes
        # worst. F# titles as heart chakra (Anahata), as the double drone does.
        #
        # In the second clip the black played 2-42 s and the Jayras only the
        # last 5 s. A brightness change at 8 s first looked like the switch; it
        # was dynamics. Split a comparison clip by its NOTES, not its timbre.
        "note": "black wood, plain; F#, bottom note ~370Hz",
        "sounds_in": {"F#", "F"},   # a slug loses the "#"
        "lowcut": 180,   # an octave under the 368-372Hz home note
    },
]

# Last-resort overrides, for a clip whose file name simply lacks the
# information a rule would need. "Drone in Mexico City" names no key; it was
# identified as G minor by measuring the recording, and Johnny confirmed the
# Gm clips are the Nova.
MAP = {
    "drone-in-mexico-city": "High Spirits Nova G",
    # 2026-10-07: the first cut of the Quenas Jayras quena, made before the
    # flute had a name. Kept so a re-run of that cut still files correctly.
    "nervous-system-reset-new-quena-in-g": "Quena Jayras",
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


# LOWCUT: a high-pass, in Hz, applied to a flute's audio before reverb. It
# removes traffic, wind and handling rumble the flute itself never reaches.
# Set only where the flute's lowest note has been MEASURED, and keep it about
# an octave below that note so no fundamental is touched. Flutes without a
# measured low end get none; a guessed cutoff on a drone flute would thin the
# drone, which is the whole point of the instrument.
def lowcut_for(folder):
    """The low cut for a flute folder, or 0 when none has been set."""
    for f in FLUTES:
        if f["folder"] == folder:
            return int(f.get("lowcut", 0))
    return 0


def folder_for(slug, title=None):
    """The folder this cut belongs in, or UNSORTED if the list can't place it."""
    if slug in MAP:
        return MAP[slug]
    hay = f"{slug} {title or ''}".lower().replace("-", " ")
    key = key_of(slug, title)

    # A flute with no key is identified by name alone. Where two share the
    # name (three quenas answer to "quena"), the key in the title decides:
    # "quena in F#" is the black quena, never the bamboo one in G. A name
    # that matches but whose key fits none of them is a question, not a
    # reason to fall through to a keyed flute that was never named.
    named = [f for f in FLUTES if any(_has(hay, w) for w in f.get("keyless", []))]
    if named:
        fits = [f for f in named if not (key and f.get("sounds_in") and key not in f["sounds_in"])]
        return fits[0]["folder"] if fits else UNSORTED

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
            k = "/".join(sorted(f.get("key", ()) or f.get("sounds_in", ()))) or "no key"
            print(f"  {f['folder']:<26} {k:<8} {f.get('note','')}")
        raise SystemExit
    for a in args:
        slug, _, title = a.partition("::")
        print(f"{a}\n    -> {folder_for(slug, title or None)}")
