"""
Facebook captions for Etsy listings, in Johnny's voice.

Facebook is not Pinterest. Pin copy is written for search; a Facebook
caption is read by someone scrolling past, so it stays short, plain and
human. No emojis, no hashtags, no em dashes.

Each category has three variants. A listing's first post uses the first
variant, its second post (next time round the rotation) the second, and
so on, so a repeat never reads like a repeat.

Johnny's own words always win: put a caption (or a list of them) in
facebook/captions.json under the listing id and it is used instead.
Only Johnny's real details go there, never invented ones.
"""
import json
from pathlib import Path

CUSTOM_FILE = Path(__file__).parent / "captions.json"

TEMPLATES = {
    "kids": [
        "{name}. Watercolor and ink, painted by hand, for the kid who already knows exactly what they love.",
        "Kids' rooms deserve real art too. Not another poster from the big box aisle.\n\n{name}, hand-painted watercolor and ink.",
        "A gift that will still be on the wall in ten years.\n\n{name}. Original watercolor and ink, ships rolled.",
    ],
    "space": [
        "{name}. Pen, ink and watercolor, for anyone who still looks up.",
        "For the dreamers, the skaters, the late-night sci-fi crowd.\n\n{name}, hand-painted, ships rolled.",
        "A little strange, a little cosmic. The kind of print people ask about.\n\n{name}",
    ],
    "wine_country": [
        "{name}. Watercolor and ink of the vineyards, for the kitchen, the dining room, or the friend who just got back from Napa.",
        "A housewarming gift that isn't another candle.\n\n{name}, hand-painted, ships rolled.",
        "Bring the wine country home.\n\n{name}. Original watercolor and ink.",
    ],
    "travel_europe": [
        "{name}. Painted by hand in watercolor and ink, for the trip you still think about.",
        "Some places you collect. This one goes on the wall.\n\n{name}",
        "Not a stock travel poster. Hand-painted watercolor and ink.\n\n{name}, ships rolled.",
    ],
    "travel_us": [
        "{name}. Watercolor and ink, for anyone who loves this city or misses it.",
        "For the friend who moved away and still talks about home.\n\n{name}, hand-painted, ships rolled.",
        "City pride, painted by hand.\n\n{name}",
    ],
    "wellness": [
        "{name}. Botanical watercolor for the quiet corner of the house.",
        "For the yoga room, the reading chair, the place you go to slow down.\n\n{name}, hand-painted watercolor and ink.",
        "A calm gift for the person who takes care of everyone else.\n\n{name}",
    ],
    "art_general": [
        "{name}. Original watercolor and ink, made by hand.",
        "Handmade art for the wall that's been empty too long.\n\n{name}, ships rolled.",
        "Something real for the wall. Not mass-produced.\n\n{name}",
    ],
}


MEDIUM_WORDS = {"watercolor", "print", "prints", "art", "wall", "poster", "painting",
                "illustration", "ink", "original", "giclee", "fine"}


def display_name(etsy_title: str) -> str:
    """The piece's name without the SEO tail Etsy titles carry.

    "Florence Duomo Watercolor Print, Italy Wall Art" -> "Florence Duomo",
    since every caption already says it's watercolor and ink.
    """
    name = etsy_title
    for sep in [" — ", " – ", " | ", " (", ","]:
        name = name.split(sep)[0]
    words = name.split()
    while len(words) > 1 and words[-1].lower().strip(".") in MEDIUM_WORDS:
        words.pop()
    return " ".join(words)


def load_custom() -> dict:
    if CUSTOM_FILE.exists():
        return json.loads(CUSTOM_FILE.read_text())
    return {}


def caption_for(listing: dict, times_posted: int, custom: dict) -> str:
    """Caption for this listing's next post. Ends with the Etsy link."""
    own = custom.get(str(listing["listing_id"]))
    if own:
        variants = own if isinstance(own, list) else [own]
    else:
        variants = TEMPLATES.get(listing["category"], TEMPLATES["art_general"])
    body = variants[times_posted % len(variants)].format(name=display_name(listing["title"]))
    return f"{body}\n\nOn Etsy: {listing['url']}"
