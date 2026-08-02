# Lemoine pixel transition — portable spec

Hand this to any tool or session that needs to reproduce the intro/outro
pixelation. The reference implementation is public:
**github.com/lumorae/lemoine**, branch `claude/high-spirits-spanish-cedar-clip-klh8cr`,
directory `tools/lemoine-cut/` — `make_intro.py` (logo assemble + explosion +
ethereal reveal), `make_outro.py` (dissolve to end-card, `dissolve_field`),
`make_lower3.py` (lower-third wipe + falling pixels).

## Design tokens

- Charcoal background `#191919` (box charcoal `#181818`)
- Coral `#CC3565` (brand) / `#D54664` (video templates' dot)
- Cream `#F3EFE1`
- Particle palette (`digitalPalette` from lemoine-explosion-github.js, coral-weighted):
  `#CC3666 #F2386B #F5702A #E6AD38 #52AD85 #388FC7 #7A5CC7 #E07AAD #C78C73 #8CA68C #F2CFC8 #F3EFE1`
- Font: Outfit Light (300)

## 1. Ethereal dissolve (charcoal ↔ footage)

Never flip binary blocks. Build a static per-pixel threshold field `TH ∈ [0.02, 0.95]`:

```
TH = 0.58 * clouds + 0.27 * grain6 + 0.15 * grain2
clouds = random low-res grid (~1 cell per 192px), bilinear-upsampled  → organic flow
grain6 = random 6px blocks, nearest-upsampled                         → pixel identity
grain2 = random 2px blocks, nearest-upsampled                         → fine dust edge
```

Per frame with progress `p: 0→1` (scaled by `1+SOFT`, `SOFT = 0.14`):

- charcoal DISAPPEARING (intro): `alpha = clip((TH − p)/SOFT + 1, 0, 1)`
- charcoal APPEARING (outro):    `alpha = clip((p − TH)/SOFT, 0, 1)`

Each pixel eases over the soft band instead of popping; erosion travels in
cloud-shaped patches. ~400 fine dust squares (2–6px) release exactly when
their patch erodes (spawn time = `TH(x,y)` mapped into the dissolve window)
and fall out of frame (physics below).

## 2. Explosion (site above-the-fold language)

Shards sampled from the logo on a 7px grid; 45% keep the logo pixel color,
the rest draw from the coral-weighted palette.

- Launch: radial from logo centroid, speed 120–780 px/s, angle jitter ±0.45
  rad, extra upward lift 40–220 px/s. Staggered start over 0.3s.
- Sizes: 55% 3–6px, 30% 7–11px, 15% 12–18px.
- Mass physics (`m = s/18`): gravity `300+420m`, terminal velocity `280+360m`
  px/s; small pixels get sine air-wobble (amp ≈ `8−0.45s`, 0.7–1.9 Hz).
- Rotation ±3 rad/s. Shards ≥7px crumble mid-flight via a **4×4 sub-cell
  dissolve** (per-sub-cell hash vs decaying integrity; the last ~2 cells never
  vanish mid-air) — this is the exact mechanic of the site shader.
- Exits are REAL: a particle ends only by crossing any frame edge (top counts
  during launch). A 0.55s ease-out backstop near the asset's end catches
  stragglers *while they are moving*. Never fade a resting particle.

## 3. Pixelate-in (logo assembly / text reveal)

10px cells over the artwork; each cell appears when `progress ≥
0.02 + smoothstep(hash(cell)) * 0.92`; a freshly-appeared cell jitters ±4px
for ~0.1 of progress, then locks. Draw jittered copies UNDER settled artwork.

## 4. Timing (intro, 7.0s @ 30fps)

- 0.15–1.35 logo pixelates in → hold
- 2.0 explosion; 2.2–3.9 charcoal erodes to footage
- audio fades in 2.2→3.6 (qsin curve) — silent over the logo card
- all particles clear frame by ~6.3; 6.3–6.85 in-motion ease backstop

Deterministic seeds everywhere so renders are reproducible.
