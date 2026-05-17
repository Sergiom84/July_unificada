from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from july.project_text import summarize_text

if TYPE_CHECKING:
    from july.db import JulyDatabase

README_NAMES = ("README.md", "README.txt", "README")
OPTIONAL_DOCS = ("AGENTS.md",)
MAX_SURFACE_SCAN_DEPTH = 3
IGNORED_DIR_NAMES = {
    ".dart_tool",
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "vendor",
}
LEGACY_PATH_NAMES = {"archive", "archives", "legacy", "quarantine"}
MANIFEST_FILES = (
    "package.json",
    "pubspec.yaml",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "Cargo.toml",
    "go.mod",
    "composer.json",
    "Gemfile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
)
ENTRYPOINT_FILES = (
    "main.py",
    "app.py",
    "server.py",
    "manage.py",
    "wsgi.py",
    "asgi.py",
    "index.js",
    "server.js",
    "app.js",
    "main.ts",
    "index.ts",
    "server.ts",
    "src/main.ts",
    "src/index.ts",
    "src/main.js",
    "src/index.js",
    "lib/main.dart",
)

STACK_HINTS = {
    "python": "python",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "pipfile": "python",
    "package.json": "node",
    "pubspec.yaml": "flutter",
    "cargo.toml": "rust",
    "go.mod": "go",
    "composer.json": "php",
    "gemfile": "ruby",
    "dockerfile": "docker",
    "docker-compose.yml": "docker-compose",
    "docker-compose.yaml": "docker-compose",
}

STACK_ORDER = {
    "flutter": 10,
    "node": 20,
    "python": 30,
    "rust": 40,
    "go": 50,
    "php": 60,
    "ruby": 70,
    "docker": 90,
    "docker-compose": 91,
}

INTEGRATION_KEYWORDS = {
    "supabase": "Supabase",
    "render": "Render",
    "anthropic": "Anthropic",
    "openai": "OpenAI",
    "claude": "Anthropic",
    "ollama": "Ollama",
    "mcp": "MCP",
    "excel": "Excel",
    "google sheets": "Google Sheets",
    "stripe": "Stripe",
    "postgres": "Postgres",
    "sqlite": "SQLite",
    "docker": "Docker",
}


@dataclass(slots=True)
class ProjectComponent:
    role: str
    tech: str
    path: str
    markers: list[str]

    def public_dict(self) -> dict[str, str]:
        return {"role": self.role, "tech": self.tech, "path": self.path}


@dataclass(slots=True)
class RepositorySurface:
    repo_root: Path
    repo_name: str
    manifests: list[str]
    entrypoints: list[str]
    docs: list[str]
    stack: list[str]
    components: list[ProjectComponent]


@dataclass(slots=True)
class ProjectProfile:
    project_kind: str
    project_tags: list[str]
    preferences: dict[str, Any]


def detect_repo_root(repo_path: str | None) -> Path:
    start = Path(repo_path).expanduser().resolve() if repo_path else Path.cwd().resolve()
    current = start if start.is_dir() else start.parent

    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
        if any((candidate / name).exists() for name in README_NAMES + MANIFEST_FILES + OPTIONAL_DOCS):
            return candidate
    return current


def derive_project_key(repo_root: Path, *, explicit: str | None = None) -> str:
    value = explicit or repo_root.name
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def resolve_project_identity(
    database: JulyDatabase,
    *,
    repo_path: str | None = None,
    project_key: str | None = None,
) -> tuple[Path, str]:
    explicit_key = project_key.strip().lower() if isinstance(project_key, str) and project_key.strip() else None
    if explicit_key and not repo_path:
        existing = database.get_project(explicit_key)
        if existing is None:
            raise ValueError(
                f"Project {explicit_key} not found in the registry. Provide repo_path to register it first."
            )
        return Path(existing["repo_root"]).resolve(), explicit_key

    repo_root = detect_repo_root(repo_path)
    resolved_project_key = derive_project_key(repo_root, explicit=project_key)
    existing = database.get_project(resolved_project_key)
    if existing is not None and not repo_path:
        return Path(existing["repo_root"]).resolve(), resolved_project_key
    return repo_root, resolved_project_key


