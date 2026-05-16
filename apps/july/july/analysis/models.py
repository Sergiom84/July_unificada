from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FileInfo:
    path: str
    extension: str
    lines: int
    size_bytes: int


@dataclass(slots=True)
class ImportInfo:
    source_file: str
    module: str
    names: list[str]


@dataclass(slots=True)
class CodeSmell:
    file: str
    kind: str
    detail: str
    severity: str  # "info", "warning", "critical"


@dataclass(slots=True)
class ArchitectureInsight:
    pattern: str
    confidence: float
    detail: str
    suggestion: str


@dataclass(slots=True)
class AnalysisResult:
    repo_root: str
    total_files: int
    source_files: int
    languages: dict[str, int]
    directory_tree: list[str]
    layers_detected: dict[str, list[str]]
    architecture_pattern: str
    architecture_insights: list[ArchitectureInsight]
    imports: list[ImportInfo]
    dependency_hotspots: list[dict[str, Any]]
    code_smells: list[CodeSmell]
    proactive_questions: list[str]
    suggestions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "total_files": self.total_files,
            "source_files": self.source_files,
            "languages": self.languages,
            "directory_tree": self.directory_tree,
            "layers_detected": self.layers_detected,
            "architecture_pattern": self.architecture_pattern,
            "architecture_insights": [
                {"pattern": i.pattern, "confidence": i.confidence,
                 "detail": i.detail, "suggestion": i.suggestion}
                for i in self.architecture_insights
            ],
            "dependency_hotspots": self.dependency_hotspots,
            "code_smells": [
                {"file": s.file, "kind": s.kind, "detail": s.detail, "severity": s.severity}
                for s in self.code_smells
            ],
            "proactive_questions": self.proactive_questions,
            "suggestions": self.suggestions,
        }

