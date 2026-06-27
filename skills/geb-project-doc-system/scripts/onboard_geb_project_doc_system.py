#!/usr/bin/env python3
# GEB-L3
# Input: local agent directories, selected agents, project candidates, and skill source
# Output: onboarding report plus optional skill links, global prompt snippets, and project hooks
# Pos: skills/geb-project-doc-system/scripts/onboard_geb_project_doc_system.py
"""Guide first-time GEB rollout across local agents and owned projects."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


SNIPPET_START = "<!-- GEB_PROJECT_DOC_SYSTEM_START -->"
SNIPPET_END = "<!-- GEB_PROJECT_DOC_SYSTEM_END -->"
SNIPPET_BODY = """## GEB 项目文档规范

仓库工作默认遵守 GEB 项目文档规范。读文件前按 L1 根文档 -> L2 目录文档 -> L3 文件头渐进披露；写文件时也按 GEB 记录：新项目创建/更新 L1，新目录或模块创建/更新 L2，新源文件、测试、重要配置或长期脚本补短 L3。结构变更后按 L3 -> L2 -> L1 同步更新。初始化、审计、迁移或发现项目文档缺口时，使用 `geb-project-doc-system` Skill。"""

# install_hook 写入的标记行，用于幂等检测
GEB_HOOK_MARKER = "# GEB-HOOK-MANAGED"

EXCLUDED_SCAN_DIRS = {
    ".cache",
    ".git",
    ".next",
    ".venv",
    "__pycache__",
    "cache",
    "coverage",
    "dist",
    "logs",
    "node_modules",
    "runtime",
    "sessions",
    "site",
    "vendor",
    "venv",
}


@dataclass(frozen=True)
class AgentSpec:
    name: str
    skill_dir: str
    global_doc: str
    kind: str = "standard_agent"


STANDARD_AGENTS = [
    AgentSpec("codex", ".codex/skills", ".codex/AGENTS.md"),
    AgentSpec("claude", ".claude/skills", ".claude/CLAUDE.md"),
    AgentSpec("gemini", ".gemini/skills", ".gemini/GEMINI.md"),
    AgentSpec("antigravity", ".antigravity/.agents/skills", ".antigravity/AGENTS.md"),
    AgentSpec("openclaw", ".openclaw/workspace/skills", ".openclaw/workspace/AGENTS.md"),
    AgentSpec("grok", ".grok/skills", ".grok/AGENTS.md"),
]

PLUGIN_RUNTIMES = [
    AgentSpec("agents-runtime", ".agents/skills", ".agents/AGENTS.md", "plugin_runtime"),
    AgentSpec("superpowers", ".config/superpowers/skills", ".config/superpowers/AGENTS.md", "plugin_runtime"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Onboard GEB for local agents and projects.")
    parser.add_argument("--home", default=str(Path.home()), help="Home directory to inspect.")
    parser.add_argument(
        "--skill-source",
        default=str(Path(__file__).resolve().parents[1]),
        help="geb-project-doc-system skill directory to link.",
    )
    parser.add_argument(
        "--agents",
        default="",
        help="Comma-separated selected standard agents, or 'all'. Required before agent writes.",
    )
    parser.add_argument("--project", action="append", default=[], help="Owned project candidate path.")
    parser.add_argument("--scan-root", action="append", default=[], help="Scan root for Git project candidates.")
    parser.add_argument("--scan-depth", type=int, default=3, help="Maximum scan depth for --scan-root.")
    parser.add_argument("--install-hooks", action="store_true", help="Install GEB pre-commit hooks for projects.")
    parser.add_argument("--apply", action="store_true", help="Write selected agent config and project hooks.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def agent_path(home: Path, relative: str) -> Path:
    return home / relative


def has_managed_snippet(path: Path) -> bool:
    return path.exists() and SNIPPET_START in path.read_text(encoding="utf-8", errors="replace")


def detect_agent(home: Path, spec: AgentSpec, skill_name: str) -> dict[str, object]:
    skill_dir = agent_path(home, spec.skill_dir)
    global_doc = agent_path(home, spec.global_doc)
    skill_target = skill_dir / skill_name
    detected = skill_dir.exists() or global_doc.exists()
    managed_snippet_installed = has_managed_snippet(global_doc)
    return {
        "name": spec.name,
        "kind": spec.kind,
        "detected": detected,
        "skill_dir": str(skill_dir),
        "global_doc": str(global_doc),
        "global_doc_exists": global_doc.exists(),
        "skill_installed": skill_target.exists(),
        "managed_snippet_installed": managed_snippet_installed,
        "prompt_review_required": detected and not managed_snippet_installed,
        "needs_skill": detected and not skill_target.exists(),
        "needs_managed_snippet": detected and not managed_snippet_installed,
    }


def selected_agent_names(raw: str, detected_agents: list[dict[str, object]]) -> list[str]:
    if not raw:
        return []
    names = [item.strip() for item in raw.split(",") if item.strip()]
    if names == ["all"]:
        return [str(agent["name"]) for agent in detected_agents if agent["detected"]]
    return names


def upsert_snippet(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    snippet = f"{SNIPPET_START}\n{SNIPPET_BODY}\n{SNIPPET_END}"
    if SNIPPET_START in existing and SNIPPET_END in existing:
        before, rest = existing.split(SNIPPET_START, 1)
        _, after = rest.split(SNIPPET_END, 1)
        updated = f"{before}{snippet}{after}"
    else:
        separator = "\n\n" if existing and not existing.endswith("\n\n") else ""
        updated = f"{existing}{separator}{snippet}\n"
    path.write_text(updated, encoding="utf-8")


def link_skill(skill_source: Path, skill_dir: Path, skill_name: str) -> str:
    """将 skill 链接到 agent skill 目录，幂等处理已有 symlink/目录。

    - 非 symlink 的已有条目：跳过，不动用户文件。
    - 已是 symlink 且指向正确目标：跳过（幂等）。
    - 已是 symlink 但指向其他地方：备份为 .bak，然后重新链接。
    - 不存在：直接创建 symlink。
    """
    skill_dir.mkdir(parents=True, exist_ok=True)
    target = skill_dir / skill_name

    if target.exists() and not target.is_symlink():
        # 普通目录或文件，跳过，不覆盖用户已有内容
        return "skipped_existing_non_symlink"

    if target.is_symlink():
        current_dest = target.resolve()
        expected_dest = skill_source.resolve()
        if current_dest == expected_dest:
            # 已指向正确目标，幂等跳过
            return "already_linked"
        # 指向不同目标，备份后重新链接
        bak = Path(str(target) + ".bak")
        bak.unlink(missing_ok=True)
        target.rename(bak)
        print(f"  ⚠ symlink 原指向 {current_dest}，已备份至 {bak}，重新链接到 {skill_source}", file=sys.stderr)

    target.symlink_to(skill_source)
    return "linked"


def scan_projects(scan_roots: list[str], max_depth: int) -> list[Path]:
    candidates: list[Path] = []
    for raw_root in scan_roots:
        root = Path(raw_root).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            continue
        root_depth = len(root.parts)
        for current, dirs, _files in os.walk(root):
            current_path = Path(current)
            depth = len(current_path.parts) - root_depth
            dirs[:] = [item for item in dirs if item not in EXCLUDED_SCAN_DIRS and not item.endswith(".app")]
            if depth > max_depth:
                dirs[:] = []
                continue
            if (current_path / ".git").is_dir():
                candidates.append(current_path)
                dirs[:] = []
    return sorted(set(candidates))


def classify_project(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    return {
        "path": str(resolved),
        "exists": resolved.exists(),
        "is_git_repo": (resolved / ".git").is_dir(),
        "has_l1": (resolved / "AGENTS.md").exists() or (resolved / "CLAUDE.md").exists(),
        "recommended_action": "confirm_before_digitalization",
    }


def _hook_is_managed(hook_path: Path) -> bool:
    """检测 hook 文件是否由本工具生成（含 GEB_HOOK_MARKER 标记行）。"""
    try:
        return GEB_HOOK_MARKER in hook_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def install_hook(project_dir: Path, skill_source: Path) -> bool:
    """在项目安装 GEB pre-commit hook，幂等且不破坏用户已有 hook。

    - hook 不存在：直接写入。
    - hook 存在且含本工具标记：更新（幂等）。
    - hook 存在但非本工具生成：备份为 .bak，打印警告，跳过写入，返回 False。
    """
    git_dir = project_dir / ".git"
    if not git_dir.is_dir():
        return False
    hook_path = git_dir / "hooks" / "pre-commit"
    hook_path.parent.mkdir(parents=True, exist_ok=True)

    if hook_path.exists():
        if not _hook_is_managed(hook_path):
            # 用户自有 hook，备份后拒绝覆盖
            bak_path = Path(str(hook_path) + ".bak")
            try:
                import shutil
                shutil.copy2(str(hook_path), str(bak_path))
            except OSError as exc:
                print(
                    f"  ✗ 无法备份已有 hook {hook_path}: {exc}，跳过安装。",
                    file=sys.stderr,
                )
                return False
            print(
                f"  ⚠ {hook_path} 已存在且非本工具生成，已备份至 {bak_path}。\n"
                f"    请手动将 GEB 审计逻辑合并，或删除后重新运行。",
                file=sys.stderr,
            )
            return False
        # 本工具已管理，允许更新（幂等）

    audit_script = skill_source / "scripts" / "audit_geb_docs.py"
    hook_path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                GEB_HOOK_MARKER,
                "set -euo pipefail",
                f'python3 "{audit_script}" "$(git rev-parse --show-toplevel)"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    hook_path.chmod(0o755)
    return True


def build_report(args: argparse.Namespace) -> dict[str, object]:
    home = Path(args.home).expanduser().resolve()
    skill_source = Path(args.skill_source).expanduser().resolve()
    skill_name = skill_source.name

    detected_agents = [detect_agent(home, spec, skill_name) for spec in STANDARD_AGENTS]
    plugin_runtimes = [detect_agent(home, spec, skill_name) for spec in PLUGIN_RUNTIMES]
    selected_names = selected_agent_names(args.agents, detected_agents)
    known_specs = {spec.name: spec for spec in STANDARD_AGENTS}

    configured_agents: list[str] = []
    agent_actions: list[dict[str, str]] = []
    if args.apply:
        for name in selected_names:
            spec = known_specs.get(name)
            if spec is None:
                agent_actions.append({"name": name, "status": "unknown_agent"})
                continue
            skill_status = link_skill(skill_source, agent_path(home, spec.skill_dir), skill_name)
            global_doc = agent_path(home, spec.global_doc)
            if not has_managed_snippet(global_doc):
                upsert_snippet(global_doc)
            configured_agents.append(name)
            agent_actions.append({"name": name, "status": skill_status})

    project_paths = [Path(item) for item in args.project]
    project_paths.extend(scan_projects(args.scan_root, args.scan_depth))
    project_candidates = [classify_project(path) for path in sorted(set(project_paths))]

    configured_hooks: list[str] = []
    hook_actions: list[dict[str, str]] = []
    if args.apply and args.install_hooks:
        for candidate in project_candidates:
            project_path = Path(str(candidate["path"]))
            ok = install_hook(project_path, skill_source)
            if ok:
                configured_hooks.append(str(project_path))
                hook_actions.append({"path": str(project_path), "status": "installed"})
            else:
                # 区分 missing_git_dir 与 existing_hook_skipped
                git_present = (project_path / ".git").is_dir()
                status = "existing_hook_skipped" if git_present else "missing_git_dir"
                hook_actions.append({"path": str(project_path), "status": status})

    next_steps: list[str] = []
    if project_candidates:
        paths = ", ".join(str(item["path"]) for item in project_candidates)
        next_steps.append(f"Review and confirm project candidate list before digitalization: {paths}")
    if not selected_names:
        next_steps.append("Select standard agents with --agents codex,claude,gemini,antigravity,openclaw or --agents all.")
    if selected_names and not args.apply:
        next_steps.append("Rerun with --apply after reviewing selected agents.")
    if project_candidates and not args.install_hooks:
        next_steps.append("Use --install-hooks --apply after confirming project hook scope.")

    return {
        "ok": True,
        "dry_run": not args.apply,
        "requires_user_selection": not selected_names,
        "detected_agents": detected_agents,
        "plugin_runtimes": plugin_runtimes,
        "selected_agents": selected_names,
        "configured_agents": configured_agents,
        "agent_actions": agent_actions,
        "project_candidates": project_candidates,
        "configured_hooks": configured_hooks,
        "hook_actions": hook_actions,
        "next_steps": next_steps,
    }


def print_human(report: dict[str, object]) -> None:
    mode = "dry-run" if report["dry_run"] else "apply"
    print(f"GEB onboarding report ({mode})")
    print("\nDetected standard agents:")
    for agent in report["detected_agents"]:
        if not agent["detected"]:
            continue
        print(
            f"- {agent['name']}: skill_installed={agent['skill_installed']} "
            f"managed_snippet_installed={agent['managed_snippet_installed']} "
            f"prompt_review_required={agent['prompt_review_required']}"
        )
    if report["plugin_runtimes"]:
        print("\nPlugin/capability runtimes are listed separately and are not standard agents.")
    if report["project_candidates"]:
        print("\nProject candidate list:")
        for project in report["project_candidates"]:
            print(f"- {project['path']} git={project['is_git_repo']} l1={project['has_l1']}")
    if report["next_steps"]:
        print("\nNext steps:")
        for step in report["next_steps"]:
            print(f"- {step}")


def main() -> int:
    args = parse_args()
    skill_source = Path(args.skill_source).expanduser().resolve()
    if not (skill_source / "SKILL.md").is_file():
        print(f"missing skill source: {skill_source}", file=sys.stderr)
        return 2
    report = build_report(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
