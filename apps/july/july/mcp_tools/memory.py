from __future__ import annotations

from typing import Any

from july.external_refs import suggest_references_for_context
from july.mcp_utils import ToolSpec, require_string, rows_to_dicts
from july.pipeline import create_capture_plan, enrich_plan_with_proactive_recall
from july.url_fetcher import fetch_url_metadata


class MemoryToolHandlers:
    def tool_capture_input(self, arguments: dict[str, Any]) -> dict[str, Any]:
        raw_input = require_string(arguments, "text")
        source = arguments.get("source", "mcp")
        source_ref = arguments.get("source_ref")
        use_llm = bool(arguments.get("use_llm", False))
        dry_run = bool(arguments.get("dry_run", False))
        fetch_urls = bool(arguments.get("fetch_urls", False))
        model_name = arguments.get("model_name")

        plan = create_capture_plan(raw_input)
        if use_llm:
            plan = self._maybe_enrich_capture_with_llm(raw_input, plan)

        project_key = plan["classification"].get("project_key")
        recall = self.database.proactive_recall(raw_input, project_key=project_key)
        plan = enrich_plan_with_proactive_recall(plan, recall)

        if dry_run:
            return {"saved": False, "plan": plan}

        result = self.database.capture(raw_input, source, source_ref, plan)

        if fetch_urls:
            for url in plan["context"].get("urls", []):
                meta = fetch_url_metadata(url)
                self.database.save_url_metadata(url, **{key: value for key, value in meta.items() if key != "url"})

        if model_name:
            self.database.save_model_contribution(
                model_name=model_name,
                contribution_type="capture_input",
                title=plan["classification"]["normalized_summary"],
                content=raw_input,
                inbox_item_id=result["inbox_item_id"],
                project_key=project_key,
            )

        return {"saved": True, "result": result, "plan": plan}

    def tool_search_context(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = require_string(arguments, "query")
        limit = int(arguments.get("limit", 10))
        return rows_to_dicts(self.database.search(query, limit=limit))

    def tool_project_context(self, arguments: dict[str, Any]) -> dict[str, Any]:
        project_key = require_string(arguments, "project_key")
        limit = int(arguments.get("limit", 10))
        return rows_to_dicts(self.database.project_context(project_key, limit=limit))

    def tool_list_inbox(self, arguments: dict[str, Any]) -> dict[str, Any]:
        limit = int(arguments.get("limit", 20))
        return {"items": [dict(row) for row in self.database.list_inbox(limit=limit)]}

    def tool_clarify_input(self, arguments: dict[str, Any]) -> dict[str, Any]:
        inbox_item_id = int(arguments["inbox_item_id"])
        answer = require_string(arguments, "answer")
        use_llm = bool(arguments.get("use_llm", False))

        inbox_item = self.database.get_record("inbox_items", inbox_item_id)
        if inbox_item is None:
            raise ValueError(f"Inbox item {inbox_item_id} not found")

        raw_input = inbox_item["raw_input"]
        plan = create_capture_plan(raw_input, clarification_answer=answer)
        if use_llm:
            plan = self._maybe_enrich_capture_with_llm(raw_input, plan, clarification_answer=answer)
        result = self.database.resolve_clarification(inbox_item_id, answer, plan)
        return {"resolved": True, "result": result, "plan": plan}

    def tool_promote_memory(self, arguments: dict[str, Any]) -> dict[str, Any]:
        memory_item_id = int(arguments["memory_item_id"])
        memory_item = self.database.get_record("memory_items", memory_item_id)
        if memory_item is None:
            raise ValueError(f"Memory item {memory_item_id} not found")

        updates: dict[str, Any] = {}
        if bool(arguments.get("use_llm", False)):
            updates = self._maybe_draft_memory_with_llm(memory_item)

        promoted = self.database.promote_memory(
            memory_item_id,
            title=arguments.get("title") or updates.get("title"),
            summary=arguments.get("summary") or updates.get("summary"),
            distilled_knowledge=arguments.get("knowledge") or updates.get("distilled_knowledge"),
            scope=arguments.get("scope"),
            importance=arguments.get("importance"),
        )
        return {"promoted": True, "memory_item": dict(promoted)}

    def tool_proactive_recall(self, arguments: dict[str, Any]) -> dict[str, Any]:
        text = require_string(arguments, "text")
        project_key = arguments.get("project_key")
        limit = int(arguments.get("limit", 5))
        recall = self.database.proactive_recall(text, project_key=project_key, limit=limit)

        ext_suggestions = suggest_references_for_context(text, project_key=project_key)
        recall["external_ref_suggestions"] = ext_suggestions
        return recall


def build_memory_tools(server) -> dict[str, ToolSpec]:
    return {
        "capture_input": ToolSpec(
            name="capture_input",
            title="Capture Input",
            description="Capture a free-form input into July with proactive recall and external reference suggestions.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Raw free-form input from the user."},
                    "source": {"type": "string", "description": "Source channel such as cli, telegram, email, or mcp."},
                    "source_ref": {"type": "string", "description": "Optional external message id or reference."},
                    "use_llm": {"type": "boolean", "description": "Whether to refine classification using the configured LLM."},
                    "dry_run": {"type": "boolean", "description": "When true, return the plan without saving it."},
                    "fetch_urls": {"type": "boolean", "description": "Fetch metadata for detected URLs."},
                    "model_name": {"type": "string", "description": "Name of the contributing model for traceability."},
                },
                "required": ["text"],
            },
            handler=server.tool_capture_input,
        ),
        "search_context": ToolSpec(
            name="search_context",
            title="Search Context",
            description="Search inbox, tasks, and memory items stored in July.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "limit": {"type": "integer", "description": "Maximum number of rows per section."},
                },
                "required": ["query"],
            },
            handler=server.tool_search_context,
        ),
        "project_context": ToolSpec(
            name="project_context",
            title="Project Context",
            description="Return inbox items, pending tasks, memory, and improvement ideas linked to a project key.",
            input_schema={
                "type": "object",
                "properties": {
                    "project_key": {"type": "string", "description": "Project key to inspect."},
                    "limit": {"type": "integer", "description": "Maximum rows per section."},
                },
                "required": ["project_key"],
            },
            handler=server.tool_project_context,
        ),
        "list_inbox": ToolSpec(
            name="list_inbox",
            title="List Inbox",
            description="List the latest inbox items captured by July.",
            input_schema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "description": "Maximum number of inbox items."}},
            },
            handler=server.tool_list_inbox,
        ),
        "clarify_input": ToolSpec(
            name="clarify_input",
            title="Clarify Input",
            description="Resolve a needs_clarification inbox item by providing the user's answer.",
            input_schema={
                "type": "object",
                "properties": {
                    "inbox_item_id": {"type": "integer", "description": "Inbox item id to clarify."},
                    "answer": {"type": "string", "description": "Clarification answer from the user."},
                    "use_llm": {"type": "boolean", "description": "Whether to refine resolved classification using the configured LLM."},
                },
                "required": ["inbox_item_id", "answer"],
            },
            handler=server.tool_clarify_input,
        ),
        "promote_memory": ToolSpec(
            name="promote_memory",
            title="Promote Memory",
            description="Promote a candidate memory into stable ready memory, optionally refining it with the configured LLM.",
            input_schema={
                "type": "object",
                "properties": {
                    "memory_item_id": {"type": "integer", "description": "Memory item id to promote."},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "knowledge": {"type": "string", "description": "Override distilled knowledge."},
                    "scope": {"type": "string", "enum": ["global", "project", "session"]},
                    "importance": {"type": "integer"},
                    "use_llm": {"type": "boolean"},
                },
                "required": ["memory_item_id"],
            },
            handler=server.tool_promote_memory,
        ),
        "proactive_recall": ToolSpec(
            name="proactive_recall",
            title="Proactive Recall",
            description="Find related July context and external reference suggestions for a text.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "project_key": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["text"],
            },
            handler=server.tool_proactive_recall,
        ),
    }
