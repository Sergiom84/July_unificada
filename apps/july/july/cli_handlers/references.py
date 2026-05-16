from __future__ import annotations

import json
import sys

from july.cli_context import CLIContext
from july.cli_output import print_rows
from july.external_refs import fetch_reference_page
from july.url_fetcher import fetch_url_metadata


def handle_model_contribution(ctx: CLIContext) -> int:
    content = ctx.args.content if ctx.args.content is not None else sys.stdin.read().strip()
    if not content:
        ctx.parser.error("model-contribution requires content")
    result = ctx.database.save_model_contribution(
        model_name=ctx.args.model_name,
        contribution_type=ctx.args.contribution_type,
        title=ctx.args.title,
        content=content,
        project_key=ctx.args.project,
        domain=ctx.args.domain,
        adopted=ctx.args.adopted,
        notes=ctx.args.notes,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_model_contributions(ctx: CLIContext) -> int:
    print_rows(ctx.database.list_model_contributions(
        model_name=ctx.args.model,
        project_key=ctx.args.project,
        limit=ctx.args.limit,
    ))
    return 0


def handle_adopt_contribution(ctx: CLIContext) -> int:
    result = ctx.database.adopt_contribution(ctx.args.contribution_id, notes=ctx.args.notes)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_fetch_url(ctx: CLIContext) -> int:
    meta = fetch_url_metadata(ctx.args.url)
    db_result = ctx.database.save_url_metadata(
        ctx.args.url,
        artifact_id=ctx.args.artifact_id,
        **{key: value for key, value in meta.items() if key not in ("url", "fetch_status")},
        fetch_status=meta["fetch_status"],
    )
    combined = {**meta, **db_result}
    print(json.dumps(combined, indent=2, ensure_ascii=True))
    return 0


def handle_fetch_reference(ctx: CLIContext) -> int:
    result = fetch_reference_page(ctx.args.source_key)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_external_references(ctx: CLIContext) -> int:
    print_rows(ctx.database.list_external_references(
        project_key=ctx.args.project,
        limit=ctx.args.limit,
    ))
    return 0


REFERENCE_HANDLERS = {
    "model-contribution": handle_model_contribution,
    "model-contributions": handle_model_contributions,
    "adopt-contribution": handle_adopt_contribution,
    "fetch-url": handle_fetch_url,
    "fetch-reference": handle_fetch_reference,
    "external-references": handle_external_references,
}
