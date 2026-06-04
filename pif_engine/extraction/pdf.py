"""
Извличане на текст от PDF с координатно подравняване (pdfplumber).

Същата техника, валидирана в сесията: групираме думите по близка y-координата
и ги подреждаме по x, за да получим коректни редове (така стойността `0.752`
се връзва с правилния ред, а не със съседния).
"""
from __future__ import annotations


def _cluster_words(words: list[dict], y_tol: float) -> list[str]:
    """Групира думите в редове чрез близост по y (не по фиксирана решетка).

    Така стойност, чийто текст е леко изместен по вертикала (напр. пренесен
    CAS или число на собствен ред), се присъединява към правилния ред —
    това решава пропускането на Limonene/Rose Ketones при IFF/Symrise.
    """
    if not words:
        return []
    ws = sorted(words, key=lambda w: w["top"])
    clusters: list[list[dict]] = []
    cur: list[dict] = [ws[0]]
    cur_top = ws[0]["top"]
    for w in ws[1:]:
        if w["top"] - cur_top <= y_tol:
            cur.append(w)
        else:
            clusters.append(cur)
            cur = [w]
            cur_top = w["top"]
    clusters.append(cur)
    return [" ".join(t["text"] for t in sorted(c, key=lambda t: t["x0"]))
            for c in clusters]


def extract_lines(path: str, y_tol: float = 6.0) -> list[list[str]]:
    """Връща списък от страници; всяка страница е списък от редове (низове)."""
    try:
        import pdfplumber
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "За извличане от PDF е нужен pdfplumber (`pip install pdfplumber`)."
        ) from e

    pages: list[list[str]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(_cluster_words(page.extract_words(), y_tol))
    return pages


def all_lines(path: str, y_tol: float = 6.0) -> list[str]:
    """Всички редове от всички страници, в ред."""
    out: list[str] = []
    for page in extract_lines(path, y_tol=y_tol):
        out.extend(page)
    return out
