from __future__ import annotations

import ast
import re
from pathlib import Path

from july.analysis.models import FileInfo, ImportInfo


def extract_imports(repo_root: Path, files: list[FileInfo]) -> list[ImportInfo]:
    """Extract import statements from Python and JS/TS files."""
    imports: list[ImportInfo] = []

    for f in files:
        if f.extension == ".py":
            imports.extend(_extract_python_imports(repo_root, f.path))
        elif f.extension in (".js", ".ts", ".jsx", ".tsx"):
            imports.extend(_extract_js_imports(f.path, repo_root))

    return imports


def _extract_python_imports(repo_root: Path, rel_path: str) -> list[ImportInfo]:
    result: list[ImportInfo] = []
    full_path = repo_root / rel_path
    try:
        source = full_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=rel_path)
    except (SyntaxError, OSError):
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.append(ImportInfo(
                    source_file=rel_path,
                    module=alias.name,
                    names=[alias.asname or alias.name],
                ))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            result.append(ImportInfo(
                source_file=rel_path,
                module=module,
                names=names,
            ))
    return result


_JS_IMPORT_RE = re.compile(
    r"""(?:import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]*\}|\*\s+as\s+\w+|\w+))*\s+from\s+)?['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""",
    re.MULTILINE,
)


def _extract_js_imports(rel_path: str, repo_root: Path) -> list[ImportInfo]:
    result: list[ImportInfo] = []
    full_path = repo_root / rel_path
    try:
        content = full_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return result

    for match in _JS_IMPORT_RE.finditer(content):
        module = match.group(1) or match.group(2)
        if module:
            result.append(ImportInfo(
                source_file=rel_path,
                module=module,
                names=[],
            ))
    return result

