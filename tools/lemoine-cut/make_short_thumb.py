#!/usr/bin/env python3
"""Generate a Lemoine thumbnail for a YouTube Short, 1080x1920.

The 16:9 template in make_thumbnail.py cannot be re-cropped into this. It works
by putting a narrow type column beside the photograph, and 9:16 has no beside —
the frame is all subject. So the type has to go above the subject instead, and
the layout is a different one built from the same tokens: flat #191919, a
bracketed eyebrow in Outfit Light led by a coral dot, a lowercase headline in
Outfit Bold, a coral period closing it, the lemon top-left.

    python3 make_short_thumb.py --video short.mp4 --at 24.5 \
        --eyebrow "san diego garden" --line1 "double drone" --line2 "in F#."

Two things here are not taste:

  the bottom     YouTube overlays the view count across the bottom of a Shorts
                 grid tile. Nothing that has to be read goes in the bottom
                 SAFE_BOTTOM of the frame. This is the vertical equivalent of
                 the duration badge that pushed the lemon top-left on 16:9.
  the small test Every run writes a <name>-test.png at 180px wide, roughly a
                 real Shorts grid tile. A vertical thumbnail judged full size
                 is how you ship one that is a grey smear in the grid.

Pull the frame from the ORIGINAL clip, not the finished cut: the cut has the
lower third burned into its first seconds and is 1080 wide, while the source is
2160x3840 and has resolution to spare.

Two layouts, because which one wins depends on where the subject's head is:

  band    a charcoal band across the top, photo below it. Unmissable at grid
          size, costs about a fifth of the image.
  bleed   photo full frame, darkened under the type by a soft gradient. Keeps
          the whole picture, and needs real sky or shadow up top to work.
"""
import argparse
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))

# from :root on johnnylemoine.com
OLD_LACE = (243, 239, 225)      # --old-lace  #f3efe1
INK = (25, 25, 25)              # --black     #191919
CORAL = (204, 53, 101)          # --new-coral #cc3565

FONT_LIGHT = os.path.join(HERE, "Outfit-300.ttf")
FONT_BOLD = os.path.join(HERE, "Outfit-Bold.otf")
ENDCARD = os.path.join(HERE, "endcards", "endcard-dont-blend-in-1080x1920.png")
LEMON_BOX = (360, 553, 718, 845)

W, H = 1080, 1920
MARGIN = 72
SAFE_BOTTOM = 0.18               # view-count overlay lives here; keep type out
TILE = 180                       # a Shorts grid tile, roughly, for the test sheet

TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv")


def grab(video, at):
    """One tone-mapped frame from an HLG clip, at full source resolution."""
    out = os.path.join(tempfile.mkdtemp(), "frame.png")
    subprocess.run(["ffmpeg", "-v", "error", "-ss", str(at), "-i", video,
                    "-frames:v", "1", "-vf", TONEMAP, out], check=True)
    return Image.open(out).convert("RGB")


def lemon(height, tint):
    """The brand mark, recoloured, lifted from the end-card artwork."""
    src = Image.open(ENDCARD).convert("RGB").crop(LEMON_BOX)
    a = np.asarray(src).astype(int)
    mask = (np.abs(a - np.array(INK)).sum(axis=2) > 24).astype(np.uint8) * 255
    solid = Image.new("RGBA", src.size, (*tint, 255))
    solid.putalpha(Image.fromarray(mask))
    k = height / solid.height
    return solid.resize((int(solid.width * k), height), Image.LANCZOS)


def _fit(text, path, start, maxw, floor=24):
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    size = start
    while size > floor:
        f = ImageFont.truetype(path, size)
        b = d.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= maxw:
            return f, b
        size -= 2
    f = ImageFont.truetype(path, floor)
    return f, d.textbbox((0, 0), text, font=f)


def _fit_lines(lines, path, start, maxw, floor=40):
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    size = start
    while size > floor:
        f = ImageFont.truetype(path, size)
        if max(d.textbbox((0, 0), l, font=f)[2] for l in lines) <= maxw:
            return f
        size -= 3
    return ImageFont.truetype(path, floor)


def photo(frame, height, subject_y=0.30, place_at=0.34, zoom=1.0):
    """Crop the source frame to 1080 x `height`, landing the subject sensibly.

    `subject_y` is where the head sits in the SOURCE (0-1 from the top) and
    `place_at` where it should sit in the finished photo. Solving for the window
    beats guessing a centre, which is how the first 16:9 draft ended up with the
    headline across his face.
    """
    sw, sh = frame.size
    cw = int(sw / zoom)
    ch = min(int(cw * height / W), sh)
    x0 = max(0, (sw - cw) // 2)
    y0 = int(subject_y * sh - place_at * ch)
    y0 = max(0, min(sh - ch, y0))
    im = frame.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, height), Image.LANCZOS)
    return ImageEnhance.Color(im).enhance(1.06)


