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
from datetime import date
from pathlib import Path

CUSTOM_FILE = Path(__file__).parent / "captions.json"

# Nov 1 to Dec 20 is when people shop for gifts, so captions lead with the gift.
HOLIDAY_START, HOLIDAY_END = (11, 1), (12, 20)

HOLIDAY_TEMPLATES = {
    "kids": [
        "A gift for the kid who already knows exactly what they love.\n\n{name}. Hand-painted watercolor and ink, ships rolled.",
        "Something for their wall that will outlast every toy under the tree.\n\n{name}",
    ],
    "space": [
        "A gift for the dreamer in your life.\n\n{name}. Pen, ink and watercolor, ships rolled.",
        "For the one who's hard to shop for.\n\n{name}",
    ],
    "wine_country": [
        "For the host who already has every candle.\n\n{name}. Hand-painted watercolor and ink, ships rolled.",
        "A gift for the friend who talks about Napa like it's home.\n\n{name}",
    ],
    "travel_europe": [
        "A gift for the person still thinking about that trip.\n\n{name}. Hand-painted watercolor and ink, ships rolled.",
        "Give them the place, not another thing.\n\n{name}",
    ],
    "travel_us": [
        "A gift for the friend who moved away and still misses home.\n\n{name}. Hand-painted watercolor and ink, ships rolled.",
        "For the one who loves this city.\n\n{name}",
        "A gift for someone's first apartment in a new city.\n\n{name}. Watercolor and ink, ships rolled.",
        "Wrap up the city they call home.\n\n{name}",
    ],
    "wellness": [
        "A calm gift for the person who takes care of everyone else.\n\n{name}. Botanical watercolor, ships rolled.",
        "For their quiet corner.\n\n{name}",
    ],
    "art_general": [
        "A gift that's real art, made by hand.\n\n{name}. Watercolor and ink, ships rolled.",
        "For the wall that's been empty too long.\n\n{name}",
    ],
}


def holiday_season(today: date | None = None) -> bool:
    today = today or date.today()
    return HOLIDAY_START <= (today.month, today.day) <= HOLIDAY_END

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
        "Every city has a block you'd know anywhere. This is one of mine.\n\n{name}. Watercolor and ink.",
        "Painted street by street, window by window.\n\n{name}, ships rolled.",
        "{name}. For the hallway, the home office, or the first apartment in a new city.",
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
                "illustration", "ink", "original", "giclee", "fine", "and", "&", "pen"}


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


def variants_for(listing: dict, custom: dict) -> list[str]:
    own = custom.get(str(listing["listing_id"]))
    if own:
        return own if isinstance(own, list) else [own]
    bank = HOLIDAY_TEMPLATES if holiday_season() else TEMPLATES
    return bank.get(listing["category"], bank["art_general"])


def caption_for(listing: dict, times_posted: int, custom: dict,
                recent: list[str] = ()) -> tuple[str, str]:
    """Caption for this listing's next post, ending with the Etsy link,
    plus the template it came from.

    `recent` is the templates of recent posts, oldest first. Those are
    skipped, so two pieces from the same category don't go out with the
    same wording; if every variant was used recently, the one used longest
    ago wins.
    """
    variants = variants_for(listing, custom)
    start = times_posted % len(variants)
    order = variants[start:] + variants[:start]
    last_use = {t: i for i, t in enumerate(recent)}
    template = min(order, key=lambda t: last_use.get(t, -1))
    body = template.format(name=display_name(listing["title"]))
    return f"{body}\n\nOn Etsy: {listing['url']}", template
