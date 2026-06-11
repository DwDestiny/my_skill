#!/usr/bin/env bash
# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by skills/geb-project-doc-system/scripts/install_git_hook.sh
# Pos: skills/geb-project-doc-system/scripts/install_git_hook.sh
set -euo pipefail

repo_dir="${1:-$(pwd)}"
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hook_path="${repo_dir}/.git/hooks/pre-commit"

if [[ ! -d "${repo_dir}/.git" ]]; then
  echo "missing .git directory: ${repo_dir}" >&2
  exit 2
fi

mkdir -p "$(dirname "${hook_path}")"
cat >"${hook_path}" <<HOOK
#!/usr/bin/env bash
set -euo pipefail

python3 "${skill_dir}/scripts/audit_geb_docs.py" "\$(git rev-parse --show-toplevel)"
HOOK

chmod +x "${hook_path}"
echo "installed GEB pre-commit hook: ${hook_path}"
