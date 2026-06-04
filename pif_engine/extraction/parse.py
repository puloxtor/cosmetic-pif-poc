"""
Евристичен парсър: редове текст → ПРЕДЛОЖЕНА композиция / алергени.

Покрива редовните случаи, които срещнахме (Phenbiox/Vitapherole числа и
диапазони, IFF/Symrise алергени, прости „INCI 100%", ARDA легенда-кодирано
A–G). Изходът е ЧЕРНОВА за човешка проверка — не доверен източник на числа
(CLAUDE.md).

Стратегия за композиция: ако открием заглавие на композиционна секция,
парсваме САМО нея (region focus) — така отрязваме адреси/спецификации/легенда.
В тази секция позволяваме и легенда-кодове (A–G → диапазони). Извън секция
ползваме филтър за спецификации.

Не покрива (маркира се за ръчно въвеждане): сканирани изображения / ръкопис.
"""
from __future__ import annotations
import copy
import re

CAS_RE = re.compile(r"\b\d{2,7}-\d{2}-\d\b")
EINECS_RE = re.compile(r"\b\d{3}-\d{3}-\d\b")
ANNEX_RE = re.compile(r"\b(?:II|III|IV|V|VI)\s*/\s*\d+[a-z]?\b")
RANGE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)")
NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
ND_RE = re.compile(r"(n\.?\s*d\.?|----|—{2,})", re.I)

# Заглавие на композиционна секция / стоп маркери
COMP_HEADING_RE = re.compile(
    r"composi[tz]ion|inci\s+name|inci\s+statement|%\s*inclusion|content,\s*wt", re.I)
STOP_HEADING_RE = re.compile(
    r"legenda|index|preparato|specification|caratteristic|disclaimer|recommendation|"
    r"storage|shelf|trattandosi|as the product|all the information|hazard|first aid|"
    r"section\s+\d", re.I)
# Редове, дефиниращи легендата (да се пропускат)
LEGEND_DEF_RE = re.compile(r"\b(superiore|inferiore|compreso|above|below|between)\b", re.I)
LEGEND_CODE_RE = re.compile(r"^(.+?)\s+([A-G])$")
LEGEND_MAP = {
    "A": {"remainder": True},          # над 50% (отворена горна граница)
    "B": {"range": [25.0, 50.0]},
    "C": {"range": [10.0, 24.9]},
    "D": {"range": [5.0, 9.9]},
    "E": {"range": [1.0, 4.9]},
    "F": {"range": [0.1, 0.9]},
    "G": {"range": [0.0, 0.1]},
}
# Спецификации/футъри (отрязват се при липса на разпозната секция)
SPEC_SKIP_RE = re.compile(
    r"\b(pH|densit|density|peroxid|iodine|refraction|viscosit|saponif|acid value|"
    r"aspect|aspetto|appearance|odour|odor|colour|color|microbial|conta|cfu|yeast|"
    r"mould|absent|assente|tariff|customs|revision|pagina|page|tel|fax|www|e-mail|"
    r"email|box|shelf|storage|hazard|section|via|sede|sito|web)\b", re.I)


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def _strip_codes(text: str) -> str:
    return EINECS_RE.sub(" ", CAS_RE.sub(" ", text))


def _clean_name(text: str) -> str:
    text = ANNEX_RE.sub(" ", text)
    text = re.sub(r"\bAND\b", " ", text)
    text = re.sub(r"\bN\.?A\.?\b", " ", text)
    text = re.sub(r"[*/()]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -.,:;")
    return text


def _plausible_name(name: str) -> bool:
    return sum(c.isalpha() for c in name) >= 3


def _focus_region(lines: list[str]) -> list[str] | None:
    """Връща композиционната секция (от заглавие до стоп), или None."""
    start = None
    for i, l in enumerate(lines):
        if COMP_HEADING_RE.search(l):
            start = i
            break
    if start is None:
        return None
    region = [lines[start]]
    for l in lines[start + 1:]:
        if STOP_HEADING_RE.search(l):
            break
        region.append(l)
    return region


def _value_spec(line: str) -> tuple[dict, str] | None:
    """Опитва да извлече (spec, name) от ред с число/диапазон."""
    s = _strip_codes(line)
    m = RANGE_RE.search(s)
    if m:
        lo, hi = _num(m.group(1)), _num(m.group(2))
        if 0 < lo <= hi <= 100:
            name = _clean_name(s[: m.start()])
            return ({"inci_name": name, "range": [lo, hi]}, name)
    nums = list(NUM_RE.finditer(s))
    if nums:
        v = _num(nums[-1].group(0))
        if 0 < v <= 100:
            name = _clean_name(s[: nums[-1].start()])
            return ({"inci_name": name, "pct": v}, name)
    return None


def parse_composition(lines: list[str]) -> list[dict]:
    """Редове → [{inci_name, pct|range|remainder}]. Виж стратегията горе."""
    region = _focus_region(lines)
    if region is not None:
        scope, legend_ok, skip_specs = region, True, False
    else:
        scope, legend_ok, skip_specs = lines, False, True

    out: list[dict] = []
    for raw in scope:
        if LEGEND_DEF_RE.search(raw):
            continue
        if skip_specs and SPEC_SKIP_RE.search(raw):
            continue

        parsed = _value_spec(raw)
        if parsed:
            spec, name = parsed
            if _plausible_name(name):
                out.append(spec)
            continue

        if legend_ok:
            s = _clean_name(_strip_codes(raw))
            m = LEGEND_CODE_RE.match(s)
            if m and _plausible_name(m.group(1)) and not any(c.isdigit() for c in s):
                out.append({"inci_name": m.group(1).strip(),
                            **copy.deepcopy(LEGEND_MAP[m.group(2)])})
    return out


def parse_fragrance(lines: list[str]) -> list[dict]:
    """Редове → [{name, cas, pct_in_fragrance}] за ДЕКЛАРИРАНИ алергени.

    Изисква CAS на реда (отсява заглавия/адреси). 'n.d.'/'----' се пропускат.
    """
    out: list[dict] = []
    for raw in lines:
        cas_m = CAS_RE.search(raw)
        if not cas_m or ND_RE.search(raw):
            continue
        stripped = _strip_codes(raw)
        nums = list(NUM_RE.finditer(stripped))
        if not nums:
            continue
        val = _num(nums[-1].group(0))
        if not (0 < val <= 100):
            continue
        name = _clean_name(stripped[: nums[-1].start()])
        if _plausible_name(name):
            out.append({"name": name, "cas": cas_m.group(0), "pct_in_fragrance": val})
    return out


def looks_like_fragrance(lines: list[str], filename: str = "") -> bool:
    """Бърза евристика: документ за ароматни алергени?"""
    hay = (filename + " " + " ".join(lines[:15])).lower()
    if any(k in hay for k in ("allergen", "fragrance", "parfum", "parfüm")):
        return True
    return sum(1 for l in lines if CAS_RE.search(l)) >= 10
