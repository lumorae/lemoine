#!/usr/bin/env python3
"""Generate a lemoine lower-third overlay (.mov with alpha) in the brand style.

Replicates the look of the existing lemoine-lower3-* templates:
charcoal #191919 box, coral bullet dot, Outfit Light text in brand cream,
blocky left-to-right pixel wipe in/out with digital-palette particles
(same palette as the site's lemon-explosion effect).

Usage:
  python3 make_lower3.py --text "high spirits - 432hz spanish cedar" \
      --orientation landscape --font Outfit-300.ttf --outdir out/

Produces PNG frames and (if ffmpeg is present) a ProRes 4444 .mov with alpha.
"""
import argparse
import hashlib
import math
import os
import random
import subprocess

from PIL import Image, ImageDraw, ImageFont

FPS = 30
DURATION = 5.4
N_FRAMES = int(round(FPS * DURATION))

CHARCOAL = (25, 25, 25, 255)          # #191919 site background
CREAM = (243, 239, 225, 255)          # #F3EFE1 brand cream
CORAL = (204, 53, 101, 255)           # #CC3565 brand coral
# digitalPalette from lemoine-explosion-github.js
PARTICLE_COLORS = [
    (204, 54, 102), (242, 56, 107), (245, 112, 66), (230, 173, 56),
    (82, 173, 133), (56, 143, 199), (122, 92, 199), (224, 122, 173),
    (199, 140, 115), (140, 166, 140), (242, 207, 200), (243, 239, 225),
]

# geometry measured off lemoine-lower3-walnut-flute-key-of-a templates
GEOM = {
    "landscape": dict(size=(1920, 1080), box_x=96, box_bottom=993, box_h=85,
                      dot_dx=37, dot_r=4, text_dx=59, font_size=35, pad_right=36),
    "vertical": dict(size=(1080, 1920), box_x=64, box_bottom=1593, box_h=101,
                     dot_dx=41, dot_r=5, text_dx=69, font_size=42, pad_right=41),
}

WIPE_IN = (0.10, 0.65)
WIPE_OUT = (4.35, 4.95)


def cell_hash(i, j, salt):
    h = hashlib.md5(f"{i}:{j}:{salt}".encode()).digest()
    return h[0] / 255.0


def wipe_progress(t, span):
    a, b = span
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    x = (t - a) / (b - a)
    return x * x * (3 - 2 * x)  # smoothstep, matches the site easing


def build(text, orientation, font_path, outdir, basename=None, keep_frames=False):
    g = GEOM[orientation]
    W, H = g["size"]
    font = ImageFont.truetype(font_path, g["font_size"])

    label = f"[ {text} ]"
    bb = font.getbbox(label)
    text_w = bb[2] - bb[0]
    box_w = g["text_dx"] + text_w + g["pad_right"]
    box_h = g["box_h"]
    box_x, box_y = g["box_x"], g["box_bottom"] - box_h
    cy = box_y + box_h / 2

    # render the static design once
    design = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(design)
    d.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=CHARCOAL)
    dx, r = box_x + g["dot_dx"], g["dot_r"]
    d.ellipse([dx - r, cy - r, dx + r, cy + r], fill=CORAL)
    d.text((box_x + g["text_dx"], cy), label, font=font, anchor="lm", fill=CREAM)

    cell = max(8, round(box_h / 8))
    cols = math.ceil((box_w + 2) / cell)
    rows = math.ceil((box_h + 2) / cell)

    # particles ride the wipe edge, drifting down-right (site explosion vibe)
    rng = random.Random(432)
    particles = []
    for phase, span in (("in", WIPE_IN), ("out", WIPE_OUT)):
        for _ in range(26):
            u = rng.random()
            t0 = span[0] + u * (span[1] - span[0])
            particles.append(dict(
                t0=t0,
                x=box_x + u * box_w + rng.uniform(-20, 60),
                y=box_y + box_h + rng.uniform(-10, 8),
                vx=rng.uniform(-15, 55), vy=rng.uniform(15, 90),
                life=rng.uniform(0.5, 1.6),
                s=rng.choice([3, 3, 4, 4, 5, 6]),
                c=rng.choice(PARTICLE_COLORS),
            ))

    frame_dir = os.path.join(outdir, f"frames-{orientation}")
    os.makedirs(frame_dir, exist_ok=True)

    for n in range(N_FRAMES):
        t = n / FPS
        p_in = wipe_progress(t, WIPE_IN)
        p_out = wipe_progress(t, WIPE_OUT)

        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if p_in > 0 and p_out < 1:
            # blocky reveal mask over the box area
            mask = Image.new("L", (W, H), 0)
            md = ImageDraw.Draw(mask)
            for i in range(cols):
                xc = (i + 0.5) / cols
                for j in range(rows):
                    # threshold stays within [0, 1] so the box is complete at hold
                    thr = xc * 0.78 + 0.22 * cell_hash(i, j, "w")
                    on = (p_in >= thr) and not (p_out > 0 and p_out >= thr)
                    if on:
                        x0 = box_x + i * cell
                        y0 = box_y + j * cell
                        x1 = min(x0 + cell, box_x + box_w)
                        y1 = min(y0 + cell, box_y + box_h)
                        if x1 > x0 and y1 > y0:
                            md.rectangle([x0, y0, x1, y1], fill=255)
            frame.paste(design, (0, 0), mask)

        pd = ImageDraw.Draw(frame)
        for pt in particles:
            age = t - pt["t0"]
            if age < 0 or age > pt["life"]:
                continue
            fade = 1 - age / pt["life"]
            x = pt["x"] + pt["vx"] * age
            y = pt["y"] + pt["vy"] * age
            s = pt["s"]
            c = (*pt["c"], int(230 * fade))
            pd.rectangle([x, y, x + s, y + s], fill=c)

        frame.save(os.path.join(frame_dir, f"f{n:04d}.png"))

    name = basename or f"lemoine-lower3-{text.replace(' ', '-')}-{W}x{H}-alpha"
    name = "".join(ch for ch in name if ch.isalnum() or ch in "-_")
    out_mov = os.path.join(outdir, name + ".mov")
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
        "-i", os.path.join(frame_dir, "f%04d.png"),
        "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
        out_mov,
    ], check=True)
    if not keep_frames:
        for f in os.listdir(frame_dir):
            os.remove(os.path.join(frame_dir, f))
        os.rmdir(frame_dir)
    return out_mov


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help="lower-third text, without brackets")
    ap.add_argument("--orientation", choices=["landscape", "vertical", "both"], default="both")
    ap.add_argument("--font", default=os.path.join(os.path.dirname(__file__), "Outfit-300.ttf"))
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--keep-frames", action="store_true")
    args = ap.parse_args()

    todo = ["landscape", "vertical"] if args.orientation == "both" else [args.orientation]
    for o in todo:
        print(build(args.text, o, args.font, args.outdir, keep_frames=args.keep_frames))
