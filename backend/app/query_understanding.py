"""Deterministic query understanding (architecture §6 "QUERY UNDERSTANDING", §7 step 4).

Extracts structured attributes (category, colour, occasion, gender, max price) from free text,
validated only against the catalogue's own controlled vocabulary (architecture §8.3) — never a
guessed or invented value. Deliberately deterministic, not an LLM: architecture §16 names "LLM
parser unpredictability" (invalid filters, fabricated attributes) as a named risk, mitigated by
"strict schema, allowed values, deterministic fallback" — this module *is* that deterministic
fallback. An LLM parser (EXP20) remains optional and, per the architecture, would need isolated
evaluation before being trusted anywhere near this path — not built here.

Extracted attributes become hard filters (architecture "hard constraints before soft
preference") applied alongside, not instead of, the full free-text query — the lexical/BM25
scoring in app/opensearch.py still sees the whole original query text.

Vocabulary below is a snapshot of the live catalogue (`SELECT DISTINCT colour FROM
product_variant`, etc.) taken during Stage 9 — regenerate if the catalogue's controlled values
change (architecture §8.3 "allowed categories, colours, sizes... controlled values").
"""

import re
from dataclasses import dataclass

# Longest-first so "Navy Blue" matches before "Blue" does.
CONTROLLED_COLOURS = sorted(
    [
        "Beige", "Black", "Blue", "Bronze", "Brown", "Burgundy", "Charcoal", "Coffee Brown",
        "Copper", "Cream", "Fluorescent Green", "Gold", "Green", "Grey", "Grey Melange", "Khaki",
        "Lavender", "Lime Green", "Magenta", "Maroon", "Mauve", "Metallic", "Multi",
        "Mushroom Brown", "Mustard", "Navy Blue", "Nude", "Off White", "Olive", "Orange",
        "Peach", "Pink", "Purple", "Red", "Rose", "Rust", "Sea Green", "Silver", "Skin", "Steel",
        "Tan", "Taupe", "Teal", "Turquoise Blue", "White", "Yellow",
    ],
    key=len,
    reverse=True,
)

CONTROLLED_OCCASIONS = sorted(
    ["Casual", "Ethnic", "Formal", "Home", "Party", "Smart Casual", "Sports", "Travel"],
    key=len,
    reverse=True,
)

CONTROLLED_GENDERS = ["Men", "Women", "Boys", "Girls", "Unisex"]

# The catalogue's real `category` column values (`SELECT DISTINCT category FROM product`),
# minus a handful deliberately excluded: "skin", "hair", "lips", "eyes", "nails", "home" are
# real category values in this dataset (Personal Care sub-categories) but are also common
# English words untethered from shopping intent ("skin" in "true to skin tone", "home" in
# almost anything) — auto-filtering on them risks wrongly *excluding* good results, which is a
# worse failure than not filtering at all (a hard filter is exactly that: hard). Safety over
# coverage, per architecture "build safe filters".
CONTROLLED_CATEGORIES = sorted(
    [
        "accessories", "apparel set", "bags", "bath and body", "beauty accessories", "belts",
        "bottomwear", "cufflinks", "dress", "eyewear", "flip flops", "fragrance", "free gifts",
        "gloves", "headwear", "innerwear", "jewellery", "loungewear and nightwear", "makeup",
        "mufflers", "perfumes", "sandal", "saree", "scarves", "shoe accessories", "shoes",
        "skin care", "socks", "sports accessories", "sports equipment", "stoles", "ties",
        "topwear", "umbrellas", "vouchers", "wallets", "watches", "water bottle", "wristbands",
    ],
    key=len,
    reverse=True,
)

# A small, deliberately narrow set of category words known NOT to appear in the catalogue's own
# vocabulary at all (see database/ingest.py's controlled category list) but that shoppers
# actually use — same gap EXP14 (synonym expansion) fixed for free-text search, applied here for
# filtering too. Checked only if no CONTROLLED_CATEGORIES term matched directly.
CATEGORY_ALIASES = {
    "trainers": "shoes",
    "sneakers": "shoes",
}

PRICE_PATTERN = re.compile(
    r"(?:under|below|less than|up to|max(?:imum)?)\s*£?\s*(\d+(?:\.\d+)?)", re.IGNORECASE
)

# The catalogue's real `size` column values (`SELECT DISTINCT size FROM product_variant`) — a
# mix of shoe sizes, waist-inch bottomwear sizes and letter tops sizes, with no numeric dress
# sizing at all (so a query like "size 12" genuinely has nothing to match — see Stage 12's data
# sheet note). Only extracted when preceded by the literal word "size": a bare number elsewhere
# in the query (a price, a quantity) must never be misread as a size — same "safe filters"
# principle as the ambiguous-category exclusions above.
_CANONICAL_SIZES = [
    "4", "5", "6", "7", "8", "9", "10", "11", "26", "28", "30", "32", "34", "36",
    "XS", "S", "M", "L", "XL", "XXL", "One Size",
]
CONTROLLED_SIZES = {size.lower(): size for size in _CANONICAL_SIZES}
SIZE_PATTERN = re.compile(r"\bsize\s*:?\s*([a-z0-9]+)\b", re.IGNORECASE)


@dataclass
class ParsedQuery:
    category: str | None = None
    colour: str | None = None
    occasion: str | None = None
    gender: str | None = None
    max_price: float | None = None
    size: str | None = None

    def is_empty(self) -> bool:
        return not any(
            (self.category, self.colour, self.occasion, self.gender, self.max_price, self.size)
        )


def _find_first(text_lower: str, vocabulary: list[str]) -> str | None:
    for term in vocabulary:
        if re.search(rf"\b{re.escape(term.lower())}\b", text_lower):
            return term
    return None


def parse_query(raw_query: str) -> ParsedQuery:
    text_lower = raw_query.lower()

    max_price = None
    price_match = PRICE_PATTERN.search(raw_query)
    if price_match:
        max_price = float(price_match.group(1))

    category = _find_first(text_lower, CONTROLLED_CATEGORIES)
    if category is None:
        for alias, real_category in CATEGORY_ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", text_lower):
                category = real_category
                break

    size = None
    if "one size" in text_lower:
        size = "One Size"
    else:
        size_match = SIZE_PATTERN.search(text_lower)
        if size_match:
            size = CONTROLLED_SIZES.get(size_match.group(1).lower())

    return ParsedQuery(
        category=category,
        colour=_find_first(text_lower, CONTROLLED_COLOURS),
        occasion=_find_first(text_lower, CONTROLLED_OCCASIONS),
        gender=_find_first(text_lower, CONTROLLED_GENDERS),
        max_price=max_price,
        size=size,
    )
