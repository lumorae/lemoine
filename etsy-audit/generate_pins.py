"""
Generate Pinterest pin descriptions for every active Etsy listing.
Categorizes each listing, then produces 3 angled pins per listing:
  - Angle A: room/use-case (dorm, kids room, kitchen, etc.)
  - Angle B: gift angle (birthday, housewarming, etc.)
  - Angle C: aesthetic angle (watercolor, travel poster, minimalist, etc.)
Output: pins.md — one big markdown file, paste-ready.
"""
import json
import re
from pathlib import Path

SRC = Path(__file__).parent / "listings.json"
OUT = Path(__file__).parent / "pins.md"
OUT_JSON = Path(__file__).parent / "pins.json"

with SRC.open() as f:
    data = json.load(f)

def categorize(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["lightning", "mater", "cars ", "t-rex", "dinosaur", "elephant"]):
        return "kids"
    if any(w in t for w in ["astronaut", "cosmic", "space"]):
        return "space"
    if any(w in t for w in ["napa", "sonoma", "vineyard", "wine"]):
        return "wine_country"
    if any(w in t for w in ["florence", "vatican", "st. mark", "eiffel", "venice", "naples", "european", "italian", "paris", "rome"]):
        return "travel_europe"
    if any(w in t for w in ["boston", "san francisco", "sf ", "painted ladies", "golden gate"]):
        return "travel_us"
    if any(w in t for w in ["cacao", "meditation", "botanical", "sacred"]):
        return "wellness"
    return "art_general"

# Category → three angles: (label, board, description_template)
# Description templates use {short_title} and {url}
ANGLES = {
    "kids": [
        ("Kids Room", "Kids Room Decor",
         "{short_title} — hand-painted watercolor and ink print, perfect for kids' bedrooms, nurseries, and playrooms. Original artwork by Johnny Lemoine, printed on archival paper. Signed fine art print, ships flat. Shop on Etsy → {url}"),
        ("Gift", "Kids Gift Ideas",
         "Looking for a thoughtful gift for a car-loving, dinosaur-obsessed, or animal-crazy kid? This original watercolor by Johnny Lemoine is a keepsake, not another plastic toy. Available in 5 sizes plus digital download. → {url}"),
        ("Nursery Aesthetic", "Boys Nursery Ideas",
         "Whimsical hand-illustrated watercolor art for a modern nursery. Minimalist palette, playful subject, and a story behind every piece. A calmer alternative to mass-produced kids' decor. → {url}"),
    ],
    "space": [
        ("Dorm/Teen", "Dorm Room Decor",
         "{short_title} — surreal astronaut art print for dorm rooms, teen bedrooms, and creative studios. Bold pen-and-ink illustration by Johnny Lemoine. Signed fine art print. Shop on Etsy → {url}"),
        ("Gift for Dreamers", "Unique Gift Ideas",
         "A one-of-a-kind gift for space enthusiasts, skaters, sci-fi lovers, and grown-up dreamers. Hand-painted watercolor print by Johnny Lemoine. Available in multiple sizes + digital option. → {url}"),
        ("Modern Wall Art", "Modern Wall Art",
         "Cosmic pen-and-ink illustration — the kind of print that makes a room feel a little more interesting. For lofts, studios, and design-forward homes. → {url}"),
    ],
    "wine_country": [
        ("Kitchen/Dining", "Kitchen & Dining Art",
         "{short_title} — hand-painted watercolor print of California wine country, perfect for kitchens, dining rooms, and wine cellars. Original artwork by Johnny Lemoine. Ships flat. → {url}"),
        ("Housewarming Gift", "Housewarming Gift Ideas",
         "Wine-lover housewarming gift that isn't a candle. Hand-painted watercolor of Napa, Sonoma, and vineyard scenes. Fine art print by Johnny Lemoine. → {url}"),
        ("Travel Memory", "California Travel Art",
         "Bring the vineyards home. Original watercolor and ink prints of the wine country worth remembering. → {url}"),
    ],
    "travel_europe": [
        ("Living Room", "Living Room Wall Art",
         "{short_title} — hand-painted watercolor of European architecture, perfect for living rooms, hallways, and travel-inspired spaces. Original by Johnny Lemoine. Ships flat. → {url}"),
        ("Travel Gift", "Travel Gift Ideas",
         "For the friend who's still thinking about that trip. Hand-painted watercolor of Europe's most beautiful places. Signed fine art print. → {url}"),
        ("Travel Poster Aesthetic", "Travel Art & Posters",
         "Modern travel poster in hand-painted watercolor and ink — not a stock print. For homes that collect places instead of things. → {url}"),
    ],
    "travel_us": [
        ("Living Room", "Living Room Wall Art",
         "{short_title} — hand-painted watercolor of American cityscapes, perfect for living rooms, home offices, and travel-inspired spaces. Original by Johnny Lemoine. → {url}"),
        ("City Pride Gift", "City Pride Gift Ideas",
         "For someone who loves their city. Hand-painted watercolor of San Francisco, Boston, and the American cities worth framing. → {url}"),
        ("City Art Aesthetic", "American Cities Art",
         "Modern watercolor and ink illustration of iconic American landmarks. For city dwellers, ex-pats, and travelers. → {url}"),
    ],
    "wellness": [
        ("Meditation Space", "Meditation Room Decor",
         "{short_title} — hand-painted botanical watercolor for meditation rooms, yoga studios, and quiet spaces. Original by Johnny Lemoine. Signed fine art print. → {url}"),
        ("Wellness Gift", "Wellness Gift Ideas",
         "A calming gift for the yogi, healer, or meditator in your life. Hand-painted watercolor by Johnny Lemoine. → {url}"),
        ("Botanical Aesthetic", "Botanical Wall Art",
         "Sacred botanical watercolor for spaces that need a moment of quiet. Original pen-and-ink art. → {url}"),
    ],
    "art_general": [
        ("Living Room", "Living Room Wall Art",
         "{short_title} — original hand-painted watercolor and ink art by Johnny Lemoine. Perfect for living rooms and design-forward homes. Ships flat. → {url}"),
        ("Art Gift", "Art Gift Ideas",
         "A hand-painted watercolor print, not a mass-produced poster. Signed fine art print by Johnny Lemoine. → {url}"),
        ("Modern Art Aesthetic", "Modern Wall Art",
         "Original pen-and-ink illustration with watercolor. For homes that value handmade over stock. → {url}"),
    ],
}


