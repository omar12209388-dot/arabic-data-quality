"""Arabic text normalization for downstream matching and dedup.

Conservative defaults: fold Eastern Arabic-Indic digits, strip tatweel
and diacritics, unify alef/ya/ta-marbuta variants, collapse whitespace.
Each step is a separate function so pipelines can opt out.
"""

from __future__ import annotations

import re

_EASTERN = "٠١٢٣٤٥٦٧٨٩"
_TATWEEL = "ـ"
_DIACRITICS_RE = re.compile(r"[ً-ٰٟ]")
_WS_RE = re.compile(r"\s+")

_ALEF_VARIANTS = "أإآٱ"
_TA_MARBUTA = "ة"
_FINAL_YA = "ى"


def fold_digits(text: str) -> str:
    """Eastern Arabic-Indic digits -> Western digits."""
    return text.translate({ord(ch): str(i) for i, ch in enumerate(_EASTERN)})


def strip_tatweel(text: str) -> str:
    return text.replace(_TATWEEL, "")


def strip_diacritics(text: str) -> str:
    return _DIACRITICS_RE.sub("", text)


def unify_alef(text: str) -> str:
    return text.translate({ord(ch): "ا" for ch in _ALEF_VARIANTS})


def unify_ya(text: str) -> str:
    return text.replace(_FINAL_YA, "ي")


def unify_ta_marbuta(text: str) -> str:
    return text.replace(_TA_MARBUTA, "ه")


def collapse_whitespace(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def normalize(
    text: str,
    *,
    digits: bool = True,
    tatweel: bool = True,
    diacritics: bool = True,
    alef: bool = True,
    ya: bool = False,
    ta_marbuta: bool = False,
) -> str:
    """Normalize with conservative defaults.

    `ya` and `ta_marbuta` unification are off by default: they help
    dedup/matching but destroy valid orthographic distinctions, so a
    pipeline should opt in explicitly.
    """
    if digits:
        text = fold_digits(text)
    if tatweel:
        text = strip_tatweel(text)
    if diacritics:
        text = strip_diacritics(text)
    if alef:
        text = unify_alef(text)
    if ya:
        text = unify_ya(text)
    if ta_marbuta:
        text = unify_ta_marbuta(text)
    return collapse_whitespace(text)
