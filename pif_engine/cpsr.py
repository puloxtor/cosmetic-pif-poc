"""
Генератор на Доклад за безопасност (CPSR) — Част А и Част Б.
Регламент 1223/2009, Анекс I.
"""
from __future__ import annotations
from datetime import date
from .models import Product
from .allergens import (
    generate_inci, allergens_to_declare, calculate_allergens, ALLERGEN_THRESHOLD,
)
from .composition import suppressed_ingredients
from .toxicology import product_is_safe, MOS_SAFETY_THRESHOLD
from .claims import validate_all_claims
from .provenance import engine_provenance
from .regulatory_refs import REGULATORY_REFS


def check_documentation_gates(product: Product) -> list[str]:
    """Блокери: суровина без задължителни документи не може да премине."""
    issues = []
    for line in product.formula:
        ing = line.ingredient
        missing = []
        if not ing.has_coa:
            missing.append("CoA")
        if not ing.has_sds:
            missing.append("SDS")
        if ing.is_fragrance and not ing.has_ifra:
            missing.append("IFRA")
        if missing:
            issues.append(f"{ing.inci_name}: липсват {', '.join(missing)}")
        if ing.restricted and ing.max_allowed_pct is not None:
            if line.concentration_pct > ing.max_allowed_pct:
                issues.append(
                    f"{ing.inci_name}: {line.concentration_pct}% надвишава "
                    f"лимита {ing.max_allowed_pct}% (Анекси II–VI)"
                )
    return issues


