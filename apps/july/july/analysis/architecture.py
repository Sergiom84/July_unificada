from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from july.analysis.models import ArchitectureInsight, FileInfo

LAYER_PATTERNS = {
    "controllers": "controller",
    "routes": "controller",
    "handlers": "controller",
    "api": "controller",
    "services": "service",
    "usecases": "service",
    "use_cases": "service",
    "application": "service",
    "models": "model",
    "entities": "model",
    "domain": "model",
    "schemas": "model",
    "repositories": "repository",
    "repos": "repository",
    "adapters": "repository",
    "infrastructure": "repository",
    "views": "view",
    "templates": "view",
    "components": "view",
    "pages": "view",
    "middleware": "middleware",
    "utils": "utility",
    "helpers": "utility",
    "lib": "utility",
    "config": "config",
    "tests": "test",
    "test": "test",
    "__tests__": "test",
    "specs": "test",
}


def detect_layers(repo_root: Path, files: list[FileInfo]) -> dict[str, list[str]]:
    layers: dict[str, list[str]] = defaultdict(list)

    for path in repo_root.iterdir():
        if path.is_dir():
            name = path.name.lower()
            if name in LAYER_PATTERNS:
                layers[LAYER_PATTERNS[name]].append(path.name)

    src = repo_root / "src"
    if src.is_dir():
        for path in src.iterdir():
            if path.is_dir():
                name = path.name.lower()
                if name in LAYER_PATTERNS:
                    layers[LAYER_PATTERNS[name]].append(f"src/{path.name}")

    for f in files:
        parts = Path(f.path).parts
        for part in parts[:-1]:
            lower = part.lower()
            if lower in LAYER_PATTERNS:
                layer = LAYER_PATTERNS[lower]
                dir_path = str(Path(*parts[:parts.index(part) + 1]))
                if dir_path not in layers[layer]:
                    layers[layer].append(dir_path)

    return dict(layers)


def infer_architecture(
    layers: dict[str, list[str]],
    files: list[FileInfo],
    repo_root: Path,
) -> tuple[str, list[ArchitectureInsight]]:
    insights: list[ArchitectureInsight] = []
    layer_types = set(layers.keys())

    if {"service", "repository", "model"} <= layer_types:
        if "controller" in layer_types:
            pattern = "layered_mvc"
            insights.append(ArchitectureInsight(
                pattern="Layered / MVC",
                confidence=0.85,
                detail=f"Capas detectadas: {', '.join(sorted(layer_types))}",
                suggestion="Verifica que los controllers no accedan directamente a repositories sin pasar por services.",
            ))
        else:
            pattern = "clean_architecture"
            insights.append(ArchitectureInsight(
                pattern="Clean Architecture",
                confidence=0.75,
                detail=f"Capas core detectadas: {', '.join(sorted(layer_types))}",
                suggestion="Asegurate de que el domain/models no importe de infrastructure/adapters.",
            ))
    elif {"controller", "model"} <= layer_types:
        pattern = "mvc"
        insights.append(ArchitectureInsight(
            pattern="MVC",
            confidence=0.7,
            detail="Controllers y models detectados sin capa de services explicita.",
            suggestion="Considera extraer logica de negocio de los controllers a una capa de services.",
        ))
    elif {"view", "model"} <= layer_types or {"view", "controller"} <= layer_types:
        pattern = "frontend_component"
        insights.append(ArchitectureInsight(
            pattern="Frontend componentizado",
            confidence=0.7,
            detail="Estructura basada en componentes/vistas.",
            suggestion="Verifica que la logica de estado no este acoplada a los componentes de presentacion.",
        ))
    elif len(files) <= 10:
        pattern = "script"
        insights.append(ArchitectureInsight(
            pattern="Script / utilidad",
            confidence=0.8,
            detail=f"Proyecto pequeno con {len(files)} archivos fuente.",
            suggestion="Para proyectos pequenos, mantener la simplicidad es una virtud. No sobrearquitectures.",
        ))
    else:
        pattern = "flat"
        insights.append(ArchitectureInsight(
            pattern="Estructura plana",
            confidence=0.6,
            detail="No se detectan capas arquitectonicas claras.",
            suggestion="Si el proyecto crece, considera separar en capas (domain, services, infrastructure).",
        ))

    workspace_indicators = [
        repo_root / "packages",
        repo_root / "apps",
        repo_root / "libs",
    ]
    if any(p.is_dir() for p in workspace_indicators):
        insights.append(ArchitectureInsight(
            pattern="Monorepo",
            confidence=0.8,
            detail="Detectados directorios packages/, apps/ o libs/.",
            suggestion="Verifica que las dependencias entre paquetes esten bien definidas y no haya imports circulares.",
        ))

    if (repo_root / "Dockerfile").exists() or (repo_root / "docker-compose.yml").exists():
        insights.append(ArchitectureInsight(
            pattern="Containerizado",
            confidence=0.9,
            detail="Dockerfile o docker-compose detectado.",
            suggestion="Revisa que los multi-stage builds esten optimizados y no copien archivos innecesarios.",
        ))

    return pattern, insights

