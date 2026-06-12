"""Произход на енджина за одит (Finding R3): версия + git SHA на инсталирания пакет.

Подписващият оценител (Член 10) носи юридическа отговорност за досието, затова
всеки генериран CPSR трябва да казва ТОЧНО коя версия на правилата го е
произвела. `engine_provenance()` е резолвър, който НИКОГА не вдига изключение и
опитва по ред:

  1. ``importlib.metadata`` → ``direct_url.json`` (PEP 610): точният SHA, който
     pip е инсталирал от git пина. Това е продукционният случай — UX пинова
     ``pif-engine[extraction] @ git+...@<SHA>`` в ``requirements.txt``.
  2. ``.git/HEAD`` разходка относно пакета — за editable/dev инсталация
     (``pip install -e ../cosmetic-pif-poc``). Същата техника като
     UX ``app/main.py::_git_commit()``.
  3. ``"unknown"`` — нищо не е намерено (никога не чупи генерирането).
"""
from __future__ import annotations
import json
from pathlib import Path


def _sha_from_direct_url() -> str | None:
    """SHA от PEP 610 direct_url.json (pip-from-git инсталация)."""
    try:
        from importlib import metadata
        text = metadata.distribution("pif-engine").read_text("direct_url.json")
        if not text:
            return None
        vcs = (json.loads(text) or {}).get("vcs_info") or {}
        return vcs.get("commit_id") or None
    except Exception:
        return None


def _sha_from_git() -> str | None:
    """SHA от .git/HEAD относно пакета (editable/dev инсталация)."""
    try:
        git_dir = Path(__file__).resolve().parent.parent / ".git"
        if not git_dir.exists():
            return None
        head = (git_dir / "HEAD").read_text().strip()
        if not head.startswith("ref: "):
            return head or None          # detached HEAD вече е SHA
        ref_name = head[5:]
        ref_file = git_dir / ref_name
        if ref_file.exists():
            return ref_file.read_text().strip() or None
        # packed-refs резервен вариант
        packed = git_dir / "packed-refs"
        if packed.exists():
            for ln in packed.read_text().splitlines():
                if ln and not ln.startswith(("#", "^")) and ln.endswith(ref_name):
                    return ln.split()[0]
        return None
    except Exception:
        return None


def engine_provenance() -> dict:
    """Връща ``{version, sha, source}``. Никога не вдига изключение.

    ``source`` ∈ {``"direct_url"``, ``"git"``, ``"none"``}. ``sha`` е скъсен до
    12 знака, или ``"unknown"`` ако не може да се определи.
    """
    from . import __version__
    sha = _sha_from_direct_url()
    if sha:
        return {"version": __version__, "sha": sha[:12], "source": "direct_url"}
    sha = _sha_from_git()
    if sha:
        return {"version": __version__, "sha": sha[:12], "source": "git"}
    return {"version": __version__, "sha": "unknown", "source": "none"}
