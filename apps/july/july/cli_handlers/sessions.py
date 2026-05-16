from __future__ import annotations

import json
import sys

from july.cli_context import CLIContext
from july.cli_output import print_rows


def handle_session_start(ctx: CLIContext) -> int:
    result = ctx.database.session_start(
        ctx.args.session_key,
        project_key=ctx.args.project,
        agent_name=ctx.args.agent,
        goal=ctx.args.goal,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_session_summary(ctx: CLIContext) -> int:
    summary = ctx.args.summary if ctx.args.summary is not None else sys.stdin.read().strip()
    if not summary:
        ctx.parser.error("session-summary requires a summary text")
    result = ctx.database.session_summary(
        ctx.args.session_key,
        summary=summary,
        discoveries=ctx.args.discoveries,
        accomplished=ctx.args.accomplished,
        next_steps=ctx.args.next_steps,
        relevant_files=ctx.args.relevant_files,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_session_end(ctx: CLIContext) -> int:
    result = ctx.database.session_end(ctx.args.session_key)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_session_context(ctx: CLIContext) -> int:
    rows = ctx.database.session_context(project_key=ctx.args.project, limit=ctx.args.limit)
    if not rows:
        print("(no sessions found)")
    else:
        for row in rows:
            print(json.dumps(row, indent=2, ensure_ascii=True))
    return 0


def handle_sessions(ctx: CLIContext) -> int:
    print_rows(ctx.database.list_sessions(status=ctx.args.status, limit=ctx.args.limit))
    return 0


SESSION_HANDLERS = {
    "session-start": handle_session_start,
    "session-summary": handle_session_summary,
    "session-end": handle_session_end,
    "session-context": handle_session_context,
    "sessions": handle_sessions,
}
