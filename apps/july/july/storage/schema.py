from __future__ import annotations

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS inbox_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_input TEXT NOT NULL,
    source_channel TEXT NOT NULL,
    source_ref TEXT,
    detected_intent TEXT NOT NULL,
    intent_confidence REAL NOT NULL,
    status TEXT NOT NULL,
    clarification_question TEXT,
    normalized_summary TEXT NOT NULL,
    domain TEXT NOT NULL,
    project_key TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT,
    project_key TEXT,
    due_hint TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
    memory_kind TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    distilled_knowledge TEXT NOT NULL,
    domain TEXT NOT NULL,
    scope TEXT NOT NULL,
    project_key TEXT,
    importance INTEGER NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_item_id INTEGER NOT NULL REFERENCES inbox_items(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    value TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE CASCADE,
    memory_item_id INTEGER REFERENCES memory_items(id) ON DELETE CASCADE,
    project_key TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key TEXT NOT NULL UNIQUE,
    repo_root TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    project_kind TEXT NOT NULL DEFAULT 'unknown',
    project_tags_json TEXT NOT NULL DEFAULT '[]',
    preferences_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_improvements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    priority TEXT NOT NULL DEFAULT 'normal',
    source_channel TEXT NOT NULL DEFAULT 'cli',
    source_ref TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_project_improvements_project_status
ON project_improvements(project_key, status, updated_at);

CREATE TABLE IF NOT EXISTS project_distillations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key TEXT NOT NULL,
    from_session_id INTEGER,
    to_session_id INTEGER,
    session_count INTEGER NOT NULL DEFAULT 0,
    wiki_pages_changed_json TEXT NOT NULL DEFAULT '[]',
    notes TEXT,
    distilled_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_project_distillations_project_session
ON project_distillations(project_key, to_session_id, distilled_at);

CREATE TABLE IF NOT EXISTS memory_audit_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key TEXT,
    finding_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    subject_table TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    related_table TEXT,
    related_id INTEGER,
    reason TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    suggestion TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    reviewed_at TEXT,
    reviewed_by TEXT,
    review_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_memory_audit_findings_project_status
ON memory_audit_findings(project_key, status, finding_type, created_at);

CREATE INDEX IF NOT EXISTS idx_memory_audit_findings_subject
ON memory_audit_findings(subject_table, subject_id, finding_type, status);

CREATE TABLE IF NOT EXISTS clarification_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_item_id INTEGER NOT NULL REFERENCES inbox_items(id) ON DELETE CASCADE,
    question TEXT,
    answer TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT NOT NULL UNIQUE,
    project_key TEXT,
    agent_name TEXT,
    goal TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    summary TEXT,
    discoveries TEXT,
    accomplished TEXT,
    next_steps TEXT,
    relevant_files TEXT,
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS topic_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_key TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    domain TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topic_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_key_id INTEGER NOT NULL REFERENCES topic_keys(id) ON DELETE CASCADE,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
    memory_item_id INTEGER REFERENCES memory_items(id) ON DELETE SET NULL,
    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    contribution_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
    memory_item_id INTEGER REFERENCES memory_items(id) ON DELETE SET NULL,
    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    project_key TEXT,
    domain TEXT,
    adopted INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS url_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id INTEGER REFERENCES artifacts(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    resolved_title TEXT,
    description TEXT,
    content_type TEXT,
    extracted_text TEXT,
    youtube_video_id TEXT,
    youtube_channel TEXT,
    youtube_duration TEXT,
    fetch_status TEXT NOT NULL DEFAULT 'pending',
    fetched_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS external_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,
    source_name TEXT NOT NULL,
    reference_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    relevance_note TEXT,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
    memory_item_id INTEGER REFERENCES memory_items(id) ON DELETE SET NULL,
    project_key TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    source_path TEXT,
    trigger_text TEXT NOT NULL,
    domains_json TEXT NOT NULL DEFAULT '[]',
    project_keys_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_skill_references_status
ON skill_references(status, updated_at);

CREATE TABLE IF NOT EXISTS developer_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_key TEXT NOT NULL UNIQUE DEFAULT 'default',
    inferred_level TEXT NOT NULL DEFAULT 'junior',
    total_interactions INTEGER NOT NULL DEFAULT 0,
    decisions_count INTEGER NOT NULL DEFAULT 0,
    architecture_questions INTEGER NOT NULL DEFAULT 0,
    code_smells_addressed INTEGER NOT NULL DEFAULT 0,
    patterns_applied INTEGER NOT NULL DEFAULT 0,
    last_interaction_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS developer_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_key TEXT NOT NULL DEFAULT 'default',
    interaction_type TEXT NOT NULL,
    complexity TEXT NOT NULL DEFAULT 'basic',
    project_key TEXT,
    detail TEXT,
    created_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS inbox_items_fts USING fts5(
    raw_input,
    normalized_summary,
    content='inbox_items',
    content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS memory_items_fts USING fts5(
    title,
    summary,
    distilled_knowledge,
    content='memory_items',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS inbox_items_ai AFTER INSERT ON inbox_items BEGIN
    INSERT INTO inbox_items_fts(rowid, raw_input, normalized_summary)
    VALUES (new.id, new.raw_input, new.normalized_summary);
END;

CREATE TRIGGER IF NOT EXISTS inbox_items_ad AFTER DELETE ON inbox_items BEGIN
    INSERT INTO inbox_items_fts(inbox_items_fts, rowid, raw_input, normalized_summary)
    VALUES ('delete', old.id, old.raw_input, old.normalized_summary);
END;

CREATE TRIGGER IF NOT EXISTS inbox_items_au AFTER UPDATE ON inbox_items BEGIN
    INSERT INTO inbox_items_fts(inbox_items_fts, rowid, raw_input, normalized_summary)
    VALUES ('delete', old.id, old.raw_input, old.normalized_summary);
    INSERT INTO inbox_items_fts(rowid, raw_input, normalized_summary)
    VALUES (new.id, new.raw_input, new.normalized_summary);
END;

CREATE TRIGGER IF NOT EXISTS memory_items_ai AFTER INSERT ON memory_items BEGIN
    INSERT INTO memory_items_fts(rowid, title, summary, distilled_knowledge)
    VALUES (new.id, new.title, new.summary, new.distilled_knowledge);
END;

CREATE TRIGGER IF NOT EXISTS memory_items_ad AFTER DELETE ON memory_items BEGIN
    INSERT INTO memory_items_fts(memory_items_fts, rowid, title, summary, distilled_knowledge)
    VALUES ('delete', old.id, old.title, old.summary, old.distilled_knowledge);
END;

CREATE TRIGGER IF NOT EXISTS memory_items_au AFTER UPDATE ON memory_items BEGIN
    INSERT INTO memory_items_fts(memory_items_fts, rowid, title, summary, distilled_knowledge)
    VALUES ('delete', old.id, old.title, old.summary, old.distilled_knowledge);
    INSERT INTO memory_items_fts(rowid, title, summary, distilled_knowledge)
    VALUES (new.id, new.title, new.summary, new.distilled_knowledge);
END;
"""
