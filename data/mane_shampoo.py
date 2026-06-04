"""
РЕАЛЕН ПРОДУКТ: maxi mane MANE Protect Shampoo (CPNP 5623994)
Данните са извлечени от истинския CPSR в Google Drive (Шаман Студио ООД).

Бележки за моделирането:
- В реалния документ съставките са дадени като "mixtures" (търговски суровини).
  За INCI и алергени работим с крайните INCI имена и техните ефективни
  концентрации в продукта.
- Limonene идва от Citrus Grandis Peel Oil (грейпфрутово масло), НЕ от
  екстрактите. Декларира се на етикета (присъства в реалния INCI).
- Токсикологичните PoD стойности тук са примерни/илюстративни за теста на
  изчислението; реалните идват от досието "Exposure and risk characterisation".
"""
from pif_engine.models import (
    Product, ProductType, Ingredient, FormulaLine, Claim,
    AllergenContent, ToxProfile,
)

# ---- Ключови суровини (с документи от доставчик) ----

def ing(name, cas, func, **kw):
    base = dict(has_sds=True, has_coa=True)
    base.update(kw)
    return Ingredient(inci_name=name, cas=cas, function=func, **base)

aqua = ing("Aqua", "7732-18-5", "разтворител")
dls = ing("Disodium Laureth Sulfosuccinate", "39354-45-5", "ПАВ - почистване",
          tox=ToxProfile(pod=300.0, dermal_absorption=0.50))  # NOAEL 300 от док.
capb = ing("Cocamidopropyl Betaine", "61789-40-0", "ПАВ - почистване",
           tox=ToxProfile(pod=250.0, dermal_absorption=0.50))
coco = ing("Coco-Glucoside", "110615-47-9", "ПАВ - почистване",
           tox=ToxProfile(pod=2000.0, dermal_absorption=0.50))
saw = ing("Serenoa Serrulata Fruit Extract", "84604-15-9", "балсам за кожа",
          tox=ToxProfile(pod=1000.0, dermal_absorption=0.50))
peg120 = ing("PEG-120 Methyl Glucose Dioleate", "86893-19-8", "емулгатор",
             tox=ToxProfile(pod=1000.0, dermal_absorption=0.10))
amla = ing("Phyllanthus Emblica Fruit Extract", "90028-28-7", "хумектант")
pumpkin = ing("Cucurbita Pepo Seed Extract", "89998-03-8", "балсам за кожа")
biotin = ing("Biotin", "58-85-5", "балсам за коса")
panthenyl = ing("Panthenyl Hydroxypropyl Steardimonium Chloride", "132467-76-6",
                "балсам за коса")
tocopherol = ing("Tocopherol", "59-02-9", "антиоксидант",
                 tox=ToxProfile(pod=500.0, dermal_absorption=0.10))
propanediol = ing("Propanediol", "504-63-2", "разтворител")
glycerin = ing("Glycerin", "56-81-5", "хумектант",
               tox=ToxProfile(pod=2000.0, dermal_absorption=0.10))
# Грейпфрутово масло — НОСИ алергена Limonene
grapefruit = Ingredient(
    inci_name="Citrus Grandis Peel Oil", cas="90045-43-5",
    function="балсам за кожа", is_fragrance=True,
    has_sds=True, has_coa=True, has_ifra=True,
    allergens=[
        # Грейпфрутовото масло е ~90%+ Limonene
        AllergenContent(name="Limonene", cas="5989-27-5", fraction=0.90),
    ],
)
citric = ing("Citric Acid", "77-92-9", "буфер")
hpgc = ing("Hydrogenated Palm Glycerides Citrate", "91744-68-2", "емолиент")
ehg = ing("Ethylhexylglycerin", "70445-33-9", "консервант")
lactic = ing("Lactic Acid", "50-21-5", "буфер")
sodben = ing("Sodium Benzoate", "532-32-1", "консервант V/1",
             restricted=True, max_allowed_pct=2.5,
             tox=ToxProfile(pod=400.0, dermal_absorption=0.50))
potsorb = ing("Potassium Sorbate", "24634-61-5", "консервант V/4",
              restricted=True, max_allowed_pct=0.6)
glyceryl_oleate = ing("Glyceryl Oleate", "25496-72-4", "емолиент")
phenoxy = ing("Phenoxyethanol", "122-99-6", "консервант V/29",
              restricted=True, max_allowed_pct=1.0,
              tox=ToxProfile(pod=400.0, dermal_absorption=0.50))

# ---- Формулата (ефективни концентрации в крайния продукт, % w/w) ----
# Извлечени от таблицата на реалния CPSR. Mixtures са разложени до
# доминиращите INCI; малките add-up до 100%.
mane_shampoo = Product(
    name="maxi mane MANE Protect Shampoo (CPNP 5623994)",
    product_type=ProductType.RINSE_OFF,
    applied_amount_g=10.46,
    retention_factor=0.01,
    body_weight_kg=60.0,
    formula=[
        FormulaLine(aqua, 28.15),
        FormulaLine(dls, 20.0),       # от 32% mixture, доминираща
        FormulaLine(capb, 5.0),       # от 15% mixture aqua+capb
        FormulaLine(saw, 9.0),        # от 10% Serenoa mixture
        FormulaLine(coco, 7.0),
        FormulaLine(glyceryl_oleate, 2.0),
        FormulaLine(tocopherol, 0.5),
        FormulaLine(pumpkin, 1.0),
        FormulaLine(propanediol, 0.6),
        FormulaLine(glycerin, 0.4),
        FormulaLine(amla, 0.3),
        FormulaLine(panthenyl, 0.5),
        FormulaLine(phenoxy, 0.4),
        FormulaLine(ehg, 0.1),
        FormulaLine(peg120, 1.0),
        FormulaLine(sodben, 0.5),
        FormulaLine(grapefruit, 0.30),   # Citrus Grandis Peel Oil
        FormulaLine(citric, 0.3),
        FormulaLine(hpgc, 0.2),
        FormulaLine(lactic, 0.05),
        FormulaLine(potsorb, 0.2),
        FormulaLine(biotin, 0.0001),
        # Остатъкът се балансира с вода:
        FormulaLine(aqua, 12.0),   # ще се обедини при INCI чрез име
    ],
    claims=[
        Claim("Защитава косата от изтъняване и осигурява по-гъста, по-здрава коса"),
        Claim("Без сулфати"),          # денигрираща -> трябва да се блокира
        Claim("Дерматологично тестван"),  # нужно досие
        Claim("Подходящ за честа употреба"),  # OK
        Claim("Стимулира растежа на косата"),  # гранична — нужно досие/може медицинска
    ],
    sale_countries=["BG"],
)
