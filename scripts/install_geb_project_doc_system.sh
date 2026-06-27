#!/usr/bin/env bash
# GEB-L3
# Input: local my_skill checkout and selected onboarding arguments
# Output: delegated GEB onboarding report plus optional selected writes
# Pos: scripts/install_geb_project_doc_system.sh
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill_name="geb-project-doc-system"
skill_source="${repo_root}/skills/${skill_name}"
onboard_script="${skill_source}/scripts/onboard_geb_project_doc_system.py"

if [[ ! -d "${skill_source}" ]]; then
  echo "missing skill source: ${skill_source}" >&2
  exit 2
fi

if [[ ! -f "${onboard_script}" ]]; then
  echo "missing onboarding script: ${onboard_script}" >&2
  exit 2
fi

args=()
json_mode="false"
for arg in "$@"; do
  # Backward compatible dry-run spelling. The onboarding script is dry-run by
  # default: no writes without --apply.
  if [[ "${arg}" == "--dry-run" ]]; then
    continue
  fi
  if [[ "${arg}" == "--json" ]]; then
    json_mode="true"
  fi
  args+=("${arg}")
done

if [[ "${json_mode}" != "true" ]]; then
cat <<'EOF'
Onboarding flow:
1. Run onboard_geb_project_doc_system.py to list detected agents.
2. Choose which agent entries to configure; standard agents only.
3. Keep plugin runtimes separately; they are not standard agents.
4. Use --apply only after review. There are no writes without --apply.
5. Confirm the project candidate list before installing any pre-commit hook.
6. Finish with an acceptance report and estimated token savings.

Write-side Contract:
1. For a new project, create or update the L1 root guide.
2. For a new or expanded module, create or update the L2 folder guide.
3. For a new source file, test, important config, or durable script, add a short L3 header.
4. Documentation is part of the change; update L3 -> L2 -> L1 before acceptance.

First-run bootstrap:
1. Run a first-run inventory before writing headers.
2. Classify targets as project repositories, Agent runtime, active sessions, or archives.
3. Pick one small sample project first, then expand module by module.
4. Keep secrets, sessions, logs, caches, worktrees, generated output, browser profiles, and databases out of bulk L3 updates.

EOF
fi

exec python3 "${onboard_script}" --skill-source "${skill_source}" "${args[@]}"
