from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from july.cockpit import ProjectCockpitService
from july.db import JulyDatabase
from july.project_conversation import ProjectConversationService


@dataclass(slots=True)
class CLIContext:
    parser: Any
    args: Any
    database: JulyDatabase
    llm_provider: Any
    project_service: ProjectConversationService
    cockpit_service: ProjectCockpitService
