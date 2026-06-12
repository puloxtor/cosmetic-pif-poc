"""Структурирани предупреждения от енджина (Finding R5).

`EngineWarning` е ПОДКЛАС на `str`: рендерира се като старото съобщение (със
същия емоджи префикс), затова целият стар код продължава да работи без промяна —
Jinja `{{ w }}`, `substring in w`, `w.lower()`, `"\\n".join(...)`,
`isinstance(w, str)`. Новият код чете `.severity` / `.code` / `.subject` за
машинно-четима тежест, която управлява диференцирания гейт в UX-а (Finding R6).

ПРИНЦИП (CLAUDE.md): това НЕ е тих пропуск. Старите низове остават дословни;
само добавяме машинно-четими атрибути отгоре.
"""
from __future__ import annotations


class Severity:
    """Нива на тежест. Обикновени низове (тривиална сериализация/шаблони)."""
    BLOCKER = "blocker"   # твърд блокер — НЕ се отхвърля с потвърждение (R6)
    WARNING = "warning"   # ⚠️ аларма — отхвърля се с потвърждение
    INFO = "info"         # ℹ️ бележка — НЕ бива да заключва изходите

    ALL = ("blocker", "warning", "info")


class EngineWarning(str):
    """Низ-съобщение + машинно-четими severity/code/subject.

    Подклас на ``str``, за да е напълно съвместим назад: всеки стар консуматор,
    който третира предупреждението като низ, продължава да работи.
    """
    __slots__ = ("severity", "code", "subject")

    def __new__(cls, severity: str, code: str, message: str, subject: str = ""):
        obj = super().__new__(cls, message)
        obj.severity = severity
        obj.code = code
        obj.subject = subject
        return obj

    @property
    def message(self) -> str:
        """Пълният текст на съобщението (със стария емоджи префикс)."""
        return str(self)

    def __reduce__(self):
        # Коректно pickling на str-подклас с допълнителни атрибути.
        return (self.__class__, (self.severity, self.code, str(self), self.subject))

    def __repr__(self) -> str:
        return f"EngineWarning(severity={self.severity!r}, code={self.code!r}, message={str(self)!r})"
