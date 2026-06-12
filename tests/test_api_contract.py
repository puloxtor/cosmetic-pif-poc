"""Тестове за типизирания контракт ComputeResult (Finding R1)."""
from __future__ import annotations
from pif_engine import ComputeResult, TableRow, AllergenRow


def test_compute_result_required_and_optional_keys():
    assert set(ComputeResult.__required_keys__) == {
        "name", "product_type", "warnings", "table", "total",
        "sum_ok", "inci", "declared", "allergens",
    }
    assert set(ComputeResult.__optional_keys__) == {"cpsr", "blockers"}


def test_nested_row_contracts():
    assert set(TableRow.__required_keys__) == {"inci", "pct"}
    assert set(AllergenRow.__required_keys__) == {
        "name", "cas", "conc_pct", "threshold_pct", "declared",
    }
