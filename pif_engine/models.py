"""
Даннови модели за PIF/CPSR системата.
Дефинира структурата на суровини, формули, сертификати и продукти.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProductType(str, Enum):
    """Класификация определя праговете за алергени и фактора на излагане."""
    LEAVE_ON = "leave-on"      # праг алерген 0.001%
    RINSE_OFF = "rinse-off"    # праг алерген 0.01%


class CramerClass(int, Enum):
    """Cramer класове за мигриращи вещества от опаковка (SCCS NoG)."""
    CLASS_1 = 1   # лимит 46 µg/kg bw/day
    CLASS_3 = 3   # лимит 2.3 µg/kg bw/day


@dataclass
class AllergenContent:
    """Съдържание на един от 80+ регулирани алергени в ароматен компонент.
    fraction = масов дял на алергена в компонента (0..1)."""
    name: str            # INCI име на алергена, напр. "Limonene"
    cas: str
    fraction: float      # напр. 0.08 = 8% от компонента


@dataclass
class ToxProfile:
    """Токсикологичен профил за изчисление на MoS."""
    pod: float                 # Point of Departure (NOAEL), mg/kg bw/day
    dermal_absorption: float = 0.5   # DAp дял 0..1 (по подразбиране 50%)


@dataclass
class Ingredient:
    """Суровина от master таблицата (въвеждат Милена/Хаби)."""
    inci_name: str
    cas: str
    function: str                       # напр. "emollient", "fragrance"
    is_fragrance: bool = False          # парфюм/етерично масло -> носи алергени
    allergens: list[AllergenContent] = field(default_factory=list)
    tox: Optional[ToxProfile] = None
    # Регулаторни ограничения (Анекси II–VI)
    restricted: bool = False
    max_allowed_pct: Optional[float] = None
    # Контрол на документацията
    has_sds: bool = False
    has_coa: bool = False
    has_ifra: bool = False


@dataclass
class FormulaLine:
    """Един ред от формулата на Мими: суровина + концентрация."""
    ingredient: Ingredient
    concentration_pct: float   # % w/w в крайния продукт


@dataclass
class Claim:
    """Маркетингова претенция за валидиране."""
    text: str
    category: str = "general"   # напр. "performance", "ingredient", "comparative"


@dataclass
class Product:
    """Цялостен продукт за обработка."""
    name: str
    product_type: ProductType
    formula: list[FormulaLine]
    claims: list[Claim] = field(default_factory=list)
    sale_countries: list[str] = field(default_factory=list)
    # Параметри на излагане (SCCS таблици 3A/3B)
    body_weight_kg: float = 60.0  # стандартно тегло SCCS
    # Реална методология (както в CPSR на MANE Shampoo):
    # A се изчислява от приложено количество × фактор на ретенция / тегло
    applied_amount_g: float = 10.46   # приложено количество (g/ден)
    retention_factor: float = 0.01    # 0.01 rinse-off, 1.0 leave-on (типично)

    @property
    def daily_exposure_g(self) -> float:
        """Калкулирана дневна експозиция (g/ден)."""
        return self.applied_amount_g * self.retention_factor

    @property
    def exposure_A_mg_per_kg(self) -> float:
        """A (mg/kg bw/day) — дневна експозиция на продукта за кг телесна маса.
        = (приложено_g × ретенция × 1000 mg/g) / тегло_kg
        За MANE Shampoo: 10.46 × 0.01 × 1000 / 60 = 1.743 mg/kg bw/day."""
        return (self.daily_exposure_g * 1000.0) / self.body_weight_kg
