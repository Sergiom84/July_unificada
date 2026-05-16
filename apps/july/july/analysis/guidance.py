from __future__ import annotations

from typing import Any

from july.analysis.models import CodeSmell, FileInfo
from july.analysis.smells import MAX_FILE_LINES


def generate_proactive_questions(
    arch_pattern: str,
    layers: dict[str, list[str]],
    smells: list[CodeSmell],
    languages: dict[str, int],
    files: list[FileInfo],
) -> list[str]:
    questions: list[str] = []

    if arch_pattern == "flat" and len(files) > 15:
        questions.append(
            "El proyecto tiene bastantes archivos pero sin estructura clara de capas. "
            "Estas pensando en reorganizarlo o prefieres mantenerlo plano?"
        )

    if "service" not in layers and "controller" in layers:
        questions.append(
            "Veo controllers pero no una capa de services. "
            "La logica de negocio esta directamente en los controllers?"
        )

    if "test" not in layers and len(files) > 5:
        questions.append(
            "No detecto tests en el proyecto. Quieres que te sugiera una estrategia de testing?"
        )

    critical_smells = [s for s in smells if s.severity == "critical"]
    if critical_smells:
        questions.append(
            f"He detectado {len(critical_smells)} problemas criticos de estructura. "
            "Quieres que los revisemos antes de seguir trabajando?"
        )

    if len(languages) > 3:
        questions.append(
            f"El proyecto usa {len(languages)} lenguajes diferentes. "
            "Es intencionado o hay archivos que deberian limpiarse?"
        )

    return questions[:3]


def generate_suggestions(
    arch_pattern: str,
    layers: dict[str, list[str]],
    smells: list[CodeSmell],
    hotspots: list[dict[str, Any]],
    languages: dict[str, int],
) -> list[str]:
    suggestions: list[str] = []

    if arch_pattern == "flat" and sum(languages.values()) > 15:
        suggestions.append(
            "Considera organizar en capas: domain/ para modelos y logica pura, "
            "services/ para casos de uso, infrastructure/ para adaptadores externos."
        )

    if arch_pattern == "mvc" and "service" not in layers:
        suggestions.append(
            "Patron MVC detectado sin capa de servicios. "
            "Extraer logica de controllers a services mejora testabilidad y reutilizacion."
        )

    large_files = [s for s in smells if s.kind == "large_file"]
    if large_files:
        suggestions.append(
            f"Hay {len(large_files)} archivos que superan {MAX_FILE_LINES} lineas. "
            "Archivos mas pequenos son mas faciles de entender, testear y mantener."
        )

    god_classes = [s for s in smells if s.kind == "god_class"]
    if god_classes:
        suggestions.append(
            "Se detectan clases con muchos metodos (God Class). "
            "Aplica el Principio de Responsabilidad Unica: cada clase deberia tener una sola razon para cambiar."
        )

    high_fan_out = [h for h in hotspots if h["kind"] == "high_fan_out"]
    if high_fan_out:
        suggestions.append(
            "Algunos archivos importan demasiados modulos. "
            "Esto puede indicar que mezclan responsabilidades o que falta una capa de abstraccion."
        )

    no_tests = [s for s in smells if s.kind == "no_tests"]
    if no_tests:
        suggestions.append(
            "No hay tests detectados. Empieza por testear la logica de negocio critica "
            "y los edge cases que mas te han fallado."
        )

    return suggestions[:5]

