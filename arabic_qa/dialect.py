"""Heuristic Arabic dialect cues: MSA vs Egyptian vs Levantine vs Gulf.

This is a cue-counting heuristic, not a classifier: it scores marker
words per variety and reports the evidence. Useful for spotting
mislabeled dialect rows in annotation batches, useless as a sole
arbiter — a human reviewer makes the call on borderline text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Marker lexicons: high-precision cue words per variety.
MARKERS: dict[str, list[str]] = {
    "egyptian": [
        "عايز", "عاوز", "عايزة", "إيه", "ايه", "كده", "كدا", "ليه", "دلوقتي",
        "بقى", "مش", "اوي", "قوي", "جداً", "جدا", "برضه", "برضو", "هيجي",
        "بتاع", "بتاعت", "عشان", "لما", "جوة", "بره", "كويس", "زي",
    ],
    "levantine": [
        "شو", "هلق", "بدي", "بدك", "مين", "ليش", "هيك", "كتير", "هلأ",
        "منيح", "شلون", "بكرة", "هسا",
    ],
    "gulf": [
        "شلون", "وش", "ليش", "الحين", "بغيت", "أبغى", "ترى", "وايد",
        "چذي", "هال", "مب", "زين",
    ],
    "msa": [
        "الذي", "التي", "ليس", "لكن", "حيث", "إذ", "قد", "سوف", "غير",
        "بينما", "خلال", "منذ", "حول", "ضد", "لدى", "إن", "أن",
    ],
}


@dataclass
class DialectGuess:
    variety: str
    confidence: str  # "low" | "medium" | "high"
    scores: dict[str, int]
    hits: dict[str, list[str]]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[ء-غف-ي٠-٩]+", text)


def guess_dialect(text: str) -> DialectGuess:
    tokens = _tokenize(text)
    hits: dict[str, list[str]] = {}
    scores: dict[str, int] = {}
    for variety, words in MARKERS.items():
        found = [t for t in tokens if t in words]
        hits[variety] = found
        scores[variety] = len(found)
    best = max(scores, key=lambda v: scores[v])
    total = sum(scores.values())
    if total == 0 or scores[best] == 0:
        return DialectGuess("unknown", "low", scores, hits)
    share = scores[best] / total
    confidence = "high" if scores[best] >= 3 and share >= 0.6 else (
        "medium" if scores[best] >= 2 else "low"
    )
    return DialectGuess(best, confidence, scores, hits)
