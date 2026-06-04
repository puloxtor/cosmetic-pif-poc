#!/usr/bin/env python3
"""
EXTRACT — Слой 2: документ(и) → ЧЕРНОВА на raw_materials (YAML).

Тънък CLI над pif_engine.extraction.router.extract_drafts (същата логика, която
ползва и UX-ът). Хибрид: цифров PDF → детерминистично; изображение/сканиран PDF
→ AI-зрение (Claude).

Употреба:
    python3 extract.py FILE [FILE ...] \
        [--type composition|fragrance|formula|auto] \
        [--name NAME] [--dose D] [--ocr | --no-ocr] [--model MODEL]

⚠️ Изходът е ЧЕРНОВА за проверка от човек — НЕ доверен източник на числа.
"""
from __future__ import annotations
import argparse
import os
import sys

from pif_engine.extraction.router import extract_drafts
from pif_engine.extraction.draft import to_yaml


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Извличане на чернова raw_materials от документи (PDF/изображение).")
    ap.add_argument("files", nargs="+", help="PDF или изображение")
    ap.add_argument("--type", choices=["composition", "fragrance", "formula", "auto"], default="auto")
    ap.add_argument("--name", default=None, help="име на суровината (по подразбиране: името на файла)")
    ap.add_argument("--dose", type=float, default=None, help="доза %% в продукта (ако се знае)")
    ap.add_argument("--model", default=None, help="модел за AI-зрение (по подразбиране: claude-opus-4-8)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--ocr", dest="ocr", action="store_const", const="force", help="винаги ползвай AI-зрение")
    g.add_argument("--no-ocr", dest="ocr", action="store_const", const="never", help="забрани AI-зрение")
    ap.set_defaults(ocr="auto")
    args = ap.parse_args(argv)

    raw_materials: list[dict] = []
    all_notes: list[str] = []
    for path in args.files:
        if not os.path.isfile(path):
            print(f"Пропуснат (липсва): {path}", file=sys.stderr)
            continue
        name = args.name if len(args.files) == 1 else None
        rms, notes = extract_drafts(path, args.type, args.ocr, name, args.dose, args.model)
        raw_materials.extend(rms)
        all_notes.extend(notes)

    if not raw_materials:
        print("Няма извлечени суровини.", file=sys.stderr)
        if all_notes:
            print("\n".join("# " + n for n in all_notes), file=sys.stderr)
        return 2

    print(to_yaml(raw_materials, notes=all_notes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
