"""
Филтър на кандидати: не-INCI текст не бива да става съставка (Слой 2).

Извличането (parse/vision) понякога подава правни/таблични/адресни редове като
„съставки". Тук, в енджина, ги отсяваме, преди да могат да станат част от
черновата. Консервативно — извлеченото е само предложение за човешка проверка.

ПРИНЦИП (CLAUDE.md): не пропускаме тихо. Извикващият (router) добавя бележка с
броя на изхвърлените редове, за да се види, че нещо е премахнато.

Логиката (_CI_RE / _NON_INCI_RE / _plausible_inci / filter_candidates) е
пренесена дословно от UX слоя (app/engine.py), за да има ЕДИН източник в
енджина, а не дублирана евристика в презентационния слой.
"""
from __future__ import annotations
import re

# „CI 77491“ / „C.I. 77491“ е валиден Colour Index → не се отсява.
_CI_RE = re.compile(r"^(ci|c\.i\.)\s*\d{4,6}$", re.IGNORECASE)
_NON_INCI_RE = re.compile(
    r"(ppm|reach|regul|\breg\.|annex|registration|exempt|country of origin|"
    r"origin\b|refined|see point|paragraph|declaration|status|1907/?2006|"
    r"ec\s*1907|einecs|directive|according to|manufacturer|supplier|address|"
    r"batch|specification|\blimit\b|σ|gmbh|stra(?:ss|ß)e|seite|\btel\b|\bfax\b|"
    r"e-?mail|www|säure|\bpage\b|\bvon\b)",
    re.IGNORECASE)


def _plausible_inci(name: str) -> bool:
    """Грубо: прилича ли низът на INCI име, а НЕ на правен/табличен/адресен текст.

    Маркери за изхвърляне: двоеточие (напр. фатти-acid „C20:1“ или „Origin:“),
    процент/запетая в самото име, дълги изречения, цели числа (адрес/страница/
    пощенски код), ключови думи (REACh, ppm, „Limit“, GmbH, Seite, säure…).
    """
    s = (name or "").strip()
    if not s:
        return False
    if _CI_RE.match(s):                       # „CI 77491“ е валиден Colour Index
        return True
    if len(s) > 60:
        return False
    if any(ch in s for ch in (":", "%", "@")) or ", " in s:
        return False
    if _NON_INCI_RE.search(s):
        return False
    if re.search(r"\d{4,}", s):               # пощенски код / „1907“ / ppm число
        return False
    if any(re.fullmatch(r"\d+", tok) for tok in s.split()):  # самостоятелно число → адрес/страница
        return False
    letters = sum(c.isalpha() for c in s)
    if letters < 3 or letters / len(s) < 0.5:  # предимно цифри/пунктуация
        return False
    if len(s.split()) > 6:                     # цели изречения не са INCI
        return False
    return True


def filter_candidates(raw_materials: list[dict]) -> tuple[list[dict], int]:
    """Маха не-INCI кандидати от композициите. Връща (raw_materials, брой_изхвърлени)."""
    dropped = 0
    for rm in raw_materials or []:
        comp = rm.get("composition")
        if isinstance(comp, list) and comp:
            kept = [c for c in comp if _plausible_inci(c.get("inci_name", ""))]
            dropped += len(comp) - len(kept)
            rm["composition"] = kept
    return raw_materials, dropped
