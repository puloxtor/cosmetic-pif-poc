"""
Parametric regression tests — runs against every fixture in tests/fixtures/*.yaml.

Adding a new product fixture with an `expected:` block automatically enrolls it
in all assertions below — no code changes required.

Assertion keys (all optional in the `expected:` block):
  allergen_count  — exact count of declared allergens above threshold
  sum_alarm       — true → expect a sum≠100% warning; false → expect none
  no_silent_drops — true → expect zero "непознат за енджина алерген" warnings
  inci_list       — exact ordered INCI list
"""
import pytest
from pif_engine import generate_inci, allergens_to_declare


# ── Smoke: every fixture must load without raising ──────────────────────────

def test_fixture_loads(any_fixture):
    """build_product() must not raise for any fixture file."""
    assert any_fixture["product"] is not None


# ── Assertions for fixtures with an `expected:` block ──────────────────────

def test_allergen_count(fixture_with_expected):
    exp = fixture_with_expected["expected"]
    if "allergen_count" not in exp:
        pytest.skip("no allergen_count expectation")
    product = fixture_with_expected["product"]
    declared = allergens_to_declare(product)
    expected_count = exp["allergen_count"]
    assert len(declared) == expected_count, (
        f"[{fixture_with_expected['id']}] "
        f"Expected {expected_count} declared allergens, got {len(declared)}: {declared}"
    )


def test_sum_alarm(fixture_with_expected):
    exp = fixture_with_expected["expected"]
    if "sum_alarm" not in exp:
        pytest.skip("no sum_alarm expectation")
    warnings = fixture_with_expected["warnings"]
    sum_warnings = [w for w in warnings if "сумата" in w.lower() or "≠ 100" in w]
    if exp["sum_alarm"]:
        assert sum_warnings, (
            f"[{fixture_with_expected['id']}] Expected a sum≠100% warning but none found."
        )
    else:
        assert not sum_warnings, (
            f"[{fixture_with_expected['id']}] Unexpected sum≠100% warning: {sum_warnings}"
        )


def test_no_silent_drops(fixture_with_expected):
    exp = fixture_with_expected["expected"]
    if not exp.get("no_silent_drops"):
        pytest.skip("no_silent_drops not set")
    warnings = fixture_with_expected["warnings"]
    unknown = [w for w in warnings if "непознат за енджина алерген" in w]
    assert not unknown, (
        f"[{fixture_with_expected['id']}] "
        f"Unexpected unknown-allergen warnings (silent drop risk): {unknown}"
    )


def test_inci_list(fixture_with_expected):
    exp = fixture_with_expected["expected"]
    if "inci_list" not in exp:
        pytest.skip("no inci_list expectation")
    product = fixture_with_expected["product"]
    actual = generate_inci(product)
    expected_list = exp["inci_list"]
    if actual != expected_list:
        missing = [n for n in expected_list if n not in actual]
        extra = [n for n in actual if n not in expected_list]
        wrong_order = [
            (i + 1, e, a)
            for i, (e, a) in enumerate(zip(expected_list, actual))
            if e != a
        ]
        parts = [
            f"\n[{fixture_with_expected['id']}]",
            f"ACTUAL   ({len(actual)}): {actual}",
            f"EXPECTED ({len(expected_list)}): {expected_list}",
        ]
        if missing:
            parts.append(f"MISSING from actual: {missing}")
        if extra:
            parts.append(f"UNEXPECTED in actual: {extra}")
        if wrong_order:
            parts.append(f"WRONG POSITION (pos, expected, got): {wrong_order}")
        pytest.fail("\n".join(parts))
