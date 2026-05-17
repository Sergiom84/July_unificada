from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any

from july.storage.utils import utc_now

AUDIT_OPEN_STATUSES = {"open"}
AUDIT_REVIEW_STATUSES = {"open", "accepted", "dismissed", "resolved"}
MEMORY_APPLY_STATUSES = {"ready", "needs_review", "archived", "superseded", "duplicate"}

MOJIBAKE_RE = re.compile(r"(Ã.|Â.|â€™|â€œ|â€|�)")

LOW_QUALITY_PATTERNS = (
    ("mojibake", MOJIBAKE_RE, "El texto parece tener caracteres corruptos o mojibake."),
    ("stack_unknown", re.compile(r"stack:\s*(no detectado|unknown)", re.IGNORECASE), "La memoria conserva un stack no detectado."),
    ("entrypoints_missing", re.compile(r"entrypoints?:\s*(ninguno|no detectado|none)", re.IGNORECASE), "La memoria conserva entrypoints no detectados."),
    ("objective_missing", re.compile(r"no hay una descripci[oó]n expl[ií]cita", re.IGNORECASE), "La memoria indica que faltaba descripción del proyecto."),
)

COMPLETION_WORDS = (
    "validado", "validada", "validar completado", "resuelto", "resuelta",
    "actualizado", "actualizada", "completado", "completada", "implementado",
    "implementada", "cerrado", "cerrada", "qa", "probado", "probada",
)


