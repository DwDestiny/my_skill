#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill_dir="${repo_root}/skills/visual-ppt-deck-builder"
spec="${repo_root}/tests/fixtures/visual_ppt_smoke_deck.json"
tmp_dir="$(mktemp -d)"

cleanup() {
  rm -rf "${tmp_dir}"
}
trap cleanup EXIT

qa_report="${tmp_dir}/qa_report.json"
preview_dir="${tmp_dir}/preview"
deck_output="${tmp_dir}/final_deck.pptx"

node "${skill_dir}/scripts/validate_deck_quality.js" \
  --spec "${spec}" \
  --report "${qa_report}"

node "${skill_dir}/scripts/build_deck_preview.js" \
  --spec "${spec}" \
  --output-dir "${preview_dir}"

node "${skill_dir}/scripts/build_visual_pptx.js" \
  --spec "${spec}" \
  --output "${deck_output}"

test -s "${deck_output}"
test -s "${preview_dir}/contact-sheet.svg"

unzip -p "${deck_output}" "ppt/slides/slide*.xml" > "${tmp_dir}/slides.xml"

grep -Fq "AI 视觉 PPT 测试" "${tmp_dir}/slides.xml"
grep -Fq "母稿定审美" "${tmp_dir}/slides.xml"
grep -Fq "关键文字可编辑" "${tmp_dir}/slides.xml"
grep -Fq "用 PPT 形状重建图表" "${tmp_dir}/slides.xml"

echo "ok: visual-ppt-deck-builder smoke test"
