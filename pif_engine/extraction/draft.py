"""
Сглобяване на ЧЕРНОВА (draft) за ревизия от човек и export към YAML,
съвместим с формата на products/TEMPLATE.yaml.
"""
from __future__ import annotations
import yaml


class _NoAliasDumper(yaml.SafeDumper):
    """Без YAML anchors/aliases — четим, самостоятелен изход."""
    def ignore_aliases(self, data):
        return True


def raw_material_draft(name, dose_pct, *, constituents=None, allergens=None,
                       is_fragrance=False) -> dict:
    rm: dict = {"name": name, "dose_pct": dose_pct}
    if is_fragrance:
        rm["is_fragrance"] = True
        rm["allergens"] = allergens or []
    else:
        rm["composition"] = constituents or []
    return rm


def to_yaml(raw_materials: list[dict], notes: list[str] | None = None) -> str:
    """YAML фрагмент с раздел raw_materials + ясна бележка, че е чернова."""
    header = [
        "# ====================================================================",
        "# ЧЕРНОВА — извлечено автоматично от документи. ПРОВЕРИ ВСЯКО ЧИСЛО",
        "# преди употреба. Дозите (dose_pct) се попълват от рецептата (ръчно).",
        "# ====================================================================",
    ]
    if notes:
        header += [f"# БЕЛЕЖКА: {n}" for n in notes]
    body = yaml.dump({"raw_materials": raw_materials}, Dumper=_NoAliasDumper,
                     allow_unicode=True, sort_keys=False, default_flow_style=False)
    return "\n".join(header) + "\n" + body
