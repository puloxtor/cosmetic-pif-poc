#!/usr/bin/env python3
"""
PIFGEN — CLI за един продукт (една сесия).

Употреба:
    python3 pifgen.py <product.yaml> [--out OUTPUT_DIR]

Зарежда продуктов YAML (суровини + композишън стейтмънти), смята разбивката
на целия състав, генерира INCI и пълния CPSR, и записва изходите в
OUTPUT_DIR/<slug>/ (по подразбиране ./outputs/<slug>/).

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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Генериране на PIF/CPSR от продуктов YAML.")
    ap.add_argument("product", help="път до продуктов YAML файл")
    ap.add_argument("--out", default="outputs", help="директория за изходите (по подразбиране: outputs)")
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

    print("--- Разбивка на състава (сумирано по INCI), % в краен продукт ---")
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

    report = generate_cpsr(product)

    out_dir = os.path.join(args.out, slugify(product.name))
    os.makedirs(out_dir, exist_ok=True)
    cpsr_path = os.path.join(out_dir, "CPSR_report.md")
    inci_path = os.path.join(out_dir, "INCI.txt")
    with open(cpsr_path, "w", encoding="utf-8") as f:
        f.write(report)
    with open(inci_path, "w", encoding="utf-8") as f:
        f.write(", ".join(inci) + "\n")

    print(f"Записано: {cpsr_path}")
    print(f"Записано: {inci_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
