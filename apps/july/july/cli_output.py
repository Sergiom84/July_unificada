from __future__ import annotations

import json


def print_rows(rows) -> None:
    if not rows:
        print("(empty)")
        return
    for row in rows:
        print(json.dumps(dict(row), ensure_ascii=True))


def print_skill_catalog(registered, local_commands) -> None:
    print("--- Skills de trabajo reutilizable ---")
    print_rows(registered)
    if local_commands:
        print()
        print("--- Comandos July / memoria operativa ---")
        print_rows(local_commands)


def print_capture_result(plan: dict, result: dict) -> None:
    classification = plan["classification"]
    print(f"inbox_item_id={result['inbox_item_id']}")
    print(f"intent={classification['intent']} confidence={classification['confidence']}")
    print(f"status={classification['status']}")
    print(f"summary={classification['normalized_summary']}")
    if classification["clarification_question"]:
        print(f"clarification={classification['clarification_question']}")
    if result["task_id"]:
        print(f"task_id={result['task_id']}")
    if result["memory_item_id"]:
        print(f"memory_item_id={result['memory_item_id']}")

    ext_refs = plan.get("external_ref_suggestions", [])
    if ext_refs:
        print("\n--- Sugerencias de referencia externa ---")
        for ref in ext_refs:
            print(f"  [{ref['source_name']}] {ref['reason']}")
            print(f"    URL: {ref['source_url']}")


def print_proactive_hints(plan: dict) -> None:
    hints = plan.get("proactive_hints", [])
    recall = plan.get("proactive_recall", {})
    memories = recall.get("related_memories", [])
    sessions = recall.get("related_sessions", [])
    skill_suggestions = recall.get("skill_suggestions", [])

    if not hints and not memories and not sessions and not skill_suggestions:
        return

    print("\n--- Recuperacion proactiva ---")
    if memories:
        print(f"  Memorias relacionadas encontradas: {len(memories)}")
        for mem in memories[:3]:
            print(f"    [{mem.get('memory_kind', '?')}] {mem.get('title', '?')}")
            if mem.get("project_key"):
                print(f"      proyecto: {mem['project_key']}")
    if sessions:
        print(f"  Sesiones recientes relevantes: {len(sessions)}")
        for sess in sessions[:2]:
            print(f"    [{sess.get('session_key', '?')}] {sess.get('goal', sess.get('summary', '?')[:80])}")
    if hints:
        print("  Sugerencias:")
        for hint in hints:
            print(f"    > {hint}")
    if skill_suggestions:
        print("  Skills sugeridas:")
        for skill in skill_suggestions[:3]:
            print(f"    > {skill.get('display_name', skill.get('skill_name'))}: {skill.get('reason')}")
