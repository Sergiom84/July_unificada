from __future__ import annotations

import json

from july.cli_context import CLIContext
from july.cli_output import print_rows


def handle_topic_create(ctx: CLIContext) -> int:
    result = ctx.database.create_topic(
        ctx.args.topic_key,
        ctx.args.label,
        ctx.args.domain,
        description=ctx.args.description,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_topic_link(ctx: CLIContext) -> int:
    result = ctx.database.link_to_topic(
        ctx.args.topic_key,
        inbox_item_id=ctx.args.inbox_item_id,
        memory_item_id=ctx.args.memory_item_id,
        session_id=ctx.args.session_id,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_topic_context(ctx: CLIContext) -> int:
    result = ctx.database.topic_context(ctx.args.topic_key, limit=ctx.args.limit)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def handle_topics(ctx: CLIContext) -> int:
    print_rows(ctx.database.list_topics(limit=ctx.args.limit))
    return 0


TOPIC_HANDLERS = {
    "topic-create": handle_topic_create,
    "topic-link": handle_topic_link,
    "topic-context": handle_topic_context,
    "topics": handle_topics,
}
