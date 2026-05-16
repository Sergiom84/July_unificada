from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from july.config import Settings
from july.repositories.distillation_repository import DistillationRepository
from july.repositories.memory_repository import MemoryRepository
from july.repositories.project_repository import ProjectRepository
from july.repositories.reference_repository import ReferenceRepository
from july.repositories.search_repository import SearchRepository
from july.repositories.session_repository import SessionRepository
from july.repositories.skill_repository import SkillRepository
from july.repositories.task_repository import TaskRepository
from july.repositories.topic_repository import TopicRepository
from july.storage.migrations import run_migrations
from july.storage.schema import SCHEMA_SQL
from july.storage.utils import utc_now


class JulyDatabase:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.projects = ProjectRepository(self.connection)
        self.sessions = SessionRepository(self.connection)
        self.skills = SkillRepository(self.connection)
        self.tasks = TaskRepository(self.connection)
        self.memory = MemoryRepository(self.connection)
        self.topics = TopicRepository(self.connection)
        self.references = ReferenceRepository(self.connection)
        self.distillations = DistillationRepository(self.connection)
        self.searches = SearchRepository(self.connection, self.suggest_skill_references)

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.settings.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self.connection() as conn:
            conn.executescript(SCHEMA_SQL)
            run_migrations(conn)

    def capture(self, *args, **kwargs):
        return self.memory.capture(*args, **kwargs)

    def resolve_clarification(self, *args, **kwargs):
        return self.memory.resolve_clarification(*args, **kwargs)

    def promote_memory(self, *args, **kwargs):
        return self.memory.promote_memory(*args, **kwargs)

    def project_context(self, *args, **kwargs):
        return self.projects.project_context(*args, **kwargs)

    def upsert_project(self, *args, **kwargs):
        return self.projects.upsert_project(*args, **kwargs)

    def touch_project(self, *args, **kwargs):
        return self.projects.touch_project(*args, **kwargs)

    def get_project(self, *args, **kwargs):
        return self.projects.get_project(*args, **kwargs)

    def list_projects(self, *args, **kwargs):
        return self.projects.list_projects(*args, **kwargs)

    def get_project_totals(self, *args, **kwargs):
        return self.projects.get_project_totals(*args, **kwargs)

    def create_project_improvement(self, *args, **kwargs):
        return self.tasks.create_project_improvement(*args, **kwargs)

    def list_project_improvements(self, *args, **kwargs):
        return self.tasks.list_project_improvements(*args, **kwargs)

    def update_project_improvement_status(self, *args, **kwargs):
        return self.tasks.update_project_improvement_status(*args, **kwargs)

    def create_manual_task(self, *args, **kwargs):
        return self.tasks.create_manual_task(*args, **kwargs)

    def list_project_tasks(self, *args, **kwargs):
        return self.tasks.list_project_tasks(*args, **kwargs)

    def update_task_status(self, *args, **kwargs):
        return self.tasks.update_task_status(*args, **kwargs)

    def list_inbox(self, *args, **kwargs):
        return self.memory.list_inbox(*args, **kwargs)

    def list_tasks(self, *args, **kwargs):
        return self.memory.list_tasks(*args, **kwargs)

    def list_memory(self, *args, **kwargs):
        return self.memory.list_memory(*args, **kwargs)

    def search(self, *args, **kwargs):
        return self.searches.search(*args, **kwargs)

    def get_record(self, *args, **kwargs):
        return self.memory.get_record(*args, **kwargs)

    # ── Session protocol ──────────────────────────────────────────────

    def session_start(self, *args, **kwargs):
        return self.sessions.session_start(*args, **kwargs)

    def session_summary(self, *args, **kwargs):
        return self.sessions.session_summary(*args, **kwargs)

    def session_end(self, *args, **kwargs):
        result = self.sessions.session_end(*args, **kwargs)
        project_key = result.get("project_key")
        if project_key:
            result["distillation"] = self.distill_candidates(project_key, limit=3)
        return result

    def session_context(self, *args, **kwargs):
        return self.sessions.session_context(*args, **kwargs)

    def get_open_session(self, *args, **kwargs):
        return self.sessions.get_open_session(*args, **kwargs)

    def list_sessions(self, *args, **kwargs):
        return self.sessions.list_sessions(*args, **kwargs)

    # ── July -> wiki distillation ────────────────────────────────────

    def distill_candidates(self, *args, **kwargs):
        return self.distillations.distill_candidates(*args, **kwargs)

    def record_distillation(self, *args, **kwargs):
        return self.distillations.record_distillation(*args, **kwargs)

    def list_distillations(self, *args, **kwargs):
        return self.distillations.list_distillations(*args, **kwargs)

    # ── Topic keys ────────────────────────────────────────────────────

    def create_topic(self, *args, **kwargs):
        return self.topics.create_topic(*args, **kwargs)

    def link_to_topic(self, *args, **kwargs):
        return self.topics.link_to_topic(*args, **kwargs)

    def topic_context(self, *args, **kwargs):
        return self.topics.topic_context(*args, **kwargs)

    def list_topics(self, *args, **kwargs):
        return self.topics.list_topics(*args, **kwargs)

    # ── Model contributions / traceability ────────────────────────────

    def save_model_contribution(self, *args, **kwargs):
        return self.references.save_model_contribution(*args, **kwargs)

    def list_model_contributions(self, *args, **kwargs):
        return self.references.list_model_contributions(*args, **kwargs)

    def adopt_contribution(self, *args, **kwargs):
        return self.references.adopt_contribution(*args, **kwargs)

    # ── URL metadata ──────────────────────────────────────────────────

    def save_url_metadata(self, *args, **kwargs):
        return self.references.save_url_metadata(*args, **kwargs)

    def get_url_metadata(self, *args, **kwargs):
        return self.references.get_url_metadata(*args, **kwargs)

    # ── External references (skills.sh, agents.md, etc.) ─────────────

    def save_external_reference(self, *args, **kwargs):
        return self.references.save_external_reference(*args, **kwargs)

    def list_external_references(self, *args, **kwargs):
        return self.references.list_external_references(*args, **kwargs)

    # ── Skill references ─────────────────────────────────────────────

    def upsert_skill_reference(self, *args, **kwargs):
        return self.skills.upsert_skill_reference(*args, **kwargs)

    def list_skill_references(self, *args, **kwargs):
        return self.skills.list_skill_references(*args, **kwargs)

    def suggest_skill_references(self, *args, **kwargs):
        return self.skills.suggest_skill_references(*args, **kwargs)

    # ── Proactive recall ──────────────────────────────────────────────

    def proactive_recall(self, *args, **kwargs):
        return self.searches.proactive_recall(*args, **kwargs)

    def stats(self) -> dict[str, int]:
        with self.connection() as conn:
            return {
                "inbox_items": conn.execute("SELECT COUNT(*) FROM inbox_items").fetchone()[0],
                "tasks": conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
                "memory_items": conn.execute("SELECT COUNT(*) FROM memory_items").fetchone()[0],
                "artifacts": conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0],
                "project_links": conn.execute("SELECT COUNT(*) FROM project_links").fetchone()[0],
                "clarification_events": conn.execute("SELECT COUNT(*) FROM clarification_events").fetchone()[0],
                "sessions": conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
                "topic_keys": conn.execute("SELECT COUNT(*) FROM topic_keys").fetchone()[0],
                "model_contributions": conn.execute("SELECT COUNT(*) FROM model_contributions").fetchone()[0],
                "url_metadata": conn.execute("SELECT COUNT(*) FROM url_metadata").fetchone()[0],
                "external_references": conn.execute("SELECT COUNT(*) FROM external_references").fetchone()[0],
                "skill_references": conn.execute("SELECT COUNT(*) FROM skill_references").fetchone()[0],
                "projects": conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
                "project_improvements": conn.execute("SELECT COUNT(*) FROM project_improvements").fetchone()[0],
                "project_distillations": conn.execute("SELECT COUNT(*) FROM project_distillations").fetchone()[0],
                "developer_interactions": conn.execute("SELECT COUNT(*) FROM developer_interactions").fetchone()[0],
            }

    # ── Developer profile ──────────────────────────────────────

    def get_developer_profile(self, profile_key: str = "default") -> dict | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM developer_profile WHERE profile_key = ?",
                (profile_key,),
            ).fetchone()
            return dict(row) if row else None

    def ensure_developer_profile(self, profile_key: str = "default") -> dict:
        existing = self.get_developer_profile(profile_key)
        if existing:
            return existing
        timestamp = utc_now()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO developer_profile (
                    profile_key, inferred_level, total_interactions,
                    decisions_count, architecture_questions,
                    code_smells_addressed, patterns_applied,
                    last_interaction_at, created_at, updated_at
                ) VALUES (?, 'junior', 0, 0, 0, 0, 0, ?, ?, ?)
                """,
                (profile_key, timestamp, timestamp, timestamp),
            )
        return self.get_developer_profile(profile_key)

    def record_developer_interaction(
        self,
        interaction_type: str,
        *,
        complexity: str = "basic",
        project_key: str | None = None,
        detail: str | None = None,
        profile_key: str = "default",
    ) -> dict:
        timestamp = utc_now()
        self.ensure_developer_profile(profile_key)

        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO developer_interactions (
                    profile_key, interaction_type, complexity, project_key, detail, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (profile_key, interaction_type, complexity, project_key, detail, timestamp),
            )

            # Update counters
            increment_field = {
                "decision": "decisions_count",
                "architecture_question": "architecture_questions",
                "smell_fix": "code_smells_addressed",
                "pattern_apply": "patterns_applied",
            }.get(interaction_type)

            update_parts = [
                "total_interactions = total_interactions + 1",
                "last_interaction_at = ?",
                "updated_at = ?",
            ]
            params: list = [timestamp, timestamp]

            if increment_field:
                update_parts.append(f"{increment_field} = {increment_field} + 1")

            conn.execute(
                f"UPDATE developer_profile SET {', '.join(update_parts)} WHERE profile_key = ?",
                (*params, profile_key),
            )

        return self._infer_and_update_level(profile_key)

    def _infer_and_update_level(self, profile_key: str = "default") -> dict:
        profile = self.get_developer_profile(profile_key)
        if not profile:
            return {"level": "junior", "profile": None}

        total = profile["total_interactions"]
        decisions = profile["decisions_count"]
        arch_q = profile["architecture_questions"]
        smells = profile["code_smells_addressed"]
        patterns = profile["patterns_applied"]

        # Inference logic
        score = 0
        score += min(total // 10, 5)  # Up to 5 points for volume
        score += min(decisions // 3, 4)  # Up to 4 points for decisions
        score += min(arch_q // 2, 3)  # Up to 3 for architecture engagement
        score += min(smells // 2, 3)  # Up to 3 for addressing smells
        score += min(patterns // 2, 3)  # Up to 3 for applying patterns

        if score >= 12:
            level = "senior"
        elif score >= 5:
            level = "mid"
        else:
            level = "junior"

        if level != profile["inferred_level"]:
            with self.connection() as conn:
                conn.execute(
                    "UPDATE developer_profile SET inferred_level = ?, updated_at = ? WHERE profile_key = ?",
                    (level, utc_now(), profile_key),
                )

        return {
            "level": level,
            "score": score,
            "profile": {**profile, "inferred_level": level},
        }

    def get_developer_level(self, profile_key: str = "default") -> str:
        profile = self.get_developer_profile(profile_key)
        if not profile:
            return "junior"
        return profile["inferred_level"]

    def export_json(self, output_path: Path) -> None:
        payload: dict[str, list[dict]] = {}
        with self.connection() as conn:
            for table in (
                "inbox_items", "tasks", "memory_items", "artifacts", "project_links",
                "clarification_events", "sessions", "topic_keys", "topic_links",
                "model_contributions", "url_metadata", "external_references", "skill_references", "projects",
                "project_improvements", "project_distillations", "developer_profile", "developer_interactions",
        ):
                rows = conn.execute(f"SELECT * FROM {table} ORDER BY id ASC").fetchall()
                payload[table] = [dict(row) for row in rows]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