class MemoryAuditRepository:
    """Detect suspicious memory that should be reviewed, without deleting automatically."""

    def __init__(self, connection_factory):
        self.connection = connection_factory

    def audit_project_memory(
        self,
        project_key: str,
        *,
        current_entrypoints: list[str] | None = None,
        dry_run: bool = False,
        limit: int = 20,
    ) -> dict[str, Any]:
        timestamp = utc_now()
        current_entrypoints = current_entrypoints or []

        with self.connection() as conn:
            memory_rows = self._project_memory_rows(conn, project_key)
            findings: list[dict[str, Any]] = []
            findings.extend(self._detect_low_quality(memory_rows))
            findings.extend(self._detect_entrypoint_obsolete(memory_rows, current_entrypoints))
            findings.extend(self._detect_duplicate_onboarding(memory_rows))
            findings.extend(self._detect_possible_completed_pendings(conn, project_key, memory_rows))

            findings = findings[:limit]
            if dry_run:
                persisted = [
                    {
                        **finding,
                        "id": None,
                        "status": "preview",
                        "created_at": timestamp,
                    }
                    for finding in findings
                ]
            else:
                persisted = [self._upsert_finding(conn, project_key, finding, timestamp) for finding in findings]

        counts: dict[str, int] = defaultdict(int)
        for finding in persisted:
            counts[finding["finding_type"]] += 1

        return {
            "project_key": project_key,
            "dry_run": dry_run,
            "created_or_existing": len(persisted),
            "finding_counts": dict(counts),
            "findings": persisted,
        }

    def list_findings(
        self,
        *,
        project_key: str | None = None,
        status: str | None = "open",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        params: list[object] = []
        clauses: list[str] = []
        if project_key:
            clauses.append("project_key = ?")
            params.append(project_key)
        if status and status != "all":
            clauses.append("status = ?")
            params.append(status)

        query = "SELECT * FROM memory_audit_findings"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self.connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self._finding_row(row) for row in rows]

    def summary(self, project_key: str) -> dict[str, Any]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT finding_type, COUNT(*) AS count
                FROM memory_audit_findings
                WHERE project_key = ?
                  AND status = 'open'
                GROUP BY finding_type
                ORDER BY finding_type
                """,
                (project_key,),
            ).fetchall()
        counts = {row["finding_type"]: row["count"] for row in rows}
        return {
            "project_key": project_key,
            "open_count": sum(counts.values()),
            "counts": counts,
            "needs_review": bool(counts),
        }

    def resolve_finding(
        self,
        finding_id: int,
        status: str,
        *,
        review_notes: str | None = None,
        reviewed_by: str | None = None,
        apply_memory_status: str | None = None,
    ) -> dict[str, Any]:
        if status not in AUDIT_REVIEW_STATUSES:
            raise ValueError("Audit finding status must be open, accepted, dismissed, or resolved")
        if apply_memory_status and apply_memory_status not in MEMORY_APPLY_STATUSES:
            raise ValueError("Memory status must be ready, needs_review, archived, superseded, or duplicate")

        timestamp = utc_now()
        applied: dict[str, Any] | None = None
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM memory_audit_findings WHERE id = ?",
                (finding_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Memory audit finding {finding_id} not found")

            if apply_memory_status:
                if row["subject_table"] != "memory_items":
                    raise ValueError("apply_memory_status can only be used when the finding subject is a memory item")
                conn.execute(
                    "UPDATE memory_items SET status = ?, updated_at = ? WHERE id = ?",
                    (apply_memory_status, timestamp, row["subject_id"]),
                )
                applied = {
                    "table": "memory_items",
                    "id": row["subject_id"],
                    "status": apply_memory_status,
                }

            conn.execute(
                """
                UPDATE memory_audit_findings
                SET status = ?, reviewed_at = ?, reviewed_by = ?, review_notes = ?
                WHERE id = ?
                """,
                (status, timestamp, reviewed_by, review_notes, finding_id),
            )
            updated = conn.execute(
                "SELECT * FROM memory_audit_findings WHERE id = ?",
                (finding_id,),
            ).fetchone()

        return {
            "finding": self._finding_row(updated),
            "applied": applied,
        }

    def _project_memory_rows(self, conn, project_key: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT id, memory_kind, title, summary, distilled_knowledge, status,
                   scope, project_key, created_at, updated_at
            FROM memory_items
            WHERE project_key = ?
              AND status NOT IN ('archived', 'superseded', 'duplicate')
            ORDER BY id DESC
            LIMIT 250
            """,
            (project_key,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _detect_low_quality(self, memory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        findings = []
        for row in memory_rows:
            text = self._memory_text(row)
            for code, pattern, reason in LOW_QUALITY_PATTERNS:
                if pattern.search(text):
                    findings.append({
                        "finding_type": "low_quality",
                        "severity": "medium",
                        "subject_table": "memory_items",
                        "subject_id": row["id"],
                        "related_table": None,
                        "related_id": None,
                        "reason": reason,
                        "evidence": [
                            {
                                "code": code,
                                "memory_id": row["id"],
                                "title": row["title"],
                            }
                        ],
                        "suggestion": "Revisar, corregir o archivar esta memoria si ya no aporta contexto útil.",
                    })
                    break
        return findings

    def _detect_entrypoint_obsolete(
        self,
        memory_rows: list[dict[str, Any]],
        current_entrypoints: list[str],
    ) -> list[dict[str, Any]]:
        if not current_entrypoints:
            return []
        findings = []
        for row in memory_rows:
            text = self._memory_text(row).lower()
            mentions_entrypoints = "entrypoint" in text or "punto de entrada" in text
            says_missing = "no detect" in text or "ninguno" in text or "none detected" in text
            if mentions_entrypoints and says_missing:
                findings.append({
                    "finding_type": "possibly_obsolete",
                    "severity": "high",
                    "subject_table": "memory_items",
                    "subject_id": row["id"],
                    "related_table": None,
                    "related_id": None,
                    "reason": "La memoria dice que no había entrypoints, pero la superficie actual del repo sí los detecta.",
                    "evidence": [
                        {
                            "memory_id": row["id"],
                            "title": row["title"],
                            "current_entrypoints": current_entrypoints,
                        }
                    ],
                    "suggestion": "Confirmar si la memoria quedó obsoleta y marcarla como archived o superseded.",
                })
        return findings

    def _detect_duplicate_onboarding(self, memory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        onboarding = [
            row for row in sorted(memory_rows, key=lambda item: item["id"])
            if self._looks_like_onboarding(row)
        ]
        if len(onboarding) <= 1:
            return []
        canonical = onboarding[-1]
        findings = []
        for row in onboarding[:-1]:
            findings.append({
                "finding_type": "duplicate",
                "severity": "medium",
                "subject_table": "memory_items",
                "subject_id": row["id"],
                "related_table": "memory_items",
                "related_id": canonical["id"],
                "reason": "Hay varios onboarding/perfiles iniciales del mismo proyecto; conviene conservar el más reciente o más rico.",
                "evidence": [
                    {
                        "older_memory_id": row["id"],
                        "newer_memory_id": canonical["id"],
                        "older_title": row["title"],
                        "newer_title": canonical["title"],
                    }
                ],
                "suggestion": "Revisar si la memoria antigua debe marcarse como duplicate o superseded.",
            })
        return findings

    def _detect_possible_completed_pendings(
        self,
        conn,
        project_key: str,
        memory_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        tasks = conn.execute(
            """
            SELECT id, title, details, status, updated_at
            FROM tasks
            WHERE project_key = ?
              AND task_type = 'manual_follow_up'
              AND status IN ('pending', 'in_progress')
            ORDER BY id DESC
            LIMIT 100
            """,
            (project_key,),
        ).fetchall()

        findings = []
        for task in tasks:
            task_text = f"{task['title']} {task['details'] or ''}".lower()
            task_tokens = self._strong_tokens(task_text)
            if not task_tokens:
                continue
            for memory in memory_rows:
                memory_text = self._memory_text(memory).lower()
                if memory["created_at"] < task["updated_at"]:
                    continue
                if not any(word in memory_text for word in COMPLETION_WORDS):
                    continue
                overlap = sorted(task_tokens.intersection(self._strong_tokens(memory_text)))
                if not overlap:
                    continue
                findings.append({
                    "finding_type": "possibly_completed",
                    "severity": "medium",
                    "subject_table": "tasks",
                    "subject_id": task["id"],
                    "related_table": "memory_items",
                    "related_id": memory["id"],
                    "reason": "Un pendiente abierto parece cubierto por una memoria posterior.",
                    "evidence": [
                        {
                            "task_id": task["id"],
                            "memory_id": memory["id"],
                            "overlap": overlap[:8],
                            "memory_title": memory["title"],
                        }
                    ],
                    "suggestion": "Confirmar si el pendiente está hecho antes de cerrarlo.",
                })
                break
        return findings

    def _upsert_finding(self, conn, project_key: str, finding: dict[str, Any], timestamp: str) -> dict[str, Any]:
        existing = conn.execute(
            """
            SELECT *
            FROM memory_audit_findings
            WHERE status = 'open'
              AND finding_type = ?
              AND subject_table = ?
              AND subject_id = ?
              AND COALESCE(related_table, '') = COALESCE(?, '')
              AND COALESCE(related_id, -1) = COALESCE(?, -1)
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                finding["finding_type"],
                finding["subject_table"],
                finding["subject_id"],
                finding.get("related_table"),
                finding.get("related_id"),
            ),
        ).fetchone()
        if existing:
            return self._finding_row(existing)

        cursor = conn.execute(
            """
            INSERT INTO memory_audit_findings (
                project_key, finding_type, severity, subject_table, subject_id,
                related_table, related_id, reason, evidence_json, suggestion,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (
                project_key,
                finding["finding_type"],
                finding["severity"],
                finding["subject_table"],
                finding["subject_id"],
                finding.get("related_table"),
                finding.get("related_id"),
                finding["reason"],
                json.dumps(finding.get("evidence", []), ensure_ascii=True),
                finding.get("suggestion"),
                timestamp,
            ),
        )
        row = conn.execute(
            "SELECT * FROM memory_audit_findings WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return self._finding_row(row)

    def _finding_row(self, row) -> dict[str, Any]:
        result = dict(row)
        result["evidence"] = json.loads(result.pop("evidence_json") or "[]")
        return result

    def _memory_text(self, row: dict[str, Any]) -> str:
        return " ".join(str(row.get(key) or "") for key in ("title", "summary", "distilled_knowledge"))

    def _looks_like_onboarding(self, row: dict[str, Any]) -> bool:
        text = self._memory_text(row).lower()
        return (
            "perfil inicial del proyecto" in text
            or "onboarding inicial" in text
            or "repository_onboarding" in text
        )

    def _strong_tokens(self, text: str) -> set[str]:
        stopwords = {
            "para", "como", "este", "esta", "esto", "hacer", "revisar", "pendiente",
            "proyecto", "memoria", "actualizado", "actualizada", "validado", "validada",
            "the", "and", "with", "from", "this", "that",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9_/-]{4,}", text.lower())
            if token not in stopwords
        }
