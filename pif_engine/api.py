"""Типизиран контракт за резултата на ``compute_from_yaml`` (Finding R1).

UX ``app/engine.py::compute_from_yaml`` произвежда този dict; типизирането прави
счупване на контракта грешка при разработка/инсталация, вместо тих ``KeyError``
в продукцията. Обикновен ``dict`` удовлетворява ``TypedDict`` по време на
изпълнение, затова промяната е напълно съвместима назад.

Двата опционални ключа (``cpsr``, ``blockers``) са моделирани чрез наследяване с
``total=False`` — работи на всяка поддържана версия на Python без ``NotRequired``.
"""
from __future__ import annotations
from typing import TypedDict

from .warnings import EngineWarning


class TableRow(TypedDict):
    inci: str
    pct: float


class AllergenRow(TypedDict):
    name: str
    cas: str
    conc_pct: float
    threshold_pct: float
    declared: bool


class _ComputeResultRequired(TypedDict):
    name: str
    product_type: str
    warnings: list[EngineWarning]
    table: list[TableRow]
    total: float
    sum_ok: bool
    inci: list[str]
    declared: list[str]
    allergens: list[AllergenRow]


class ComputeResult(_ComputeResultRequired, total=False):
    """Контрактът, който UX ``compute_from_yaml`` връща към шаблоните.

    Задължителни: всички полета от ``_ComputeResultRequired``.
    Опционални: ``cpsr`` (при include_cpsr), ``blockers`` (твърди блокери, R6).
    """
    cpsr: str
    blockers: list[str]
