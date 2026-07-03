"""
MCP сървър за pif_engine — излага детерминистичния енджин като инструменти,
които Claude (chat/Desktop/Code) може да вика директно.

Слой ИНТЕРФЕЙС: тънка обвивка над публичния API. НЕ съдържа собствена
регулаторна логика — всички числа идват от pif_engine. Изходът е чернова;
подписващият оценител носи отговорността (Член 10).

Стартиране:
    pif-mcp                      # stdio (Claude Desktop / Claude Code)
    pif-mcp --transport http     # streamable HTTP на $PORT (claude.ai connector)

Зависимостта `mcp` е опционална (extra "mcp"); ядрото работи и без нея.
"""
from __future__ import annotations
import argparse
import os

import yaml

from . import __version__
from .composition import build_product, consolidated_concentrations
from .allergens import (
    ALLERGEN_THRESHOLD, calculate_allergens, allergens_to_declare, generate_inci,
)
from .claims import validate_all_claims
from .cpsr import generate_cpsr

NOTE = ("Детерминистичен изход от pif-engine v" + __version__ +
        ". Чернова — не замества квалифициран оценител (Член 10).")

# Компактен шаблон за вход (пълният е в products/TEMPLATE.yaml на репото).
TEMPLATE_YAML = """\
# Продуктов YAML — един файл = един продукт.
# Стойности на конституент: pct: X | range: [lo, hi] (взима се ГОРНАТА) |
# at_most: X | remainder: true (остатък до 100%). Сума на дозите ≈ 100%.
product:
  name: "Примерен продукт"
  product_type: "leave-on"        # leave-on | rinse-off
  applied_amount_g: 2.0
  retention_factor: 1.0           # 1.0 leave-on; 0.01 rinse-off
  body_weight_kg: 60.0
  sale_countries: ["BG"]

raw_materials:
  - name: "Sweet Almond Oil"
    dose_pct: 96.5
    composition:
      - { inci_name: "Prunus Amygdalus Dulcis Oil", cas: "8007-69-0", pct: 100 }

  - name: "Parfum (пример)"
    dose_pct: 3.0
    is_fragrance: true
    allergens:
      - { name: "Limonene", cas: "5989-27-5", pct_in_fragrance: 4.0 }
      - { name: "Linalool", cas: "78-70-6", pct_in_fragrance: 1.5 }

  - name: "Tocopherol"
    dose_pct: 0.5
    composition:
      - { inci_name: "Tocopherol", cas: "59-02-9", pct: 100 }

claims:
  - "Подхранва кожата"
"""


# ---------------------------------------------------------------- чисти функции
# (тестват се без инсталиран `mcp`; MCP слоят само ги регистрира като tools)

def _product_from_yaml(formula_yaml: str):
    try:
        doc = yaml.safe_load(formula_yaml)
    except yaml.YAMLError as e:
        raise ValueError(f"Невалиден YAML: {e}") from e
    if not isinstance(doc, dict) or "product" not in doc:
        raise ValueError("Очаквам YAML с ключове 'product' и 'raw_materials' "
                         "(виж инструмента product_template).")
    return build_product(doc)


def compute_result(formula_yaml: str, include_cpsr: bool = False) -> dict:
    """Пълна разбивка: таблица, INCI, алергени (+ по избор CPSR)."""
    product, warnings = _product_from_yaml(formula_yaml)

    totals = consolidated_concentrations(product)
    table = [{"inci": k, "pct": round(v, 4)}
             for k, v in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)]

    threshold = ALLERGEN_THRESHOLD[product.product_type]
    allergen_totals = calculate_allergens(product)
    declared = set(allergens_to_declare(product))
    allergens = [{"name": n, "total_pct": round(c, 6),
                  "threshold_pct": threshold, "declare": n in declared}
                 for n, c in sorted(allergen_totals.items(),
                                    key=lambda kv: kv[1], reverse=True)]

    result = {
        "product": product.name,
        "product_type": product.product_type.value,
        "warnings": warnings,
        "table": table,
        "sum_pct": round(sum(totals.values()), 4),
        "inci": ", ".join(generate_inci(product)),
        "allergens": allergens,
        "note": NOTE,
    }
    if include_cpsr:
        result["cpsr_markdown"] = generate_cpsr(product)
    return result


def claims_result(formula_yaml: str) -> dict:
    """Валидиране на претенциите (Регламент 655/2013, Член 20)."""
    product, _ = _product_from_yaml(formula_yaml)
    return {
        "product": product.name,
        "claims": [{"claim": r.claim, "status": r.status, "reason": r.reason}
                   for r in validate_all_claims(product)],
        "note": NOTE,
    }


# ------------------------------------------------------------------- MCP слой

def build_server():
    """Създава FastMCP сървъра (изисква екстрата `mcp`)."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as e:
        raise SystemExit(
            "Липсва зависимостта 'mcp'. Инсталирай:  pip install 'pif-engine[mcp]'"
        ) from e

    server = FastMCP(
        "pif-engine",
        instructions=(
            "Детерминистичен енджин за козметичен PIF/CPSR (Регламент (ЕО) № "
            "1223/2009). Подай продуктов YAML (виж product_template) на "
            "compute_product за таблица с разбивката, INCI и алергени. "
            "Всички числа са изчислени от код, не от модела; изходът е чернова "
            "за проверка от оценител."
        ),
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
    )

    @server.tool()
    def compute_product(formula_yaml: str, include_cpsr: bool = False) -> dict:
        """Смята разбивката на продукт от продуктов YAML: консолидирана таблица
        (INCI + % w/w, низходящо), генериран INCI списък, алергени спрямо прага
        за типа продукт и аларми (диапазони, сума≠100%). С include_cpsr=true
        връща и пълния CPSR доклад (markdown). Форматът на входа → product_template."""
        return compute_result(formula_yaml, include_cpsr)

    @server.tool()
    def validate_claims(formula_yaml: str) -> dict:
        """Валидира претенциите (claims) на продукта по Регламент 655/2013 /
        Член 20: approved | blocked | needs_evidence, с причина."""
        return claims_result(formula_yaml)

    @server.tool()
    def product_template() -> str:
        """Връща шаблона на продуктовия YAML вход + правилата за композишън
        стейтмънти (pct / range→горна граница / at_most / remainder)."""
        return TEMPLATE_YAML

    return server


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="MCP сървър за pif-engine.")
    ap.add_argument("--transport", choices=["stdio", "http"], default="stdio",
                    help="stdio за Claude Desktop/Code; http (streamable) за claude.ai connector")
    args = ap.parse_args(argv)

    server = build_server()
    server.run(transport="streamable-http" if args.transport == "http" else "stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
