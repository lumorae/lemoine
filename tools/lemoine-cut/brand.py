"""Lemoine motion color system.

Coral, charcoal, and cream carry the brand — each as a ramp of shades and
tints so particles get depth and dimension instead of confetti. Random
accent colors are capped at ~5%.
"""

CORAL = (204, 53, 101)          # #CC3565
CHARCOAL = (25, 25, 25)         # #191919
CREAM = (243, 239, 225)         # #F3EFE1

CORAL_RAMP = [
    (122, 30, 60),              # deep wine shadow
    (142, 35, 70),
    (166, 44, 85),
    (204, 53, 101),             # brand coral
    (213, 70, 100),             # template dot coral
    (224, 106, 133),
    (232, 144, 159),            # blush tint
]

CHARCOAL_RAMP = [
    (15, 15, 15),
    (25, 25, 25),               # background charcoal
    (36, 36, 36),
    (48, 48, 48),
    (60, 60, 60),
]

CREAM_RAMP = [
    (255, 253, 245),
    (243, 239, 225),            # brand cream
    (231, 225, 205),
    (216, 209, 187),
]

ACCENTS = [
    (230, 173, 56),             # gold
    (82, 173, 133),             # teal
    (56, 143, 199),             # blue
    (122, 92, 199),             # violet
]


def pick(rng, coral=0.42, charcoal=0.28, cream=0.25):
    """Weighted brand color; whatever is left of 1.0 (~5%) goes to accents."""
    r = rng.random()
    if r < coral:
        return CORAL_RAMP[rng.randrange(len(CORAL_RAMP))]
    if r < coral + charcoal:
        return CHARCOAL_RAMP[rng.randrange(len(CHARCOAL_RAMP))]
    if r < coral + charcoal + cream:
        return CREAM_RAMP[rng.randrange(len(CREAM_RAMP))]
    return ACCENTS[rng.randrange(len(ACCENTS))]


def coral_faces(rng):
    """Three neighbouring coral-ramp shades for a solid cube: side, front, top."""
    i = rng.randrange(1, len(CORAL_RAMP) - 1)
    return CORAL_RAMP[i - 1], CORAL_RAMP[i], CORAL_RAMP[i + 1]
