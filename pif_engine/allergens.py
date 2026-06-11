"""
Изчисление на алергени и генериране на INCI списък (Член 19).
"""
from __future__ import annotations
from .models import Product, ProductType, FormulaLine


# Прагове за деклариране на алергени (Регламент 1223/2009, Анекс III)
ALLERGEN_THRESHOLD = {
    ProductType.LEAVE_ON: 0.001,   # 0.001%
    ProductType.RINSE_OFF: 0.01,   # 0.01%
}


def calculate_allergens(product: Product) -> dict[str, float]:
    """Сумира всеки алерген от всички ароматни компоненти.

    Връща: {allergen_inci: обща_концентрация_в_продукта_%}
    Логика: принос = концентрация_на_компонента × масов_дял_на_алергена
    """
    totals: dict[str, float] = {}
    for line in product.formula:
        ing = line.ingredient
        if not ing.is_fragrance:
            continue
        for allergen in ing.allergens:
            contribution = line.concentration_pct * allergen.fraction
            totals[allergen.name] = totals.get(allergen.name, 0.0) + contribution
    return totals


def allergens_to_declare(product: Product) -> list[str]:
    """Връща алергените, които надвишават прага и трябва да са на етикета."""
    threshold = ALLERGEN_THRESHOLD[product.product_type]
    totals = calculate_allergens(product)
    declared = [name for name, conc in totals.items() if conc > threshold]
    # Сортирани по концентрация (низходящо), както изисква конвенцията
    declared.sort(key=lambda n: totals[n], reverse=True)
    return declared


def _consolidated_lines(product: Product) -> list[FormulaLine]:
    """Обединява редове със същото INCI име (напр. вода добавена на части),
    като сумира концентрациите. Връща нов списък FormulaLine."""
    merged: dict[str, FormulaLine] = {}
    order: list[str] = []
    for line in product.formula:
        key = line.ingredient.inci_name
        if key in merged:
            merged[key] = FormulaLine(
                merged[key].ingredient,
                merged[key].concentration_pct + line.concentration_pct,
            )
        else:
            merged[key] = FormulaLine(line.ingredient, line.concentration_pct)
            order.append(key)
    return [merged[k] for k in order]


def generate_inci(product: Product) -> list[str]:
    """Генерира INCI списък в низходящ ред по концентрация (Член 19).

    Правила:
    - Дублирани имена се обединяват (сумиране на концентрациите)
    - Съставки >= 1%: низходящ ред по концентрация
    - Съставки < 1%: след тях, в произволен ред (тук запазваме реда)
    - Декларируемите алергени се добавят СЛЕД целия списък със съставки
      (винаги в края, низходящо по концентрация — виж allergens_to_declare).
    """
    lines = _consolidated_lines(product)
    above_1 = sorted(
        [l for l in lines if l.concentration_pct >= 1.0],
        key=lambda l: l.concentration_pct, reverse=True
    )
    below_1 = [l for l in lines if l.concentration_pct < 1.0]

    inci: list[str] = [line.ingredient.inci_name for line in above_1 + below_1]

    # Алергените винаги трасират пълния списък със съставки (след Parfum,
    # който е част от съставките), без да изпреварват съставки с по-висока
    # концентрация. Не дублираме вече присъстващи имена.
    for a in allergens_to_declare(product):
        if a not in inci:
            inci.append(a)
    return inci
