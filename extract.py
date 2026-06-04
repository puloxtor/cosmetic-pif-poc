#!/usr/bin/env python3
"""
EXTRACT — Слой 2: документ(и) → ЧЕРНОВА на raw_materials (YAML).

Хибрид:
  - Цифров PDF (текстов слой)        → детерминистично четене (pdfplumber).
  - Изображение / сканиран PDF / ръкопис → AI-зрение (Claude), ако е позволено.

Употреба:
    python3 extract.py FILE [FILE ...] \
        [--type composition|fragrance|formula|auto] \
        [--name NAME] [--dose D] [--ocr | --no-ocr] [--model MODEL]

⚠️ Изходът е ЧЕРНОВА за проверка от човек — НЕ доверен източник на числа.
AI-зрението е недетерминистично; всяко число се проверява. Дозите идват от
рецептата (или от --type formula извличане, също за проверка).
"""
from __future__ import annotations
import argparse
import os
import sys

from pif_engine.extraction.pdf import all_lines, has_text_layer
from pif_engine.extraction.parse import (
    parse_composition, parse_fragrance, looks_like_fragrance,
)
from pif_engine.extraction.draft import raw_material_draft, to_yaml

_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _is_pdf(path: str) -> bool:
    return os.path.splitext(path)[1].lower() == ".pdf"


def _deterministic(path: str, kind: str, name: str, dose, notes: list[str]) -> dict:
    lines = all_lines(path)
    if kind == "auto":
        kind = "fragrance" if looks_like_fragrance(lines, path) else "composition"
        notes.append(f"{name}: авто-разпознат тип = {kind}")
    if kind == "fragrance":
        allergens = parse_fragrance(lines)
        if not allergens:
            notes.append(f"{name}: 0 алергена разпознати — провери ръчно.")
        return raw_material_draft(name, dose, allergens=allergens, is_fragrance=True)
    comp = parse_composition(lines)
    if not comp:
        notes.append(f"{name}: 0 съставки разпознати — въведи ръчно или пробвай --ocr.")
    return raw_material_draft(name, dose, constituents=comp)


def _vision(path: str, kind: str, name: str, dose, model, notes: list[str]):
    from pif_engine.extraction import vision
    notes.append(f"{name}: AI-зрение (модел {model or vision.DEFAULT_MODEL}) — ПРОВЕРИ всяко число.")
    if kind == "auto":
        kind = "composition"
        notes.append(f"{name}: при AI-зрение приемам тип = composition (смени с --type).")
    if kind == "formula":
        rms, vnotes = vision.extract(path, "formula", model)
        notes.extend(vnotes)
        return rms  # списък от суровини (без композиция)
    if kind == "fragrance":
        allergens, vnotes = vision.extract(path, "fragrance", model)
        notes.extend(vnotes)
        return raw_material_draft(name, dose, allergens=allergens, is_fragrance=True)
    comp, vnotes = vision.extract(path, "composition", model)
    notes.extend(vnotes)
    return raw_material_draft(name, dose, constituents=comp)


def process_file(path, kind, name, dose, ocr_mode, model, notes):
    rm_name = name or os.path.splitext(os.path.basename(path))[0]
    dose_val = dose if dose is not None else "TODO"
    is_image = os.path.splitext(path)[1].lower() in _IMAGE_EXT

    # Маршрутиране: кога AI-зрение vs детерминистично
    use_vision = False
    if ocr_mode == "force":
        use_vision = True
    elif ocr_mode == "never":
        use_vision = False
    else:  # auto
        if is_image:
            use_vision = True
        elif _is_pdf(path) and not has_text_layer(path):
            use_vision = True
            notes.append(f"{rm_name}: сканиран PDF (без текстов слой) → AI-зрение.")

    if use_vision:
        if ocr_mode == "never":
            notes.append(f"{rm_name}: нужен е OCR, но е забранен (--no-ocr) — пропуснат.")
            return None
        return _vision(path, kind, rm_name, dose_val, model, notes)

    if is_image:  # не би трябвало да стигне тук при auto, но за всеки случай
        notes.append(f"{rm_name}: изображение, но OCR е забранен — въведи ръчно.")
        return raw_material_draft(rm_name, dose_val, constituents=[])
    return _deterministic(path, kind, rm_name, dose_val, notes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Извличане на чернова raw_materials от документи (PDF/изображение).")
    ap.add_argument("files", nargs="+", help="PDF или изображение")
    ap.add_argument("--type", choices=["composition", "fragrance", "formula", "auto"], default="auto")
    ap.add_argument("--name", default=None, help="име на суровината (по подразбиране: името на файла)")
    ap.add_argument("--dose", type=float, default=None, help="доза %% в продукта (ако се знае)")
    ap.add_argument("--model", default=None, help="модел за AI-зрение (по подразбиране: claude-opus-4-8)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--ocr", dest="ocr", action="store_const", const="force", help="винаги ползвай AI-зрение")
    g.add_argument("--no-ocr", dest="ocr", action="store_const", const="never", help="забрани AI-зрение (само детерминистично)")
    ap.set_defaults(ocr="auto")
    args = ap.parse_args(argv)

    raw_materials: list[dict] = []
    all_notes: list[str] = []
    for path in args.files:
        if not os.path.isfile(path):
            print(f"Пропуснат (липсва): {path}", file=sys.stderr)
            continue
        name = args.name if len(args.files) == 1 else None
        result = process_file(path, args.type, name, args.dose, args.ocr, args.model, all_notes)
        if result is None:
            continue
        if isinstance(result, list):     # formula → няколко суровини
            raw_materials.extend(result)
        else:
            raw_materials.append(result)

    if not raw_materials:
        print("Няма извлечени суровини.", file=sys.stderr)
        if all_notes:
            print("\n".join("# " + n for n in all_notes), file=sys.stderr)
        return 2

    print(to_yaml(raw_materials, notes=all_notes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