def inspect_repository_surface(repo_root: Path) -> RepositorySurface:
    candidate_dirs = list(iter_surface_dirs(repo_root))
    root_names = {path.name.lower(): path.name for path in repo_root.iterdir() if path.is_file()}
    docs = [root_names[name.lower()] for name in README_NAMES + OPTIONAL_DOCS if name.lower() in root_names]

    manifests = sorted(
        {
            relative_file_path(repo_root, directory / child.name)
            for directory in candidate_dirs
            for child in directory.iterdir()
            if child.is_file() and child.name.lower() in {name.lower() for name in MANIFEST_FILES}
        }
    )
    entrypoints = sorted(
        {
            relative_file_path(repo_root, directory / child.name)
            for directory in candidate_dirs
            for child in directory.iterdir()
            if child.is_file() and child.name.lower() in entrypoint_basenames()
        }
        | {
            relative
            for relative in ENTRYPOINT_FILES
            if (repo_root / relative).exists() and not is_ignored_relative_path(Path(relative))
        }
    )
    components = detect_project_components(repo_root, candidate_dirs)
    stack = derive_stack_from_surface(manifests, components)
    return RepositorySurface(
        repo_root=repo_root,
        repo_name=repo_root.name,
        manifests=manifests,
        entrypoints=entrypoints,
        docs=docs,
        stack=stack,
        components=components,
    )


def analyze_repository(repo_root: Path) -> dict[str, Any]:
    surface = inspect_repository_surface(repo_root)
    profile = infer_project_profile(repo_root, surface)
    files_to_read = []
    for name in surface.docs + surface.manifests:
        candidate = repo_root / name
        if candidate.exists():
            files_to_read.append(candidate)
    for relative in surface.entrypoints:
        candidate = repo_root / relative
        if candidate.exists():
            files_to_read.append(candidate)

    unique_files = []
    seen: set[Path] = set()
    for path in files_to_read:
        if path not in seen:
            unique_files.append(path)
            seen.add(path)

    file_contents = {str(path.relative_to(repo_root)): read_limited_text(path) for path in unique_files[:12]}
    combined_text = "\n".join(file_contents.values()).lower()

    package_commands = extract_surface_package_commands(repo_root, surface)
    visible_commands = package_commands or infer_default_commands(surface)
    integrations = detect_integrations(combined_text)
    objective = extract_objective(file_contents)
    open_questions = build_open_questions(surface, objective, visible_commands)

    return {
        "repo_name": surface.repo_name,
        "repo_root": str(repo_root),
        "files_read": list(file_contents.keys()),
        "objective": objective,
        "stack": surface.stack or ["No detectado"],
        "components": [component.public_dict() for component in surface.components],
        "commands": visible_commands,
        "integrations": integrations,
        "entrypoints": surface.entrypoints,
        "open_questions": open_questions,
        "docs": surface.docs,
        "manifests": surface.manifests,
        "project_kind": profile.project_kind,
        "project_tags": profile.project_tags,
        "preferences": profile.preferences,
    }


