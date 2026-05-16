from __future__ import annotations

from collections import Counter
from pathlib import Path

from july.analysis.models import FileInfo

IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".next", ".nuxt", "dist", "build", "out", ".output",
    "target", "vendor", ".tox", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", "coverage", ".coverage", "htmlcov",
    ".idea", ".vscode", ".vs", "egg-info",
}

IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".class", ".o", ".so", ".dll",
    ".lock", ".map", ".min.js", ".min.css",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".bz2",
    ".db", ".sqlite", ".sqlite3",
}

SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".go", ".rs", ".rb", ".php",
    ".java", ".kt", ".cs", ".cpp", ".c", ".h",
    ".vue", ".svelte",
}

LANG_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "React JSX", ".tsx": "React TSX",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".java": "Java", ".kt": "Kotlin", ".cs": "C#",
    ".cpp": "C++", ".c": "C", ".h": "C/C++ Header",
    ".vue": "Vue", ".svelte": "Svelte",
}


def iter_all_files(repo_root: Path, *, max_files: int = 1000) -> list[FileInfo]:
    result: list[FileInfo] = []
    count = 0
    for path in _walk_files(repo_root):
        if count >= max_files:
            break
        try:
            stat = path.stat()
            result.append(FileInfo(
                path=str(path.relative_to(repo_root)),
                extension=path.suffix.lower(),
                lines=0,
                size_bytes=stat.st_size,
            ))
            count += 1
        except OSError:
            continue
    return result


def collect_source_files(repo_root: Path, *, max_files: int = 500) -> list[FileInfo]:
    result: list[FileInfo] = []
    for path in _walk_files(repo_root):
        if len(result) >= max_files:
            break
        ext = path.suffix.lower()
        if ext not in SOURCE_EXTENSIONS:
            continue
        if ext in IGNORE_EXTENSIONS:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            result.append(FileInfo(
                path=str(path.relative_to(repo_root)),
                extension=ext,
                lines=lines,
                size_bytes=len(content.encode("utf-8")),
            ))
        except OSError:
            continue
    return result


def _walk_files(repo_root: Path):
    try:
        for entry in sorted(repo_root.iterdir()):
            if entry.name.startswith(".") and entry.name != ".":
                if entry.name not in (".github", ".gitlab"):
                    continue
            if entry.is_dir():
                if entry.name.lower() in IGNORE_DIRS:
                    continue
                yield from _walk_files(entry)
            elif entry.is_file():
                if entry.suffix.lower() not in IGNORE_EXTENSIONS:
                    yield entry
    except PermissionError:
        pass


def count_languages(files: list[FileInfo]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for f in files:
        lang = LANG_MAP.get(f.extension)
        if lang:
            counter[lang] += 1
    return dict(counter.most_common())


def build_directory_tree(repo_root: Path, *, depth: int = 3) -> list[str]:
    lines: list[str] = []
    _tree_recurse(repo_root, repo_root, lines, depth=depth, prefix="")
    return lines


def _tree_recurse(path: Path, root: Path, lines: list[str], *, depth: int, prefix: str) -> None:
    if depth <= 0:
        return
    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return

    visible = [
        e for e in entries
        if not (e.name.startswith(".") and e.name not in (".github", ".gitlab"))
        and e.name.lower() not in IGNORE_DIRS
    ]

    for i, entry in enumerate(visible[:30]):
        connector = "└── " if i == len(visible[:30]) - 1 else "├── "
        suffix = "/" if entry.is_dir() else ""
        lines.append(f"{prefix}{connector}{entry.name}{suffix}")
        if entry.is_dir():
            ext = "    " if i == len(visible[:30]) - 1 else "│   "
            _tree_recurse(entry, root, lines, depth=depth - 1, prefix=prefix + ext)
