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

`lemoine_publish.sh` files each run into `Cut/YYYY-MM/YYYY-MM-DD/` (a fresh
day folder per session) and stamps filenames with date+time — several clips
of the same flute cut on the same day get their own folder and never collide
on name. Dates are computed in Pacific time (`America/Los_Angeles`, override
with `LEMOINE_TZ`) since the container's clock runs UTC and Johnny is in San
Diego — otherwise a late-evening session gets stamped as tomorrow.
