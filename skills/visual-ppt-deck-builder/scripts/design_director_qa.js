#!/usr/bin/env node

// GEB-L3
// Input: caller, project conventions, and local dependencies
// Output: behavior defined by skills/visual-ppt-deck-builder/scripts/design_director_qa.js
// Pos: skills/visual-ppt-deck-builder/scripts/design_director_qa.js
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const slide_cx = 12191695;
const slide_cy = 6858000;

const design_brief_defaults = {
  boardroom_summary_matrix: {
    expression_system: "boardroom_report_matrix",
    style_intent: "董事会汇报感，用克制留白、建筑背景和矩阵证明对象承载经营判断。",
    title_anchor: "左上董事会报告标题",
    body_pattern: "底部三段洞察简报",
    proof_object: "右侧象限矩阵证明对象",
    metric_pattern: "左侧纵向 KPI 梯子",
    typography_system: "粗标题 + 小号正文 + 克制数字层级",
    color_strategy: "近黑正文、青绿色强调、金色辅助，保持轻商务可信感。",
    chart_language: "象限矩阵、点位、低透明细线",
    layout_rhythm: "左侧结论，右侧证明，底部洞察收束",
  },
  future_launch_stage: {
    expression_system: "tech_launch_stage",
    style_intent: "科技发布会感，用中央舞台柱图、光轨和右侧遥测数据制造发布节奏。",
    title_anchor: "左上发布会标题",
    body_pattern: "底部横向遥测 ticker",
    proof_object: "中央发射台柱状证明对象",
    metric_pattern: "右侧遥测数据栈",
    typography_system: "大标题 + 高亮数字 + 短句 ticker",
    color_strategy: "深蓝底、青蓝主色、紫色辅助，保证科技感与可读性。",
    chart_language: "中央发光柱图、顶部数值、弱化坐标",
    layout_rhythm: "上方定题，中部证明，右侧指标，底部进度流",
  },
  oriental_scroll_narrative: {
    expression_system: "oriental_scroll_narrative",
    style_intent: "东方文化提案感，用宣纸留白、题签标题、卷轴分栏和路径线形成叙事。",
    title_anchor: "右上横排题签",
    body_pattern: "左侧卷轴式三段叙事",
    proof_object: "底部路径时间线证明对象",
    metric_pattern: "右侧印章式指标",
    typography_system: "宋体标题 + 分栏短文 + 低噪声脚注",
    color_strategy: "墨黑、朱红、金色与宣纸底色协同，避免现代科技色干扰。",
    chart_language: "路径线、节点、题签式标签",
    layout_rhythm: "左文右景，底部证明线，右侧指标像印章落点",
  },
  editorial_feature_spread: {
    expression_system: "editorial_feature_spread",
    style_intent: "杂志专题页感，用大标题、专题短文、横向条形叙事图和引用式指标讲观点。",
    title_anchor: "左上杂志头版标题",
    body_pattern: "左侧专题短文",
    proof_object: "右上横向条形叙事图",
    metric_pattern: "右下 pull-quote 指标",
    typography_system: "强标题 + 编辑编号 + 短段落正文",
    color_strategy: "暗色纸感背景、酒红强调、米金辅助，保持编辑感和高级感。",
    chart_language: "横向条形叙事图、短标签、右侧数值",
    layout_rhythm: "左侧观点，右上证据，右下指标引用",
  },
};

function parse_args(argv) {
  const args = {};
  for (let index = 2; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--sample-dir") {
      args.sample_dir = argv[index + 1];
      index += 1;
    } else if (token === "--report") {
      args.report = argv[index + 1];
      index += 1;
    } else if (token === "--help" || token === "-h") {
      args.help = true;
    } else {
      throw new Error(`unknown argument: ${token}`);
    }
  }
  return args;
}

function usage() {
  return [
    "Usage:",
    "  node design_director_qa.js --sample-dir /absolute/path/multi-style-samples --report /absolute/path/design-director-qa.json",
  ].join("\n");
}

function fail(message) {
  console.error(message);
  process.exit(1);
}

function read_json(file_path) {
  return JSON.parse(fs.readFileSync(file_path, "utf8"));
}

