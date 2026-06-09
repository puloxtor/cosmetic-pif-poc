"""
INCI регресионен тест — SK5071025 Beard Oil (golden fixture).

Тестът зарежда известна рецепта, пуска generate_inci() и сравнява изхода
с точно очаквания списък. Всяко отклонение е регулаторен бъг.

ВАЖНО: ползва ПЪЛНИЯ фикстур (beard_oil_sk5071025.yaml) — всичките 25 алергена
от реалния IFRA сертификат (Symrise 212878 „Peace on Earth"), а НЕ съкратен
вариант. По-ранен съкратен фикстур скриваше липсващи Анекс III записи в базата
(OTNE/III-344, Pogostemon/III-365, Pinene/III-371) → фалшиво „зелен" тест.

Ако тестът се провали:
  1. Провери дали е променена nomenclature.py (_DECLARABLE_EXTRA / _DECLARABLE_26)
  2. Провери дали е променен fixtures/beard_oil_sk5071025.yaml
  3. Провери дали е променена логиката в allergens.py (generate_inci / _consolidated_lines)
  4. Поправи причината, НЕ очакването (освен ако регулацията действително е сменена).
"""
import pathlib
import yaml
import pytest

from pif_engine import build_product, generate_inci

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "beard_oil_sk5071025.yaml"

# Точно очакваният INCI списък за SK5071025 Beard Oil (BG, leave-on, 2 g).
#
# Ред              Причина
# ─────────────────────────────────────────────────────────────────────────────
# Prunus …         69.5 % ≥ 1 %, низходящ
# Ricinus …        20.0 % ≥ 1 %
# Coconut Alkanes   3.0 % ≥ 1 %, суровина 4 в рецептата
# Argania …         3.0 % ≥ 1 %, суровина 5
# Parfum            3.0 % ≥ 1 %, суровина 8 (последна → Python stable sort)
# [алергени]       Анекс III, декларирани > 0.001 % leave-on, по концентрация
# Helianthus …     1.80 % ≥ 1 %, но под Parfum в сортирания ред
# Olea …           1.05 % ≥ 1 %
# Simmondsia …     1.00 % ≥ 1 %
# Cucurbita …      0.60 % < 1 %, ред на първа поява
# Hippophae …      0.24 % < 1 %
# Tocopherol       0.377 % < 1 %

EXPECTED_INCI_SK5071025 = [
    "Prunus Amygdalus Dulcis Oil",
    "Ricinus Communis Seed Oil",
    "Coconut Alkanes",
    "Argania Spinosa Kernel Oil",
    "Parfum",
    # allergens sorted by concentration in product (descending), all > 0.001 %
    "Citrus Aurantium Peel Oil",            # 4.121 % × 3 % = 0.12363 %
    "Limonene",                             # 4.000 % × 3 % = 0.12000 %
    "Hexamethylindanopyran",                # 2.352 % × 3 % = 0.07056 %
    "Tetramethyl Acetyloctahydronaphthalenes",  # 2.349 % × 3 % = 0.07047 % (OTNE, III/344)
    "Linalool",                             # 1.565 % × 3 % = 0.04695 %
    "Amyl Salicylate",                      # 1.452 % × 3 % = 0.04356 %
    "Coumarin",                             # 0.588 % × 3 % = 0.01764 %
    "Citral",                               # 0.213 % × 3 % = 0.00639 %
    "Pogostemon Cablin Oil",                # 0.188 % × 3 % = 0.00564 % (III/365)
    "Pinene",                               # 0.186 % × 3 % = 0.00558 % (III/371)
    "beta-Caryophyllene",                   # 0.162 % × 3 % = 0.00486 %
    "Lavandula Angustifolia Oil",           # 0.118 % × 3 % = 0.00354 % ("Lavandula Oil/Extract")
    "Linalyl Acetate",                      # 0.076 % × 3 % = 0.00228 %
    "Eugenol",                              # 0.048 % × 3 % = 0.00144 %
    "Geranyl Acetate",                      # 0.039 % × 3 % = 0.00117 %
    # Camphor 0.024 %×3 %=0.00072 % < 0.001 % → NOT declared
    # Terpineol 0.032 %×3 %=0.00096 % < 0.001 % → recognized but NOT declared
    # Terpinolene 0.028 %×3 %=0.00084 % < 0.001 % → recognized but NOT declared
    # ≥1 % items that sorted below Parfum (stable sort, first appearance before Parfum)
    "Helianthus Annuus Seed Oil",   # 1.65 % + 0.15 % = 1.80 %
    "Olea Europaea Fruit Oil",      # 1.05 %
    "Simmondsia Chinensis Seed Oil", # 1.00 %
    # <1 % items in first-appearance order
    "Cucurbita Pepo Seed Oil",      # 0.60 %
    "Hippophae Rhamnoides Oil",     # 0.24 %
    "Tocopherol",                   # 0.377 %
]


