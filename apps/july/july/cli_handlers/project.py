from __future__ import annotations

import json
import sys

from july.cli_context import CLIContext


def handle_project_entry(ctx: CLIContext) -> int:
    result = ctx.project_service.project_entry(
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
        limit=ctx.args.limit,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_project_onboard(ctx: CLIContext) -> int:
    result = ctx.project_service.project_onboard(
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
        agent_name=ctx.args.agent,
        source=ctx.args.source,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_project_action(ctx: CLIContext) -> int:
    result = ctx.project_service.project_action(
        ctx.args.action,
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
        agent_name=ctx.args.agent,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_conversation_checkpoint(ctx: CLIContext) -> int:
    text = ctx.args.text if ctx.args.text is not None else sys.stdin.read().strip()
    if not text:
        ctx.parser.error("conversation-checkpoint requires text or stdin input")
    result = ctx.project_service.conversation_checkpoint(
        text,
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
        persist=ctx.args.persist,
        source=ctx.args.source,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_improvement_add(ctx: CLIContext) -> int:
    text = ctx.args.text if ctx.args.text is not None else sys.stdin.read().strip()
    if not text:
        ctx.parser.error("improvement-add requires text or stdin input")
    result = ctx.project_service.add_project_improvement(
        text,
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
        priority=ctx.args.priority,
        source=ctx.args.source,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_improvements(ctx: CLIContext) -> int:
    result = ctx.project_service.list_project_improvements(
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
        status=ctx.args.status,
        include_closed=ctx.args.include_closed,
        limit=ctx.args.limit,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_improvement_status(ctx: CLIContext) -> int:
    result = ctx.project_service.update_project_improvement_status(
        ctx.args.improvement_id,
        ctx.args.status,
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_pending_add(ctx: CLIContext) -> int:
    text = ctx.args.text if ctx.args.text is not None else sys.stdin.read().strip()
    if not text:
        ctx.parser.error("pending-add requires text or stdin input")
    result = ctx.project_service.add_project_pending(
        text,
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
        source=ctx.args.source,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_pendings(ctx: CLIContext) -> int:
    result = ctx.project_service.list_project_pendings(
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
        status=ctx.args.status,
        include_done=ctx.args.include_done,
        limit=ctx.args.limit,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_pending_status(ctx: CLIContext) -> int:
    result = ctx.project_service.update_project_pending_status(
        ctx.args.pending_id,
        ctx.args.status,
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_distill_candidates(ctx: CLIContext) -> int:
    result = ctx.project_service.distill_candidates(
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
        threshold=ctx.args.threshold,
        limit=ctx.args.limit,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_distill_record(ctx: CLIContext) -> int:
    result = ctx.project_service.record_distillation(
        repo_path=ctx.args.repo_path,
        project_key=ctx.args.project_key,
        wiki_pages_changed=ctx.args.wiki_page,
        notes=ctx.args.notes,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


PROJECT_HANDLERS = {
    "project-entry": handle_project_entry,
    "project-onboard": handle_project_onboard,
    "project-action": handle_project_action,
    "conversation-checkpoint": handle_conversation_checkpoint,
    "improvement-add": handle_improvement_add,
    "improvements": handle_improvements,
    "improvement-status": handle_improvement_status,
    "pending-add": handle_pending_add,
    "pendings": handle_pendings,
    "pending-status": handle_pending_status,
    "distill-candidates": handle_distill_candidates,
    "distill-record": handle_distill_record,
}
