#!/usr/bin/env python3
"""
CLI validation runner.

Usage:
    python validation/validate_product.py tests/fixtures/beard_oil_sk5071025.yaml
    python validation/validate_product.py tests/fixtures/beard_oil_sk5071025.yaml --strict

Loads a product fixture YAML, runs the full engine pipeline, and prints:
  - Computed INCI list
  - Declared allergens with concentrations
  - Any engine warnings
  - PASS / FAIL against the `expected:` block (if present)

Exit code 0 = PASS (or no expected block), 1 = FAIL or error.
"""
from __future__ import annotations
import argparse
import pathlib
import sys
import yaml

# Allow running from the repo root without installing the package
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from pif_engine import build_product, generate_inci, allergens_to_declare


def _fmt_allergen(a) -> str:
    if isinstance(a, str):
        return f"  {a}"
    pct = getattr(a, "concentration_pct", None) or getattr(a, "fraction", None)
    name = getattr(a, "name", str(a))
    if pct is not None:
        return f"  {name:<50} {pct:.5f} %"
    return f"  {name}"


def run(fixture_path: pathlib.Path, strict: bool = False) -> int:
    if not fixture_path.exists():
        print(f"ERROR: fixture not found: {fixture_path}", file=sys.stderr)
        return 1

    doc = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or "product" not in doc:
        print(f"ERROR: not a valid product fixture: {fixture_path}", file=sys.stderr)
        return 1

    try:
        product, warnings = build_product(doc)
    except Exception as exc:
        print(f"ERROR building product: {exc}", file=sys.stderr)
        return 1

    inci = generate_inci(product)
    declared = allergens_to_declare(product)

    print(f"\n{'─' * 60}")
    print(f"Product : {product.name}")
    print(f"Type    : {product.product_type.value}")
    print(f"Fixture : {fixture_path}")
    print(f"{'─' * 60}")

    print(f"\nINCI list ({len(inci)} items):")
    for i, name in enumerate(inci, 1):
        print(f"  {i:>2}. {name}")

    print(f"\nDeclared allergens ({len(declared)}):")
    for a in declared:
        print(_fmt_allergen(a))

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")

    expected = doc.get("expected")
    if not expected:
        print("\n(no expected: block — skipping assertions)")
        return 0

    failures: list[str] = []

    if "allergen_count" in expected:
        exp_count = expected["allergen_count"]
        if len(declared) != exp_count:
            failures.append(
                f"allergen_count: expected {exp_count}, got {len(declared)}"
            )

    if "sum_alarm" in expected:
        sum_warnings = [w for w in warnings if "сумата" in w.lower() or "≠ 100" in w]
        if expected["sum_alarm"] and not sum_warnings:
            failures.append("sum_alarm: expected a sum≠100% warning but none found")
        elif not expected["sum_alarm"] and sum_warnings:
            failures.append(f"sum_alarm: unexpected sum warning: {sum_warnings}")

    if expected.get("no_silent_drops"):
        unknown = [w for w in warnings if "непознат за енджина алерген" in w]
        if unknown:
            failures.append(f"no_silent_drops: unknown allergen warnings: {unknown}")

    if "inci_list" in expected:
        exp_inci = expected["inci_list"]
        if inci != exp_inci:
            missing = [n for n in exp_inci if n not in inci]
            extra = [n for n in inci if n not in exp_inci]
            wrong = [(i + 1, e, a) for i, (e, a) in enumerate(zip(exp_inci, inci)) if e != a]
            detail = []
            if missing:
                detail.append(f"  missing: {missing}")
            if extra:
                detail.append(f"  extra: {extra}")
            if wrong:
                detail.append(f"  wrong position (pos, expected, got): {wrong}")
            failures.append("inci_list mismatch:\n" + "\n".join(detail))

    print()
    if failures:
        print("FAIL")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    else:
        print("PASS — all expected assertions satisfied")
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a product fixture against expected output.")
    parser.add_argument("fixture", type=pathlib.Path, help="Path to fixture YAML")
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit 1 even when there is no expected: block (forces you to add one)"
    )
    args = parser.parse_args()
    sys.exit(run(args.fixture, strict=args.strict))


if __name__ == "__main__":
    main()
