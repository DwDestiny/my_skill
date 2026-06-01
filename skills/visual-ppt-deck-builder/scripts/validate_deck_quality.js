#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

function parse_args(argv) {
  const args = {};
  for (let index = 2; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--spec") {
      args.spec = argv[index + 1];
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
    "  node validate_deck_quality.js --spec /absolute/path/deck_spec.json --report /absolute/path/qa_report.json",
  ].join("\n");
}

function read_json(file_path) {
  if (!file_path || !fs.existsSync(file_path)) {
    throw new Error(`missing spec file: ${file_path || ""}`);
  }
  return JSON.parse(fs.readFileSync(file_path, "utf8"));
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

function collect_strings(value, strings = []) {
  if (typeof value === "string") {
    strings.push(value);
  } else if (Array.isArray(value)) {
    value.forEach((item) => collect_strings(item, strings));
  } else if (value && typeof value === "object") {
    Object.values(value).forEach((item) => collect_strings(item, strings));
  }
  return strings;
}

function has_source(slide) {
  if (slide.source) return true;
  if (slide.chart && slide.chart.source) return true;
  return false;
}

function resolve_asset_path(asset_path, spec_dir) {
  if (!asset_path || typeof asset_path !== "string") return "";
  if (path.isAbsolute(asset_path)) return asset_path;
  return path.resolve(spec_dir || process.cwd(), asset_path);
}

function validate_asset_file(slide, field_name, spec_dir, errors, slide_number) {
  const value = slide[field_name];
  if (!value || typeof value !== "string" || value.trim() === "") {
    errors.push(`slide ${slide_number} reference_visual_trend must include ${field_name}`);
    return "";
  }
  const asset_path = resolve_asset_path(value, spec_dir);
  if (!fs.existsSync(asset_path)) {
    errors.push(`slide ${slide_number} ${field_name} asset does not exist: ${value}`);
  }
  return asset_path;
}

function has_zone(blueprint, zone_name) {
  const zone = blueprint && blueprint[zone_name];
  return Boolean(
    zone &&
      typeof zone === "object" &&
      Number.isFinite(Number(zone.x)) &&
      Number.isFinite(Number(zone.y)) &&
      Number.isFinite(Number(zone.w)) &&
      Number.isFinite(Number(zone.h)),
  );
}

function validate_design_brief(slide, errors, slide_number) {
  const brief = slide.design_director_brief || {};
  [
    "expression_system",
    "style_intent",
    "typography_system",
    "color_strategy",
    "chart_language",
    "layout_rhythm",
  ].forEach((field_name) => {
    if (!brief[field_name]) {
      errors.push(`slide ${slide_number} design_director_brief must include ${field_name}`);
    }
  });
}

function validate_reference_visual_trend(slide, errors, slide_number, spec_dir) {
  const visual_draft_path = validate_asset_file(slide, "visual_draft_image", spec_dir, errors, slide_number);
  const background_path = validate_asset_file(slide, "background_image", spec_dir, errors, slide_number);
  if (visual_draft_path && background_path && path.resolve(visual_draft_path) === path.resolve(background_path)) {
    errors.push(`slide ${slide_number} visual_draft_image and background_image must be different files`);
  }
  validate_design_brief(slide, errors, slide_number);
  const blueprint = slide.coordinate_blueprint || {};
  ["title_zone", "chart_zone", "metrics_zone", "protected_empty_zone"].forEach((zone_name) => {
    if (!has_zone(blueprint, zone_name)) {
      errors.push(`slide ${slide_number} coordinate_blueprint must include ${zone_name}`);
    }
  });
  if (!has_zone(blueprint, "text_zone") && !has_zone(blueprint, "bullet_zone")) {
    errors.push(`slide ${slide_number} coordinate_blueprint must include text_zone or bullet_zone`);
  }
}

function validate_chart(slide, errors, slide_number) {
  const chart = slide.chart || {};
  const labels = Array.isArray(chart.labels) ? chart.labels : [];
  const values = Array.isArray(chart.values) ? chart.values : [];
  if (labels.length === 0 || values.length === 0 || labels.length !== values.length) {
    errors.push(`slide ${slide_number} chart must include matching labels and values`);
  }
  if (!has_source(slide)) {
    errors.push(`slide ${slide_number} chart must include source`);
  }
}

function validate_slide_shape(slide, errors, slide_number, spec_dir) {
  const layout = String(slide.layout || "content");
  const semantic_layout = String(slide.semantic_layout || layout);
  if (!slide.title) {
    errors.push(`slide ${slide_number} must include title`);
  }
  if (!["title", "section", "closing"].includes(layout) && !slide.claim) {
    errors.push(`slide ${slide_number} must include claim`);
  }
  if (!["title", "section", "closing"].includes(layout) && !has_source(slide)) {
    errors.push(`slide ${slide_number} must include source`);
  }
  if (layout === "image_text" && !slide.image) {
    errors.push(`slide ${slide_number} image_text must include image`);
  }
  if (layout === "bar_chart") {
    validate_chart(slide, errors, slide_number);
  }
  if (layout === "reference_visual_trend" || layout === "reference_anime_trend") {
    validate_reference_visual_trend(slide, errors, slide_number, spec_dir);
  }
  if (layout === "metrics") {
    const metrics = Array.isArray(slide.metrics) ? slide.metrics : [];
    if (metrics.length === 0) {
      errors.push(`slide ${slide_number} metrics must include metric cards`);
    }
    metrics.forEach((metric, metric_index) => {
      if (!metric.value || !metric.label) {
        errors.push(`slide ${slide_number} metric ${metric_index + 1} must include value and label`);
      }
    });
    if (slide.chart) validate_chart(slide, errors, slide_number);
  }
  if (semantic_layout === "executive_summary" && (!Array.isArray(slide.points) || slide.points.length < 3)) {
    errors.push(`slide ${slide_number} executive_summary must include at least 3 points`);
  }
  if (semantic_layout === "architecture" && (!Array.isArray(slide.layers) || slide.layers.length < 3)) {
    errors.push(`slide ${slide_number} architecture must include at least 3 layers`);
  }
  if (semantic_layout === "comparison" && (!Array.isArray(slide.items) || slide.items.length < 2)) {
    errors.push(`slide ${slide_number} comparison must include at least 2 items`);
  }
  if (semantic_layout === "roadmap" && (!Array.isArray(slide.phases) || slide.phases.length < 3)) {
    errors.push(`slide ${slide_number} roadmap must include at least 3 phases`);
  }
  if (semantic_layout === "risk_next_steps") {
    if (!Array.isArray(slide.risks) || slide.risks.length === 0) {
      errors.push(`slide ${slide_number} risk_next_steps must include risks`);
    }
    if (!Array.isArray(slide.actions) || slide.actions.length === 0) {
      errors.push(`slide ${slide_number} risk_next_steps must include actions`);
    }
  }
}

function validate_placeholders(spec, errors) {
  const exact_placeholders = new Set(["Topic", "Style", "Assets", "Visual deck system"]);
  const fuzzy_placeholder = /(lorem|todo|tbd|placeholder|占位)/i;
  collect_strings(spec).forEach((text) => {
    const trimmed = text.trim();
    if (exact_placeholders.has(trimmed) || fuzzy_placeholder.test(trimmed)) {
      errors.push(`placeholder text must be replaced: ${trimmed}`);
    }
  });
}

function validate_spec(spec, spec_dir) {
  const errors = [];
  const warnings = [];
  if (!spec || typeof spec !== "object") {
    return { ok: false, errors: ["spec must be a JSON object"], warnings, slide_count: 0, layout_count: 0 };
  }
  const slides = Array.isArray(spec.slides) ? spec.slides : [];
  if (slides.length === 0) {
    errors.push("spec.slides must be a non-empty array");
  }
  if (slides.length < 6) {
    errors.push("commercial deck should include at least 6 slides");
  }
  const layouts = new Set(slides.map((slide) => String(slide.semantic_layout || slide.layout || "content")));
  if (layouts.size < 5) {
    errors.push("commercial deck should use at least 5 distinct layouts");
  }
  const has_arch_or_roadmap = layouts.has("architecture") || layouts.has("roadmap");
  const has_chart_or_metrics = layouts.has("bar_chart") || layouts.has("metrics");
  [
    ["executive_summary", layouts.has("executive_summary")],
    ["architecture_or_roadmap", has_arch_or_roadmap],
    ["chart_or_metrics", has_chart_or_metrics],
    ["comparison", layouts.has("comparison")],
    ["risk_next_steps", layouts.has("risk_next_steps")],
  ].forEach(([name, ok]) => {
    if (!ok) errors.push(`commercial deck should include ${name} layout`);
  });
  slides.forEach((slide, index) => validate_slide_shape(slide, errors, index + 1, spec_dir));
  validate_placeholders(spec, errors);
  return {
    ok: errors.length === 0,
    errors,
    warnings,
    slide_count: slides.length,
    layout_count: layouts.size,
    layouts: Array.from(layouts),
  };
}

function main() {
  let args;
  try {
    args = parse_args(process.argv);
    if (args.help) {
      console.log(usage());
      return;
    }
    const report = validate_spec(read_json(args.spec), path.dirname(path.resolve(args.spec)));
    write_report(args.report, report);
    if (!report.ok) process.exit(1);
  } catch (error) {
    const report = {
      ok: false,
      errors: [error.message],
      warnings: [],
      slide_count: 0,
      layout_count: 0,
    };
    write_report(args && args.report, report);
    process.exit(1);
  }
}

main();
