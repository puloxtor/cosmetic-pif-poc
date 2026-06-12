"""
YAML зареждащ слой (Задача 3 от ROADMAP).

Чете един продуктов YAML файл и го компилира до модела Product чрез
композиционния компилатор. Един файл = един продукт (една сесия).
"""
from __future__ import annotations
import yaml

from .models import Product
from .composition import build_product
from .errors import PifInputError


def load_product(path: str) -> tuple[Product, list[str]]:
    """Зарежда продукт от YAML файл.

    Връща (product, warnings). Предупрежденията съдържат алармите
    (напр. сума ≠ 100%, използвана горна граница на диапазон, остатък).
    """
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    if doc is None:
        raise PifInputError(f"Празен или невалиден YAML файл: {path}")
    return build_product(doc)
