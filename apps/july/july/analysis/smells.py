from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path
from typing import Any

from july.analysis.models import CodeSmell, FileInfo, ImportInfo

MAX_FILE_LINES = 300
MAX_FUNCTION_LINES = 50
MAX_IMPORTS_PER_FILE = 15
MAX_PARAMS_PER_FUNCTION = 5


def find_dependency_hotspots(imports: list[ImportInfo]) -> list[dict[str, Any]]:
    """Find files that are imported the most (high fan-in) and files that import the most (high fan-out)."""
    imported_by: Counter[str] = Counter()
    imports_from: Counter[str] = Counter()

    for imp in imports:
        imports_from[imp.source_file] += 1
        if not imp.module.startswith(".") and "." in imp.module:
            imported_by[imp.module] += 1
        elif imp.module.startswith("."):
            imported_by[f"{imp.source_file}->{imp.module}"] += 1

    hotspots: list[dict[str, Any]] = []

    for path, count in imports_from.most_common(5):
        if count > MAX_IMPORTS_PER_FILE:
            hotspots.append({
                "file": path,
                "kind": "high_fan_out",
                "count": count,
                "detail": f"Importa {count} modulos. Puede indicar responsabilidades mezcladas.",
            })

    for module, count in imported_by.most_common(5):
        if count >= 5:
            hotspots.append({
                "module": module,
                "kind": "high_fan_in",
                "count": count,
                "detail": f"Importado por {count} archivos. Cambios aqui tienen alto impacto.",
            })

    return hotspots


def detect_code_smells(
    repo_root: Path,
    files: list[FileInfo],
    imports: list[ImportInfo],
) -> list[CodeSmell]:
    smells: list[CodeSmell] = []

    for f in files:
        if f.lines > MAX_FILE_LINES:
            severity = "critical" if f.lines > MAX_FILE_LINES * 3 else "warning"
            smells.append(CodeSmell(
                file=f.path,
                kind="large_file",
                detail=f"{f.lines} lineas. Considera dividirlo en modulos mas pequenos.",
                severity=severity,
            ))

        if f.extension == ".py":
            smells.extend(_detect_python_smells(repo_root, f))

    test_files = [f for f in files if "test" in f.path.lower()]
    if not test_files and len(files) > 5:
        smells.append(CodeSmell(
            file="(proyecto)",
            kind="no_tests",
            detail="No se detectan archivos de test. Los tests son esenciales para mantener calidad.",
            severity="warning",
        ))

    return smells[:20]


def _detect_python_smells(repo_root: Path, f: FileInfo) -> list[CodeSmell]:
    smells: list[CodeSmell] = []
    full_path = repo_root / f.path
    try:
        source = full_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=f.path)
    except (SyntaxError, OSError):
        return smells

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if hasattr(node, "end_lineno") and node.end_lineno:
                func_lines = node.end_lineno - node.lineno
                if func_lines > MAX_FUNCTION_LINES:
                    smells.append(CodeSmell(
                        file=f.path,
                        kind="long_function",
                        detail=f"Funcion '{node.name}' tiene {func_lines} lineas (max recomendado: {MAX_FUNCTION_LINES}).",
                        severity="warning",
                    ))

            params = node.args
            param_count = len(params.args) + len(params.kwonlyargs)
            if params.vararg:
                param_count += 1
            if params.kwarg:
                param_count += 1
            if params.args and params.args[0].arg in ("self", "cls"):
                param_count -= 1

            if param_count > MAX_PARAMS_PER_FUNCTION:
                smells.append(CodeSmell(
                    file=f.path,
                    kind="too_many_params",
                    detail=f"Funcion '{node.name}' tiene {param_count} parametros. Considera usar un dataclass o dict.",
                    severity="info",
                ))

        if isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if len(methods) > 15:
                smells.append(CodeSmell(
                    file=f.path,
                    kind="god_class",
                    detail=f"Clase '{node.name}' tiene {len(methods)} metodos. Considera dividir responsabilidades.",
                    severity="warning",
                ))

    return smells

