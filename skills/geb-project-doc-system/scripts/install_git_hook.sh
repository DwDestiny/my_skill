#!/usr/bin/env bash
# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by skills/geb-project-doc-system/scripts/install_git_hook.sh
# Pos: skills/geb-project-doc-system/scripts/install_git_hook.sh
set -euo pipefail

# 本工具在写入 hook 时插入的标记，用于幂等检测
GEB_HOOK_MARKER="# GEB-HOOK-MANAGED"

repo_dir="${1:-$(pwd)}"
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hook_path="${repo_dir}/.git/hooks/pre-commit"

if [[ ! -d "${repo_dir}/.git" ]]; then
  echo "missing .git directory: ${repo_dir}" >&2
  exit 2
fi

mkdir -p "$(dirname "${hook_path}")"

# 幂等检测：若 hook 已存在，判断是否由本工具生成
if [[ -e "${hook_path}" ]]; then
  if grep -qF "${GEB_HOOK_MARKER}" "${hook_path}" 2>/dev/null; then
    # 本工具已安装过，直接覆盖更新（幂等）
    echo "GEB pre-commit hook 已存在（本工具管理），正在更新: ${hook_path}"
  else
    # 用户自有 hook，备份后拒绝覆盖，提示用户手动合并
    bak_path="${hook_path}.bak"
    cp "${hook_path}" "${bak_path}"
    echo "⚠ 检测到用户已有 pre-commit hook（非本工具生成）：${hook_path}" >&2
    echo "  已备份至: ${bak_path}" >&2
    echo "  请手动将 GEB 审计逻辑合并到 ${hook_path}，或删除后重新运行此脚本。" >&2
    exit 1
  fi
fi

cat >"${hook_path}" <<HOOK
#!/usr/bin/env bash
${GEB_HOOK_MARKER}
set -euo pipefail

python3 "${skill_dir}/scripts/audit_geb_docs.py" "\$(git rev-parse --show-toplevel)"
HOOK

chmod +x "${hook_path}"
echo "installed GEB pre-commit hook: ${hook_path}"
