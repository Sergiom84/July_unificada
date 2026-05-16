from __future__ import annotations

from july.cli_context import CLIContext
from july.cli_handlers import dispatch_cli_command
from july.cli_parser import build_parser
from july.cockpit import ProjectCockpitService
from july.config import get_settings
from july.db import JulyDatabase
from july.llm import LLMProviderError, create_llm_provider
from july.project_conversation import ProjectConversationService


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = get_settings()
    database = JulyDatabase(settings)
    llm_provider = create_llm_provider(settings.llm)
    project_service = ProjectConversationService(database)
    cockpit_service = ProjectCockpitService(database, settings, project_service)
    ctx = CLIContext(
        parser=parser,
        args=args,
        database=database,
        llm_provider=llm_provider,
        project_service=project_service,
        cockpit_service=cockpit_service,
    )

    try:
        return dispatch_cli_command(ctx)
    except (ValueError, LLMProviderError) as exc:
        print(str(exc))
        return 1
