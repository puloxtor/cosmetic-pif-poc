"""pif_engine — детерминистичен PIF/CPSR енджин (Регламент (ЕО) № 1223/2009).

Стабилен публичен API за външни потребители (напр. UX в отделно репо).
Слоят за извличане (pif_engine.extraction) НЕ се внася тук, за да остане
ядрото без опционалните зависимости (pdfplumber/anthropic).
"""
__version__ = "0.1.0"

from .models import (
    Product, ProductType, Ingredient, FormulaLine, Claim,
    AllergenContent, ToxProfile,
)
from .composition import build_product, consolidated_concentrations
from .loader import load_product
from .allergens import generate_inci, allergens_to_declare, calculate_allergens
from .toxicology import calculate_mos, product_is_safe
from .claims import validate_all_claims
from .cpsr import generate_cpsr
from .nomenclature import (
    canonical_inci, is_declarable, declarable_name,
    localize_inci, validate_inci, DECLARABLE_ALLERGENS,
)

__all__ = [
    "__version__",
    "Product", "ProductType", "Ingredient", "FormulaLine", "Claim",
    "AllergenContent", "ToxProfile",
    "build_product", "consolidated_concentrations", "load_product",
    "generate_inci", "allergens_to_declare", "calculate_allergens",
    "calculate_mos", "product_is_safe", "validate_all_claims", "generate_cpsr",
    "canonical_inci", "is_declarable", "declarable_name",
    "localize_inci", "validate_inci", "DECLARABLE_ALLERGENS",
]
