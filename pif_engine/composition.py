"""
Композиционен компилатор (Слой 1, детерминистичен).

Превръща ВХОД ОТ ПРОДУКТ (суровини + композишън стейтмънти) в стандартния
модел Product/FormulaLine/Ingredient, който енджинът вече консумира.

Логика, демонстрирана и валидирана ръчно:
  концентрация на съставка в продукта = доза_на_суровината × дял_в_суровината/100
  - диапазон → взима се ГОРНАТА граница (worst-case)
  - повтарящи се INCI имена се сумират (прави го генераторът на INCI)
  - ароматна суровина → една съставка "Parfum" + алергени (дял в парфюма)

ПРИНЦИП (CLAUDE.md): това е детерминистичен код, не LLM. Не нормализираме
тихо — при разминаване (напр. сума ≠ 100%) връщаме предупреждение (аларма).
"""
from __future__ import annotations
from typing import Optional, Any

from .models import (
    Product, ProductType, Ingredient, FormulaLine, Claim, AllergenContent,
    ToxProfile,
)
from .nomenclature import canonical_inci, declarable_name, is_suppressed_function

SUM_TOLERANCE = 0.5   # допустимо отклонение на сумата от 100%


def _parse_tox(spec: Optional[dict]) -> Optional[ToxProfile]:
    if not spec:
        return None
    return ToxProfile(
        pod=float(spec["pod"]),
        dermal_absorption=float(spec.get("dermal_absorption", 0.5)),
    )


def resolve_amount(spec: dict) -> tuple[float, float, str, bool]:
    """Разрешава дела на един конституент в суровината.

    Връща (upper, lower, note, is_remainder):
      upper        — стойността, която ползваме за концентрацията (worst-case)
      lower        — долна граница (само за изчисляване на 'remainder' на съсед)
      note         — обяснение, ако е приложено правило
      is_remainder — True, ако стойността е отворена и се смята като остатък

    Поддържани форми:
      {pct: X}              точна стойност
      {range: [low, high]}  взима high
      {at_most: X}          (≤X) взима X
      {remainder: true}     отворена горна граница → остатък до 100%
    """
    if spec.get("remainder"):
        return (0.0, 0.0, "остатък до 100% (отворена горна граница)", True)
    if "pct" in spec:
        v = float(spec["pct"])
        return (v, v, "", False)
    if "range" in spec:
        lo, hi = spec["range"]
        lo, hi = float(lo), float(hi)
        return (hi, lo, f"диапазон {lo}-{hi}% → горна граница {hi}%", False)
    if "at_most" in spec:
        v = float(spec["at_most"])
        return (v, 0.0, f"≤{v}% → {v}%", False)
    raise ValueError(
        f"Конституент без разпозната стойност (pct/range/at_most/remainder): {spec}"
    )


def expand_raw_material(rm: dict, warnings: list[str]) -> list[FormulaLine]:
    """Разлага една суровина на редове от формулата (FormulaLine)."""
    name = rm.get("name", "?")
    if "dose_pct" not in rm:
        raise ValueError(f"Суровина '{name}': липсва dose_pct.")
    dose = float(rm["dose_pct"])

    # --- Ароматна суровина: една съставка Parfum + алергени ---
    if rm.get("is_fragrance"):
        allergens = []
        for a in rm.get("allergens", []):
            if declarable_name(a["name"]) is None:
                continue
            allergens.append(AllergenContent(
                name=declarable_name(a["name"]) or a["name"],
                cas=a.get("cas", "-"),
                fraction=float(a["pct_in_fragrance"]) / 100.0,
            ))
        parfum = Ingredient(
            inci_name=canonical_inci(rm.get("inci_name", "Parfum")),
            cas=rm.get("cas", "-"),
            function=rm.get("function", "ароматна композиция"),
            is_fragrance=True,
            allergens=allergens,
            has_sds=rm.get("has_sds", True),
            has_coa=rm.get("has_coa", True),
            has_ifra=rm.get("has_ifra", True),
        )
        return [FormulaLine(parfum, dose)]

    # --- Обикновена суровина: разлагане по композиция ---
    comp = rm.get("composition")
    if not comp:
        raise ValueError(f"Суровина '{name}': липсва composition (или is_fragrance).")

    resolved = [(resolve_amount(c), c) for c in comp]
    others_lower_sum = sum(r[0][1] for r in resolved if not r[0][3])

    lines: list[FormulaLine] = []
    for (upper, lower, note, is_remainder), c in resolved:
        if is_remainder:
            upper = max(0.0, 100.0 - others_lower_sum)
            warnings.append(
                f"⚠️ {name} / {c['inci_name']}: {note} → прието {upper:.3f}%."
            )
        elif note:
            warnings.append(f"ℹ️ {name} / {c['inci_name']}: {note}.")
        conc = dose * upper / 100.0
        ing = Ingredient(
            inci_name=canonical_inci(c["inci_name"]),
            cas=c.get("cas", "-"),
            function=c.get("function", rm.get("function", "")),
            tox=_parse_tox(c.get("tox")),
            restricted=c.get("restricted", False),
            max_allowed_pct=c.get("max_allowed_pct"),
            has_sds=rm.get("has_sds", True),
            has_coa=rm.get("has_coa", True),
        )
        lines.append(FormulaLine(ing, conc))
    return lines


