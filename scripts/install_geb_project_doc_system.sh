#!/usr/bin/env bash
# GEB-L3
# Input: local my_skill checkout and agent config directories
# Output: geb-project-doc-system symlinks plus optional global trigger snippets
# Pos: scripts/install_geb_project_doc_system.sh
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill_name="geb-project-doc-system"
skill_source="${repo_root}/skills/${skill_name}"
dry_run="false"

if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run="true"
fi

if [[ ! -d "${skill_source}" ]]; then
  echo "missing skill source: ${skill_source}" >&2
  exit 2
fi

skill_dirs=(
  "${HOME}/.codex/skills"
  "${HOME}/.agents/skills"
  "${HOME}/.claude/skills"
  "${HOME}/.grok/skills"
  "${HOME}/.config/opencode/skills"
  "${HOME}/.config/goose/skills"
  "${HOME}/.cursor/skills"
  "${HOME}/.gemini/skills"
  "${HOME}/.gemini/config/skills"
  "${HOME}/.gemini/antigravity/skills"
  "${HOME}/.gemini/antigravity-ide/skills"
  "${HOME}/.trae/skills"
  "${HOME}/.antigravity/.agents/skills"
  "${HOME}/.hermes/skills"
  "${HOME}/.hermes/hermes-agent/skills"
  "${HOME}/.openclaw/skills"
  "${HOME}/.openclaw/workspace/skills"
  "${HOME}/.amp/skills"
  "${HOME}/.kiro/skills"
)

global_docs=(
  "${HOME}/.codex/AGENTS.md"
  "${HOME}/.claude/CLAUDE.md"
  "${HOME}/.grok/AGENTS.md"
  "${HOME}/.antigravity/AGENTS.md"
  "${HOME}/.hermes/hermes-agent/AGENTS.md"
  "${HOME}/AGENTS.md"
)

snippet_start="<!-- GEB_PROJECT_DOC_SYSTEM_START -->"
snippet_end="<!-- GEB_PROJECT_DOC_SYSTEM_END -->"
snippet_body='## GEB 项目文档规范

仓库工作默认遵守 GEB 项目文档规范。结构变更前读取 L1 根文档、L2 目录文档和目标文件 L3 文件头；结构变更后按 L3 -> L2 -> L1 同步更新。初始化、审计、迁移或发现项目文档缺口时，使用 `geb-project-doc-system` Skill。'

install_skill() {
  local target_dir="$1"
  local target_path="${target_dir}/${skill_name}"

  [[ -d "${target_dir}" ]] || return 0

  if [[ -e "${target_path}" && ! -L "${target_path}" ]]; then
    echo "skip existing non-symlink: ${target_path}"
    return 0
  fi

  if [[ "${dry_run}" == "true" ]]; then
    echo "would link: ${target_path} -> ${skill_source}"
  else
    ln -sfn "${skill_source}" "${target_path}"
    echo "linked: ${target_path} -> ${skill_source}"
  fi
}

install_snippet() {
  local doc_path="$1"
  [[ -f "${doc_path}" ]] || return 0

  if grep -Fq "${snippet_start}" "${doc_path}"; then
    echo "snippet exists: ${doc_path}"
    return 0
  fi

  if [[ "${dry_run}" == "true" ]]; then
    echo "would append trigger snippet: ${doc_path}"
  else
    {
      printf '\n%s\n' "${snippet_start}"
      printf '%s\n' "${snippet_body}"
      printf '%s\n' "${snippet_end}"
    } >>"${doc_path}"
    echo "appended trigger snippet: ${doc_path}"
  fi
}

for skill_dir in "${skill_dirs[@]}"; do
  install_skill "${skill_dir}"
done

for global_doc in "${global_docs[@]}"; do
  install_snippet "${global_doc}"
done

cat <<'EOF'

First-run bootstrap:
1. Run a first-run inventory before writing headers.
2. Classify targets as project repositories, Agent runtime, active sessions, or archives.
3. Pick one small sample project first, then expand module by module.
4. Keep secrets, sessions, logs, caches, worktrees, generated output, browser profiles, and databases out of bulk L3 updates.

Suggested next step:
python3 skills/geb-project-doc-system/scripts/audit_geb_docs.py /path/to/repo --json
EOF