@pytest.fixture(scope="module")
def sk5071025():
    doc = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    product, warnings = build_product(doc)
    return product, warnings


def test_sk5071025_inci_exact(sk5071025):
    """Пълният INCI списък трябва да съвпада точно с очаквания."""
    product, _ = sk5071025
    inci = generate_inci(product)
    if inci != EXPECTED_INCI_SK5071025:
        # Показва ясна разлика за бърза диагноза
        missing = [n for n in EXPECTED_INCI_SK5071025 if n not in inci]
        extra = [n for n in inci if n not in EXPECTED_INCI_SK5071025]
        wrong_order = [
            (i, exp, got)
            for i, (exp, got) in enumerate(
                zip(EXPECTED_INCI_SK5071025, inci), start=1
            )
            if exp != got
        ]
        msg_parts = [f"\nACTUAL ({len(inci)} items):   {inci}",
                     f"EXPECTED ({len(EXPECTED_INCI_SK5071025)} items): {EXPECTED_INCI_SK5071025}"]
        if missing:
            msg_parts.append(f"MISSING from actual: {missing}")
        if extra:
            msg_parts.append(f"UNEXPECTED in actual: {extra}")
        if wrong_order:
            msg_parts.append(f"WRONG POSITION (pos, expected, got): {wrong_order}")
        pytest.fail("\n".join(msg_parts))


def test_sk5071025_allergen_count(sk5071025):
    """Трябва да се декларират точно 15 алергена (всичките > 0.001 % leave-on)."""
    from pif_engine import allergens_to_declare
    product, _ = sk5071025
    declared = allergens_to_declare(product)
    assert len(declared) == 15, (
        f"Очаквани 15 декларирани алергена, получени {len(declared)}: {declared}"
    )


def test_sk5071025_otne_declared(sk5071025):
    """OTNE (Tetramethyl Acetyloctahydronaphthalenes, III/344) е 0.07047 % в
    продукта — далеч над прага. Регресионна защита: този алерген беше тихо
    пропускан, преди да бъде добавен в _DECLARABLE_EXTRA (Reg. 2023/1545)."""
    from pif_engine import allergens_to_declare
    product, _ = sk5071025
    declared = allergens_to_declare(product)
    for required in ("Tetramethyl Acetyloctahydronaphthalenes",
                     "Pogostemon Cablin Oil", "Pinene"):
        assert required in declared, (
            f"„{required}“ е над прага и трябва да е деклариран, но липсва: {declared}"
        )


def test_sk5071025_no_silent_allergen_drop(sk5071025):
    """Нито един алерген от сертификата не бива да се пропуска тихо: всеки
    непознат за базата алерген трябва да вдигне аларма (Член 19, CLAUDE.md)."""
    product, warnings = sk5071025
    # Всичките 25 алергена в този фикстур са вече разпознати → 0 алармени за
    # „непознат алерген". Ако някой бъде махнат от базата, тестът ще го хване.
    unknown = [w for w in warnings if "непознат за енджина алерген" in w]
    assert not unknown, f"Неочаквани пропуснати алергени: {unknown}"


def test_sk5071025_no_warnings_for_sum(sk5071025):
    """Сумата на суровините е 103 % (умишлен тест-кейс) — трябва да има аларма."""
    _, warnings = sk5071025
    sum_warnings = [w for w in warnings if "сумата" in w.lower() or "≠ 100" in w]
    assert sum_warnings, "Очаквана аларма за сума ≠ 100 % не е намерена."
