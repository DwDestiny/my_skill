#!/usr/bin/env python3
# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by skills/geb-project-doc-system/scripts/update_file_headers.py
# Pos: skills/geb-project-doc-system/scripts/update_file_headers.py
"""Insert short, idempotent GEB L3 headers into source files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from audit_geb_docs import CODE_EXTENSIONS, MAX_FILE_BYTES, has_l3_header, should_skip_path


HASH_COMMENT_EXTENSIONS = {".bash", ".py", ".rb", ".sh", ".zsh"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add missing GEB L3 file headers.")
    parser.add_argument("project_dir", help="Repository or project directory to update.")
    parser.add_argument("--apply", action="store_true", help="Write changes. Default is dry-run.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def is_code_file(path: Path) -> bool:
    return path.suffix.lower() in CODE_EXTENSIONS and path.is_file()


def iter_code_files(project_dir: Path) -> list[Path]:
    code_files: list[Path] = []
    for path in project_dir.rglob("*"):
        if should_skip_path(project_dir, path):
            continue
        if not is_code_file(path):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        code_files.append(path)
    return sorted(code_files)


def comment_prefix(path: Path) -> str:
    return "# " if path.suffix.lower() in HASH_COMMENT_EXTENSIONS else "// "


def build_header(project_dir: Path, path: Path) -> str:
    relative = path.relative_to(project_dir)
    prefix = comment_prefix(path)
    return "\n".join(
        [
            f"{prefix}GEB-L3",
            f"{prefix}Input: caller, project conventions, and local dependencies",
            f"{prefix}Output: behavior defined by {relative}",
            f"{prefix}Pos: {relative}",
            "",
        ]
    )


def insertion_index(lines: list[str]) -> int:
    index = 0
    if lines and lines[0].startswith("#!"):
        index = 1
    if len(lines) > index and "coding" in lines[index] and lines[index].lstrip().startswith("#"):
        index += 1
    while len(lines) > index and not lines[index].strip():
        index += 1
    return index


def insert_header(content: str, header: str) -> str:
    lines = content.splitlines()
    index = insertion_index(lines)
    new_lines = lines[:index] + header.splitlines() + lines[index:]
    return "\n".join(new_lines) + ("\n" if content.endswith("\n") else "")


def update(project_dir: Path, apply: bool) -> dict[str, object]:
    project_dir = project_dir.resolve()
    planned_files: list[str] = []
    applied_files: list[str] = []

    for code_file in iter_code_files(project_dir):
        content = code_file.read_text(encoding="utf-8", errors="replace")
        if has_l3_header(content):
            continue
        relative = str(code_file.relative_to(project_dir))
        planned_files.append(relative)
        if apply:
            updated = insert_header(content, build_header(project_dir, code_file))
            code_file.write_text(updated, encoding="utf-8")
            applied_files.append(relative)

    return {
        "ok": True,
        "project_dir": str(project_dir),
        "dry_run": not apply,
        "planned_updates": len(planned_files),
        "applied_updates": len(applied_files),
        "planned_files": planned_files,
        "applied_files": applied_files,
    }


def print_human(report: dict[str, object]) -> None:
    action = "would update" if report["dry_run"] else "updated"
    print(f"{action}: {report['planned_updates']} files")
    for path in report["planned_files"]:
        print(f"- {path}")


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)
    if not project_dir.exists() or not project_dir.is_dir():
        print(f"missing project directory: {project_dir}", file=sys.stderr)
        return 2
    report = update(project_dir, args.apply)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
