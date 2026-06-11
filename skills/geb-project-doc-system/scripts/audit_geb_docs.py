#!/usr/bin/env python3
# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by skills/geb-project-doc-system/scripts/audit_geb_docs.py
# Pos: skills/geb-project-doc-system/scripts/audit_geb_docs.py
"""Audit a repository for GEB L1/L2/L3 documentation coverage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CODE_EXTENSIONS = {
    ".bash",
    ".c",
    ".cc",
    ".cjs",
    ".cpp",
    ".cs",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".swift",
    ".ts",
    ".tsx",
    ".zsh",
}

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    ".worktrees",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "site-packages",
    "vendor",
    "venv",
}

MAX_FILE_BYTES = 500_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit GEB project documentation coverage.")
    parser.add_argument("project_dir", help="Repository or project directory to audit.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--l2-threshold",
        type=int,
        default=4,
        help="Require a directory guide when a directory has this many direct code files.",
    )
    return parser.parse_args()


def is_code_file(path: Path) -> bool:
    return path.suffix.lower() in CODE_EXTENSIONS and path.is_file()


def iter_code_files(project_dir: Path) -> list[Path]:
    code_files: list[Path] = []
    for path in project_dir.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(project_dir).parts):
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


def has_l1_doc(project_dir: Path) -> bool:
    return (project_dir / "AGENTS.md").exists() or (project_dir / "CLAUDE.md").exists()


def has_l2_doc(directory: Path) -> bool:
    return (directory / "AGENTS.md").exists() or (directory / "CLAUDE.md").exists()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def header_window(content: str) -> str:
    return "\n".join(content.splitlines()[:40])


def has_l3_header(content: str) -> bool:
    window = header_window(content)
    if "GEB-L3" in window:
        return True
    return all(label in window for label in ("Input:", "Output:", "Pos:"))


def has_duplicate_l3_header(content: str) -> bool:
    window = header_window(content)
    if window.count("GEB-L3") > 1:
        return True
    first_lines = window.splitlines()
    input_lines = sum(1 for line in first_lines if "Input:" in line)
    output_lines = sum(1 for line in first_lines if "Output:" in line)
    pos_lines = sum(1 for line in first_lines if "Pos:" in line)
    return input_lines > 1 and output_lines > 1 and pos_lines > 1


def relative_path(project_dir: Path, path: Path) -> str:
    return str(path.relative_to(project_dir))


def add_finding(findings: list[dict[str, str]], code: str, path: str, message: str) -> None:
    findings.append({"code": code, "path": path, "message": message})


def audit(project_dir: Path, l2_threshold: int) -> dict[str, object]:
    project_dir = project_dir.resolve()
    findings: list[dict[str, str]] = []
    code_files = iter_code_files(project_dir)

    if not has_l1_doc(project_dir):
        add_finding(
            findings,
            "missing_l1_doc",
            ".",
            "Project root needs AGENTS.md or CLAUDE.md as the L1 guide.",
        )

    for code_file in code_files:
        content = read_text(code_file)
        path = relative_path(project_dir, code_file)
        if not has_l3_header(content):
            add_finding(
                findings,
                "missing_l3_header",
                path,
                "Source file needs a short Input/Output/Pos L3 header.",
            )
        if has_duplicate_l3_header(content):
            add_finding(
                findings,
                "duplicate_l3_header",
                path,
                "Source file appears to contain duplicate L3 headers.",
            )

    directories = sorted({path.parent for path in code_files if path.parent != project_dir})
    for directory in directories:
        direct_code_count = sum(1 for child in directory.iterdir() if is_code_file(child))
        if direct_code_count >= l2_threshold and not has_l2_doc(directory):
            add_finding(
                findings,
                "missing_l2_doc",
                relative_path(project_dir, directory),
                f"Directory has {direct_code_count} direct source files and needs AGENTS.md or CLAUDE.md.",
            )

    stats = {
        "code_files": len(code_files),
        "findings": len(findings),
        "l2_threshold": l2_threshold,
    }
    return {
        "ok": not findings,
        "project_dir": str(project_dir),
        "stats": stats,
        "findings": findings,
    }


def print_human(report: dict[str, object]) -> None:
    if report["ok"]:
        print("ok: GEB documentation audit passed")
        return
    print("GEB documentation audit failed:")
    for finding in report["findings"]:
        print(f"- [{finding['code']}] {finding['path']}: {finding['message']}")


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)
    if not project_dir.exists() or not project_dir.is_dir():
        print(f"missing project directory: {project_dir}", file=sys.stderr)
        return 2

    report = audit(project_dir, args.l2_threshold)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
