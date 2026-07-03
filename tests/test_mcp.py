"""
Тестове за MCP слоя (pif_engine/mcp_server.py).

Чистите функции (compute_result, claims_result) се тестват БЕЗ инсталиран
`mcp` — те са само обвивка над публичния API. Регистрацията на сървъра се
тества само ако екстрата `mcp` е налична.
"""
import pytest

from pif_engine.mcp_server import (
    TEMPLATE_YAML, compute_result, claims_result, _product_from_yaml,
)

FORMULA = """\
product:
  name: "MCP Test Oil"
  product_type: "leave-on"
  applied_amount_g: 2.0
  retention_factor: 1.0
  sale_countries: ["BG"]

raw_materials:
  - name: "Sweet Almond Oil"
    dose_pct: 96.5
    composition:
      - { inci_name: "Prunus Amygdalus Dulcis Oil", cas: "8007-69-0", pct: 100 }

  - name: "Parfum"
    dose_pct: 3.0
    is_fragrance: true
    allergens:
      - { name: "Limonene", cas: "5989-27-5", pct_in_fragrance: 4.0 }
      - { name: "Benzyl Alcohol", cas: "100-51-6", pct_in_fragrance: 0.01 }

  - name: "Tocopherol"
    dose_pct: 0.5
    composition:
      - { inci_name: "Tocopherol", cas: "59-02-9", pct: 100 }

claims:
  - "без парабени"
"""


def test_compute_result_table_and_inci():
    r = compute_result(FORMULA)
    assert r["product"] == "MCP Test Oil"
    assert r["product_type"] == "leave-on"
    # таблицата е низходяща и сумира до ~100
    pcts = [row["pct"] for row in r["table"]]
    assert pcts == sorted(pcts, reverse=True)
    assert abs(r["sum_pct"] - 100.0) < 0.01
    assert r["table"][0]["inci"] == "Prunus Amygdalus Dulcis Oil"
    # INCI: алергенът над прага е след Parfum
    assert "Parfum, Limonene" in r["inci"]


def test_compute_result_allergen_threshold_logic():
    r = compute_result(FORMULA)
    by_name = {a["name"]: a for a in r["allergens"]}
    # Limonene: 3% * 4% = 0.12% > 0.001% (leave-on) → декларира се
    assert by_name["Limonene"]["declare"] is True
    assert by_name["Limonene"]["total_pct"] == pytest.approx(0.12)
    # Benzyl Alcohol: 3% * 0.01% = 0.0003% < 0.001% → НЕ се декларира
    assert by_name["Benzyl Alcohol"]["declare"] is False
    assert by_name["Benzyl Alcohol"]["threshold_pct"] == 0.001


def test_compute_result_with_cpsr():
    r = compute_result(FORMULA, include_cpsr=True)
    assert "ДОКЛАД ЗА БЕЗОПАСНОСТ" in r["cpsr_markdown"]


def test_claims_result_blocks_denigrating():
    r = claims_result(FORMULA)
    assert r["claims"][0]["status"] == "blocked"  # "без парабени" е денигриращо


def test_invalid_yaml_raises_friendly_error():
    with pytest.raises(ValueError, match="Невалиден YAML"):
        _product_from_yaml("product: [unclosed")
    with pytest.raises(ValueError, match="product"):
        _product_from_yaml("just_a_key: 1")


def test_template_is_valid_input():
    r = compute_result(TEMPLATE_YAML)
    assert abs(r["sum_pct"] - 100.0) < 0.01


def test_server_registers_tools():
    pytest.importorskip("mcp")
    import anyio
    from pif_engine.mcp_server import build_server
    server = build_server()
    tools = anyio.run(server.list_tools)
    names = {t.name for t in tools}
    assert names == {"compute_product", "validate_claims", "product_template"}
