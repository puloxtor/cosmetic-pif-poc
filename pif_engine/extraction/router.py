"""
Маршрутизатор за извличане (Слой 2) — споделя се от CLI (extract.py) и UX.

Цифров PDF (текстов слой) → детерминистично четене (pdfplumber).
Изображение / сканиран PDF / ръкопис → AI-зрение (Claude), ако е позволено.
Изходът винаги е ЧЕРНОВА (list[dict] raw_materials + notes) за човешка проверка.
"""
from __future__ import annotations
import os

from .pdf import all_lines, has_text_layer
from .parse import parse_composition, parse_fragrance, looks_like_fragrance
from .draft import raw_material_draft
from .filter import filter_candidates

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _is_pdf(path: str) -> bool:
    return os.path.splitext(path)[1].lower() == ".pdf"


def _is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_EXT


def _deterministic(path, kind, name, dose, notes) -> list[dict]:
    lines = all_lines(path)
    if kind == "auto":
        kind = "fragrance" if looks_like_fragrance(lines, path) else "composition"
        notes.append(f"{name}: авто-разпознат тип = {kind}")
    if kind == "fragrance":
        allergens = parse_fragrance(lines)
        if not allergens:
            notes.append(f"{name}: 0 алергена разпознати — провери ръчно.")
        return [raw_material_draft(name, dose, allergens=allergens, is_fragrance=True)]
    comp = parse_composition(lines)
    if not comp:
        notes.append(f"{name}: 0 съставки разпознати — въведи ръчно или пробвай OCR.")
    return [raw_material_draft(name, dose, constituents=comp)]


def _vision(path, kind, name, dose, model, notes) -> list[dict]:
    from . import vision
    notes.append(f"{name}: AI-зрение (модел {model or vision.DEFAULT_MODEL}) — ПРОВЕРИ всяко число.")
    if kind == "auto":
        kind = "composition"
        notes.append(f"{name}: при AI-зрение приемам тип = composition (смени с type).")
    if kind == "formula":
        rms, vnotes = vision.extract(path, "formula", model)
        notes.extend(vnotes)
        return rms
    if kind == "fragrance":
        allergens, vnotes = vision.extract(path, "fragrance", model)
        notes.extend(vnotes)
        return [raw_material_draft(name, dose, allergens=allergens, is_fragrance=True)]
    comp, vnotes = vision.extract(path, "composition", model)
    notes.extend(vnotes)
    return [raw_material_draft(name, dose, constituents=comp)]


def extract_drafts(path: str, kind: str = "auto", ocr_mode: str = "auto",
                   name: str | None = None, dose=None, model: str | None = None):
    """Извлича ЧЕРНОВА от един документ.

    kind: composition | fragrance | formula | auto
    ocr_mode: auto (маршрутира по текстов слой) | force (винаги AI-зрение) | never
    Връща (raw_materials: list[dict], notes: list[str]).
    """
    notes: list[str] = []
    rm_name = name or os.path.splitext(os.path.basename(path))[0]
    dose_val = dose if dose is not None else "TODO"

    if ocr_mode == "force":
        use_vision = True
    elif ocr_mode == "never":
        use_vision = False
    else:  # auto
        use_vision = _is_image(path) or (_is_pdf(path) and not has_text_layer(path))
        if use_vision and _is_pdf(path):
            notes.append(f"{rm_name}: сканиран PDF (без текстов слой) → AI-зрение.")

    if use_vision:
        rms = _vision(path, kind, rm_name, dose_val, model, notes)
    elif _is_image(path):
        notes.append(f"{rm_name}: изображение, но OCR е забранен — въведи ръчно.")
        rms = [raw_material_draft(rm_name, dose_val, constituents=[])]
    else:
        rms = _deterministic(path, kind, rm_name, dose_val, notes)

    # Отсей не-INCI кандидати (правен/табличен/адресен текст) на ВСИЧКИ пътища,
    # преди да върнем черновата. Не е тих пропуск — добавяме бележка с броя.
    rms, dropped = filter_candidates(rms)
    if dropped:
        notes.append(
            f"{rm_name}: пропуснати {dropped} реда, които не приличат на INCI "
            "(правен/табличен/адресен текст). Провери дали не липсва реална съставка."
        )
    return rms, notes
