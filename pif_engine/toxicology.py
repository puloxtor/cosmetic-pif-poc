"""
Токсикологична безопасност: SED и MoS (CPSR Част Б).
"""
from __future__ import annotations
from dataclasses import dataclass
from .models import Product, FormulaLine, CramerClass


MOS_SAFETY_THRESHOLD = 100.0   # MoS > 100 = безопасно

# TTC лимити за мигриращи вещества от опаковка (µg/kg bw/day)
CRAMER_LIMITS = {
    CramerClass.CLASS_1: 46.0,
    CramerClass.CLASS_3: 2.3,
}


@dataclass
class MoSResult:
    inci_name: str
    sed: float        # mg/kg bw/day
    mos: float
    is_safe: bool
    note: str = ""


def calculate_sed(line: FormulaLine, product: Product) -> float:
    """Systemic Exposure Dose по методологията на SCCS (12-та ревизия),
    както е приложена в реалния CPSR на MANE Shampoo:

        SED = A × C/100 × DAp/100

      A   = дневна експозиция на продукта (mg/kg bw/day),
            изчислена от приложено количество × фактор на ретенция / тегло
      C   = концентрация на съставката (%)
      DAp = дермална абсорбция (%) — по подразбиране 50% при липса на данни
    Връща mg/kg bw/day.
    """
    ing = line.ingredient
    if ing.tox is None:
        return 0.0
    A = product.exposure_A_mg_per_kg
    c_fraction = line.concentration_pct / 100.0
    dap = ing.tox.dermal_absorption          # дял 0..1 (= DAp%/100)
    sed = A * c_fraction * dap
    return sed


def calculate_mos(product: Product) -> list[MoSResult]:
    """Изчислява MoS за всяка съставка с токсикологичен профил."""
    results: list[MoSResult] = []
    for line in product.formula:
        ing = line.ingredient
        if ing.tox is None:
            continue
        sed = calculate_sed(line, product)
        if sed <= 0:
            continue
        mos = ing.tox.pod / sed
        results.append(MoSResult(
            inci_name=ing.inci_name,
            sed=round(sed, 6),
            mos=round(mos, 1),
            is_safe=mos > MOS_SAFETY_THRESHOLD,
            note="OK" if mos > MOS_SAFETY_THRESHOLD else "MoS < 100 — реформулирай",
        ))
    return results


def product_is_safe(product: Product) -> tuple[bool, list[MoSResult]]:
    """Цялостно заключение: продуктът е безопасен, ако всички MoS > 100."""
    results = calculate_mos(product)
    safe = all(r.is_safe for r in results) if results else False
    return safe, results
