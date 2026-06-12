"""Типизирана йерархия от грешки на енджина (Finding R2).

Старият код вдигаше голи ``ValueError``. Сега ги структурираме, за да може
UX-ът (`app/engine.py::friendly_error`) да разклонява по ТИП, а не по текста на
съобщението (string-sniffing е чупливо между версии на енджина).

Двете конкретни грешки наследяват и ``ValueError`` — така всеки стар
`except ValueError` / `pytest.raises(ValueError)` продължава да работи.
Съобщенията остават дословно същите.
"""
from __future__ import annotations


class PifError(Exception):
    """Базова грешка на енджина (всичко по-долу наследява нея)."""


class PifInputError(PifError, ValueError):
    """Структурна грешка във входа: липсваща/невалидна секция, ключ или стойност.

    Напр.: липсва секция ``product`` / ``raw_materials``; задължителен ключ;
    конституент без разпозната стойност (pct/range/at_most/remainder).
    """


class PifDataGapError(PifError, ValueError):
    """Липсващи задължителни данни за конкретна суровина.

    Напр.: суровина без ``dose_pct``; обикновена суровина без ``composition``.
    """
