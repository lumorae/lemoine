# lemoine-cut

Pipeline for turning raw flute clips into branded "lemoine cuts":
trim → brand lower third → hall reverb → loudness-normalized h264.

## Pieces

- `make_lower3.py` — generates a lower-third overlay (.mov, ProRes 4444 with
  alpha) in the brand style, replicated from the existing
  `lemoine-lower3-walnut-flute-key-of-a-*` templates: `#191919` charcoal box,
  `#CC3565` coral dot, Outfit Light text in brand cream `#F3EFE1`, blocky
  left-to-right pixel wipe in/out with digital-palette particles (same palette
  as the site's lemon-explosion effect). 5.4s @ 30fps, landscape (1920x1080)
  and vertical (1080x1920).
- `make_ir.py` — synthesizes the stereo hall impulse response (T60 ≈ 2.3s,
  25ms pre-delay, faster HF decay) used for the reverb.
- `reverb.py` — convolution reverb (numpy FFT). The distro ffmpeg's `afir`
  filter is broken (outputs silence), so convolution happens here.
- `lemoine_cut.sh` — the assembly: optional trim (manual `-s`/`-e` or `-a`
  auto-trim on leading/trailing silence), lower-third overlay scaled to the
  footage, reverb wet mix (default −12 dB under dry), `loudnorm` to −14 LUFS,
  libx264 crf 18 + aac 256k, faststart.
- `Outfit-300.ttf` — Outfit Light (the site's brand font), SIL OFL, from
  Google Fonts.

## Usage

One command from a Drive link to both platform cuts:

```bash
./lemoine_publish.sh "https://drive.google.com/file/d/<id>/view" [-g brands|dontblend]
```

Produces `<title>-reels.mp4` (intro + lower third + end-card outro) and
`<title>-shorts.mp4` (clean loop: no intro/outro, raised lower third). The
title comes from the Drive file name; the file must be link-shared.

Lower-level pieces (`make_lower3.py`, `make_intro.py`, `make_outro.py`,
`lemoine_cut.sh`) can also be run individually — see their headers.

### Noisy location recordings (`-c`)

```bash
./lemoine_publish.sh "<drive-url>" -c        # clean up a noisy take
./lemoine_publish.sh "<drive-url>" -n 18     # ... with a harder denoise
```

Filmed on a balcony over a city, the flute arrives buried in traffic, wind and
room hiss. `-c` cleans the audio *before* the reverb, so the hall tail is built
from flute rather than from street:

1. **High-pass at 120 Hz.** These flutes have no fundamental down there — on
   the Mexico City clip the sub-160 Hz band measured 1–3 dB SNR, i.e. pure
   rumble — so cutting it is free.
2. **Collapse to mono.** A phone's stereo pair records the flute as correlated
   centre content and diffuse street noise as decorrelated sides. Summing to
   mono centres the flute *and* cancels much of the ambience in one move; the
   reverb downstream puts the stereo image back. This is why "clean" and
   "centred" are the same operation here.
3. **Spectral denoise** (`afftdn`) for the broadband remainder.
4. **A gentle 6 kHz shelf** to give back the air the denoiser takes off.

Measured on the Mexico City clip: noise down 7 dB below 160 Hz, ~9 dB at
1–4 kHz and ~14 dB above 4 kHz, for 0.7 dB of flute in the core band. Tune with
`-n` (10 gentle, 14 default, 18 aggressive) — spectral denoisers get watery if
pushed, and sustained flute shows it sooner than speech would.

Leave `-c` off for a clean studio take; it costs a little air for nothing. Two
numbers decide it: the sub-160 Hz SNR (1–3 dB means that band is pure rumble and
free to cut; 15 dB means the instrument is actually down there) and the gap
between mid and side (a big gap means the take is already centred, so collapsing
to mono buys nothing). The shakuhachi clips measured 15–18 dB and 24 dB and were
cut without `-c`; the Mexico City balcony clips measured 1–3 dB and 9 dB and
needed it.

### Black and white (`-bw`)

```bash
./lemoine_publish.sh "<drive-url>" -bw
```

Desaturates the footage only. The lower third, intro and end-card composite
*after* the conversion, so brand coral and cream sit on a monochrome frame.
Rec.709 luma weights, matching the colour space the footage was just tone-mapped
into.


Requires: ffmpeg, python3 with pillow + numpy.

Note: the existing intro/outro brand assets are HEVC-with-alpha, which ffmpeg
cannot decode the alpha layer of; this pipeline generates its own overlays as
ProRes 4444 instead.

## Auto-saving cuts to Google Drive

The claude.ai Drive connector can only download up to 10 MB and can't upload
video-size files at all, so renders can't land in Drive through it. Instead,
`drive_upload.py` uploads straight to the "Cut" folder via the Drive API with
a service-account key (one-time setup in its header comment). Once the key is
in place, finished cuts get pushed to Drive automatically at the end of
`lemoine_cut.sh`; until then they're committed to the repo's `renders/` and
sent in chat.

## How things are named and filed

The whole scheme exists to answer three questions without opening any videos:
what shipped today, which take is this, and where's that clip from weeks ago.

```
Inbox/                          raw clips off the phone
Cut/<Flute>/                    finished cuts, one folder per instrument
Cut/INDEX.md                    every cut ever, with links + a "to cut" list
```

Cuts file **by flute**, not by shoot date — `Cut/Ebonized Walnut A/`,
`Cut/Shakuhachi/`. There are only so many flutes, and the same instrument comes
back under slightly different names week to week ("High Spirits — Ebonized
Walnut in A", then "Ebonized Walnut Flute in A [San Diego]"); filing by
instrument puts every take of one flute in one place. The date is still in every
filename, so nothing is lost by dropping the date folders.

`categories.py` maps a cut slug to its flute folder. That map is the authority,
because only Johnny knows which names are the same physical instrument — "Drone
in F#" and "Double Drone in F#" read like a typo apart and are two different
flutes. An unmapped slug is derived from the title instead: everything before
the comma is the instrument, everything after is where it was filmed, so a
location the code has never seen ("[ Massachusetts ]") drops out on its own
rather than leaking into the folder name. To correct a grouping, add the slug to
`MAP` and re-run `drive_migrate.py`.

Cuts are named:

```
2026-08-08_1523_high-spirits-high-kestrel-in-d-take02_shorts.mp4
└── date ──┘ └time┘ └────────── title slug ──────────┘ └take┘ └platform┘
```

- **Date + time.** The folder is the flute, so the name is what carries the
  date — and it keeps several takes of one flute on one day from colliding.
- **Take.** A trailing `(02)`, `[2]`, `take 2` or `#2` on the source file is
  recognised as a take marker: it lands in the filename so takes are
  distinguishable, and is stripped from the on-screen lower third, which
  should only ever read the piece's name. A bare trailing number is left
  alone — `Nova Drone 432` keeps its 432.
- **Platform.** `reels` (intro + end-card) or `shorts` (clean loop).
- **A bracketed aside becomes a comma clause.** `Flute in A [San Diego]` is
  filed and shown as `flute in A, san diego`: the lower third already draws its
  own `[ ... ]` around the title, so a second pair nests badly on screen.
- **The key is capitalised on screen** — `in Gm`, `in A`, `in F#` — and only the
  key letter: the mode stays lowercase (`Gm`, never `GM` or `G Minor`) and so
  does the `in`. A key is only recognised when it ends the title or is followed
  by punctuation that opens an aside, which is what stops `in spanish cedar` or
  `in a church` from being read as one. Filenames stay fully lowercase.
- Dates resolve in Pacific time (`America/Los_Angeles`, override with
  `LEMOINE_TZ`); the container's clock is UTC, so without this an evening
  session files itself under tomorrow.

`drive_index.py` rebuilds `Cut/INDEX.md` — a dated table of every cut with
direct links, plus a **To cut** list built by diffing `Inbox/` against the
cuts that already exist, so anything filmed but not yet cut is visible. It
runs automatically at the end of every `lemoine_publish.sh`; run it by hand
(`--dry-run` to preview) after moving things around in Drive.
