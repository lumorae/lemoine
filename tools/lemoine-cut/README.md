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

```bash
# 1) make the lower third for a clip
python3 make_lower3.py --text "high spirits – 432hz spanish cedar" \
    --orientation vertical --outdir .

# 2) cut the clip
./lemoine_cut.sh -i raw.mov -o clip-lemoine-cut.mp4 \
    -l lemoine-lower3-high-spirits-432hz-spanish-cedar-1080x1920-alpha.mov -a
```

Requires: ffmpeg, python3 with pillow + numpy.

Note: the existing intro/outro brand assets are HEVC-with-alpha, which ffmpeg
cannot decode the alpha layer of; this pipeline generates its own overlays as
ProRes 4444 instead.
