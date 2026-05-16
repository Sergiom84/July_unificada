from __future__ import annotations

import json
import sys

from july.cli_context import CLIContext
from july.cli_output import print_rows, print_skill_catalog
from july.skill_registry import discover_local_skill_commands, load_skill_reference


def handle_skill_register(ctx: CLIContext) -> int:
    draft = load_skill_reference(ctx.args.path)
    result = ctx.database.upsert_skill_reference(
        skill_name=ctx.args.name or draft.skill_name,
        display_name=ctx.args.name or draft.display_name,
        description=ctx.args.description or draft.description,
        source_path=draft.source_path,
        trigger_text=ctx.args.trigger or draft.trigger_text,
        domains=ctx.args.domain,
        project_keys=ctx.args.project_key,
        status=ctx.args.status,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_skills(ctx: CLIContext) -> int:
    registered = ctx.database.list_skill_references(
        status=ctx.args.status,
        include_inactive=ctx.args.include_inactive,
        limit=ctx.args.limit,
    )
    local_commands = [] if ctx.args.registered_only else discover_local_skill_commands(limit=ctx.args.limit)
    print_skill_catalog(registered, local_commands)
    return 0


def handle_skill_suggest(ctx: CLIContext) -> int:
    text = ctx.args.text if ctx.args.text is not None else sys.stdin.read().strip()
    if not text:
        ctx.parser.error("skill-suggest requires text or stdin input")
    print_rows(ctx.database.suggest_skill_references(
        text,
        project_key=ctx.args.project_key,
        limit=ctx.args.limit,
    ))
    return 0


SKILL_HANDLERS = {
    "skill-register": handle_skill_register,
    "skills": handle_skills,
    "skill-suggest": handle_skill_suggest,
}
