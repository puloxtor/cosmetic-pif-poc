"""
INCI номенклатура (детерминистична, регулаторна) — Слой 1.

Привежда имената на съставките към официалния EU INCI вид и определя кои ароматни
вещества са ДЕКЛАРИРУЕМИ алергени (Анекс III, Регламент (ЕО) 1223/2009). Това е
детерминистичен код, не LLM (CLAUDE.md). Справочните таблици (синоними, алергени)
са РЕДАКТИРУЕМИ данни — поддържай ги спрямо актуалния закон.
"""
from __future__ import annotations
import re

_UPPER = {"peg", "ppg", "pvp", "pvm", "vp", "va", "sd", "mea", "dea", "tea",
          "edta", "bht", "bha", "tbhq", "pca", "ci", "pg", "ahas"}
_CI_RE = re.compile(r"^ci\s*\d{4,6}$", re.IGNORECASE)
_LOWER_PREFIX = {"alpha", "beta", "gamma", "delta", "cis", "trans",
                 "ortho", "meta", "para", "sec", "tert", "dl", "d", "l", "n"}


def _cap(w: str) -> str:
    return w[:1].upper() + w[1:].lower() if w else w


def _title_token(tok: str) -> str:
    low = tok.lower()
    if low in _UPPER:
        return tok.upper()
    m = re.match(r"^([a-z]+)-(\d+[a-z]?)$", tok, re.IGNORECASE)
    if m:
        head = m.group(1)
        head = head.upper() if head.lower() in _UPPER else _cap(head)
        return f"{head}-{m.group(2)}"
    if "-" in tok:
        parts = tok.split("-")
        out = []
        for i, p in enumerate(parts):
            out.append(p.lower() if i == 0 and p.lower() in _LOWER_PREFIX
                       else _title_token(p))
        return "-".join(out)
    if any(ch.isdigit() for ch in tok):
        return tok
    return _cap(tok)


def _to_title(name: str) -> str:
    s = re.sub(r"\s+", " ", (name or "").strip())
    if not s:
        return s
    if _CI_RE.match(s):
        return "CI " + re.sub(r"\D", "", s)
    return " ".join(_title_token(t) for t in s.split(" "))


def _key(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


_SYNONYMS = {
    "water": "Aqua", "eau": "Aqua",
    "sunflower oil": "Helianthus Annuus Seed Oil",
    "sunflower seed oil": "Helianthus Annuus Seed Oil",
    "almond oil": "Prunus Amygdalus Dulcis Oil",
    "sweet almond oil": "Prunus Amygdalus Dulcis Oil",
    "castor oil": "Ricinus Communis Seed Oil",
    "argan oil": "Argania Spinosa Kernel Oil",
    "jojoba oil": "Simmondsia Chinensis Seed Oil",
    "olive oil": "Olea Europaea Fruit Oil",
    "mixed tocopherols": "Tocopherol", "tocopherols": "Tocopherol",
    "vitamin e": "Tocopherol",
    "butylhydroxytoluol": "BHT", "butylated hydroxytoluene": "BHT",
    "fragrance": "Parfum", "parfum/aroma": "Parfum",
}


def canonical_inci(name: str) -> str:
    k = _key(name)
    if not k:
        return ""
    return _SYNONYMS.get(k) or _to_title(name)


_DECLARABLE_26 = {
    "amyl cinnamal": "Amyl Cinnamal",
    "amylcinnamyl alcohol": "Amylcinnamyl Alcohol",
    "anise alcohol": "Anise Alcohol",
    "benzyl alcohol": "Benzyl Alcohol",
    "benzyl benzoate": "Benzyl Benzoate",
    "benzyl cinnamate": "Benzyl Cinnamate",
    "benzyl salicylate": "Benzyl Salicylate",
    "cinnamal": "Cinnamal",
    "cinnamyl alcohol": "Cinnamyl Alcohol",
    "citral": "Citral",
    "citronellol": "Citronellol",
    "coumarin": "Coumarin",
    "eugenol": "Eugenol",
    "farnesol": "Farnesol",
    "geraniol": "Geraniol",
    "hexyl cinnamal": "Hexyl Cinnamal",
    "hydroxycitronellal": "Hydroxycitronellal",
    "isoeugenol": "Isoeugenol",
    "limonene": "Limonene",
    "linalool": "Linalool",
    "methyl 2-octynoate": "Methyl 2-Octynoate",
    "alpha-isomethyl ionone": "alpha-Isomethyl Ionone",
    "butylphenyl methylpropional": "Butylphenyl Methylpropional",
    "evernia prunastri extract": "Evernia Prunastri Extract",
    "evernia furfuracea extract": "Evernia Furfuracea Extract",
    "hydroxyisohexyl 3-cyclohexene carboxaldehyde":
        "Hydroxyisohexyl 3-Cyclohexene Carboxaldehyde",
}
_DECLARABLE_EXTRA: dict[str, str] = {}
DECLARABLE_ALLERGENS = {**_DECLARABLE_26, **_DECLARABLE_EXTRA}


def declarable_name(name: str) -> str | None:
    return (DECLARABLE_ALLERGENS.get(_key(canonical_inci(name)))
            or DECLARABLE_ALLERGENS.get(_key(name)))


def is_declarable(name: str) -> bool:
    return declarable_name(name) is not None


_EU = {"", "EU", "BG", "DE", "FR", "IT", "ES", "NL", "PL", "RO", "GR", "AT",
       "BE", "CZ", "DK", "EE", "FI", "HR", "HU", "IE", "LT", "LU", "LV", "MT",
       "PT", "SE", "SI", "SK", "CY"}
_US_MAP = {"Aqua": "Water", "Parfum": "Fragrance", "Aroma": "Flavor"}


def localize_inci(name: str, countries: list[str] | None) -> str:
    cs = [c.strip().upper() for c in (countries or []) if c.strip()]
    if cs and all(c not in _EU for c in cs):
        return _US_MAP.get(name, name)
    return name


_NON_INCI = re.compile(r"(ppm|reach|annex|registration|\blimit\b|gmbh|\bpage\b)",
                       re.IGNORECASE)


def validate_inci(names: list[str]) -> list[str]:
    issues, seen = [], set()
    for n in names:
        k = _key(n)
        if k in seen:
            issues.append(f'Дубликат INCI: „{n}“.')
        seen.add(k)
        if len(n) > 60 or _NON_INCI.search(n) or "%" in n or ":" in n:
            issues.append(f'Съмнително INCI име: „{n}“ — провери спрямо CosIng.')
    return issues
