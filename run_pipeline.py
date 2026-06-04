#!/usr/bin/env python3
"""
Главен pipeline: взема продукт -> генерира CPSR + INCI + валидирани претенции.

Употреба:
    python run_pipeline.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from data.example_product import demo_product
from pif_engine.cpsr import generate_cpsr


def main():
    print("=" * 60)
    print("PIF/CPSR PoC — обработка на продукт")
    print("=" * 60)

    report = generate_cpsr(demo_product)

    os.makedirs("outputs", exist_ok=True)
    out_path = os.path.join("outputs", "CPSR_report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print("\n" + "=" * 60)
    print(f"✅ Докладът е записан в: {out_path}")


if __name__ == "__main__":
    main()