def build_product(doc: dict) -> tuple[Product, list[str]]:
    """Сглобява Product от входен документ. Връща (product, warnings)."""
    if not isinstance(doc, dict) or "product" not in doc:
        raise ValueError("Невалиден вход: липсва секция 'product'.")
    p = doc["product"]
    for key in ("name", "product_type"):
        if key not in p:
            raise ValueError(f"Секция 'product': липсва задължителен ключ '{key}'.")

    warnings: list[str] = []
    raw_materials = doc.get("raw_materials", [])
    if not raw_materials:
        raise ValueError("Липсва секция 'raw_materials' (или е празна).")

    formula: list[FormulaLine] = []
    for rm in raw_materials:
        formula.extend(expand_raw_material(rm, warnings))

    # --- Аларма за сумата (не нормализираме тихо) ---
    dose_total = sum(float(rm["dose_pct"]) for rm in raw_materials)
    if abs(dose_total - 100.0) > SUM_TOLERANCE:
        warnings.append(
            f"⚠️ Сумата на суровините = {dose_total:.3f}% (≠ 100%). "
            f"Смятам по рецептата буквално, не нормализирам — провери входа."
        )

    cpnp = p.get("cpnp_code")
    name = f"{p['name']} (CPNP {cpnp})" if cpnp else p["name"]
    product = Product(
        name=name,
        product_type=ProductType(p["product_type"]),
        formula=formula,
        claims=[Claim(text=c) for c in doc.get("claims", [])],
        sale_countries=p.get("sale_countries", []),
        body_weight_kg=float(p.get("body_weight_kg", 60.0)),
        applied_amount_g=float(p.get("applied_amount_g", 10.46)),
        retention_factor=float(p.get("retention_factor", 0.01)),
    )
    return product, warnings


def suppressed_ingredients(product: Product) -> list[Ingredient]:
    """Съставки, изключени от етикетната INCI листа според функцията си
    (напр. денатуранти, Член 19). Дедупликирани по INCI име, в реда на поява.

    ЕДИНСТВЕН източник за: (1) филтъра в generate_inci и (2) одитната бележка
    в CPSR Част А. И двете тръгват оттук, за да няма тих пропуск (CLAUDE.md).
    """
    out: list[Ingredient] = []
    seen: set[str] = set()
    for line in product.formula:
        ing = line.ingredient
        if is_suppressed_function(ing.function) and ing.inci_name not in seen:
            seen.add(ing.inci_name)
            out.append(ing)
    return out


def consolidated_concentrations(product: Product) -> dict[str, float]:
    """Сумира концентрациите по INCI име (за таблицата на разбивката)."""
    totals: dict[str, float] = {}
    for line in product.formula:
        key = line.ingredient.inci_name
        totals[key] = totals.get(key, 0.0) + line.concentration_pct
    return totals
