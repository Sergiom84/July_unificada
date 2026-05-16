from __future__ import annotations

from typing import Callable

from july.cli_context import CLIContext
from july.cli_handlers.memory import MEMORY_HANDLERS
from july.cli_handlers.project import PROJECT_HANDLERS
from july.cli_handlers.references import REFERENCE_HANDLERS
from july.cli_handlers.runtime import RUNTIME_HANDLERS
from july.cli_handlers.sessions import SESSION_HANDLERS
from july.cli_handlers.skills import SKILL_HANDLERS
from july.cli_handlers.topics import TOPIC_HANDLERS

CommandHandler = Callable[[CLIContext], int]


def build_cli_handlers() -> dict[str, CommandHandler]:
    handlers: dict[str, CommandHandler] = {}
    for group in (
        RUNTIME_HANDLERS,
        MEMORY_HANDLERS,
        PROJECT_HANDLERS,
        SESSION_HANDLERS,
        TOPIC_HANDLERS,
        REFERENCE_HANDLERS,
        SKILL_HANDLERS,
    ):
        handlers.update(group)
    return handlers


def dispatch_cli_command(ctx: CLIContext) -> int:
    handler = build_cli_handlers().get(ctx.args.command)
    if handler is None:
        return 1
    return handler(ctx)