def generate_cpsr(product: Product) -> str:
    """Сглобява пълния CPSR като markdown документ."""
    gate_issues = check_documentation_gates(product)
    inci = generate_inci(product)
    allergens = allergens_to_declare(product)
    allergen_totals = calculate_allergens(product)
    safe, mos_results = product_is_safe(product)
    claim_results = validate_all_claims(product)

    L = []
    L.append(f"# ДОКЛАД ЗА БЕЗОПАСНОСТ НА КОЗМЕТИЧЕН ПРОДУКТ (CPSR)")
    L.append(f"## {product.name}")
    L.append(f"*Регламент (ЕО) № 1223/2009, Анекс I — Дата: {date.today()}*\n")

    if gate_issues:
        L.append("## ⛔ БЛОКЕРИ — документът НЕ е финализиран")
        for i in gate_issues:
            L.append(f"- {i}")
        L.append("")

    # ---- ЧАСТ А ----
    L.append("# ЧАСТ А — Информация за безопасността\n")
    L.append("## A.1 Качествен и количествен състав")
    L.append("| INCI | Функция | Концентрация (% w/w) |")
    L.append("|------|---------|----------------------|")
    for line in sorted(product.formula, key=lambda l: l.concentration_pct, reverse=True):
        L.append(f"| {line.ingredient.inci_name} | {line.ingredient.function} "
                 f"| {line.concentration_pct} |")
    total = sum(l.concentration_pct for l in product.formula)
    L.append(f"\n**Общо: {total:.2f}%** "
             f"{'✅' if abs(total-100) < 0.01 else '⚠️ ≠ 100%'}\n")

    # Одитна следа: съставки, документирани в Част А, но ИЗКЛЮЧЕНИ от етикетната
    # INCI листа според функцията си (напр. денатуранти, Член 19). Не е тих
    # пропуск — изброяваме всяка изключена съставка и причината (CLAUDE.md).
    # Воден от същия suppressed_ingredients, който управлява и филтъра в INCI.
    suppressed = suppressed_ingredients(product)
    if suppressed:
        L.append("### Изключени от етикетната INCI листа (одитна следа)")
        for ing in suppressed:
            L.append(
                f"- ⚠️ Изключено от INCI декларацията "
                f"({ing.function}, не се декларира): "
                f"„{ing.inci_name}“ — присъства в суровина, но не влиза в "
                f"етикетната INCI листа съгласно функцията си."
            )
        L.append("")

    L.append("## A.2 Класификация и излагане")
    L.append(f"- Тип продукт: **{product.product_type.value}**")
    L.append(f"- Праг за алергени: "
             f"{'0.001%' if product.product_type.value=='leave-on' else '0.01%'}")
    L.append(f"- Приложено количество: {product.applied_amount_g} g/ден")
    L.append(f"- Фактор на ретенция: {product.retention_factor}")
    L.append(f"- Калкулирана дневна експозиция: {product.daily_exposure_g:.4f} g/ден")
    L.append(f"- A (експозиция): {product.exposure_A_mg_per_kg:.4f} mg/kg bw/day")
    L.append(f"- Телесно тегло (SCCS): {product.body_weight_kg} kg\n")

    L.append("## A.3 Алергени от ароматни компоненти")
    if allergen_totals:
        L.append("| Алерген | Обща концентрация (%) | Деклариране |")
        L.append("|---------|----------------------|-------------|")
        for name, conc in sorted(allergen_totals.items(),
                                 key=lambda x: x[1], reverse=True):
            decl = "✅ ДА" if name in allergens else "—"
            L.append(f"| {name} | {conc:.5f} | {decl} |")
    else:
        L.append("Няма ароматни компоненти с регулирани алергени.")
    L.append("")

    # ---- ЧАСТ Б ----
    L.append("# ЧАСТ Б — Оценка на безопасността\n")
    L.append("## Б.1 Токсикологична оценка (SED / MoS)")
    if mos_results:
        L.append("| Съставка | SED (mg/kg bw/d) | MoS | Заключение |")
        L.append("|----------|------------------|-----|------------|")
        for r in mos_results:
            flag = "✅ безопасно" if r.is_safe else "❌ MoS<100"
            L.append(f"| {r.inci_name} | {r.sed} | {r.mos} | {flag} |")
    else:
        L.append("Няма съставки с въведен токсикологичен профил.")
    L.append("")

    L.append("## Б.2 Заключение за безопасност")
    verdict = "✅ БЕЗОПАСЕН" if safe and not gate_issues else "❌ НЕ Е ДОКАЗАН КАТО БЕЗОПАСЕН"
    L.append(f"**{verdict}**")
    L.append("\n> ⚠️ Изисква подпис на квалифициран оценител на безопасността "
             "(Член 10 от Регламент 1223/2009). Системата подготвя, не замества оценителя.\n")

    # ---- Изходи за Тенчо ----
    L.append("# ИЗХОДИ ЗА ЕТИКЕТИРАНЕ (към Тенчо)\n")
    L.append("## INCI списък (Член 19, низходящ ред)")
    L.append("`" + ", ".join(inci) + "`\n")

    L.append("## Валидиране на претенции")
    L.append("| Претенция | Статус | Причина |")
    L.append("|-----------|--------|---------|")
    for c in claim_results:
        icon = {"approved": "✅", "blocked": "⛔", "needs_evidence": "⚠️"}[c.status]
        L.append(f"| {c.claim} | {icon} {c.status} | {c.reason} |")
    L.append("")

    L.append("## Задължителни елементи на етикета (Член 19)")
    L.append("- [ ] PAO символ или дата на минимална трайност (пясъчен часовник)")
    L.append("- [ ] Партиден номер")
    L.append("- [ ] Номинално съдържание")
    L.append("- [ ] Отговорно лице и адрес")
    L.append("- [ ] Държава на произход (ако внос)")
    L.append("- [ ] Предупреждения за безопасност")

    # ---- Произход на доклада (одитна следа, R3/R4) ----
    # Кой енджин (версия + commit) и кои прагове са произвели ТОЗИ доклад.
    # Подписващият оценител (Член 10) трябва да види точно това.
    prov = engine_provenance()
    allergen_thr = ALLERGEN_THRESHOLD[product.product_type]
    L.append("\n---")
    L.append("## Произход на доклада (одитна следа)")
    L.append(f"- Енджин версия: **{prov['version']}** · commit "
             f"`{prov['sha']}` ({prov['source']})")
    L.append(f"- Дата на генериране: {date.today()}")
    L.append(f"- Праг за алергени ({product.product_type.value}): "
             f"**{allergen_thr}%** — {REGULATORY_REFS['ALLERGEN_THRESHOLD']}")
    L.append(f"- Праг за MoS: **{MOS_SAFETY_THRESHOLD}** — "
             f"{REGULATORY_REFS['MOS_SAFETY_THRESHOLD']}")
    L.append(f"- Подредба на INCI: {REGULATORY_REFS['ART_19_INCI']}")
    L.append(f"- Документация/оценка: {REGULATORY_REFS['DOC_GATES']}")
    L.append("\n> Този доклад е генериран детерминистично от посочената версия на "
             "енджина. Числата не идват от LLM. Подписващият оценител (Член 10) "
             "носи юридическата отговорност.")

    return "\n".join(L)
