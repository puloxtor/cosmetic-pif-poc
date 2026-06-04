#!/usr/bin/env python3
"""
PIFGEN — CLI за един продукт (една сесия).

Употреба:
    python3 pifgen.py <product.yaml> [--out OUTPUT_DIR] [--cpsr]

Зарежда продуктов YAML (суровини + композишън стейтмънти), смята разбивката
на целия състав и генерира INCI. По подразбиране изходът е ТАБЛИЦА + INCI.
С --cpsr се генерира и пълният CPSR доклад.

Изходите са „ефемерни" — пазиш ги ти; в репото не остава продуктови данни.
"""
from __future__ import annotations
import argparse
import os
import re
import sys

from pif_engine.loader import load_product
from pif_engine.allergens import generate_inci, allergens_to_declare
from pif_engine.composition import consolidated_concentrations
from pif_engine.cpsr import generate_cpsr


def slugify(name: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", name.strip().lower(), flags=re.UNICODE)
    return s.strip("_") or "product"


def _table_markdown(product) -> str:
    totals = consolidated_concentrations(product)
    rows = ["| INCI | Концентрация (% w/w) |", "|------|----------------------|"]
    for inci, conc in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
        rows.append(f"| {inci} | {conc:.4f} |")
    rows.append(f"| **СУМА** | **{sum(totals.values()):.4f}** |")
    return "\n".join(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Генериране на таблица + INCI (по избор CPSR) от продуктов YAML.")
    ap.add_argument("product", help="път до продуктов YAML файл")
    ap.add_argument("--out", default="outputs", help="директория за изходите (по подразбиране: outputs)")
    ap.add_argument("--cpsr", action="store_true", help="генерирай и пълния CPSR доклад")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.product):
        print(f"Грешка: файлът не съществува: {args.product}", file=sys.stderr)
        return 2

    product, warnings = load_product(args.product)

    print(f"=== Продукт: {product.name} ===")
    print(f"Тип: {product.product_type.value}\n")

    if warnings:
        print("--- АЛАРМИ / БЕЛЕЖКИ ---")
        for w in warnings:
            print(f"  {w}")
        print()

    print("--- ТАБЛИЦА: разбивка на състава (сумирано по INCI), % в краен продукт ---")
    totals = consolidated_concentrations(product)
    for inci, conc in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {inci:<42} {conc:9.4f} %")
    print(f"  {'СУМА':<42} {sum(totals.values()):9.4f} %\n")

    declared = allergens_to_declare(product)
    print(f"--- Алергени за деклариране ({len(declared)}) ---")
    print("  " + (", ".join(declared) if declared else "няма") + "\n")

    inci = generate_inci(product)
    print("--- Генериран INCI (Член 19) ---")
    print("  " + ", ".join(inci) + "\n")

    out_dir = os.path.join(args.out, slugify(product.name))
    os.makedirs(out_dir, exist_ok=True)
    table_path = os.path.join(out_dir, "table.md")
    inci_path = os.path.join(out_dir, "INCI.txt")
    with open(table_path, "w", encoding="utf-8") as f:
        f.write(_table_markdown(product) + "\n")
    with open(inci_path, "w", encoding="utf-8") as f:
        f.write(", ".join(inci) + "\n")
    print(f"Записано: {table_path}")
    print(f"Записано: {inci_path}")

    if args.cpsr:
        report = generate_cpsr(product)
        cpsr_path = os.path.join(out_dir, "CPSR_report.md")
        with open(cpsr_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Записано: {cpsr_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
