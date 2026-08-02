#!/usr/bin/env python3
"""Generate a lemoine lower-third overlay (.mov with alpha) in the brand style.

Matches the lemoine-lower3-* templates (colors sampled from the BT.709-tagged
originals): #181818 charcoal box, #D54664 coral dot, Outfit Light text in
brand cream. Blocky left-to-right pixel wipe in/out; edge blocks jitter while
settling; pixels flake off the box and fall with size-coherent gravity — big
blocks drop heavy, small ones drift like dust with a little air wobble — and
leave through the bottom of frame rather than blinking out.

Usage:
  python3 make_lower3.py --text "high spirits – 432hz spanish cedar" \
      --orientation both --outdir out/
"""
import argparse
import hashlib
import math
import os
import random
import subprocess

from PIL import Image, ImageDraw, ImageFont

FPS = 30
DURATION = 8.6
N_FRAMES = int(round(FPS * DURATION))

CHARCOAL = (24, 24, 24, 255)          # box, sampled from template
CORAL = (213, 70, 100, 255)           # dot, sampled from template
CREAM = (243, 239, 225, 255)          # #F3EFE1 brand cream
# digitalPalette from lemoine-explosion-github.js
PALETTE = [
    (204, 54, 102), (242, 56, 107), (245, 112, 66), (230, 173, 56),
    (82, 173, 133), (56, 143, 199), (122, 92, 199), (224, 122, 173),
    (199, 140, 115), (140, 166, 140), (242, 207, 200), (243, 239, 225),
]

GEOM = {
    "landscape": dict(size=(1920, 1080), box_x=96, box_bottom=993, box_h=85,
                      dot_dx=37, dot_r=4, text_dx=59, font_size=35, pad_right=36),
    "vertical": dict(size=(1080, 1920), box_x=64, box_bottom=1593, box_h=101,
                     dot_dx=41, dot_r=5, text_dx=69, font_size=42, pad_right=41),
}

WIPE_IN = (0.15, 1.05)
WIPE_OUT = (5.2, 6.1)
SAFETY_FADE = (DURATION - 0.5, DURATION - 0.1)   # backstop before asset ends


def h01(*key):
    d = hashlib.md5(":".join(str(k) for k in key).encode()).digest()
    return d[0] / 255.0


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def wipe_progress(t, span):
    a, b = span
    if t <= a:
        return 0.0
    return smoothstep((t - a) / (b - a))


class Pixel:
    """A falling pixel. mode 'exit' falls off-frame; 'dust' dissipates near the box."""

    def __init__(self, rng, x, y, t0, mode="exit", chunky_bias=0.0):
        self.t0, self.x0, self.y0, self.mode = t0, x, y, mode
        if mode == "dust":
            self.s = rng.randint(2, 4)
            self.g = rng.uniform(40, 120)
            self.vterm = rng.uniform(55, 140)
            self.vy = rng.uniform(2, 14)
            self.vx = rng.uniform(-10, 10)
            self.life = rng.uniform(1.6, 2.8)
        else:
            r = rng.random() - chunky_bias
            if r < 0.55:
                self.s = rng.randint(3, 6)
            elif r < 0.87:
                self.s = rng.randint(7, 10)
            else:
                self.s = rng.randint(11, 15)
            m = self.s / 15.0                     # mass: big falls heavy
            self.g = 110 + 480 * m + rng.uniform(-30, 30)
            self.vterm = 130 + 330 * m + rng.uniform(-25, 25)
            self.vy = rng.uniform(4, 26)
            self.vx = rng.uniform(-22, 22)
            self.life = 1e9                       # lives until off-frame
        # small pixels wobble more (air), heavy ones barely
        self.wob_amp = max(0.0, 7.5 - 0.45 * self.s) * rng.uniform(0.6, 1.4)
        self.wob_f = rng.uniform(0.7, 1.9) * 2 * math.pi
        self.wob_ph = rng.uniform(0, 2 * math.pi)
        cr = rng.random()
        if cr < 0.42:
            self.c = CHARCOAL[:3]
        elif cr < 0.52:
            self.c = CORAL[:3]
        elif cr < 0.60:
            self.c = CREAM[:3]
        else:
            self.c = PALETTE[rng.randrange(len(PALETTE))]

    def pos(self, t, H):
        a = t - self.t0
        if a < 0 or a > self.life:
            return None
        t_cap = max(0.0, (self.vterm - self.vy) / self.g)
        ta = min(a, t_cap)
        y = self.y0 + self.vy * ta + 0.5 * self.g * ta * ta
        if a > t_cap:
            y += self.vterm * (a - t_cap)
        if y > H + 20:
            return None
        x = self.x0 + self.vx * a + self.wob_amp * math.sin(self.wob_f * a + self.wob_ph)
        if self.mode == "dust":
            u = a / self.life
            fade = 1.0 - smoothstep((u - 0.35) / 0.65) if u > 0.35 else 1.0
        else:
            fade = 1.0                            # exits the frame, never blinks out
        # backstop: ease anything still alive out before the asset hard-ends
        if t > SAFETY_FADE[0]:
            fade *= 1.0 - smoothstep((t - SAFETY_FADE[0]) / (SAFETY_FADE[1] - SAFETY_FADE[0]))
        return x, y, fade


