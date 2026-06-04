"""
Примерен продукт за демонстрация на pipeline-а.
Това е мястото, където реалните данни от Мими/Милена/Хаби биха влезли.
"""
from pif_engine.models import (
    Product, ProductType, Ingredient, FormulaLine, Claim,
    AllergenContent, ToxProfile,
)

# --- Master суровини (въвеждат Милена/Хаби, с прикачени документи) ---

aqua = Ingredient(
    inci_name="Aqua", cas="7732-18-5", function="разтворител",
    has_sds=True, has_coa=True,
)

glycerin = Ingredient(
    inci_name="Glycerin", cas="56-81-5", function="хумектант",
    has_sds=True, has_coa=True,
    tox=ToxProfile(pod=2000.0, dermal_absorption=0.1),
)

cetearyl = Ingredient(
    inci_name="Cetearyl Alcohol", cas="67762-27-0", function="емолиент",
    has_sds=True, has_coa=True,
    tox=ToxProfile(pod=1000.0, dermal_absorption=0.05),
)

# Парфюм с алергени (от IFRA сертификат / алергенна листа)
parfum = Ingredient(
    inci_name="Parfum", cas="-", function="ароматизатор", is_fragrance=True,
    has_sds=True, has_coa=True, has_ifra=True,
    allergens=[
        AllergenContent(name="Limonene", cas="5989-27-5", fraction=0.15),
        AllergenContent(name="Linalool", cas="78-70-6", fraction=0.08),
        AllergenContent(name="Citronellol", cas="106-22-9", fraction=0.02),
        AllergenContent(name="Geraniol", cas="106-24-1", fraction=0.005),
    ],
)

phenoxy = Ingredient(
    inci_name="Phenoxyethanol", cas="122-99-6", function="консервант",
    restricted=True, max_allowed_pct=1.0,   # Анекс V лимит
    has_sds=True, has_coa=True,
    tox=ToxProfile(pod=400.0, dermal_absorption=0.5),
)


demo_product = Product(
    name="Хидратиращ дневен крем 'Aurora'",
    product_type=ProductType.LEAVE_ON,
    daily_amount_g=1.54,        # типично за крем за лице (SCCS таблица)
    formula=[
        FormulaLine(aqua, 70.0),
        FormulaLine(glycerin, 15.0),
        FormulaLine(cetearyl, 8.0),
        FormulaLine(phenoxy, 0.8),
        FormulaLine(parfum, 0.5),
        # допълваме до 100 с aqua вече покрито; за PoC приемаме баланс
    ],
    claims=[
        Claim("Хидратира кожата за 24 часа"),       # OK (но трябва доказателство)
        Claim("Без парабени"),                       # денигрираща -> блокира
        Claim("Дерматологично тестван"),             # нужно досие
        Claim("Лекува екзема"),                       # медицинска -> блокира
        Claim("Подходящ за чувствителна кожа"),       # OK
    ],
    sale_countries=["BG", "DE", "FR"],
)

# Корекция: добавяме баланс вода до 100% за коректна сума
demo_product.formula[0] = FormulaLine(aqua, 75.7)
