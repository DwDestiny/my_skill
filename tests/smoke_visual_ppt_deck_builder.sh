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
editability_report="${tmp_dir}/editability_report.json"

negative_assets_dir="${tmp_dir}/assets"
mkdir -p "${negative_assets_dir}"
: > "${negative_assets_dir}/clean-background.png"

negative_spec="${tmp_dir}/missing_visual_draft.json"
negative_report="${tmp_dir}/missing_visual_draft_report.json"
cat > "${negative_spec}" <<'JSON'
{
  "title": "母稿门禁负例",
  "theme": {
    "background": "101820",
    "foreground": "F5F7FA",
    "accent": "23C7F3",
    "accent_2": "F5B84B",
    "muted": "9BA7B6",
    "panel": "17212C",
    "font_face": "Aptos"
  },
  "slides": [
    {
      "layout": "reference_visual_trend",
      "layout_variant": "future_launch_stage",
      "design_director_brief": {
        "expression_system": "full_mock_first",
        "style_intent": "验证缺少整页效果图母稿时必须失败。",
        "typography_system": "大标题、短正文、可编辑图表标签。",
        "color_strategy": "深色底、青色主线、琥珀强调。",
        "chart_language": "中部可编辑柱图和趋势线。",
        "layout_rhythm": "标题、正文、图表、指标互相嵌入。"
      },
      "background_image": "assets/clean-background.png",
      "coordinate_blueprint": {
        "title_zone": {"x": 0.8, "y": 0.5, "w": 5.6, "h": 0.8},
        "text_zone": {"x": 0.8, "y": 1.5, "w": 4.4, "h": 2.8},
        "chart_zone": {"x": 6.1, "y": 1.4, "w": 5.8, "h": 4.3},
        "metrics_zone": {"x": 0.8, "y": 5.4, "w": 5.1, "h": 0.9},
        "protected_empty_zone": {"x": 0.6, "y": 0.4, "w": 12.1, "h": 6.7}
      },
      "title": "必须先有整页母稿",
      "claim": "没有母稿就不能进入可编辑重建。",
      "bullets": [{"title": "先定视觉", "body": "母稿决定色彩、构图和元素关系。"}],
      "metrics": [{"value": "0", "label": "绕过空间"}],
      "chart": {
        "title": "负例门禁",
        "labels": ["母稿", "背景", "重建"],
        "values": [0, 1, 1],
        "source": "本地负例"
      },
      "source": "本地负例"
    }
  ]
}
JSON

if node "${skill_dir}/scripts/validate_deck_quality.js" \
  --spec "${negative_spec}" \
  --report "${negative_report}"; then
  echo "expected missing visual_draft_image validation to fail" >&2
  exit 1
fi
grep -Fq "visual_draft_image" "${negative_report}"

node "${skill_dir}/scripts/validate_deck_quality.js" \
  --spec "${spec}" \
  --report "${qa_report}"

node "${skill_dir}/scripts/build_deck_preview.js" \
  --spec "${spec}" \
  --output-dir "${preview_dir}"

node "${skill_dir}/scripts/build_visual_pptx.js" \
  --spec "${spec}" \
  --output "${deck_output}"

python3 "${skill_dir}/scripts/inspect_pptx_editability.py" \
  --pptx "${deck_output}" \
  --spec "${spec}" \
  --report "${editability_report}"

test -s "${deck_output}"
test -s "${preview_dir}/contact-sheet.svg"

unzip -p "${deck_output}" "ppt/slides/slide*.xml" > "${tmp_dir}/slides.xml"

grep -Fq "AI 视觉 PPT 测试" "${tmp_dir}/slides.xml"
grep -Fq "母稿定审美" "${tmp_dir}/slides.xml"
grep -Fq "关键文字可编辑" "${tmp_dir}/slides.xml"
grep -Fq "用 PPT 形状重建图表" "${tmp_dir}/slides.xml"

echo "ok: visual-ppt-deck-builder smoke test"
