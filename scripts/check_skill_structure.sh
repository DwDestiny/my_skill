#!/usr/bin/env bash
set -euo pipefail

skill_dir="${1:-}"

if [[ -z "${skill_dir}" ]]; then
  echo "usage: scripts/check_skill_structure.sh <skill-dir>" >&2
  exit 2
fi

if [[ ! -d "${skill_dir}" ]]; then
  echo "missing skill dir: ${skill_dir}" >&2
  exit 1
fi

skill_name="$(basename "${skill_dir}")"
skill_md="${skill_dir}/SKILL.md"
agent_yaml="${skill_dir}/agents/openai.yaml"

if [[ ! -f "${skill_md}" ]]; then
  echo "missing SKILL.md: ${skill_md}" >&2
  exit 1
fi

if ! sed -n '1,12p' "${skill_md}" | grep -q '^name: '; then
  echo "missing frontmatter name in ${skill_md}" >&2
  exit 1
fi

if ! sed -n '1,16p' "${skill_md}" | grep -q '^description: '; then
  echo "missing frontmatter description in ${skill_md}" >&2
  exit 1
fi

if ! sed -n '1,12p' "${skill_md}" | grep -q "^name: ${skill_name}$"; then
  echo "frontmatter name must match directory name: ${skill_name}" >&2
  exit 1
fi

if [[ ! -f "${agent_yaml}" ]]; then
  echo "missing agents/openai.yaml: ${agent_yaml}" >&2
  exit 1
fi

if ! grep -Fq "\$${skill_name}" "${agent_yaml}"; then
  echo "agents/openai.yaml default prompt should mention \$${skill_name}" >&2
  exit 1
fi

if [[ ! -d "${skill_dir}/references" ]]; then
  echo "missing references directory: ${skill_dir}/references" >&2
  exit 1
fi

if [[ ! -d "${skill_dir}/scripts" ]]; then
  echo "missing scripts directory: ${skill_dir}/scripts" >&2
  exit 1
fi

if ! grep -q "| ${skill_name} |" README.md; then
  echo "README Skill catalog is missing ${skill_name}" >&2
  exit 1
fi

if grep -RInE 'TODO|TBD|占位' "${skill_md}" "${agent_yaml}" >/dev/null; then
  echo "placeholder text found in core skill files" >&2
  exit 1
fi

echo "ok: ${skill_name}"
