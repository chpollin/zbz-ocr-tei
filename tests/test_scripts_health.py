"""
Gesundheits-Check fuer ALLE Skripte unter scripts/.

Zwei rein statische Ebenen (keine Drittanbieter-Imports, keine Seiteneffekte,
laeuft auf jedem frischen Clone / in CI):

1. ``test_compiles`` -- jede .py-Datei parst fehlerfrei (faengt Syntaxfehler).
2. ``test_internal_imports_resolve`` -- jeder ``scripts.*``-Import zeigt auf ein
   real existierendes Modul; und auf **Modulebene** existiert der importierte
   Name auch wirklich im Ziel (Submodul oder dort definiert/importiert).

Damit waeren die beiden Fehlerklassen aus dem scripts-Reorg sofort aufgefallen:
- verschobene/umbenannte Module (``from scripts.evaluate_ocr import ...`` nach
  dem Umzug nach ``scripts/eval/``),
- der Leerzeichen-Fall ``from scripts import cer_statistics`` (Modul nach
  ``scripts/eval/`` gewandert -> Name nicht mehr aufloesbar).

Bewusst NICHT geprueft:
- Laufzeit-Import der Skripte (schwere Deps wie torch/google-genai/anthropic/
  pyspellchecker, Import-Seiteneffekte) -- die statische Pruefung genuegt fuer
  die Verdrahtung.
- Funktions-lokale, per try/except gekapselte Importe (z.B. der bekannte
  ``compute_cer``-Fall, O24): deren Ziel-MODUL wird geprueft, der Name nicht,
  da solche Importe bewusst fehlschlagen duerfen (Fallback).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
PY_FILES = sorted(SCRIPTS.rglob("*.py"))
IDS = [str(p.relative_to(REPO)).replace("\\", "/") for p in PY_FILES]


def _module_exists(dotted: str) -> bool:
    """Loest 'scripts.eval.corpus_audit' gegen das Dateisystem auf."""
    rel = Path(*dotted.split("."))
    base = REPO / rel
    return base.with_suffix(".py").exists() or (base / "__init__.py").exists()


def _module_source(dotted: str) -> Path | None:
    """Pfad zur .py bzw. __init__.py eines Moduls, falls vorhanden."""
    rel = Path(*dotted.split("."))
    base = REPO / rel
    if base.with_suffix(".py").exists():
        return base.with_suffix(".py")
    if (base / "__init__.py").exists():
        return base / "__init__.py"
    return None


def _defined_names(src: Path) -> set[str]:
    """Alle irgendwo definierten/importierten Namen eines Moduls (lenient,
    um Falschalarme bei bedingten Definitionen zu vermeiden)."""
    names: set[str] = set()
    try:
        tree = ast.parse(src.read_text(encoding="utf-8"))
    except SyntaxError:
        return {"*"}  # nicht parsebar -> nicht weiter einschraenken
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                if a.name == "*":
                    names.add("*")
                else:
                    names.add(a.asname or a.name.split(".")[0])
    return names


def _name_resolves(mod: str, name: str) -> bool:
    if _module_exists(f"{mod}.{name}"):     # Submodul, z.B. from scripts.eval import cer_statistics
        return True
    src = _module_source(mod)
    if src is None:                          # Namespace-Paket ohne __init__ (z.B. 'scripts')
        return False
    defined = _defined_names(src)
    return name in defined or "*" in defined


@pytest.mark.parametrize("py", PY_FILES, ids=IDS)
def test_compiles(py: Path):
    ast.parse(py.read_text(encoding="utf-8"))


@pytest.mark.parametrize("py", PY_FILES, ids=IDS)
def test_internal_imports_resolve(py: Path):
    tree = ast.parse(py.read_text(encoding="utf-8"))
    toplevel = {id(n) for n in tree.body}
    problems: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("scripts") and not _module_exists(a.name):
                    problems.append(f"import {a.name} (Modul fehlt)")
        elif isinstance(node, ast.ImportFrom):
            if node.level:                    # relative Importe ignorieren
                continue
            mod = node.module or ""
            if not mod.startswith("scripts"):
                continue
            if not _module_exists(mod):
                problems.append(f"from {mod} import ... (Modul fehlt)")
                continue
            # Namens-Check nur fuer Modul-Level-Importe (keine Lazy-Importe in Funktionen)
            if id(node) in toplevel:
                for a in node.names:
                    if a.name != "*" and not _name_resolves(mod, a.name):
                        problems.append(f"from {mod} import {a.name} (Name fehlt im Ziel)")
    assert not problems, f"{py.relative_to(REPO)}:\n  " + "\n  ".join(problems)
