"""
Shared pytest fixtures for the parametric test suite.

Loads every tests/fixtures/*.yaml file that has an `expected:` block and
exposes it as a parametrized fixture `fixture_with_expected`. Fixtures
without an `expected:` block are exposed separately as `all_fixtures` for
smoke tests (build must not raise).
"""
import pathlib
import yaml
import pytest

from pif_engine import build_product

_FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def _load_all_fixtures():
    result = []
    for path in sorted(_FIXTURES_DIR.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and "product" in doc:
            result.append((path.stem, doc))
    return result


_ALL = _load_all_fixtures()
_WITH_EXPECTED = [(stem, doc) for stem, doc in _ALL if "expected" in doc]


@pytest.fixture(
    params=[pytest.param((stem, doc), id=stem) for stem, doc in _ALL]
)
def any_fixture(request):
    """Every fixture file — used for smoke tests."""
    stem, doc = request.param
    product, warnings = build_product(doc)
    return {"id": stem, "doc": doc, "product": product, "warnings": warnings}


@pytest.fixture(
    params=[pytest.param((stem, doc), id=stem) for stem, doc in _WITH_EXPECTED]
)
def fixture_with_expected(request):
    """Only fixtures that carry an `expected:` block."""
    stem, doc = request.param
    product, warnings = build_product(doc)
    return {
        "id": stem,
        "doc": doc,
        "product": product,
        "warnings": warnings,
        "expected": doc["expected"],
    }
