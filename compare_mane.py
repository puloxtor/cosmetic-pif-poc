#!/usr/bin/env python3
"""
Сравнява генерирания изход с реалния CPSR на MANE Shampoo.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from data.mane_shampoo import mane_shampoo
from pif_engine.cpsr import generate_cpsr
from pif_engine.allergens import generate_inci, allergens_to_declare, calculate_allergens
from pif_engine.toxicology import calculate_mos

# Реалният INCI от документа (Шаман Студио ООД)
REAL_INCI = [
    "AQUA", "DISODIUM LAURETH SULFOSUCCINATE", "COCAMIDOPROPYL BETAINE",
    "COCO-GLUCOSIDE", "GLYCERYL OLEATE", "SERENOA SERRULATA FRUIT EXTRACT",
    "PEG-120 METHYL GLUCOSE DIOLEATE", "PHYLLANTHUS EMBLICA FRUIT EXTRACT",
    "CUCURBITA PEPO SEED EXTRACT", "BIOTIN",
    "PANTHENYL HYDROXYPROPYL STEARDIMONIUM CHLORIDE", "TOCOPHEROL",
    "PROPANEDIOL", "GLYCERIN", "CITRUS GRANDIS PEEL OIL", "CITRIC ACID",
    "HYDROGENATED PALM GLYCERIDES CITRATE", "ETHYLHEXYLGLYCERIN",
    "LACTIC ACID", "SODIUM BENZOATE", "POTASSIUM SORBATE", "PHENOXYETHANOL",
    "LIMONENE",
]


def main():
    print("=" * 70)
    print("СРАВНЕНИЕ: генериран изход vs реален CPSR — MANE Protect Shampoo")
    print("=" * 70)

    # --- Алергени ---
    print("\n## АЛЕРГЕНИ")
    totals = calculate_allergens(mane_shampoo)
    declared = allergens_to_declare(mane_shampoo)
    print(f"Изчислени: {totals}")
    print(f"Над прага (rinse-off 0.01%): {declared}")
    print(f"Реален INCI съдържа Limonene: {'LIMONENE' in REAL_INCI} ✅")
    match_allergen = ("Limonene" in declared) == ("LIMONENE" in REAL_INCI)
    print(f"➜ Съвпадение по алерген: {'✅ ДА' if match_allergen else '❌ НЕ'}")

    # --- INCI ред ---
    print("\n## INCI СПИСЪК")
    gen = [x.upper() for x in generate_inci(mane_shampoo)]
    print(f"Генериран ({len(gen)}):")
    print("  " + ", ".join(gen))
    print(f"\nРеален ({len(REAL_INCI)}):")
    print("  " + ", ".join(REAL_INCI))

    # Сравнение по присъствие
    gen_set, real_set = set(gen), set(REAL_INCI)
    missing = real_set - gen_set
    extra = gen_set - real_set
    print(f"\nЛипсват в генерирания: {missing or '— няма'}")
    print(f"В повече в генерирания: {extra or '— няма'}")

    # Проверка: Limonene последен, след съставките
    print(f"\nLimonene е последен в генерирания: "
          f"{'✅' if gen[-1]=='LIMONENE' else '❌'}")
    print(f"Aqua е първи (най-висока концентрация): "
          f"{'✅' if gen[0]=='AQUA' else '❌'}")

    # --- MoS ---
    print("\n## MoS (токсикологична безопасност)")
    for r in calculate_mos(mane_shampoo):
        print(f"  {r.inci_name:45s} SED={r.sed:.5f}  MoS={r.mos:>10.1f}  "
              f"{'✅' if r.is_safe else '❌ <100'}")

    # --- Запис на пълния доклад ---
    report = generate_cpsr(mane_shampoo)
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/MANE_CPSR_generated.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\n" + "=" * 70)
    print("✅ Пълен генериран доклад: outputs/MANE_CPSR_generated.md")


if __name__ == "__main__":
    main()
