"""Deep code analyzer facade for July architect copilot."""
from __future__ import annotations

from pathlib import Path

from july.analysis.architecture import LAYER_PATTERNS, detect_layers, infer_architecture
from july.analysis.discovery import (
    IGNORE_DIRS,
    IGNORE_EXTENSIONS,
    LANG_MAP,
    SOURCE_EXTENSIONS,
    _tree_recurse,
    _walk_files,
    build_directory_tree,
    collect_source_files,
    count_languages,
    iter_all_files,
)
from july.analysis.guidance import generate_proactive_questions, generate_suggestions
from july.analysis.imports import (
    _JS_IMPORT_RE,
    _extract_js_imports,
    _extract_python_imports,
    extract_imports,
)
from july.analysis.models import (
    AnalysisResult,
    ArchitectureInsight,
    CodeSmell,
    FileInfo,
    ImportInfo,
)
from july.analysis.smells import (
    MAX_FILE_LINES,
    MAX_FUNCTION_LINES,
    MAX_IMPORTS_PER_FILE,
    MAX_PARAMS_PER_FUNCTION,
    _detect_python_smells,
    detect_code_smells,
    find_dependency_hotspots,
)


def analyze_codebase(repo_root: Path, *, max_files: int = 500) -> AnalysisResult:
    """Run a deep analysis of the codebase at repo_root."""
    files = collect_source_files(repo_root, max_files=max_files)
    languages = count_languages(files)
    tree = build_directory_tree(repo_root, depth=3)
    layers = detect_layers(repo_root, files)
    arch_pattern, arch_insights = infer_architecture(layers, files, repo_root)
    imports = extract_imports(repo_root, files)
    hotspots = find_dependency_hotspots(imports)
    smells = detect_code_smells(repo_root, files, imports)
    questions = generate_proactive_questions(arch_pattern, layers, smells, languages, files)
    suggestions = generate_suggestions(arch_pattern, layers, smells, hotspots, languages)

    return AnalysisResult(
        repo_root=str(repo_root),
        total_files=len(list(iter_all_files(repo_root, max_files=max_files * 2))),
        source_files=len(files),
        languages=languages,
        directory_tree=tree,
        layers_detected=layers,
        architecture_pattern=arch_pattern,
        architecture_insights=arch_insights,
        imports=imports,
        dependency_hotspots=hotspots,
        code_smells=smells,
        proactive_questions=questions,
        suggestions=suggestions,
    )


__all__ = [
    "AnalysisResult",
    "ArchitectureInsight",
    "CodeSmell",
    "FileInfo",
    "IGNORE_DIRS",
    "IGNORE_EXTENSIONS",
    "ImportInfo",
    "LANG_MAP",
    "LAYER_PATTERNS",
    "MAX_FILE_LINES",
    "MAX_FUNCTION_LINES",
    "MAX_IMPORTS_PER_FILE",
    "MAX_PARAMS_PER_FUNCTION",
    "SOURCE_EXTENSIONS",
    "_JS_IMPORT_RE",
    "_detect_python_smells",
    "_extract_js_imports",
    "_extract_python_imports",
    "_tree_recurse",
    "_walk_files",
    "analyze_codebase",
    "build_directory_tree",
    "collect_source_files",
    "count_languages",
    "detect_code_smells",
    "detect_layers",
    "extract_imports",
    "find_dependency_hotspots",
    "generate_proactive_questions",
    "generate_suggestions",
    "infer_architecture",
    "iter_all_files",
]
