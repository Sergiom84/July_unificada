from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


@dataclass(slots=True)
class SkillReferenceDraft:
    skill_name: str
    display_name: str
    description: str
    source_path: str
    trigger_text: str


def load_skill_reference(path: str | Path) -> SkillReferenceDraft:
    source = Path(path).expanduser()
    if not source.exists():
        raise ValueError(f"Skill path not found: {source}")

    skill_md = _read_skill_markdown(source)
    metadata, body = _split_frontmatter(skill_md)
    skill_name = metadata.get("name") or source.stem
    description = metadata.get("description") or first_non_empty_line(body)
    if not description:
        raise ValueError(f"Skill has no description: {source}")

    return SkillReferenceDraft(
        skill_name=skill_name.strip(),
        display_name=skill_name.strip(),
        description=description.strip(),
        source_path=str(source),
        trigger_text=build_trigger_text(description, body),
    )


def build_trigger_text(description: str, body: str) -> str:
    text = f"{description}\n\n{body}".strip()
    return re.sub(r"\s+", " ", text)[:8000]


def first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def _read_skill_markdown(source: Path) -> str:
    if source.is_dir():
        skill_file = source / "SKILL.md"
        if not skill_file.exists():
            raise ValueError(f"Directory does not contain SKILL.md: {source}")
        return skill_file.read_text(encoding="utf-8")

    if source.name.lower() == "skill.md":
        return source.read_text(encoding="utf-8")

    if source.suffix.lower() == ".skill":
        with zipfile.ZipFile(source) as archive:
            candidates = [
                name for name in archive.namelist()
                if name.replace("\\", "/").endswith("/SKILL.md") or name == "SKILL.md"
            ]
            if not candidates:
                raise ValueError(f".skill archive does not contain SKILL.md: {source}")
            with archive.open(sorted(candidates, key=len)[0]) as skill_file:
                return skill_file.read().decode("utf-8")

    raise ValueError(f"Unsupported skill path. Use a .skill file, skill folder, or SKILL.md: {source}")


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    metadata: dict[str, str] = {}
    lines = match.group(1).splitlines()
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            index += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in {">", "|", ">-", "|-", ">+", "|+"}:
            block_lines = []
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line.strip() and not next_line[:1].isspace():
                    break
                block_lines.append(next_line.strip())
                index += 1
            if value.startswith("|"):
                metadata[key] = "\n".join(block_lines).strip()
            else:
                metadata[key] = " ".join(line for line in block_lines if line).strip()
            continue
        metadata[key] = value.strip('"').strip("'")
        index += 1

    return metadata, text[match.end():]
