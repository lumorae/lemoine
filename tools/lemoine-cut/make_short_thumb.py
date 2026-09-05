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

The photo always runs full frame. What changes is how far down the ink stays
solid before it dissolves into the picture:

  band    ink holds to 20% and is gone by 46%. Type sits on solid ground, and
          the falloff keeps it from reading as a sticker over a photograph.
  bleed   no solid at all, just a gradient. Keeps every pixel of the image,
          and needs real sky or shadow up top for the type to survive.

An earlier draft ended the band on a hard edge. It looked like two pictures
glued together at grid size, which is what --fade exists to prevent.
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


def film(im, strength=1.0):
    """A restrained film grade: matte blacks, warm highlights, cool shadows.

    Deliberately small numbers. The brand is clean and confident, and a heavy
    preset would read as a filter rather than as a photograph that was graded.
    """
    if strength <= 0:
        return im
    a = np.asarray(im).astype(np.float32) / 255.0
    lo, hi = 0.045 * strength, 1.0 - 0.018 * strength      # lift the black point
    a = lo + a * (hi - lo)
    lum = a.mean(axis=2, keepdims=True)
    a += np.array([0.022, 0.005, -0.018]) * strength * lum          # warm highs
    a += np.array([-0.012, -0.002, 0.016]) * strength * (1 - lum)   # cool shadows
    a = lum + (a - lum) * (1 - 0.07 * strength)                     # ease saturation
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


def grain(im, amount, seed=7):
    """Monochrome film grain, strongest in the midtones.

    Real grain all but disappears in clipped highlights and deep shadow, so
    flat noise across the frame reads as digital sensor noise instead. Seeded,
    so re-rendering the same thumbnail gives the same grain.
    """
    if amount <= 0:
        return im
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    n = np.random.default_rng(seed).normal(0.0, amount, (h, w, 1))
    lum = a.mean(axis=2, keepdims=True) / 255.0
    weight = np.clip(1.0 - np.abs(lum - 0.45) * 1.35, 0.22, 1.0)
    return Image.fromarray(np.clip(a + n * weight, 0, 255).astype(np.uint8))


def _screen(base, layer, amount):
    """Screen blend — how light actually adds, rather than clipping like sum."""
    b = base.astype(np.float32)
    l = np.clip(layer.astype(np.float32) * amount, 0, 255)
    return 255.0 - (255.0 - b) * (255.0 - l) / 255.0


def diffusion(im, strength=0.55):
    """A Pro-Mist in front of the lens: highlights bloom into a soft veil.

    This is the one cinematographers actually reach for when they want calm.
    It lowers apparent contrast without touching the black point, so the
    picture goes gentle rather than grey.
    """
    a = np.asarray(im).astype(np.float32)
    lum = a.mean(axis=2, keepdims=True) / 255.0
    mask = np.clip((lum - 0.55) / 0.45, 0, 1) ** 1.5
    hi = Image.fromarray(np.clip(a * mask, 0, 255).astype(np.uint8))
    glow = np.asarray(hi.filter(ImageFilter.GaussianBlur(H * 0.018)))
    return Image.fromarray(np.clip(_screen(a, glow, strength), 0, 255).astype(np.uint8))


def halation(im, strength=0.5):
    """The red bleed film gets where a highlight burns back off the base.

    Deliberately only in the red and a little green: neutral bloom is
    diffusion, and the warmth is the whole reason halation looks like film.
    """
    a = np.asarray(im).astype(np.float32)
    lum = a.mean(axis=2, keepdims=True) / 255.0
    mask = np.clip((lum - 0.68) / 0.32, 0, 1) ** 2
    hi = Image.fromarray(np.clip(a * mask, 0, 255).astype(np.uint8))
    glow = np.asarray(hi.filter(ImageFilter.GaussianBlur(H * 0.030))).astype(np.float32)
    glow *= np.array([1.0, 0.42, 0.22])                   # burn it warm
    return Image.fromarray(np.clip(_screen(a, glow, strength), 0, 255).astype(np.uint8))