def draw_type(im, y, eyebrow, lines, maxw, on_dark_photo=False):
    """The brand lockup: coral dot, bracketed eyebrow, headline, coral period."""
    d = ImageDraw.Draw(im)
    fe, be = _fit(f"[ {eyebrow} ]", FONT_LIGHT, 46, maxw)
    fh = _fit_lines(lines, FONT_BOLD, 200, maxw)
    he = be[3] - be[1]
    lead = int(fh.size * 0.96)

    r = 9
    d.ellipse([MARGIN, y + he // 2 - r, MARGIN + 2 * r, y + he // 2 + r], fill=CORAL)
    d.text((MARGIN + 2 * r + 20, y - be[1]), f"[ {eyebrow} ]", font=fe, fill=OLD_LACE)

    y += he + 54
    bottom = y
    for i, line in enumerate(lines):
        b = d.textbbox((0, 0), line, font=fh)
        top = y + i * lead - b[1]
        d.text((MARGIN, top), line, font=fh, fill=OLD_LACE)
        baseline = top + fh.getmetrics()[0]
        bottom = baseline
        if i == len(lines) - 1:
            # on the baseline, never on the ink box: a descender would drop it
            dr = max(9, int(fh.size * 0.11))
            cx = MARGIN + (b[2] - b[0]) + dr * 2
            d.ellipse([cx - dr, baseline - 2 * dr, cx + dr, baseline], fill=CORAL)
    return bottom, fh.size


def build(frame, eyebrow, lines, out, layout="band", band=0.24,
          subject_y=0.30, zoom=1.0, logo=True):
    im = Image.new("RGB", (W, H), INK)
    maxw = W - 2 * MARGIN

    if layout == "band":
        # Measure the type block first and size the band to it. A fixed
        # fraction looks fine until the headline needs two lines, and then the
        # words spill onto the photograph and read as a mistake rather than a
        # layout.
        probe = Image.new("RGB", (W, H), INK)
        y0 = int(H * 0.05) + (64 + 46 if logo else 0)
        block, _ = draw_type(probe, y0, eyebrow, lines, maxw)
        top = min(int(H * 0.55), block + int(H * 0.035))
        im.paste(photo(frame, H - top, subject_y=subject_y,
                       place_at=0.30, zoom=zoom), (0, top))
        y = int(H * 0.05)
    else:
        im = photo(frame, H, subject_y=subject_y, place_at=0.46, zoom=zoom)
        # a soft top-down scrim so type has ground without a hard panel edge
        alpha = Image.new("L", (W, H), 0)
        ad = ImageDraw.Draw(alpha)
        ys, ye = 0, int(H * 0.46)
        for yy in range(H):
            t = 0.0 if yy >= ye else 1.0 - (yy - ys) / (ye - ys)
            ad.line([(0, yy), (W, yy)], fill=int(238 * (t * t * (3 - 2 * t))))
        im = Image.composite(Image.new("RGB", (W, H), INK), im,
                             alpha.filter(ImageFilter.GaussianBlur(24)))
        y = int(H * 0.055)

    if logo:
        im = im.convert("RGBA")
        im.alpha_composite(lemon(64, OLD_LACE), (MARGIN, y))
        im = im.convert("RGB")
        y += 64 + 46

    bottom, hsize = draw_type(im, y, eyebrow, lines, maxw)
    im.save(out, quality=94, optimize=True)

    clear = H * (1 - SAFE_BOTTOM) - bottom
    print(f"{out}  {os.path.getsize(out)//1024} KB   layout {layout}   "
          f"headline {hsize}pt ({round(hsize/H*100)}% of height)   "
          f"clear of the view-count band by {clear:.0f}px")
    if clear < 0:
        print("  WARNING: type runs into the bottom of the tile, where YouTube "
              "prints the view count. Shorten the headline or raise the block.")

    test = os.path.splitext(out)[0] + "-test.png"
    small = im.resize((TILE, int(TILE * H / W)), Image.LANCZOS)
    sheet = Image.new("RGB", (W // 2 + TILE + 60, H // 2), (0, 0, 0))
    sheet.paste(im.resize((W // 2, H // 2), Image.LANCZOS), (0, 0))
    sheet.paste(small, (W // 2 + 30, 30))
    ImageDraw.Draw(sheet).text((W // 2 + 30, 8),
                               f"at {TILE}px — a Shorts grid tile", fill=(255, 220, 0))
    sheet.save(test)
    print(f"  grid-size test -> {test}")
    return im


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="the ORIGINAL clip, not the cut")
    ap.add_argument("--at", type=float, required=True, help="timestamp of the frame")
    ap.add_argument("--eyebrow", required=True, help="lowercase, goes inside [ ]")
    # The closing period is DRAWN, in coral, as part of the lockup. Typing one
    # into the headline gets you two: the black one you typed and the coral one
    # the layout adds after it.
    ap.add_argument("--line1", required=True)
    ap.add_argument("--line2", default=None)
    ap.add_argument("--out", default="short-thumb.jpg")
    ap.add_argument("--layout", choices=["band", "bleed"], default="band")
    ap.add_argument("--band", type=float, default=0.24, help="band height, 0-1")
    ap.add_argument("--subject-y", type=float, default=0.30,
                    help="where the head sits in the source frame, 0-1")
    ap.add_argument("--zoom", type=float, default=1.0, help=">1 crops in")
    ap.add_argument("--no-logo", action="store_true")
    a = ap.parse_args()
    lines = [l.rstrip(". ") for l in ([a.line1] + ([a.line2] if a.line2 else []))]
    build(grab(a.video, a.at), a.eyebrow, lines, a.out, layout=a.layout,
          band=a.band, subject_y=a.subject_y, zoom=a.zoom, logo=not a.no_logo)
