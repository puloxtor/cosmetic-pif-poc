#!/usr/bin/env python3
"""
EXTRACT — Слой 2: документ(и) → ЧЕРНОВА на raw_materials (YAML).

Употреба:
    python3 extract.py FILE.pdf [FILE2.pdf ...] \
        [--type composition|fragrance|auto] [--name NAME] [--dose D]

За всеки файл извлича редовете (координатно подравнени), предлага композиция
или алергени и отпечатва YAML фрагмент за поставяне в продуктов файл.

⚠️ Изходът е ЧЕРНОВА за проверка от човек — НЕ доверен източник на числа.
Дозите (dose_pct) идват от рецептата и се попълват ръчно.
"""
from __future__ import annotations
import argparse
import os
import sys

from pif_engine.extraction.pdf import all_lines
from pif_engine.extraction.parse import (
    parse_composition, parse_fragrance, looks_like_fragrance,
)
from pif_engine.extraction.draft import raw_material_draft, to_yaml


def process_file(path: str, kind: str, name: str | None, dose) -> tuple[dict, list[str]]:
    notes: list[str] = []
    lines = all_lines(path)
    rm_name = name or os.path.splitext(os.path.basename(path))[0]
    dose_val = dose if dose is not None else "TODO"

    if kind == "auto":
        kind = "fragrance" if looks_like_fragrance(lines, path) else "composition"
        notes.append(f"{rm_name}: авто-разпознат тип = {kind}")

    if kind == "fragrance":
        allergens = parse_fragrance(lines)
        if not allergens:
            notes.append(f"{rm_name}: 0 алергена разпознати — провери ръчно.")
        rm = raw_material_draft(rm_name, dose_val, allergens=allergens, is_fragrance=True)
    else:
        comp = parse_composition(lines)
        if not comp:
            notes.append(f"{rm_name}: 0 съставки разпознати (възможно легенда-кодирано "
                         "или сканирано) — въведи ръчно.")
        rm = raw_material_draft(rm_name, dose_val, constituents=comp)
    return rm, notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Извличане на чернова raw_materials от PDF документи.")
    ap.add_argument("files", nargs="+", help="PDF файл(ове)")
    ap.add_argument("--type", choices=["composition", "fragrance", "auto"], default="auto")
    ap.add_argument("--name", default=None, help="име на суровината (по подразбиране: името на файла)")
    ap.add_argument("--dose", type=float, default=None, help="доза %% в продукта (ако се знае)")
    args = ap.parse_args(argv)

    raw_materials: list[dict] = []
    all_notes: list[str] = []
    for path in args.files:
        if not os.path.isfile(path):
            print(f"Пропуснат (липсва): {path}", file=sys.stderr)
            continue
        name = args.name if len(args.files) == 1 else None
        rm, notes = process_file(path, args.type, name, args.dose)
        raw_materials.append(rm)
        all_notes.extend(notes)

    if not raw_materials:
        print("Няма обработени файлове.", file=sys.stderr)
        return 2

    print(to_yaml(raw_materials, notes=all_notes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
