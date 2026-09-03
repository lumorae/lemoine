#!/usr/bin/env python3
"""Generate a Lemoine YouTube thumbnail from a frame of the cut.

The layout is the one on johnnylemoine.com, taken from the site's own tokens
rather than approximated: a flat #191919 field, a bracketed eyebrow in Outfit
Light led by a coral dot, a lowercase two-line headline in Outfit Bold, and a
coral period closing it. The frame bleeds in from the right through a long
gradient so there is no hard seam between photograph and field.

    python3 make_thumbnail.py --frame still.png \
        --eyebrow "heart chakra meditation" --line1 drone --line2 flute

Three things here are not taste, and changing them will cost you:

  duration badge   YouTube stamps the runtime over the bottom-right corner of
                   every thumbnail in browse, search and suggested. Nothing
                   goes there. The lemon sits top-left for that reason.
  the gap          The script prints the clear distance between the end of the
                   type and where the image starts appearing. Early drafts of
                   this layout came out at MINUS 59px, which reads as the text
                   colliding with the picture. Keep it positive.
  168px            Every run writes a <name>-test.png showing the thumbnail at
                   168px wide, which is roughly its real size in a browse feed.
                   Judging a thumbnail at full size is how you ship one nobody
                   can read. Look at the small one.

Two lines, not one, is deliberate. A single-line headline has to shrink to
about 86pt to leave any air beside the photograph; stacked, the same words set
at ~139pt, which is the proportion the brand uses, and the narrower column is
what creates the space.
"""
import argparse
import os

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

W, H = 1280, 720
MARGIN = 64
COL = 380                        # type column width; the rest is air and photo


def lemon(height, tint):
    """The brand mark, recoloured, lifted from the end-card artwork."""
    src = Image.open(ENDCARD).convert("RGB").crop(LEMON_BOX)
    a = np.asarray(src).astype(int)
    mask = (np.abs(a - np.array(INK)).sum(axis=2) > 24).astype(np.uint8) * 255
    solid = Image.new("RGBA", src.size, (*tint, 255))
    solid.putalpha(Image.fromarray(mask))
    k = height / solid.height
    return solid.resize((int(solid.width * k), height), Image.LANCZOS)


