"""
ТЕСТОВ ПРОДУКТ: SK5071025 — Beard Oil (DEMO)
Източник на истина: Google Drive folder 11E_pvH140arlfoDy9_XZFaHAWraWIXKp
(ENGINE_TEST_PROMPT_SK5071025 + доставчишки TDS/IFRA документи).

Бележки за моделирането:
- Формулата СУМИРА на 103% (нарочен тестов случай — flag за sum != 100%).
- Многокомпонентните суровини се разлагат до крайни INCI:
    * Oleophen (3.0%) -> worst-case ГОРНИ граници на TDS диапазоните:
        Helianthus 55%, Olea 35%, Cucurbita 20%, Hippophae 8%
      (приноси в продукта: dose * fraction)
    * Vitapherole T-70 (0.5%) -> 70% Mixed Tocopherols + 30% Sunflower Oil
- Parfum "Peace on Earth" 212878 (3.0%) носи 18 алергена от IFRA сертификата.
  fraction = pct_in_fragrance / 100.
"""
from pif_engine.models import (
    Product, ProductType, Ingredient, FormulaLine,
    AllergenContent,
)


def ing(name, cas, func, **kw):
    base = dict(has_sds=True, has_coa=True)
    base.update(kw)
    return Ingredient(inci_name=name, cas=cas, function=func, **base)


# ---- Прости (100%) суровини ----
almond = ing("Prunus Amygdalus Dulcis Oil", "8007-69-0", "emollient")
castor = ing("Ricinus Communis Seed Oil", "8001-79-4", "emollient")
coconut_alkanes = ing("Coconut Alkanes", "928004-78-8", "emollient")
argan = ing("Argania Spinosa Kernel Oil", "223747-87-3", "emollient")
jojoba = ing("Simmondsia Chinensis Seed Oil", "90045-98-0", "emollient")

# ---- Oleophen компоненти (worst-case горни граници) ----
helianthus = ing("Helianthus Annuus Seed Oil", "8001-21-6", "emollient")
olea = ing("Olea Europaea Fruit Oil", "8001-25-0", "emollient")
cucurbita = ing("Cucurbita Pepo Seed Oil", "8016-49-7", "emollient")
hippophae = ing("Hippophae Rhamnoides Oil", "90106-68-6", "emollient")

# ---- Vitapherole T-70 компоненти ----
tocopherols = ing("Tocopherol", "1406-66-2", "antioxidant")
sunflower = ing("Helianthus Annuus Seed Oil", "8001-21-6", "carrier")

# ---- Parfum "Peace on Earth" 212878 (IFRA сертификат) ----
# (name, cas, pct_in_fragrance)
_ALLERGENS = [
    ("3-Propylidenephthalide", "17369-59-4", 0.005),
    ("Alpha-Terpinene", "99-86-5", 0.007),
    ("Amyl Salicylate", "2050-08-0", 1.452),
    ("Beta-Caryophyllene", "464-48-2", 0.162),
    ("Citral", "5392-40-5", 0.213),
    ("Citronellol", "106-22-9", 0.002),
    ("Citrus Aurantium Peel Oil", "8007-75-8", 4.121),
    ("Coumarin", "91-64-5", 0.588),
    ("Eucalyptus Globulus Oil", "8000-48-4", 0.011),
    ("Eugenol", "97-53-0", 0.048),
    ("Geraniol", "106-24-1", 0.002),
    ("Geranyl Acetate", "105-87-3", 0.039),
    ("Hexamethylindanopyran", "1222-05-5", 2.352),
    ("Isoeugenol", "5912-86-7", 0.002),
    ("Lavandula Oil Extract", "8000-28-0", 0.118),
    ("Limonene", "5989-27-5", 4.000),
    ("Linalool", "78-70-6", 1.565),
    ("Linalyl Acetate", "115-95-7", 0.076),
]

parfum = Ingredient(
    inci_name="Parfum", cas="N/A", function="fragrance",
    is_fragrance=True, has_sds=True, has_coa=True, has_ifra=True,
    allergens=[
        AllergenContent(name=n, cas=c, fraction=p / 100.0)
        for (n, c, p) in _ALLERGENS
    ],
)

# ---- Формула (ефективни концентрации в продукта, % w/w) ----
# Многокомпонентните суровини са разложени; dose * fraction.
sk5071025_beard_oil = Product(
    name="SK5071025 — Beard Oil (DEMO)",
    product_type=ProductType.LEAVE_ON,   # leave-on -> праг алерген 0.001%
    retention_factor=1.0,
    body_weight_kg=60.0,
    formula=[
        FormulaLine(almond, 69.5),
        FormulaLine(castor, 20.0),
        # Oleophen 3.0% (worst-case горни граници)
        FormulaLine(helianthus, 3.0 * 0.55),   # 1.650
        FormulaLine(olea,       3.0 * 0.35),   # 1.050
        FormulaLine(cucurbita,  3.0 * 0.20),   # 0.600
        FormulaLine(hippophae,  3.0 * 0.08),   # 0.240
        FormulaLine(coconut_alkanes, 3.0),
        FormulaLine(argan, 3.0),
        FormulaLine(jojoba, 1.0),
        # Vitapherole T-70 0.5%
        FormulaLine(tocopherols, 0.5 * 0.70),  # 0.350
        FormulaLine(sunflower,   0.5 * 0.30),  # 0.150 -> обединява с Helianthus по име
        FormulaLine(parfum, 3.0),
    ],
    sale_countries=["BG"],
)
