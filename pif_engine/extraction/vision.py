"""
AI-зрение за извличане (Слой 2) — за СКАНИРАНИ/снимани документи без текстов слой
(вкл. ръкописни рецепти), където pdfplumber не работи.

ПРИНЦИП (CLAUDE.md): AI OCR е НЕДЕТЕРМИНИСТИЧЕН — може да сгреши цифра. Затова:
  - моделът само ЧЕТЕ (OCR) и връща суров текст/таблица; НЕ смята и НЕ налучква;
  - целият изход е ЧЕРНОВА, маркирана „AI-предложение — провери";
  - парсването на числата и сметките остават в детерминистичен Python.

Изисква пакета `anthropic` и ANTHROPIC_API_KEY в средата.
Цифрови PDF-и (с текстов слой) НЕ минават оттук — те се четат от extraction/pdf.py.
"""
from __future__ import annotations
import base64
import json
import os
import re

# По подразбиране — най-способният модел (виж claude-api skill). Сменяем с env.
DEFAULT_MODEL = os.environ.get("PIF_VISION_MODEL", "claude-opus-4-8")

_MEDIA = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp",
}

SYSTEM = (
    "Ти си извличащ асистент за козметични регулаторни документи "
    "(композишън стейтмънти, листи с ароматни алергени, рецептури). "
    "Извличаш САМО това, което реално виждаш в документа. "
    "НЕ изчисляваш, НЕ преобразуваш и НЕ налучкваш стойности. "
    "Връщай числата точно както са изписани (десетична запетая → точка). "
    "Диапазон се връща като текст във вида 'low-high' (напр. '45-55'). "
    "Ако нещо е нечетливо или несигурно, върни празен низ за стойността и "
    "опиши съмнението в 'notes'. Не добавяй вещества, които не са в документа."
)

# Схеми за structured outputs — само низове (максимална съвместимост).
_SCHEMAS = {
    "fragrance": {
        "type": "object", "additionalProperties": False,
        "required": ["allergens", "notes"],
        "properties": {
            "allergens": {
                "type": "array",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["name", "cas", "pct_in_fragrance"],
                    "properties": {
                        "name": {"type": "string"},
                        "cas": {"type": "string"},
                        "pct_in_fragrance": {"type": "string"},
                    },
                },
            },
            "notes": {"type": "array", "items": {"type": "string"}},
        },
    },
    "composition": {
        "type": "object", "additionalProperties": False,
        "required": ["constituents", "notes"],
        "properties": {
            "constituents": {
                "type": "array",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["inci_name", "cas", "amount"],
                    "properties": {
                        "inci_name": {"type": "string"},
                        "cas": {"type": "string"},
                        "amount": {"type": "string"},  # '45-55' | '100' | '0.9' | 'above 50' | '<=1'
                    },
                },
            },
            "notes": {"type": "array", "items": {"type": "string"}},
        },
    },
    "formula": {
        "type": "object", "additionalProperties": False,
        "required": ["product_name", "raw_materials", "notes"],
        "properties": {
            "product_name": {"type": "string"},
            "raw_materials": {
                "type": "array",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["name", "dose_pct"],
                    "properties": {
                        "name": {"type": "string"},
                        "dose_pct": {"type": "string"},
                    },
                },
            },
            "notes": {"type": "array", "items": {"type": "string"}},
        },
    },
}

_PROMPTS = {
    "fragrance": "Извлечи всички ДЕКЛАРИРАНИ ароматни алергени (име, CAS, % в парфюма). "
                 "Пропусни редовете с 'n.d.' / '----' (не са декларирани).",
    "composition": "Извлечи композицията (INCI име, CAS, количество като текст — "
                   "точен %, диапазон 'low-high', или формулировка като 'above 50%').",
    "formula": "Извлечи рецептурата: име на продукта и всеки ред суровина с дозата ѝ (%).",
}


def detect_media_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return "application/pdf"
    if ext in _MEDIA:
        return _MEDIA[ext]
    raise ValueError(f"Неподдържан формат за AI-зрение: {ext}")


def _content_block(path: str) -> dict:
    media = detect_media_type(path)
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    btype = "document" if media == "application/pdf" else "image"
    return {"type": btype, "source": {"type": "base64", "media_type": media, "data": data}}