def read_limited_text(path: Path, limit: int = 4000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def extract_package_commands(package_json_path: Path, *, prefix: str = "") -> list[str]:
    if not package_json_path.exists():
        return []
    try:
        data = json.loads(package_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    scripts = data.get("scripts", {})
    commands = []
    for name in ("dev", "start", "build", "test", "lint"):
        if name in scripts:
            commands.append(f"{prefix}npm run {name}")
    return commands


def infer_project_profile(repo_root: Path, surface: RepositorySurface) -> ProjectProfile:
    text_parts = []
    for name in README_NAMES + OPTIONAL_DOCS + MANIFEST_FILES:
        candidate = repo_root / name
        if candidate.exists():
            text_parts.append(read_limited_text(candidate, limit=2500))
    for relative in surface.manifests[:8]:
        candidate = repo_root / relative
        if candidate.exists():
            text_parts.append(read_limited_text(candidate, limit=2500))
    combined_text = "\n".join(text_parts).lower()
    kind = infer_project_kind(surface, combined_text)
    tags = infer_project_tags(surface, combined_text, kind)
    return ProjectProfile(
        project_kind=kind,
        project_tags=tags,
        preferences=default_preferences_for_kind(kind, tags),
    )


def infer_project_kind(surface: RepositorySurface, text: str) -> str:
    has_package = has_manifest(surface, "package.json")
    has_python = any(has_manifest(surface, item) for item in ("pyproject.toml", "requirements.txt", "Pipfile"))
    has_docker = any(Path(item).name.lower().startswith("docker") for item in surface.manifests)
    entrypoints = " ".join(surface.entrypoints).lower()
    component_techs = {component.tech for component in surface.components}
    component_roles = {component.role for component in surface.components}

    if any(token in text for token in ("landing", "pagina web", "página web", "web de cliente", "sitio web", "seo local")):
        return "website"
    if "flutter" in component_techs or any(token in text for token in ("mobile app", "android", "ios", "react native", "flutter")):
        return "mobile_app"
    if any(token in text for token in ("desktop app", "electron", "tauri")):
        return "desktop_app"
    if any(token in text for token in ("cli", "command line", "terminal", "stdio")):
        return "cli_tool"
    if has_package and any(item in entrypoints for item in ("src/main", "src/index", "index.ts", "main.ts")):
        return "web_app"
    if "backend" in component_roles or any(token in text for token in ("api", "backend", "fastapi", "express", "server")) or has_docker:
        return "backend"
    if any(token in text for token in ("automatizacion", "automatización", "workflow", "script")):
        return "automation"
    if has_python and not has_package:
        return "software"
    if surface.docs and not surface.manifests:
        return "knowledge_base"
    return "unknown"


def infer_project_tags(surface: RepositorySurface, text: str, kind: str) -> list[str]:
    tags = {kind}
    for keyword, label in INTEGRATION_KEYWORDS.items():
        if keyword in text:
            tags.add(label.lower().replace(" ", "-"))
    stack_tags = {item.lower().replace(".", "").replace(" ", "-") for item in surface.stack}
    tags.update(stack_tags)
    if "cliente" in text or "client" in text:
        tags.add("cliente")
    if "landing" in text:
        tags.add("landing")
    if "ecommerce" in text or "tienda" in text:
        tags.add("ecommerce")
    if "supabase" in text:
        tags.add("supabase")
    if "render" in text:
        tags.add("render")
    if "seo" in text:
        tags.add("seo")
    return sorted(tag for tag in tags if tag and tag != "unknown")


def default_preferences_for_kind(kind: str, tags: list[str]) -> dict[str, Any]:
    is_website = kind in {"website", "web_app"} or "landing" in tags or "seo" in tags
    return {
        "ask_before_save": True,
        "auto_session_summary": True,
        "suggest_caveman": True,
        "suggest_design_extract": is_website,
        "suggest_codeburn": kind in {"web_app", "backend", "software", "cli_tool"},
        "open_cockpit": False,
    }


def infer_default_commands(surface: RepositorySurface) -> list[str]:
    commands = []
    flutter_components = [component for component in surface.components if component.tech == "flutter"]
    if flutter_components:
        prefix = command_prefix(flutter_components[0].path)
        commands.extend([f"{prefix}flutter pub get", f"{prefix}flutter run"])
    if has_manifest(surface, "package.json"):
        commands.extend(["npm install", "npm run dev"])
    if any(has_manifest(surface, item) for item in ("pyproject.toml", "requirements.txt", "Pipfile")):
        commands.extend(["python -m venv .venv", "python -m pytest"])
    return commands or ["Revisar README para comandos concretos"]


def detect_integrations(text: str) -> list[str]:
    return sorted({label for keyword, label in INTEGRATION_KEYWORDS.items() if keyword in text})


def extract_objective(file_contents: dict[str, str]) -> str:
    for name, content in file_contents.items():
        if name.lower().startswith("readme") and content.strip():
            lines = [line.strip(" #*-") for line in content.splitlines() if line.strip()]
            for line in lines:
                if len(line) > 20:
                    return summarize_text(line, limit=220)
    return "No hay una descripcion explicita; conviene confirmar el objetivo del repo."


def build_open_questions(surface: RepositorySurface, objective: str, commands: list[str]) -> list[str]:
    questions = []
    if not surface.docs:
        questions.append("Falta README o documentacion base visible.")
    if not surface.entrypoints:
        questions.append("No he detectado entrypoints obvios en superficie.")
    if objective.startswith("No hay una descripcion"):
        questions.append("Conviene confirmar el objetivo funcional del proyecto.")
    if not commands:
        questions.append("No hay comandos utiles detectados todavia.")
    return questions


def iter_surface_dirs(repo_root: Path, max_depth: int = MAX_SURFACE_SCAN_DEPTH):
    stack = [repo_root]
    while stack:
        directory = stack.pop()
        if directory != repo_root and is_ignored_relative_path(directory.relative_to(repo_root)):
            continue
        yield directory
        depth = len(directory.relative_to(repo_root).parts) if directory != repo_root else 0
        if depth >= max_depth:
            continue
        try:
            children = sorted(path for path in directory.iterdir() if path.is_dir())
        except OSError:
            continue
        for child in reversed(children):
            if not is_ignored_relative_path(child.relative_to(repo_root)):
                stack.append(child)


def is_ignored_relative_path(relative: Path) -> bool:
    parts = {part.lower() for part in relative.parts}
    return bool(parts & IGNORED_DIR_NAMES or parts & LEGACY_PATH_NAMES)


def relative_file_path(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def relative_dir_path(repo_root: Path, path: Path) -> str:
    if path == repo_root:
        return "./"
    return f"{path.relative_to(repo_root).as_posix()}/"


def entrypoint_basenames() -> set[str]:
    return {Path(relative).name.lower() for relative in ENTRYPOINT_FILES}


def detect_project_components(repo_root: Path, candidate_dirs: list[Path]) -> list[ProjectComponent]:
    components: list[ProjectComponent] = []
    seen: set[tuple[str, str, str]] = set()
    for directory in candidate_dirs:
        try:
            child_names = {child.name.lower(): child for child in directory.iterdir()}
        except OSError:
            continue
        files = {name for name, path in child_names.items() if path.is_file()}
        dirs = {name for name, path in child_names.items() if path.is_dir()}
        markers: list[str]
        role: str
        tech: str

        if "pubspec.yaml" in files and ("lib" in dirs or (directory / "lib" / "main.dart").exists()):
            markers = ["pubspec.yaml", "lib/"]
            if "android" in dirs:
                markers.append("android/")
            if "ios" in dirs:
                markers.append("ios/")
            role, tech = "frontend", "flutter"
            append_component(components, seen, repo_root, directory, role, tech, markers)

        if "package.json" in files:
            role, markers = infer_node_component(directory)
            append_component(components, seen, repo_root, directory, role, "node", markers)

        if files & {"pyproject.toml", "requirements.txt", "pipfile"}:
            role = infer_python_component_role(directory)
            markers = sorted(files & {"pyproject.toml", "requirements.txt", "pipfile"})
            append_component(components, seen, repo_root, directory, role, "python", markers)

    return sorted(components, key=component_sort_key)


def append_component(
    components: list[ProjectComponent],
    seen: set[tuple[str, str, str]],
    repo_root: Path,
    directory: Path,
    role: str,
    tech: str,
    markers: list[str],
) -> None:
    path = relative_dir_path(repo_root, directory)
    key = (role, tech, path)
    if key in seen:
        return
    seen.add(key)
    components.append(ProjectComponent(role=role, tech=tech, path=path, markers=markers))


def component_sort_key(component: ProjectComponent) -> tuple[int, int, str]:
    role_order = {"frontend": 0, "backend": 1, "software": 2, "infrastructure": 3}
    return (role_order.get(component.role, 9), STACK_ORDER.get(component.tech, 100), component.path)


def infer_node_component(directory: Path) -> tuple[str, list[str]]:
    markers = ["package.json"]
    server_files = ("server.js", "app.js", "index.js", "server.ts", "app.ts", "index.ts")
    lower_name = directory.name.lower()
    package_data = read_package_json(directory / "package.json")
    dependencies: set[str] = set()
    for section in ("dependencies", "devDependencies"):
        section_dependencies = package_data.get(section)
        if isinstance(section_dependencies, dict):
            dependencies.update(str(name).lower() for name in section_dependencies)
    if any((directory / name).exists() for name in server_files):
        markers.append("server entrypoint")
    is_backend = (
        lower_name in {"api", "backend", "server"}
        or any((directory / name).exists() for name in server_files)
        or bool(dependencies & {"express", "fastify", "koa", "hapi", "@nestjs/core"})
    )
    return ("backend" if is_backend else "frontend"), markers


def infer_python_component_role(directory: Path) -> str:
    lower_name = directory.name.lower()
    if lower_name in {"api", "backend", "server"}:
        return "backend"
    if any((directory / name).exists() for name in ("app.py", "server.py", "manage.py", "wsgi.py", "asgi.py")):
        return "backend"
    return "software"


def read_package_json(package_json_path: Path) -> dict[str, Any]:
    try:
        data = json.loads(package_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def derive_stack_from_surface(manifests: list[str], components: list[ProjectComponent]) -> list[str]:
    techs = {component.tech for component in components}
    for manifest in manifests:
        hint = STACK_HINTS.get(Path(manifest).name.lower())
        if hint:
            techs.add(hint)
    return sorted(techs, key=lambda tech: (STACK_ORDER.get(tech, 100), tech))


def has_manifest(surface: RepositorySurface, manifest_name: str) -> bool:
    target = manifest_name.lower()
    return any(Path(item).name.lower() == target for item in surface.manifests)


def extract_surface_package_commands(repo_root: Path, surface: RepositorySurface) -> list[str]:
    commands: list[str] = []
    for manifest in surface.manifests:
        if Path(manifest).name.lower() != "package.json":
            continue
        prefix = command_prefix(str(Path(manifest).parent).replace("\\", "/"))
        commands.extend(extract_package_commands(repo_root / manifest, prefix=prefix))
    return commands


def command_prefix(component_path: str) -> str:
    normalized = component_path.replace("\\", "/").strip("/")
    if not normalized or normalized == ".":
        return ""
    return f"cd {normalized} && "