def short_title(title: str) -> str:
    """Trim the descriptive tail after the em-dash / pipe for pin titles."""
    for sep in [" — ", " – ", " | ", " ("]:
        if sep in title:
            return title.split(sep)[0].strip()
    return title.strip()


def make_pin_title(short: str, angle_label: str) -> str:
    """Compose a Pinterest-searchable pin title, ≤ 100 chars."""
    base = f"{short} | {angle_label}"
    return base[:100]


listings = data["results"]

lines = [
    "# Pinterest Pin Content — johnnylemoine",
    "",
    f"Auto-generated from {len(listings)} active Etsy listings.",
    "3 pins per listing. Paste each pin's title + description into Pinterest, link to the Etsy URL, save to the suggested board.",
    "",
    "**Design specs for the pin image (do in Canva):**",
    "- 1000×1500 px vertical",
    "- Framed-on-wall mockup as primary visual (search Canva: 'wall art mockup')",
    "- Text overlay: pin title in bold sans-serif, coral or brand color",
    "- Price overlay in corner: 'From $23' pill",
    "",
    "---",
    "",
]

# Sort by views desc so highest-impact pins are at the top of the file
sorted_listings = sorted(listings, key=lambda l: -l["views"])

pins_json = []  # machine-readable output for post_pins.py

for listing in sorted_listings:
    title = listing["title"]
    short = short_title(title)
    url = listing["url"]
    views = listing["views"]
    favs = listing["num_favorers"]
    price = listing["price"]["amount"] / listing["price"]["divisor"]
    category = categorize(title)
    images = listing.get("images") or []
    primary_image = images[0].get("url_fullxfull") if images else None

    lines.append(f"## {short}")
    lines.append("")
    lines.append(f"- **Etsy title:** {title}")
    lines.append(f"- **URL:** {url}")
    lines.append(f"- **Stats:** {views} views · {favs} favorites · ${price:.2f}")
    lines.append(f"- **Category:** {category}")
    lines.append("")

    for i, (label, board, desc_tmpl) in enumerate(ANGLES[category], 1):
        pin_title = make_pin_title(short, label)
        pin_desc = desc_tmpl.format(short_title=short, url=url)
        lines.append(f"### Pin {i} — {label}")
        lines.append(f"- **Pin title:** `{pin_title}`")
        lines.append(f"- **Description:** {pin_desc}")
        lines.append(f"- **Board:** {board}")
        lines.append("")

        pins_json.append({
            "pin_id": f"{listing['listing_id']}-{i}",
            "listing_id": listing["listing_id"],
            "listing_title": title,
            "listing_url": url,
            "listing_views": views,
            "category": category,
            "angle_label": label,
            "pin_title": pin_title,
            "pin_description": pin_desc,
            "board_name": board,
            "image_url": primary_image,
        })

    lines.append("---")
    lines.append("")

OUT.write_text("\n".join(lines))
OUT_JSON.write_text(json.dumps(pins_json, indent=2))
print(f"Wrote {OUT} — {len(sorted_listings) * 3} pins for {len(sorted_listings)} listings")
print(f"Wrote {OUT_JSON} — machine-readable pin data for post_pins.py")