def _call_model(path: str, kind: str, model: str) -> dict:
    """Извиква Claude (vision) и връща JSON по схемата. Изолирано за тестване."""
    try:
        import anthropic
    except ImportError as e:  # pragma: no cover
        raise ImportError("За AI-зрение е нужен пакетът `anthropic` (`pip install anthropic`).") from e
    client = anthropic.Anthropic()  # чете ANTHROPIC_API_KEY от средата
    resp = client.messages.create(
        model=model,
        max_tokens=16000,
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMAS[kind]}},
        messages=[{
            "role": "user",
            "content": [_content_block(path), {"type": "text", "text": _PROMPTS[kind]}],
        }],
    )
    text = next((b.text for b in resp.content if b.type == "text"), "")
    return json.loads(text)


# ---- Детерминистично преобразуване на суровия текст към spec (не от LLM) ----

_RANGE = re.compile(r"(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)")
_NUM = re.compile(r"\d+(?:[.,]\d+)?")
_ATMOST = re.compile(r"(?:<=|≤|max\.?|до)\s*(\d+(?:[.,]\d+)?)", re.I)
_ABOVE = re.compile(r"(?:>=|>|≥|above|over|superiore|над)\s*\d", re.I)


def _f(s: str) -> float:
    return float(s.replace(",", "."))


def amount_to_spec(text: str) -> dict | None:
    """'45-55' → {range:[45,55]}; '100' → {pct:100}; 'above 50' → {remainder};
    '<=1' → {at_most:1}. None ако е непознато/празно."""
    if not text or not text.strip():
        return None
    m = _RANGE.search(text)
    if m:
        return {"range": [_f(m.group(1)), _f(m.group(2))]}
    m = _ATMOST.search(text)
    if m:
        return {"at_most": _f(m.group(1))}
    if _ABOVE.search(text):
        return {"remainder": True}
    m = _NUM.search(text)
    if m:
        return {"pct": _f(m.group(0))}
    return None


def to_composition(data: dict) -> tuple[list[dict], list[str]]:
    out, notes = [], list(data.get("notes", []))
    for c in data.get("constituents", []):
        spec = amount_to_spec(c.get("amount", ""))
        entry = {"inci_name": c.get("inci_name", "?"), "cas": c.get("cas", "-") or "-"}
        if spec is None:
            notes.append(f"{entry['inci_name']}: нечетимо количество '{c.get('amount','')}' — въведи ръчно.")
        else:
            entry.update(spec)
        out.append(entry)
    return out, notes


def to_fragrance(data: dict) -> tuple[list[dict], list[str]]:
    out, notes = [], list(data.get("notes", []))
    for a in data.get("allergens", []):
        spec = amount_to_spec(a.get("pct_in_fragrance", ""))
        if not spec or "pct" not in spec:
            notes.append(f"{a.get('name','?')}: нечетим % '{a.get('pct_in_fragrance','')}' — въведи ръчно.")
            continue
        out.append({"name": a.get("name", "?"), "cas": a.get("cas", "-") or "-",
                    "pct_in_fragrance": spec["pct"]})
    return out, notes


def to_formula(data: dict) -> tuple[list[dict], list[str]]:
    out, notes = [], list(data.get("notes", []))
    for rm in data.get("raw_materials", []):
        spec = amount_to_spec(rm.get("dose_pct", ""))
        dose = spec.get("pct") if spec else None
        if dose is None:
            notes.append(f"{rm.get('name','?')}: нечетима доза '{rm.get('dose_pct','')}' — въведи ръчно.")
            dose = "TODO"
        out.append({"name": rm.get("name", "?"), "dose_pct": dose, "composition": []})
    return out, notes


def extract(path: str, kind: str, model: str | None = None):
    """AI-зрение извличане. kind: fragrance|composition|formula.
    Връща (data, notes) — data е list според kind. Всичко е ЧЕРНОВА за проверка."""
    if kind not in _SCHEMAS:
        raise ValueError(f"Непознат kind: {kind}")
    raw = _call_model(path, kind, model or DEFAULT_MODEL)
    if kind == "fragrance":
        return to_fragrance(raw)
    if kind == "composition":
        return to_composition(raw)
    return to_formula(raw)