function normalize_color(value) {
  return String(value || "").replace(/^#/, "").trim().toUpperCase();
}

function is_hex_color(value) {
  return /^[0-9A-F]{6}$/.test(normalize_color(value));
}

function clamp_score(value) {
  return Math.max(0, Math.min(1, Number(value.toFixed(2))));
}

function list_specs(sample_dir) {
  const specs_dir = path.join(sample_dir, "specs");
  if (!fs.existsSync(specs_dir)) {
    throw new Error(`missing specs directory: ${specs_dir}`);
  }
  return fs
    .readdirSync(specs_dir)
    .filter((file_name) => file_name.endsWith(".json"))
    .sort()
    .map((file_name) => path.join(specs_dir, file_name));
}

function resolve_background(spec_path, slide) {
  if (!slide.background_image) return "";
  if (path.isAbsolute(slide.background_image)) return slide.background_image;
  return path.resolve(path.dirname(spec_path), slide.background_image);
}

function read_slide_xml(pptx_path) {
  if (!fs.existsSync(pptx_path)) return "";
  const result = spawnSync("unzip", ["-p", pptx_path, "ppt/slides/slide1.xml"], {
    encoding: "utf8",
  });
  if (result.status !== 0) return "";
  return result.stdout || "";
}

function shape_text(shape_xml) {
  const matches = [...shape_xml.matchAll(/<a:t>(.*?)<\/a:t>/gs)];
  return matches.map((match) => match[1]).join("");
}

function text_shape_anchor(slide_xml, needle) {
  if (!needle) return null;
  const shapes = [...slide_xml.matchAll(/<p:sp>.*?<\/p:sp>/gs)];
  for (const shape of shapes) {
    const shape_xml = shape[0];
    if (!shape_text(shape_xml).includes(needle)) continue;
    const match = shape_xml.match(/<a:off x="(-?\d+)" y="(-?\d+)"\/>/);
    if (!match) continue;
    return { x: Number(match[1]), y: Number(match[2]) };
  }
  return null;
}

function quadrant(anchor) {
  if (!anchor) return "missing";
  const x_ratio = anchor.x / slide_cx;
  const y_ratio = anchor.y / slide_cy;
  const x_bucket = x_ratio < 0.33 ? "left" : x_ratio < 0.66 ? "middle" : "right";
  const y_bucket = y_ratio < 0.33 ? "top" : y_ratio < 0.66 ? "middle" : "bottom";
  return `${y_bucket}_${x_bucket}`;
}

function role_signature(slide_xml, slide) {
  const title_anchor = text_shape_anchor(slide_xml, slide.title);
  const body_anchor = text_shape_anchor(slide_xml, slide.bullets?.[0]?.title || "");
  const metric_anchor = text_shape_anchor(slide_xml, slide.metrics?.[0]?.value || "");
  const proof_anchor = text_shape_anchor(slide_xml, slide.chart?.title || "");
  const role_quadrants = {
    title: quadrant(title_anchor),
    body: quadrant(body_anchor),
    metric: quadrant(metric_anchor),
    proof: quadrant(proof_anchor),
  };
  return {
    anchors: {
      title: title_anchor,
      body: body_anchor,
      metric: metric_anchor,
      proof: proof_anchor,
    },
    role_quadrants,
    role_signature: [
      role_quadrants.title,
      role_quadrants.body,
      role_quadrants.metric,
      role_quadrants.proof,
    ].join("|"),
  };
}

function overlay_style(slide) {
  return slide.overlay_style || {};
}

function palette_is_valid(theme, overlay) {
  const colors = [
    theme?.background,
    theme?.foreground,
    theme?.accent,
    theme?.accent_2,
    theme?.muted,
    overlay.subtitle_color,
    overlay.bullet_title_color,
    overlay.bullet_body_color,
    overlay.chart_title_color,
    overlay.chart_label_color,
    overlay.chart_value_color,
  ].filter(Boolean);
  const palette = Array.isArray(overlay.chart_bar_colors) ? colors.concat(overlay.chart_bar_colors) : colors;
  return palette.length >= 5 && palette.every(is_hex_color);
}

function typography_is_valid(theme, overlay) {
  const numeric_keys = [
    "title_font_size",
    "subtitle_font_size",
    "bullet_title_font_size",
    "bullet_body_font_size",
    "metric_value_font_size",
    "metric_label_font_size",
    "chart_title_font_size",
    "chart_label_font_size",
    "chart_value_font_size",
  ];
  const has_font = Boolean(theme?.font_face);
  const sizes = numeric_keys.map((key) => overlay[key]).filter((value) => value !== undefined);
  const valid_sizes = sizes.every((value) => Number(value) >= 4 && Number(value) <= 44);
  return has_font && sizes.length >= 6 && valid_sizes;
}

function brief_value(slide, layout_variant) {
  const explicit = slide.design_director_brief || {};
  const defaults = design_brief_defaults[layout_variant] || {};
  return { ...defaults, ...explicit };
}

function score_consistency(brief, theme, overlay, role_data) {
  let score = 0;
  const required_brief_keys = [
    "expression_system",
    "style_intent",
    "typography_system",
    "color_strategy",
    "chart_language",
    "layout_rhythm",
  ];
  if (required_brief_keys.every((key) => Boolean(brief[key]))) score += 0.32;
  if (typography_is_valid(theme, overlay)) score += 0.24;
  if (palette_is_valid(theme, overlay)) score += 0.2;
  if (Object.values(role_data.anchors).every(Boolean)) score += 0.24;
  return clamp_score(score);
}

function score_harmony(background_path, slide_xml, slide, overlay) {
  let score = 0;
  if (background_path && fs.existsSync(background_path) && fs.statSync(background_path).size > 1000) score += 0.24;
  if (!slide_xml.includes('prst="roundRect"')) score += 0.22;
  if (slide.coordinate_blueprint && Object.keys(slide.coordinate_blueprint).length >= 5) score += 0.18;
  if (Array.isArray(overlay.chart_bar_colors) && overlay.chart_bar_colors.length >= 4) score += 0.18;
  if (slide_xml.includes("<a:t>") && slide_xml.includes("<p:sp>")) score += 0.18;
  return clamp_score(score);
}

function build_item(sample_dir, spec_path) {
  const slug = path.basename(spec_path, ".json");
  const spec = read_json(spec_path);
  const slide = spec.slides?.[0] || {};
  const theme = spec.theme || {};
  const layout_variant = String(slide.layout_variant || "").trim();
  const brief = brief_value(slide, layout_variant);
  const pptx_path = path.join(sample_dir, "pptx", `${slug}.pptx`);
  const background_path = resolve_background(spec_path, slide);
  const slide_xml = read_slide_xml(pptx_path);
  const role_data = role_signature(slide_xml, slide);
  const overlay = overlay_style(slide);
  const consistency_score = score_consistency(brief, theme, overlay, role_data);
  const harmony_score = score_harmony(background_path, slide_xml, slide, overlay);
  const diversity_signature = [
    brief.expression_system || layout_variant,
    brief.title_anchor || "unknown_title_anchor",
    brief.body_pattern || "unknown_body_pattern",
    brief.proof_object || "unknown_proof_object",
    brief.metric_pattern || "unknown_metric_pattern",
    role_data.role_signature,
  ].join("::");
  const item_errors = [];
  if (consistency_score < 0.8) item_errors.push("consistency_score below 0.8");
  if (harmony_score < 0.8) item_errors.push("harmony_score below 0.8");
  if (!brief.expression_system) item_errors.push("missing expression_system");
  if (!fs.existsSync(pptx_path)) item_errors.push("missing pptx sample");
  if (!background_path || !fs.existsSync(background_path)) item_errors.push("missing raster background");
  return {
    slug,
    layout_variant,
    expression_system: brief.expression_system || layout_variant,
    style_intent: brief.style_intent || "",
    title_anchor: brief.title_anchor || "",
    body_pattern: brief.body_pattern || "",
    proof_object: brief.proof_object || "",
    metric_pattern: brief.metric_pattern || "",
    typography_system: brief.typography_system || "",
    color_strategy: brief.color_strategy || "",
    chart_language: brief.chart_language || "",
    layout_rhythm: brief.layout_rhythm || "",
    main_visual_source: "raster_background",
    pptx_path,
    background_path,
    consistency_score,
    harmony_score,
    diversity_signature,
    role_signature: role_data.role_signature,
    role_quadrants: role_data.role_quadrants,
    editable_text_run_count: (slide_xml.match(/<a:t>/g) || []).length,
    round_rect_count: (slide_xml.match(/prst="roundRect"/g) || []).length,
    status: item_errors.length === 0 ? "pass" : "fail",
    errors: item_errors,
  };
}

function build_report(sample_dir) {
  const spec_paths = list_specs(sample_dir);
  const items = spec_paths.map((spec_path) => build_item(sample_dir, spec_path));
  const expression_systems = new Set(items.map((item) => item.expression_system));
  const diversity_signatures = new Set(items.map((item) => item.diversity_signature));
  const errors = [];
  items.forEach((item) => {
    item.errors.forEach((error) => errors.push(`${item.slug}: ${error}`));
  });
  if (diversity_signatures.size < items.length) {
    errors.push("diversity signatures must be unique across style samples");
  }
  if (expression_systems.size < Math.min(items.length, 4)) {
    errors.push("expression systems must be diverse across style samples");
  }
  return {
    ok: errors.length === 0,
    gate: "design director QA: consistency, harmony, diversity",
    sample_count: items.length,
    failed_count: items.filter((item) => item.status !== "pass").length,
    unique_expression_system_count: expression_systems.size,
    unique_diversity_signature_count: diversity_signatures.size,
    min_consistency_score: items.length ? Math.min(...items.map((item) => item.consistency_score)) : 0,
    min_harmony_score: items.length ? Math.min(...items.map((item) => item.harmony_score)) : 0,
    errors,
    items,
  };
}

function write_report(report_path, report) {
  const output = JSON.stringify(report, null, 2);
  if (report_path) {
    const absolute_path = path.resolve(report_path);
    fs.mkdirSync(path.dirname(absolute_path), { recursive: true });
    fs.writeFileSync(absolute_path, `${output}\n`, "utf8");
  }
  console.log(output);
}

function main() {
  let args;
  try {
    args = parse_args(process.argv);
  } catch (error) {
    fail(error.message);
  }
  if (args.help) {
    console.log(usage());
    return;
  }
  if (!args.sample_dir) {
    fail(usage());
  }
  try {
    const sample_dir = path.resolve(args.sample_dir);
    const report = build_report(sample_dir);
    write_report(args.report, report);
    if (!report.ok) process.exit(1);
  } catch (error) {
    fail(error.message);
  }
}

main();
