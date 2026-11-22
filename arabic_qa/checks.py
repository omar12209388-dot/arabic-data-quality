"""Text-level quality checks for Arabic and mixed Arabic-English data.

Each check returns a Finding with a severity and an explanation, so a
reviewer can see exactly what was flagged and why. The checks encode
failure modes that show up constantly in Arabic annotation work:
mojibake, tatweel padding, leftover diacritics, mixed digit systems,
unintended code-switching, and Latin punctuation inside Arabic runs.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class Finding:
    check: str
    severity: str  # "info" | "warning" | "error"
    message: str


ARABIC_RE = re.compile(r"[؀-ۿ]")
LATIN_RE = re.compile(r"[A-Za-z]")
TATWEEL = "ـ"
DIACRITICS_RE = re.compile(r"[ً-ٰٟ]")
EASTERN_DIGITS_RE = re.compile(r"[٠-٩]")
WESTERN_DIGITS_RE = re.compile(r"[0-9]")

# UTF-8 Arabic misdecoded as Latin-1: the classic Ø/Ù + continuation-byte shapes.
MOJIBAKE_RE = re.compile(r"(?:[ØÙÚÛ][\u0080-\u00bf])+")


def script_stats(text: str) -> dict[str, float]:
    letters = [ch for ch in text if ch.isalpha()]
    n = len(letters)
    if not n:
        return {"letters": 0, "arabic_ratio": 0.0, "latin_ratio": 0.0}
    arabic = sum(1 for ch in letters if ARABIC_RE.match(ch))
    latin = sum(1 for ch in letters if LATIN_RE.match(ch))
    return {
        "letters": n,
        "arabic_ratio": round(arabic / n, 3),
        "latin_ratio": round(latin / n, 3),
    }


def check_mojibake(text: str) -> list[Finding]:
    hits = MOJIBAKE_RE.findall(text)
    if hits:
        return [Finding("mojibake", "error",
                        f"{len(hits)} likely misdecoded UTF-8 sequences "
                        f"(e.g. {hits[0]!r}); re-decode the source as UTF-8")]
    return []


def check_tatweel(text: str) -> list[Finding]:
    runs = re.findall(TATWEEL + r"{2,}", text)
    if runs:
        return [Finding("tatweel", "warning",
                        f"{len(runs)} tatweel stretch(es); usually stylistic "
                        "padding that breaks matching and search")]
    return []


def check_diacritics(text: str, max_ratio: float = 0.02) -> list[Finding]:
    stats = script_stats(text)
    if not stats["letters"]:
        return []
    n = len(DIACRITICS_RE.findall(text))
    ratio = n / stats["letters"]
    if ratio > max_ratio:
        return [Finding("diacritics", "info",
                        f"diacritic ratio {ratio:.1%} of letters; fine for "
                        "liturgical/learning text, noise for most NLP labels")]
    return []


def check_mixed_digits(text: str) -> list[Finding]:
    eastern = len(EASTERN_DIGITS_RE.findall(text))
    western = len(WESTERN_DIGITS_RE.findall(text))
    if eastern and western:
        return [Finding("mixed_digits", "warning",
                        f"{eastern} Eastern Arabic-Indic and {western} Western "
                        "digits in one string; normalize before numeric parsing")]
    return []


def check_code_switch(text: str, expected: str = "ar") -> list[Finding]:
    """Flag unexpected script mixing.

    expected="ar": warn when Latin words appear that are not common
    loanwords/brands; expected="mixed": no finding (true code-switched data).
    """
    if expected == "mixed":
        return []
    stats = script_stats(text)
    if expected == "ar" and stats["latin_ratio"] > 0.15:
        latin_words = re.findall(r"[A-Za-z]{2,}", text)
        return [Finding("code_switch", "warning",
                        f"latin ratio {stats['latin_ratio']:.0%} in Arabic-expected "
                        f"text; latin tokens: {latin_words[:6]}")]
    return []


def check_arabic_punctuation(text: str) -> list[Finding]:
    findings = []
    if ARABIC_RE.search(text) and re.search(r"[?]", text) and "؟" not in text:
        findings.append(Finding(
            "punctuation", "info",
            "Latin '?' in Arabic text; '؟' is the conventional form"))
    if re.search(r"\w,\s*[\u0621-\u064a]", text):
        findings.append(Finding(
            "punctuation", "info",
            "Latin comma directly before Arabic word; '،' is the conventional form"))
    return findings


CHECKS = [
    check_mojibake,
    check_tatweel,
    check_diacritics,
    check_mixed_digits,
    check_code_switch,
    check_arabic_punctuation,
]


def run_checks(text: str, expected: str = "ar") -> list[Finding]:
    findings: list[Finding] = []
    for check in CHECKS:
        if check is check_code_switch:
            findings.extend(check(text, expected=expected))
        else:
            findings.extend(check(text))
    return findings
