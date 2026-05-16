from __future__ import annotations

import json
import sys
from pathlib import Path

from july.cli_context import CLIContext
from july.cli_output import print_capture_result, print_proactive_hints, print_rows
from july.pipeline import apply_classification_overrides, create_capture_plan, enrich_plan_with_proactive_recall
from july.url_fetcher import fetch_url_metadata


def handle_capture(ctx: CLIContext) -> int:
    raw_input = ctx.args.text if ctx.args.text is not None else sys.stdin.read().strip()
    if not raw_input:
        ctx.parser.error("capture requires text or stdin input")

    plan = create_capture_plan(raw_input)
    if ctx.args.use_llm:
        plan = maybe_enrich_capture_with_llm(ctx, raw_input, plan)

    project_key = plan["classification"].get("project_key")
    recall = ctx.database.proactive_recall(raw_input, project_key=project_key)
    plan = enrich_plan_with_proactive_recall(plan, recall)

    if ctx.args.dry_run:
        print(json.dumps(plan, indent=2, ensure_ascii=True))
        return 0

    result = ctx.database.capture(raw_input, ctx.args.source, ctx.args.source_ref, plan)

    if ctx.args.fetch_urls:
        for url in plan["context"].get("urls", []):
            meta = fetch_url_metadata(url)
            ctx.database.save_url_metadata(url, **{key: value for key, value in meta.items() if key != "url"})

    if ctx.args.model_name:
        ctx.database.save_model_contribution(
            model_name=ctx.args.model_name,
            contribution_type="capture_input",
            title=plan["classification"]["normalized_summary"],
            content=raw_input,
            inbox_item_id=result["inbox_item_id"],
            project_key=project_key,
        )

    print_capture_result(plan, result)
    print_proactive_hints(plan)
    return 0


def handle_clarify(ctx: CLIContext) -> int:
    answer = ctx.args.answer if ctx.args.answer is not None else sys.stdin.read().strip()
    if not answer:
        ctx.parser.error("clarify requires an answer or stdin input")

    inbox_item = ctx.database.get_record("inbox_items", ctx.args.inbox_item_id)
    if inbox_item is None:
        print("Inbox item not found")
        return 1

    raw_input = inbox_item["raw_input"]
    plan = create_capture_plan(raw_input, clarification_answer=answer)
    if ctx.args.use_llm:
        plan = maybe_enrich_capture_with_llm(ctx, raw_input, plan, clarification_answer=answer)
    result = ctx.database.resolve_clarification(ctx.args.inbox_item_id, answer, plan)
    print_capture_result(plan, result)
    return 0


def handle_promote_memory(ctx: CLIContext) -> int:
    memory_item = ctx.database.get_record("memory_items", ctx.args.memory_item_id)
    if memory_item is None:
        print("Memory item not found")
        return 1

    memory_updates = {}
    if ctx.args.use_llm:
        memory_updates = maybe_draft_memory_with_llm(ctx, memory_item)

    promoted = ctx.database.promote_memory(
        ctx.args.memory_item_id,
        title=ctx.args.title or memory_updates.get("title"),
        summary=ctx.args.summary or memory_updates.get("summary"),
        distilled_knowledge=ctx.args.knowledge or memory_updates.get("distilled_knowledge"),
        scope=ctx.args.scope,
        importance=ctx.args.importance,
    )
    print(json.dumps(dict(promoted), indent=2, ensure_ascii=True))
    return 0


def handle_inbox(ctx: CLIContext) -> int:
    print_rows(ctx.database.list_inbox(limit=ctx.args.limit))
    return 0


def handle_tasks(ctx: CLIContext) -> int:
    print_rows(ctx.database.list_tasks(status=ctx.args.status, limit=ctx.args.limit))
    return 0


def handle_memory(ctx: CLIContext) -> int:
    print_rows(ctx.database.list_memory(limit=ctx.args.limit))
    return 0


def handle_project_context(ctx: CLIContext) -> int:
    project_ctx = ctx.database.project_context(ctx.args.project_key, limit=ctx.args.limit)
    for section, rows in project_ctx.items():
        print(f"[{section}]")
        print_rows(rows)
        print()
    return 0


def handle_search(ctx: CLIContext) -> int:
    results = ctx.database.search(ctx.args.query, limit=ctx.args.limit)
    for section, rows in results.items():
        print(f"[{section}]")
        print_rows(rows)
        print()
    return 0


def handle_show(ctx: CLIContext) -> int:
    row = ctx.database.get_record(ctx.args.table, ctx.args.record_id)
    if row is None:
        print("Record not found")
        return 1
    print(json.dumps(dict(row), indent=2, ensure_ascii=True))
    return 0


def handle_stats(ctx: CLIContext) -> int:
    payload = ctx.database.stats()
    payload["llm_provider_available"] = int(ctx.llm_provider.is_available())
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


def handle_export(ctx: CLIContext) -> int:
    output_path = Path(ctx.args.output)
    ctx.database.export_json(output_path)
    print(f"Exported July data to {output_path}")
    return 0


def maybe_enrich_capture_with_llm(
    ctx: CLIContext,
    raw_input: str,
    plan: dict,
    clarification_answer: str | None = None,
) -> dict:
    overrides = ctx.llm_provider.enrich_capture(raw_input, plan)
    if not overrides:
        return plan
    return apply_classification_overrides(raw_input, plan, overrides, clarification_answer=clarification_answer)


def maybe_draft_memory_with_llm(ctx: CLIContext, memory_item) -> dict:
    inbox_item_id = memory_item["inbox_item_id"]
    raw_input = ""
    if inbox_item_id:
        inbox_item = ctx.database.get_record("inbox_items", inbox_item_id)
        if inbox_item is not None:
            raw_input = inbox_item["raw_input"]
    return ctx.llm_provider.draft_memory(raw_input, dict(memory_item)) or {}


MEMORY_HANDLERS = {
    "capture": handle_capture,
    "clarify": handle_clarify,
    "promote-memory": handle_promote_memory,
    "inbox": handle_inbox,
    "tasks": handle_tasks,
    "memory": handle_memory,
    "project-context": handle_project_context,
    "search": handle_search,
    "show": handle_show,
    "stats": handle_stats,
    "export": handle_export,
}