def _fit(text, path, start, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    size = start
    while size > 24:
        f = ImageFont.truetype(path, size)
        b = d.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= maxw:
            return f, b
        size -= 2
    return ImageFont.truetype(path, 24), (0, 0, 0, 0)


def _fit_lines(lines, path, start, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    size = start
    while size > 30:
        f = ImageFont.truetype(path, size)
        if max(d.textbbox((0, 0), l, font=f)[2] for l in lines) <= maxw:
            return f
        size -= 3
    return ImageFont.truetype(path, 30)


def build(frame, eyebrow, lines, out, zoom=0.66, y_centre=0.40,
          subject_x=0.54, place_at=0.80, fade=(0.40, 0.78), logo=True):
    im = Image.new("RGB", (W, H), INK)

    src = Image.open(frame).convert("RGB")
    sw, sh = src.size
    cw = int(sw * zoom)
    ch = min(int(cw * H / W), sh)
    # solve the window so the player lands where we want him, rather than
    # guessing a centre and discovering the type is across his face
    x0 = max(0.0, min(1 - zoom, subject_x - place_at * zoom))
    cy = max(0, min(sh - ch, int(y_centre * sh - ch / 2)))
    photo = src.crop((int(x0 * sw), cy, int(x0 * sw) + cw, cy + ch))
    photo = ImageEnhance.Color(photo.resize((W, H), Image.LANCZOS)).enhance(1.05)

    alpha = Image.new("L", (W, H), 0)
    ad = ImageDraw.Draw(alpha)
    xs, xe = int(W * fade[0]), int(W * fade[1])
    for x in range(W):
        if x <= xs:
            v = 0
        elif x >= xe:
            v = 255
        else:
            t = (x - xs) / (xe - xs)
            v = int(255 * (t * t * (3 - 2 * t)))       # smoothstep, no banding
        ad.line([(x, 0), (x, H)], fill=v)
    im = Image.composite(photo, im, alpha.filter(ImageFilter.GaussianBlur(14)))

    d = ImageDraw.Draw(im)
    fe, be = _fit(f"[ {eyebrow} ]", FONT_LIGHT, 32, COL)
    fh = _fit_lines(lines, FONT_BOLD, 190, COL)
    hh = d.textbbox((0, 0), lines[-1], font=fh)[3] - d.textbbox((0, 0), lines[-1], font=fh)[1]
    lead = int(fh.size * 0.94)
    he = be[3] - be[1]

    y = (H - (he + 46 + lead * (len(lines) - 1) + hh)) // 2
    r = 7
    d.ellipse([MARGIN, y + he // 2 - r, MARGIN + 2 * r, y + he // 2 + r], fill=CORAL)
    d.text((MARGIN + 2 * r + 16, y - be[1]), f"[ {eyebrow} ]", font=fe, fill=OLD_LACE)

    y += he + 46
    widest = 0
    for i, line in enumerate(lines):
        b = d.textbbox((0, 0), line, font=fh)
        top = y + i * lead - b[1]
        d.text((MARGIN, top), line, font=fh, fill=OLD_LACE)
        widest = max(widest, b[2] - b[0])
        if i == len(lines) - 1:
            # Sit the period on the BASELINE, not on the bottom of the ink box.
            # A word with a descender ("journey", "youtube") has an ink box that
            # runs below the baseline, and a period aligned to that hangs
            # visibly low. getmetrics is the only reliable anchor: text drawn
            # at `top` has its baseline at top + ascent.
            baseline = top + fh.getmetrics()[0]
            dr = max(7, int(hh * 0.15))
            cx = MARGIN + (b[2] - b[0]) + dr * 2
            d.ellipse([cx - dr, baseline - 2 * dr, cx + dr, baseline], fill=CORAL)

    if logo:
        im = im.convert("RGBA")
        im.alpha_composite(lemon(52, OLD_LACE), (MARGIN, 52))
        im = im.convert("RGB")

    im.save(out, quality=94, optimize=True)

    gap = xs - (MARGIN + widest)
    print(f"{out}  {os.path.getsize(out)//1024} KB   headline {fh.size}pt "
          f"({round(hh/H*100)}% of height)   gap {gap}px")
    if gap < 40:
        print("  WARNING: less than 40px of clear field between the type and the "
              "image. Narrow COL, shorten the headline, or push `fade` right.")

    test = os.path.splitext(out)[0] + "-test.png"
    sheet = Image.new("RGB", (W, H + 200), (0, 0, 0))
    sheet.paste(im, (0, 0))
    small = im.resize((168, 95), Image.LANCZOS)
    sheet.paste(small.resize((W // 2, H // 2 * 168 // 640), Image.NEAREST), (20, H + 20))
    td = ImageDraw.Draw(sheet)
    td.text((20, H + 4), "at 168px wide, roughly browse-feed size", fill=(255, 220, 0))
    sheet.save(test)
    print(f"  legibility test -> {test}")
    return im


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", required=True, help="still from the cut (4K preferred)")
    ap.add_argument("--eyebrow", required=True, help="lowercase, goes inside [ ]")
    ap.add_argument("--line1", required=True)
    ap.add_argument("--line2", default=None)
    ap.add_argument("--out", default="thumbnail.jpg")
    ap.add_argument("--zoom", type=float, default=0.66,
                    help="bigger = wider shot, less face")
    ap.add_argument("--y-centre", type=float, default=0.40)
    ap.add_argument("--subject-x", type=float, default=0.54,
                    help="where the player sits across the source frame")
    ap.add_argument("--no-logo", action="store_true")
    a = ap.parse_args()
    lines = [a.line1] + ([a.line2] if a.line2 else [])
    build(a.frame, a.eyebrow, lines, a.out, zoom=a.zoom, y_centre=a.y_centre,
          subject_x=a.subject_x, logo=not a.no_logo)