def build(text, orientation, font_path, outdir, basename=None, keep_frames=False):
    g = GEOM[orientation]
    W, H = g["size"]
    font = ImageFont.truetype(font_path, g["font_size"])

    label = f"[ {text} ]"
    bb = font.getbbox(label)
    box_w = g["text_dx"] + (bb[2] - bb[0]) + g["pad_right"]
    box_h = g["box_h"]
    box_x, box_y = g["box_x"], g["box_bottom"] - box_h
    cy = box_y + box_h / 2

    design = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(design)
    d.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=CHARCOAL)
    dx, r = box_x + g["dot_dx"], g["dot_r"]
    d.ellipse([dx - r, cy - r, dx + r, cy + r], fill=CORAL)
    d.text((box_x + g["text_dx"], cy), label, font=font, anchor="lm", fill=CREAM)

    cell = max(10, round(box_h / 6))
    cols = math.ceil((box_w + 2) / cell)
    rows = math.ceil((box_h + 2) / cell)

    rng = random.Random(432)
    pixels = []
    # wipe-in: a light shake-loose under the traveling edge
    for i in range(cols):
        u = (i + 0.5) / cols
        t_edge = WIPE_IN[0] + u * (WIPE_IN[1] - WIPE_IN[0])
        for _ in range(rng.choice([0, 1, 1])):
            pixels.append(Pixel(rng, box_x + u * box_w + rng.uniform(-8, 8),
                                box_y + box_h - 2, t_edge + rng.uniform(0, 0.25)))
    # hold: sparse dust flaking off the bottom edge, dissipating nearby
    t = WIPE_IN[1]
    while t < WIPE_OUT[0] - 0.3:
        t += rng.uniform(0.25, 0.7)
        pixels.append(Pixel(rng, box_x + rng.uniform(4, box_w - 4),
                            box_y + box_h - 2, t, mode="dust"))
    # wipe-out: the box sheds properly — everything falls out of frame
    for i in range(cols):
        u = (i + 0.5) / cols
        t_edge = WIPE_OUT[0] + u * (WIPE_OUT[1] - WIPE_OUT[0])
        for _ in range(rng.choice([1, 2, 2, 3])):
            pixels.append(Pixel(rng, box_x + u * box_w + rng.uniform(-10, 10),
                                box_y + rng.uniform(box_h * 0.35, box_h),
                                t_edge + rng.uniform(0, 0.2), chunky_bias=0.18))

    frame_dir = os.path.join(outdir, f"frames-{orientation}")
    os.makedirs(frame_dir, exist_ok=True)

    for n in range(N_FRAMES):
        t = n / FPS
        p_in = wipe_progress(t, WIPE_IN)
        p_out = wipe_progress(t, WIPE_OUT)

        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if p_in > 0 and p_out < 1:
            # jitter only while a wipe is actually running — never during hold
            wipe_active = t <= WIPE_IN[1] + 0.1 or t >= WIPE_OUT[0] - 0.1
            mask = Image.new("L", (W, H), 0)
            md = ImageDraw.Draw(mask)
            edge_cells = []
            for i in range(cols):
                xc = (i + 0.5) / cols
                for j in range(rows):
                    thr = xc * 0.75 + 0.25 * h01(i, j, "w")
                    on = (p_in >= thr) and not (p_out > 0 and p_out >= thr)
                    if not on:
                        continue
                    x0 = box_x + i * cell
                    y0 = box_y + j * cell
                    x1 = min(x0 + cell, box_x + box_w)
                    y1 = min(y0 + cell, box_y + box_h)
                    if x1 <= x0 or y1 <= y0:
                        continue
                    settling = wipe_active and (
                        (p_in - thr) < 0.12 or (0 < p_out and (thr - p_out) < 0.12))
                    if settling:
                        edge_cells.append((x0, y0, x1, y1, i, j))
                    else:
                        md.rectangle([x0, y0, x1, y1], fill=255)
            # displaced settling blocks go UNDER the settled design so they
            # never eat into legible text
            for x0, y0, x1, y1, i, j in edge_cells:
                jx = int((h01(i, j, n, "jx") - 0.5) * cell * 0.9)
                jy = int((h01(i, j, n, "jy") - 0.5) * cell * 0.9)
                block = design.crop((x0, y0, x1, y1))
                frame.paste(block, (x0 + jx, y0 + jy), block)
            frame.paste(design, (0, 0), mask)

        pd = ImageDraw.Draw(frame)
        for px in pixels:
            p = px.pos(t, H)
            if p is None:
                continue
            x, y, fade = p
            if fade <= 0.01:
                continue
            pd.rectangle([x, y, x + px.s, y + px.s], fill=(*px.c, int(235 * fade)))

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
