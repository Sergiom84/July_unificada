#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_root/skills"
target_dir="$HOME/.codex/skills"

if [[ ! -d "$source_dir" ]]; then
  echo "No skills directory found at $source_dir" >&2
  exit 1
fi

mkdir -p "$target_dir"

find "$source_dir" -mindepth 1 -maxdepth 1 -type d | while read -r skill_dir; do
  skill_name="$(basename "$skill_dir")"
  rm -rf "$target_dir/$skill_name"
  cp -R "$skill_dir" "$target_dir/$skill_name"
done

echo "Synced Codex skills from $source_dir to $target_dir"
