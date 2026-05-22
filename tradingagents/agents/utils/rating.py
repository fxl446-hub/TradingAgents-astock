"""Shared 5-tier rating vocabulary and a deterministic heuristic parser.

The same five-tier scale (Buy, Overweight, Hold, Underweight, Sell) is used by:
- The Research Manager (investment plan recommendation)
- The Portfolio Manager (final position decision)
- The signal processor (rating extracted for downstream consumers)
- The memory log (rating tag stored alongside each decision entry)

Centralising it here avoids drift between those call sites.
"""

from __future__ import annotations

import re
from typing import Tuple


# Canonical, ordered 5-tier scale (most bullish to most bearish).
RATINGS_5_TIER: Tuple[str, ...] = (
    "Buy", "Overweight", "Hold", "Underweight", "Sell",
)

_RATING_SET = {r.lower() for r in RATINGS_5_TIER}

# Heading-style rating: "# **卖出**", "## Hold", etc.
# Must appear as a standalone heading line (not buried in prose).
_HEADING_RATING_RE = re.compile(
    r"^#{1,3}\s*\*{0,2}\s*(买入|持有|卖出|增持|减持|Buy|Hold|Sell|Overweight|Underweight)\s*\*{0,2}\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Structured label pattern: "Rating: Hold", "最终评级：持有", "**Rating**: Hold", etc.
# [\s*]* handles bold markers + whitespace between keyword and colon.
_RATING_LABEL_RE = re.compile(
    r"(?:rating|评级|建议|推荐)[\s*]*[：:\-][\s\*]*(买入|持有|卖出|增持|减持|Buy|Hold|Sell|Overweight|Underweight)",
    re.IGNORECASE,
)

_CN_RATING_MAP = {"买入": "Buy", "持有": "Hold", "卖出": "Sell",
                  "增持": "Overweight", "减持": "Underweight"}

# Only search the header/conclusion area for loose keywords to avoid false
# positives from analysis body text that discusses bullish/bearish arguments.
_HEADER_WINDOW = 600


def _extract_rating_from_text(text: str) -> str | None:
    """Try to extract a canonical rating from a single text blob."""

    # Pass 1a: markdown heading rating — "# **卖出**", "## Hold", etc.
    # These are the most authoritative signal, checked before everything.
    m = _HEADING_RATING_RE.search(text)
    if m:
        word = m.group(1)
        low = word.lower()
        if low in _RATING_SET:
            return word.capitalize()
        if word in _CN_RATING_MAP:
            return _CN_RATING_MAP[word]

    # Pass 1b: structured label per line — "Rating: Hold", "最终评级：持有", etc.
    for line in text.splitlines():
        m = _RATING_LABEL_RE.search(line)
        if m:
            word = m.group(1)
            low = word.lower()
            if low in _RATING_SET:
                return word.capitalize()
            if word in _CN_RATING_MAP:
                return _CN_RATING_MAP[word]

    # Pass 2: Chinese keyword in header window — first occurrence wins.
    header = text[:_HEADER_WINDOW]
    best_idx = len(header)
    best_label = None
    for cn_word, label in _CN_RATING_MAP.items():
        idx = header.find(cn_word)
        if idx != -1 and idx < best_idx:
            best_idx = idx
            best_label = label
    if best_label:
        return best_label

    # Pass 3: English keyword in header window — first occurrence wins.
    header_lower = header.lower()
    best_idx = len(header_lower)
    best_rating = None
    for rating in ("buy", "overweight", "hold", "underweight", "sell"):
        idx = header_lower.find(rating)
        if idx != -1 and idx < best_idx:
            best_idx = idx
            best_rating = rating.capitalize()
    if best_rating:
        return best_rating

    # Pass 4: last resort — scan full text for English keywords.
    for line in text.splitlines():
        for word in line.lower().split():
            clean = word.strip("*:.,()（）")
            if clean in _RATING_SET:
                return clean.capitalize()

    return None


def parse_rating(text: str, default: str = "Hold") -> str:
    """Extract a rating from prose, supporting English and Chinese markers."""
    result = _extract_rating_from_text(text)
    return result if result else default

