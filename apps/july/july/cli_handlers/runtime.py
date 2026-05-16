from __future__ import annotations

import json
from importlib import import_module

from july.analyzer import analyze_codebase
from july.cli_context import CLIContext
from july.mcp import main as mcp_main
from july.project_conversation import derive_project_key, detect_repo_root


def handle_mcp(ctx: CLIContext) -> int:
    return mcp_main()


def handle_ui(ctx: CLIContext) -> int:
    ui_module = import_module("july.ui")
    return ui_module.run_ui_server(host=ctx.args.host, port=ctx.args.port, open_browser=ctx.args.open)


def handle_ui_link(ctx: CLIContext) -> int:
    result = ctx.cockpit_service.project_ui_link(
        project_key=ctx.args.project_key,
        repo_path=ctx.args.repo_path,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_plug(ctx: CLIContext) -> int:
    repo_root = detect_repo_root(ctx.args.path)
    resolved_key = derive_project_key(repo_root, explicit=ctx.args.project_key)
    ctx.database.upsert_project(resolved_key, str(repo_root), repo_name=repo_root.name)

    print(f"July enchufado a: {repo_root.name}")
    print(f"project_key: {resolved_key}")
    print(f"repo_root: {repo_root}")
    print()

    print("Analizando codigo fuente...")
    analysis = analyze_codebase(repo_root)
    print(f"Archivos fuente: {analysis.source_files}")
    print(f"Lenguajes: {', '.join(f'{lang} ({count})' for lang, count in analysis.languages.items())}")
    print(f"Arquitectura: {analysis.architecture_pattern}")
    print()

    if analysis.architecture_insights:
        print("--- Insights de arquitectura ---")
        for insight in analysis.architecture_insights:
            print(f"  [{insight.pattern}] (confianza: {insight.confidence:.0%})")
            print(f"    {insight.detail}")
            print(f"    Sugerencia: {insight.suggestion}")
        print()

    if analysis.code_smells:
        print(f"--- Code smells ({len(analysis.code_smells)}) ---")
        for smell in analysis.code_smells[:5]:
            print(f"  [{smell.severity}] {smell.file}: {smell.detail}")
        print()

    if analysis.proactive_questions:
        print("--- Preguntas del arquitecto ---")
        for question in analysis.proactive_questions:
            print(f"  > {question}")
        print()

    if analysis.suggestions:
        print("--- Sugerencias ---")
        for suggestion in analysis.suggestions:
            print(f"  * {suggestion}")
        print()

    if not ctx.args.skip_onboard:
        result = ctx.project_service.project_onboard(
            repo_path=str(repo_root),
            project_key=resolved_key,
            agent_name=ctx.args.agent,
            source="plug",
        )
        print(f"Onboarding completado. Session: {result['session']['session_key']}")

    return 0


def handle_architect(ctx: CLIContext) -> int:
    repo_root = detect_repo_root(ctx.args.path)
    resolved_key = derive_project_key(repo_root, explicit=ctx.args.project_key)
    analysis = analyze_codebase(repo_root)

    if ctx.args.json_output:
        print(json.dumps(analysis.to_dict(), indent=2, ensure_ascii=True))
        return 0

    print(f"Proyecto: {repo_root.name} ({resolved_key})")
    print(f"Archivos fuente: {analysis.source_files} | Total: {analysis.total_files}")
    print(f"Lenguajes: {', '.join(f'{language} ({count})' for language, count in analysis.languages.items())}")
    print(f"Arquitectura: {analysis.architecture_pattern}")
    print()

    if analysis.directory_tree:
        print("--- Estructura ---")
        for line in analysis.directory_tree[:25]:
            print(f"  {line}")
        print()

    if analysis.architecture_insights:
        print("--- Insights ---")
        for insight in analysis.architecture_insights:
            print(f"  [{insight.pattern}] {insight.detail}")
            print(f"    >> {insight.suggestion}")
        print()

    if analysis.code_smells:
        print(f"--- Code smells ({len(analysis.code_smells)}) ---")
        for smell in analysis.code_smells[:10]:
            print(f"  [{smell.severity}] {smell.file}: {smell.detail}")
        print()

    if analysis.dependency_hotspots:
        print("--- Dependency hotspots ---")
        for hotspot in analysis.dependency_hotspots:
            print(f"  [{hotspot['kind']}] {hotspot.get('file', hotspot.get('module', '?'))}: {hotspot['detail']}")
        print()

    if analysis.proactive_questions:
        print("--- Preguntas ---")
        for question in analysis.proactive_questions:
            print(f"  > {question}")
        print()

    if analysis.suggestions:
        print("--- Sugerencias ---")
        for suggestion in analysis.suggestions:
            print(f"  * {suggestion}")

    return 0


RUNTIME_HANDLERS = {
    "mcp": handle_mcp,
    "ui": handle_ui,
    "ui-link": handle_ui_link,
    "plug": handle_plug,
    "architect": handle_architect,
}