def vignette(im, strength=0.35):
    """Corners fall away, so the eye goes to the middle and stays there."""
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    k = 1.0 - strength * np.clip((r - 0.55) / 0.75, 0, 1) ** 1.6
    a = np.asarray(im).astype(np.float32) * k[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def duotone(im, mix=1.0, dark=INK, light=OLD_LACE):
    """Map luminance across the brand's own two colours.

    Not a colour cast over the photograph — the photograph is rebuilt out of
    #191919 and #f3efe1, which is why it sits inside the palette instead of
    beside it.
    """
    lum = (np.asarray(im.convert("L")).astype(np.float32) / 255.0)[:, :, None]
    duo = np.array(dark) + (np.array(light) - np.array(dark)) * lum
    a = np.asarray(im).astype(np.float32)
    return Image.fromarray(np.clip(a * (1 - mix) + duo * mix, 0, 255).astype(np.uint8))


EFFECTS = {
    "none": lambda im: im,
    "diffusion": diffusion,
    "halation": halation,
    "vignette": vignette,
    "duotone": duotone,
}


def scrim(im, solid=0.0, fade=0.46):
    """Ink over the top of the photo: opaque to `solid`, faded to nothing by `fade`.

    One control instead of two layouts. A hard-edged band reads as a sticker
    stuck over a photograph; carrying it down into the image on a smoothstep
    makes it look like the picture darkens, which is what it should look like.
    """
    if fade <= solid:
        return im
    y0, y1 = int(H * solid), int(H * fade)
    alpha = Image.new("L", (W, H), 0)
    ad = ImageDraw.Draw(alpha)
    for yy in range(y1):
        if yy <= y0:
            v = 255
        else:
            t = 1.0 - (yy - y0) / (y1 - y0)
            v = int(255 * (t * t * (3 - 2 * t)))
        ad.line([(0, yy), (W, yy)], fill=v)
    blur = max(2, int(H * (fade - solid) * 0.06))
    return Image.composite(Image.new("RGB", (W, H), INK), im,
                           alpha.filter(ImageFilter.GaussianBlur(blur)))


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


# solid ink to, faded out by, subject sits at.
#
# The fade endpoint is the one number worth being careful with. Too shallow and
# the ink stops abruptly in open sky; too deep and it crosses the face, which
# goes grey and stops reading as the subject. On this footage the face turns at
# about 0.70, so the band stops well short of it.
PRESETS = {
    "band":  (0.20, 0.58, 0.52),
    "bleed": (0.00, 0.58, 0.46),
}


def build(frame, eyebrow, lines, out, layout="band", subject_y=0.30, zoom=1.0,
          logo=True, grade=1.0, grain_amount=7.0, solid=None, fade=None,
          effect="none"):
    maxw = W - 2 * MARGIN
    s, f, place = PRESETS[layout]
    s = s if solid is None else solid
    f = f if fade is None else fade

    im = photo(frame, H, subject_y=subject_y, place_at=place, zoom=zoom)
    im = film(im, grade)
    # The effect goes on the photograph, before the ink. Applying it after
    # would drag the flat #191919 into whatever the effect does, and a bloomed
    # or duotoned brand colour is a mistake rather than a texture.
    im = EFFECTS[effect](im)
    im = scrim(im, solid=s, fade=f)
    # Grain goes on AFTER the scrim so the dark top is grained too — that is
    # what makes it read as one photograph rather than as type over a picture —
    # but BEFORE the type, so the letterforms stay clean.
    im = grain(im, grain_amount)

    y = int(H * 0.05)
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
    ap.add_argument("--layout", choices=list(PRESETS), default="band")
    ap.add_argument("--solid", type=float, default=None,
                    help="fraction of the height held fully ink (overrides the preset)")
    ap.add_argument("--fade", type=float, default=None,
                    help="fraction by which the ink has faded to nothing")
    ap.add_argument("--grade", type=float, default=1.0, help="film grade, 0 = off")
    ap.add_argument("--grain", type=float, default=7.0, help="grain sigma, 0 = off")
    ap.add_argument("--effect", choices=list(EFFECTS), default="none")
    ap.add_argument("--subject-y", type=float, default=0.30,
                    help="where the head sits in the source frame, 0-1")
    ap.add_argument("--zoom", type=float, default=1.0, help=">1 crops in")
    ap.add_argument("--no-logo", action="store_true")
    a = ap.parse_args()
    lines = [l.rstrip(". ") for l in ([a.line1] + ([a.line2] if a.line2 else []))]
    build(grab(a.video, a.at), a.eyebrow, lines, a.out, layout=a.layout,
          subject_y=a.subject_y, zoom=a.zoom, logo=not a.no_logo,
          grade=a.grade, grain_amount=a.grain, solid=a.solid, fade=a.fade,
          effect=a.effect)
