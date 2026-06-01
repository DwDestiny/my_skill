#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");

let pptxgen_module;
try {
  pptxgen_module = require("pptxgenjs");
} catch (_error) {
  const bundled_module_path = path.join(
    os.homedir(),
    ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pptxgenjs"
  );
  pptxgen_module = require(bundled_module_path);
}

const PptxGenJS = pptxgen_module.default || pptxgen_module;

const slide_width = 13.333;
const slide_height = 7.5;

function parse_args(argv) {
  const args = {};
  for (let index = 2; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--spec") {
      args.spec = argv[index + 1];
      index += 1;
    } else if (token === "--output") {
      args.output = argv[index + 1];
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
    "  node build_visual_pptx.js --spec /absolute/path/deck_spec.json --output /absolute/path/deck.pptx",
    "",
    "The spec must contain title and a non-empty slides array.",
  ].join("\n");
}

function fail(message) {
  console.error(message);
  process.exit(1);
}

function read_json(file_path) {
  if (!file_path || !fs.existsSync(file_path)) {
    throw new Error(`missing spec file: ${file_path || ""}`);
  }
  return JSON.parse(fs.readFileSync(file_path, "utf8"));
}

function normalize_color(value, fallback) {
  const raw_value = String(value || fallback || "").replace(/^#/, "").trim();
  if (!/^[0-9a-fA-F]{6}$/.test(raw_value)) {
    return String(fallback || "000000").replace(/^#/, "");
  }
  return raw_value.toUpperCase();
}

function overlay_color(slide_data, key, fallback) {
  const overlay_style = slide_data.overlay_style || {};
  return normalize_color(overlay_style[key], fallback);
}

function overlay_palette(slide_data, key, fallback) {
  const overlay_style = slide_data.overlay_style || {};
  const raw_palette = overlay_style[key];
  if (!Array.isArray(raw_palette) || raw_palette.length === 0) {
    return fallback;
  }
  return raw_palette.map((color, index) => normalize_color(color, fallback[index % fallback.length]));
}

function overlay_number(slide_data, key, fallback, options = {}) {
  const overlay_style = slide_data.overlay_style || {};
  const value = Number(overlay_style[key]);
  if (!Number.isFinite(value)) {
    return fallback;
  }
  const min = Number.isFinite(options.min) ? options.min : -Infinity;
  const max = Number.isFinite(options.max) ? options.max : Infinity;
  return Math.min(max, Math.max(min, value));
}

function normalize_spec(spec) {
  if (!spec || typeof spec !== "object") {
    throw new Error("spec must be a JSON object");
  }
  if (!Array.isArray(spec.slides) || spec.slides.length === 0) {
    throw new Error("spec.slides must be a non-empty array");
  }
  const theme = spec.theme || {};
  return {
    title: String(spec.title || "Untitled deck"),
    subtitle: String(spec.subtitle || ""),
    author: String(spec.author || ""),
    theme: {
      background: normalize_color(theme.background, "F7F4EF"),
      foreground: normalize_color(theme.foreground, "17202A"),
      accent: normalize_color(theme.accent, "1F8A70"),
      accent_2: normalize_color(theme.accent_2, "E76F51"),
      muted: normalize_color(theme.muted, "6B7280"),
      panel: normalize_color(theme.panel, "FFFFFF"),
      font_face: String(theme.font_face || "Aptos"),
    },
    slides: spec.slides,
  };
}

function ensure_output_path(output_path) {
  if (!output_path) {
    throw new Error("missing --output path");
  }
  const absolute_output = path.resolve(output_path);
  fs.mkdirSync(path.dirname(absolute_output), { recursive: true });
  return absolute_output;
}

function add_background(slide, theme, slide_data) {
  const background = normalize_color(slide_data.background, theme.background);
  slide.background = { color: background };
  slide.addShape("rect", {
    x: 0,
    y: 0,
    w: slide_width,
    h: slide_height,
    fill: { color: background },
    line: { color: background, transparency: 100 },
  });
  slide.addShape("rect", {
    x: 0,
    y: 0,
    w: 0.12,
    h: slide_height,
    fill: { color: theme.accent },
    line: { color: theme.accent, transparency: 100 },
  });
}

function add_footer(slide, theme, slide_number, total_slides) {
  slide.addText(`${slide_number}/${total_slides}`, {
    x: 11.9,
    y: 7.06,
    w: 0.85,
    h: 0.18,
    fontFace: theme.font_face,
    fontSize: 7,
    color: theme.muted,
    align: "right",
    margin: 0,
  });
}

function add_title(slide, theme, title, options = {}) {
  slide.addText(String(title || ""), {
    x: options.x || 0.72,
    y: options.y || 0.58,
    w: options.w || 11.7,
    h: options.h || 0.8,
    fontFace: theme.font_face,
    fontSize: options.font_size || 27,
    bold: true,
    color: theme.foreground,
    margin: 0,
    fit: "shrink",
  });
}

function add_claim(slide, theme, claim, options = {}) {
  if (!claim) return;
  slide.addText(String(claim), {
    x: options.x || 0.76,
    y: options.y || 1.3,
    w: options.w || 10.4,
    h: options.h || 0.64,
    fontFace: theme.font_face,
    fontSize: options.font_size || 12.5,
    bold: true,
    color: options.color || theme.accent,
    margin: 0,
    fit: "shrink",
  });
}

function add_body(slide, theme, body, box) {
  if (!body) return;
  slide.addText(String(body), {
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
    fontFace: theme.font_face,
    fontSize: box.font_size || 14,
    color: box.color || theme.muted,
    valign: "top",
    breakLine: false,
    margin: 0,
    fit: "shrink",
  });
}

function add_source_note(slide, theme, source) {
  if (!source) return;
  slide.addText(String(source), {
    x: 0.76,
    y: 6.98,
    w: 8.9,
    h: 0.16,
    fontFace: theme.font_face,
    fontSize: 6.5,
    color: theme.muted,
    margin: 0,
    fit: "shrink",
  });
}

function add_bullets(slide, theme, bullets, box) {
  if (!Array.isArray(bullets) || bullets.length === 0) return;
  const runs = bullets.map((bullet) => ({
    text: String(bullet),
    options: { bullet: { type: "ul" }, breakLine: true },
  }));
  slide.addText(runs, {
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
    fontFace: theme.font_face,
    fontSize: box.font_size || 13,
    color: theme.foreground,
    margin: 0.05,
    breakLine: false,
    fit: "shrink",
  });
}

function resolve_asset_path(asset_path, spec_dir) {
  if (!asset_path) return null;
  const candidate = path.isAbsolute(asset_path)
    ? asset_path
    : path.resolve(spec_dir, asset_path);
  if (!fs.existsSync(candidate)) {
    throw new Error(`missing image asset: ${candidate}`);
  }
  return candidate;
}

function add_image(slide, image_path, box) {
  if (!image_path) return;
  slide.addImage({
    path: image_path,
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
  });
}

function zone_value(blueprint, zone_name, fallback) {
  const zone = blueprint && blueprint[zone_name] ? blueprint[zone_name] : fallback;
  return {
    x: Number(zone.x),
    y: Number(zone.y),
    w: Number(zone.w),
    h: Number(zone.h),
  };
}

function add_reference_background(slide, theme, slide_data, spec_dir) {
  const background_image = resolve_asset_path(slide_data.background_image, spec_dir);
  if (background_image) {
    add_image(slide, background_image, { x: 0, y: 0, w: slide_width, h: slide_height });
    return;
  }
  add_background(slide, theme, slide_data);
}

function add_reference_anime_title(slide, theme, slide_data, zones) {
  const title_zone = zones.title_zone;
  const subtitle_zone = zones.subtitle_zone;
  const title = String(slide_data.title || "");
  const title_match = title.match(/^(\d{4})(.*)$/);
  const title_runs = title_match
    ? [
        { text: title_match[1], options: { color: theme.accent, bold: true } },
        { text: title_match[2], options: { color: theme.foreground, bold: true } },
      ]
    : [{ text: title, options: { color: theme.foreground, bold: true } }];

  slide.addText(title_runs, {
    x: title_zone.x,
    y: title_zone.y,
    w: title_zone.w,
    h: title_zone.h,
    fontFace: theme.font_face,
    fontSize: overlay_number(slide_data, "title_font_size", 26, { min: 8, max: 54 }),
    margin: 0,
    fit: "shrink",
  });
  slide.addText(String(slide_data.subtitle || ""), {
    x: subtitle_zone.x,
    y: subtitle_zone.y,
    w: subtitle_zone.w,
    h: subtitle_zone.h,
    fontFace: theme.font_face,
    fontSize: overlay_number(slide_data, "subtitle_font_size", 16, { min: 6, max: 30 }),
    color: overlay_color(slide_data, "subtitle_color", "3C4F73"),
    margin: 0,
    fit: "shrink",
  });
}

function add_reference_anime_bullets(slide, theme, slide_data, zones) {
  const bullet_zone = zones.bullet_zone;
  const bullets = Array.isArray(slide_data.bullets) ? slide_data.bullets.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "bullet_icon_colors", [theme.accent, theme.accent_2, "42C6A5"]);
  const overlay_style = slide_data.overlay_style || {};
  const icon_texts = Array.isArray(overlay_style.bullet_icon_texts) && overlay_style.bullet_icon_texts.length > 0
    ? overlay_style.bullet_icon_texts.map((text) => String(text))
    : ["学", "产", "协"];
  const bullet_title_color = overlay_color(slide_data, "bullet_title_color", theme.foreground);
  const bullet_body_color = overlay_color(slide_data, "bullet_body_color", theme.muted);
  bullets.forEach((bullet, index) => {
    const y_position = bullet_zone.y + index * 0.74;
    const color = colors[index % colors.length];
    const icon_text = icon_texts[index % icon_texts.length];
    const icon_font_size = Number(overlay_style.bullet_icon_font_size) || (icon_text.length > 1 ? 7.2 : 9);
    slide.addShape("ellipse", {
      x: bullet_zone.x,
      y: y_position + 0.02,
      w: 0.46,
      h: 0.46,
      fill: { color, transparency: 8 },
      line: { color: "FFFFFF", pt: 1.2, transparency: 12 },
    });
    slide.addText(icon_text, {
      x: bullet_zone.x,
      y: y_position + 0.14,
      w: 0.46,
      h: 0.16,
      fontFace: theme.font_face,
      fontSize: icon_font_size,
      bold: true,
      color: "FFFFFF",
      align: "center",
      margin: 0,
    });
    slide.addText(String(bullet.title || ""), {
      x: bullet_zone.x + 0.72,
      y: y_position + 0.02,
      w: bullet_zone.w - 0.8,
      h: 0.28,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_title_font_size", 14, { min: 6, max: 24 }),
      bold: true,
      color: bullet_title_color,
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(bullet.body || ""), {
      x: bullet_zone.x + 0.72,
      y: y_position + 0.36,
      w: bullet_zone.w - 0.8,
      h: 0.22,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_body_font_size", 9.4, { min: 5, max: 16 }),
      color: bullet_body_color,
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_anime_metrics(slide, theme, slide_data, zones) {
  const metrics_zone = zones.metrics_zone;
  const metrics = Array.isArray(slide_data.metrics) ? slide_data.metrics.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "metric_value_colors", [theme.accent, theme.accent_2, "42BFA3"]);
  const metrics_divider_color = overlay_color(slide_data, "metrics_divider_color", "B9D2F0");
  const metric_label_color = overlay_color(slide_data, "metric_label_color", theme.foreground);
  const metric_dot_line_color = overlay_color(slide_data, "metric_dot_line_color", "FFFFFF");
  const metrics_divider_transparency = overlay_number(slide_data, "metrics_divider_transparency", 45, { min: 0, max: 100 });
  const metrics_vertical_divider_transparency = overlay_number(slide_data, "metrics_vertical_divider_transparency", 52, { min: 0, max: 100 });
  const metric_value_font_size = overlay_number(slide_data, "metric_value_font_size", 21, { min: 8, max: 34 });
  const metric_label_font_size = overlay_number(slide_data, "metric_label_font_size", 8.8, { min: 5, max: 16 });
  const metric_width = metrics_zone.w / Math.max(metrics.length, 1);

  slide.addShape("line", {
    x: metrics_zone.x - 0.5,
    y: metrics_zone.y - 0.25,
    w: metrics_zone.w + 1.05,
    h: 0,
    line: { color: metrics_divider_color, pt: 1, transparency: metrics_divider_transparency, dash: "dash" },
  });

  metrics.forEach((metric, index) => {
    const x_position = metrics_zone.x + index * metric_width;
    if (index > 0) {
      slide.addShape("line", {
        x: x_position - 0.12,
        y: metrics_zone.y + 0.06,
        w: 0,
        h: 0.82,
        line: { color: metrics_divider_color, pt: 1, transparency: metrics_vertical_divider_transparency, dash: "dash" },
      });
    }
    slide.addText(String(metric.value || ""), {
      x: x_position,
      y: metrics_zone.y,
      w: metric_width - 0.15,
      h: 0.4,
      fontFace: theme.font_face,
      fontSize: metric_value_font_size,
      bold: true,
      color: colors[index % colors.length],
      align: "center",
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(metric.label || ""), {
      x: x_position,
      y: metrics_zone.y + 0.45,
      w: metric_width - 0.15,
      h: 0.22,
      fontFace: theme.font_face,
      fontSize: metric_label_font_size,
      bold: true,
      color: metric_label_color,
      align: "center",
      margin: 0,
      fit: "shrink",
    });
    slide.addShape("ellipse", {
      x: x_position + metric_width / 2 - 0.16,
      y: metrics_zone.y + 0.73,
      w: 0.32,
      h: 0.32,
      fill: { color: colors[index % colors.length], transparency: 58 },
      line: { color: metric_dot_line_color, transparency: 20 },
    });
  });
}

function add_reference_anime_chart(slide, theme, slide_data, zones) {
  const chart = slide_data.chart || {};
  const chart_title_zone = zones.chart_title_zone;
  const chart_zone = zones.chart_zone;
  const labels = Array.isArray(chart.labels) ? chart.labels : [];
  const values = Array.isArray(chart.values) ? chart.values.map(Number) : [];
  if (labels.length === 0 || values.length === 0 || labels.length !== values.length) {
    throw new Error(`reference_anime_trend slide requires chart labels and values: ${slide_data.title || ""}`);
  }
  const chart_title_font_size = overlay_number(slide_data, "chart_title_font_size", 13, { min: 6, max: 24 });

  slide.addText(String(chart.title || ""), {
    x: chart_title_zone.x,
    y: chart_title_zone.y,
    w: chart_title_zone.w,
    h: chart_title_zone.h,
    fontFace: theme.font_face,
    fontSize: chart_title_font_size,
    bold: true,
    color: overlay_color(slide_data, "chart_title_color", theme.foreground),
    margin: 0,
    fit: "shrink",
  });
  slide.addShape("line", {
    x: chart_title_zone.x,
    y: chart_title_zone.y + 0.42,
    w: 0.32,
    h: 0,
    line: { color: overlay_color(slide_data, "chart_accent_color", theme.accent), pt: 1.6 },
  });

  const plot_x = chart_zone.x + 0.55;
  const plot_y = chart_zone.y + 0.42;
  const plot_w = chart_zone.w - 0.85;
  const plot_h = chart_zone.h - 0.82;
  const max_value = Math.max(...values, 100);
  const colors = overlay_palette(slide_data, "chart_bar_colors", ["FFC83D", "FF7F95", "72D9AA", "5B8FF9"]);
  const chart_grid_color = overlay_color(slide_data, "chart_grid_color", "C7D5EA");
  const chart_tick_color = overlay_color(slide_data, "chart_tick_color", "587092");
  const chart_label_color = overlay_color(slide_data, "chart_label_color", "52637A");
  const chart_value_color = overlay_color(slide_data, "chart_value_color", theme.foreground);
  const chart_source_color = overlay_color(slide_data, "chart_source_color", "8AA0BB");
  const chart_accent_color = overlay_color(slide_data, "chart_accent_color", theme.accent);
  const chart_tick_font_size = overlay_number(slide_data, "chart_tick_font_size", 7.5, { min: 4, max: 14 });
  const chart_label_font_size = overlay_number(slide_data, "chart_label_font_size", 8, { min: 4, max: 14 });
  const chart_value_font_size = overlay_number(slide_data, "chart_value_font_size", 9.5, { min: 4, max: 16 });
  const chart_source_font_size = overlay_number(slide_data, "chart_source_font_size", 5.8, { min: 4, max: 10 });
  const chart_bar_transparency = overlay_number(slide_data, "chart_bar_transparency", 8, { min: 0, max: 100 });
  const chart_grid_transparency = overlay_number(slide_data, "chart_grid_transparency", 52, { min: 0, max: 100 });
  const chart_zero_grid_transparency = overlay_number(slide_data, "chart_zero_grid_transparency", 10, { min: 0, max: 100 });

  [0, 25, 50, 75, 100].forEach((tick) => {
    const y_position = plot_y + plot_h - (tick / 100) * plot_h;
    slide.addShape("line", {
      x: plot_x,
      y: y_position,
      w: plot_w,
      h: 0,
      line: {
        color: chart_grid_color,
        pt: 0.7,
        transparency: tick === 0 ? chart_zero_grid_transparency : chart_grid_transparency,
        dash: tick === 0 ? "solid" : "dash",
      },
    });
    slide.addText(String(tick), {
      x: plot_x - 0.36,
      y: y_position - 0.07,
      w: 0.25,
      h: 0.12,
      fontFace: theme.font_face,
      fontSize: chart_tick_font_size,
      color: chart_tick_color,
      align: "right",
      margin: 0,
    });
  });

  const bar_gap = 0.52;
  const bar_w = (plot_w - bar_gap * (values.length - 1)) / values.length * 0.58;
  const slot_w = plot_w / values.length;
  const points = [];
  values.forEach((value, index) => {
    const slot_x = plot_x + index * slot_w;
    const bar_x = slot_x + slot_w / 2 - bar_w / 2;
    const bar_h = (value / max_value) * (plot_h - 0.16);
    const bar_y = plot_y + plot_h - bar_h;
    const color = colors[index % colors.length];
    const point_x = bar_x + bar_w / 2;
    const point_y = bar_y + 0.16;
    points.push({ x: point_x, y: point_y });
    slide.addShape("rect", {
      x: bar_x,
      y: bar_y,
      w: bar_w,
      h: bar_h,
      fill: { color, transparency: chart_bar_transparency },
      line: { color, transparency: 100 },
    });
    slide.addText(String(value), {
      x: bar_x - 0.12,
      y: bar_y - 0.26,
      w: bar_w + 0.24,
      h: 0.18,
      fontFace: theme.font_face,
      fontSize: chart_value_font_size,
      bold: true,
      color: chart_value_color,
      align: "center",
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(labels[index]), {
      x: slot_x + 0.03,
      y: plot_y + plot_h + 0.14,
      w: slot_w - 0.06,
      h: 0.34,
      fontFace: theme.font_face,
      fontSize: chart_label_font_size,
      color: chart_label_color,
      align: "center",
      margin: 0,
      fit: "shrink",
      breakLine: false,
    });
  });

  points.slice(0, -1).forEach((point, index) => {
    const next_point = points[index + 1];
    slide.addShape("line", {
      x: point.x,
      y: point.y,
      w: next_point.x - point.x,
      h: next_point.y - point.y,
      line: { color: chart_accent_color, pt: 1.8 },
    });
  });
  points.forEach((point) => {
    slide.addShape("ellipse", {
      x: point.x - 0.06,
      y: point.y - 0.06,
      w: 0.12,
      h: 0.12,
      fill: { color: "FFFFFF" },
      line: { color: chart_accent_color, pt: 1.3 },
    });
  });

  slide.addText(String(chart.source || ""), {
    x: chart_zone.x + 1.08,
    y: chart_zone.y + chart_zone.h + 0.18,
    w: chart_zone.w - 1.2,
    h: 0.12,
    fontFace: theme.font_face,
    fontSize: chart_source_font_size,
    color: chart_source_color,
    margin: 0,
    fit: "shrink",
  });
}

function reference_layout_variant(slide_data) {
  const variant = String(slide_data.layout_variant || "minimal_left_report").trim();
  return variant || "minimal_left_report";
}

function reference_zone_defaults(variant) {
  const variants = {
    minimal_left_report: {
      title_zone: { x: 1.0, y: 1.08, w: 5.1, h: 0.62 },
      subtitle_zone: { x: 1.02, y: 1.78, w: 4.6, h: 0.42 },
      bullet_zone: { x: 1.02, y: 2.46, w: 4.95, h: 2.02 },
      metrics_zone: { x: 2.05, y: 5.12, w: 3.95, h: 1.08 },
      chart_title_zone: { x: 6.82, y: 1.7, w: 3.2, h: 0.38 },
      chart_zone: { x: 6.7, y: 2.38, w: 5.08, h: 3.7 },
    },
    future_dashboard_focus: {
      title_zone: { x: 0.78, y: 0.72, w: 5.05, h: 0.66 },
      subtitle_zone: { x: 0.82, y: 1.42, w: 4.65, h: 0.34 },
      bullet_zone: { x: 0.88, y: 2.26, w: 3.7, h: 2.34 },
      metrics_zone: { x: 0.88, y: 5.76, w: 4.55, h: 0.72 },
      chart_title_zone: { x: 5.55, y: 0.98, w: 4.65, h: 0.36 },
      chart_zone: { x: 5.1, y: 1.52, w: 6.25, h: 4.28 },
    },
    oriental_vertical_scroll: {
      title_zone: { x: 0.76, y: 0.82, w: 4.85, h: 0.68 },
      subtitle_zone: { x: 0.78, y: 1.5, w: 4.05, h: 0.34 },
      bullet_zone: { x: 0.9, y: 2.1, w: 3.78, h: 3.32 },
      metrics_zone: { x: 10.12, y: 1.64, w: 1.7, h: 3.82 },
      chart_title_zone: { x: 5.2, y: 1.68, w: 3.75, h: 0.36 },
      chart_zone: { x: 4.98, y: 2.26, w: 4.78, h: 3.55 },
    },
    editorial_feature_story: {
      title_zone: { x: 0.72, y: 0.68, w: 5.0, h: 0.78 },
      subtitle_zone: { x: 0.76, y: 1.44, w: 4.5, h: 0.34 },
      bullet_zone: { x: 0.86, y: 2.08, w: 4.75, h: 3.34 },
      metrics_zone: { x: 5.9, y: 5.22, w: 4.98, h: 0.84 },
      chart_title_zone: { x: 5.98, y: 1.16, w: 4.3, h: 0.36 },
      chart_zone: { x: 5.76, y: 1.78, w: 5.28, h: 2.92 },
    },
    boardroom_summary_matrix: {
      title_zone: { x: 0.72, y: 0.72, w: 5.25, h: 0.64 },
      subtitle_zone: { x: 0.74, y: 1.42, w: 4.35, h: 0.34 },
      bullet_zone: { x: 0.78, y: 4.62, w: 5.45, h: 1.45 },
      metrics_zone: { x: 0.82, y: 2.1, w: 3.35, h: 1.84 },
      chart_title_zone: { x: 6.72, y: 0.92, w: 4.2, h: 0.36 },
      chart_zone: { x: 6.42, y: 1.58, w: 5.45, h: 3.72 },
    },
    future_launch_stage: {
      title_zone: { x: 0.76, y: 0.82, w: 5.28, h: 0.74 },
      subtitle_zone: { x: 0.78, y: 1.62, w: 4.3, h: 0.34 },
      bullet_zone: { x: 0.82, y: 5.86, w: 7.45, h: 0.82 },
      metrics_zone: { x: 10.55, y: 0.96, w: 1.75, h: 2.85 },
      chart_title_zone: { x: 4.92, y: 1.18, w: 3.95, h: 0.36 },
      chart_zone: { x: 4.32, y: 1.74, w: 5.46, h: 3.12 },
    },
    oriental_scroll_narrative: {
      title_zone: { x: 6.1, y: 0.78, w: 5.75, h: 0.68 },
      subtitle_zone: { x: 6.12, y: 1.5, w: 4.65, h: 0.34 },
      bullet_zone: { x: 0.86, y: 2.0, w: 4.15, h: 3.18 },
      metrics_zone: { x: 9.86, y: 2.08, w: 1.72, h: 2.72 },
      chart_title_zone: { x: 1.0, y: 5.46, w: 3.6, h: 0.3 },
      chart_zone: { x: 3.02, y: 5.18, w: 6.1, h: 0.98 },
    },
    editorial_feature_spread: {
      title_zone: { x: 0.72, y: 0.7, w: 5.22, h: 0.82 },
      subtitle_zone: { x: 0.76, y: 1.54, w: 4.22, h: 0.34 },
      bullet_zone: { x: 0.86, y: 2.62, w: 4.72, h: 2.18 },
      metrics_zone: { x: 7.58, y: 5.42, w: 4.0, h: 0.86 },
      chart_title_zone: { x: 7.0, y: 1.02, w: 3.7, h: 0.32 },
      chart_zone: { x: 6.62, y: 1.5, w: 4.72, h: 2.35 },
    },
  };
  return variants[variant] || variants.minimal_left_report;
}

function add_reference_signal_bullets(slide, theme, slide_data, zones) {
  const bullet_zone = zones.bullet_zone;
  const bullets = Array.isArray(slide_data.bullets) ? slide_data.bullets.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "bullet_icon_colors", [theme.accent, theme.accent_2, "42C6A5"]);
  const bullet_title_color = overlay_color(slide_data, "bullet_title_color", theme.foreground);
  const bullet_body_color = overlay_color(slide_data, "bullet_body_color", theme.muted);
  const divider_color = overlay_color(slide_data, "bullet_divider_color", colors[0]);
  slide.addShape("line", {
    x: bullet_zone.x,
    y: bullet_zone.y - 0.04,
    w: 0,
    h: bullet_zone.h + 0.08,
    line: { color: divider_color, pt: 1.1, transparency: 38 },
  });
  bullets.forEach((bullet, index) => {
    const y_position = bullet_zone.y + index * 0.72;
    const color = colors[index % colors.length];
    slide.addShape("line", {
      x: bullet_zone.x,
      y: y_position + 0.13,
      w: 0.42,
      h: 0,
      line: { color, pt: 2.2 },
    });
    slide.addText(`0${index + 1}`, {
      x: bullet_zone.x + 0.55,
      y: y_position,
      w: 0.38,
      h: 0.2,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_index_font_size", 7.6, { min: 4, max: 14 }),
      bold: true,
      color,
      margin: 0,
    });
    slide.addText(String(bullet.title || ""), {
      x: bullet_zone.x + 1.02,
      y: y_position - 0.02,
      w: bullet_zone.w - 1.12,
      h: 0.26,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_title_font_size", 11.4, { min: 6, max: 22 }),
      bold: true,
      color: bullet_title_color,
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(bullet.body || ""), {
      x: bullet_zone.x + 0.55,
      y: y_position + 0.33,
      w: bullet_zone.w - 0.62,
      h: 0.24,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_body_font_size", 8.2, { min: 5, max: 15 }),
      color: bullet_body_color,
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_oriental_bullets(slide, theme, slide_data, zones) {
  const bullet_zone = zones.bullet_zone;
  const bullets = Array.isArray(slide_data.bullets) ? slide_data.bullets.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "bullet_icon_colors", [theme.accent, theme.accent_2, "7C2D12"]);
  const icon_texts = ["壹", "贰", "叁"];
  const bullet_title_color = overlay_color(slide_data, "bullet_title_color", theme.foreground);
  const bullet_body_color = overlay_color(slide_data, "bullet_body_color", theme.muted);
  slide.addShape("line", {
    x: bullet_zone.x + 0.2,
    y: bullet_zone.y - 0.08,
    w: 0,
    h: Math.min(bullet_zone.h, 2.7),
    line: { color: overlay_color(slide_data, "bullet_divider_color", colors[0]), pt: 0.8, transparency: 36, dash: "dash" },
  });
  bullets.forEach((bullet, index) => {
    const y_position = bullet_zone.y + index * 0.86;
    const color = colors[index % colors.length];
    slide.addShape("ellipse", {
      x: bullet_zone.x,
      y: y_position,
      w: 0.42,
      h: 0.42,
      fill: { color, transparency: 0 },
      line: { color, transparency: 100 },
    });
    slide.addText(icon_texts[index], {
      x: bullet_zone.x,
      y: y_position + 0.11,
      w: 0.42,
      h: 0.14,
      fontFace: theme.font_face,
      fontSize: 7.2,
      bold: true,
      color: "FFFFFF",
      align: "center",
      margin: 0,
    });
    slide.addText(String(bullet.title || ""), {
      x: bullet_zone.x + 0.66,
      y: y_position - 0.02,
      w: bullet_zone.w - 0.78,
      h: 0.28,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_title_font_size", 13.2, { min: 6, max: 24 }),
      bold: true,
      color: bullet_title_color,
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(bullet.body || ""), {
      x: bullet_zone.x + 0.66,
      y: y_position + 0.34,
      w: bullet_zone.w - 0.72,
      h: 0.28,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_body_font_size", 8.8, { min: 5, max: 15 }),
      color: bullet_body_color,
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_vertical_metrics(slide, theme, slide_data, zones) {
  const metrics_zone = zones.metrics_zone;
  const metrics = Array.isArray(slide_data.metrics) ? slide_data.metrics.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "metric_value_colors", [theme.accent, theme.accent_2, "7C2D12"]);
  const line_color = overlay_color(slide_data, "metrics_divider_color", colors[0]);
  slide.addShape("line", {
    x: metrics_zone.x,
    y: metrics_zone.y - 0.1,
    w: 0,
    h: metrics_zone.h + 0.12,
    line: { color: line_color, pt: 0.9, transparency: 25 },
  });
  metrics.forEach((metric, index) => {
    const y_position = metrics_zone.y + index * (metrics_zone.h / Math.max(metrics.length, 1));
    if (index > 0) {
      slide.addShape("line", {
        x: metrics_zone.x,
        y: y_position - 0.12,
        w: metrics_zone.w,
        h: 0,
        line: { color: line_color, pt: 0.7, transparency: 48, dash: "dash" },
      });
    }
    slide.addText(String(metric.value || ""), {
      x: metrics_zone.x + 0.18,
      y: y_position,
      w: metrics_zone.w - 0.2,
      h: 0.36,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_value_font_size", 17.5, { min: 8, max: 34 }),
      bold: true,
      color: colors[index % colors.length],
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(metric.label || ""), {
      x: metrics_zone.x + 0.18,
      y: y_position + 0.46,
      w: metrics_zone.w - 0.2,
      h: 0.22,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_label_font_size", 7.6, { min: 5, max: 16 }),
      bold: true,
      color: overlay_color(slide_data, "metric_label_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_future_metrics(slide, theme, slide_data, zones) {
  const metrics_zone = zones.metrics_zone;
  const metrics = Array.isArray(slide_data.metrics) ? slide_data.metrics.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "metric_value_colors", [theme.accent, theme.accent_2, "16E0B3"]);
  const metric_width = metrics_zone.w / Math.max(metrics.length, 1);
  const line_color = overlay_color(slide_data, "metrics_divider_color", colors[0]);
  slide.addShape("line", {
    x: metrics_zone.x,
    y: metrics_zone.y - 0.1,
    w: metrics_zone.w,
    h: 0,
    line: { color: line_color, pt: 1, transparency: 35 },
  });
  metrics.forEach((metric, index) => {
    const x_position = metrics_zone.x + index * metric_width;
    const color = colors[index % colors.length];
    slide.addShape("line", {
      x: x_position,
      y: metrics_zone.y + 0.64,
      w: Math.max(0.42, metric_width * 0.34),
      h: 0,
      line: { color, pt: 2.1, transparency: 12 },
    });
    slide.addText(String(metric.value || ""), {
      x: x_position,
      y: metrics_zone.y,
      w: metric_width - 0.12,
      h: 0.32,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_value_font_size", 17.6, { min: 8, max: 34 }),
      bold: true,
      color,
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(metric.label || ""), {
      x: x_position,
      y: metrics_zone.y + 0.39,
      w: metric_width - 0.12,
      h: 0.18,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_label_font_size", 6.9, { min: 5, max: 16 }),
      bold: true,
      color: overlay_color(slide_data, "metric_label_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_editorial_bullets(slide, theme, slide_data, zones) {
  const bullet_zone = zones.bullet_zone;
  const bullets = Array.isArray(slide_data.bullets) ? slide_data.bullets.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "bullet_icon_colors", [theme.accent, theme.accent_2, "111827"]);
  const bullet_title_color = overlay_color(slide_data, "bullet_title_color", theme.foreground);
  const bullet_body_color = overlay_color(slide_data, "bullet_body_color", theme.muted);
  bullets.forEach((bullet, index) => {
    const y_position = bullet_zone.y + index * 0.9;
    const color = colors[index % colors.length];
    slide.addShape("line", {
      x: bullet_zone.x,
      y: y_position - 0.08,
      w: bullet_zone.w * 0.72,
      h: 0,
      line: { color, pt: 0.9, transparency: index === 0 ? 12 : 42 },
    });
    slide.addText(String(index + 1).padStart(2, "0"), {
      x: bullet_zone.x,
      y: y_position + 0.08,
      w: 0.42,
      h: 0.18,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_index_font_size", 7.6, { min: 4, max: 14 }),
      bold: true,
      color,
      margin: 0,
    });
    slide.addText(String(bullet.title || ""), {
      x: bullet_zone.x + 0.58,
      y: y_position,
      w: bullet_zone.w - 0.66,
      h: 0.3,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_title_font_size", 13.6, { min: 6, max: 24 }),
      bold: true,
      color: bullet_title_color,
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(bullet.body || ""), {
      x: bullet_zone.x + 0.58,
      y: y_position + 0.38,
      w: bullet_zone.w - 0.72,
      h: 0.28,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_body_font_size", 8.7, { min: 5, max: 15 }),
      color: bullet_body_color,
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_editorial_metrics(slide, theme, slide_data, zones) {
  const metrics_zone = zones.metrics_zone;
  const metrics = Array.isArray(slide_data.metrics) ? slide_data.metrics.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "metric_value_colors", [theme.accent, theme.accent_2, "111827"]);
  const metric_width = metrics_zone.w / Math.max(metrics.length, 1);
  slide.addShape("line", {
    x: metrics_zone.x,
    y: metrics_zone.y - 0.1,
    w: metrics_zone.w,
    h: 0,
    line: { color: overlay_color(slide_data, "metrics_divider_color", colors[0]), pt: 1.1, transparency: 22 },
  });
  metrics.forEach((metric, index) => {
    const x_position = metrics_zone.x + index * metric_width;
    slide.addText(String(metric.value || ""), {
      x: x_position,
      y: metrics_zone.y,
      w: metric_width - 0.16,
      h: 0.34,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_value_font_size", 18.5, { min: 8, max: 34 }),
      bold: true,
      color: colors[index % colors.length],
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(metric.label || ""), {
      x: x_position,
      y: metrics_zone.y + 0.43,
      w: metric_width - 0.16,
      h: 0.22,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_label_font_size", 7.3, { min: 5, max: 16 }),
      bold: true,
      color: overlay_color(slide_data, "metric_label_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_boardroom_metrics(slide, theme, slide_data, zones) {
  const metrics_zone = zones.metrics_zone;
  const metrics = Array.isArray(slide_data.metrics) ? slide_data.metrics.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "metric_value_colors", [theme.accent, theme.accent_2, "B38E52"]);
  metrics.forEach((metric, index) => {
    const y_position = metrics_zone.y + index * 0.58;
    const color = colors[index % colors.length];
    slide.addText(String(metric.value || ""), {
      x: metrics_zone.x,
      y: y_position,
      w: 1.05,
      h: 0.34,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_value_font_size", 18.8, { min: 8, max: 34 }),
      bold: true,
      color,
      margin: 0,
      fit: "shrink",
    });
    slide.addShape("line", {
      x: metrics_zone.x + 1.18,
      y: y_position + 0.18,
      w: 1.0 + index * 0.24,
      h: 0,
      line: { color, pt: 1.6, transparency: 18 },
    });
    slide.addText(String(metric.label || ""), {
      x: metrics_zone.x + 2.32,
      y: y_position + 0.06,
      w: metrics_zone.w - 2.35,
      h: 0.2,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_label_font_size", 7.6, { min: 5, max: 16 }),
      bold: true,
      color: overlay_color(slide_data, "metric_label_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_boardroom_insights(slide, theme, slide_data, zones) {
  const bullet_zone = zones.bullet_zone;
  const bullets = Array.isArray(slide_data.bullets) ? slide_data.bullets.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "bullet_icon_colors", [theme.accent, theme.accent_2, "B38E52"]);
  const width = bullet_zone.w / Math.max(bullets.length, 1);
  slide.addShape("line", {
    x: bullet_zone.x,
    y: bullet_zone.y - 0.18,
    w: bullet_zone.w,
    h: 0,
    line: { color: overlay_color(slide_data, "metrics_divider_color", "AEBABC"), pt: 1.0, transparency: 35 },
  });
  bullets.forEach((bullet, index) => {
    const x_position = bullet_zone.x + index * width;
    const color = colors[index % colors.length];
    slide.addText(String(index + 1).padStart(2, "0"), {
      x: x_position,
      y: bullet_zone.y,
      w: 0.36,
      h: 0.18,
      fontFace: theme.font_face,
      fontSize: 7.3,
      bold: true,
      color,
      margin: 0,
    });
    slide.addText(String(bullet.title || ""), {
      x: x_position + 0.45,
      y: bullet_zone.y - 0.02,
      w: width - 0.58,
      h: 0.28,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_title_font_size", 11.6, { min: 6, max: 24 }),
      bold: true,
      color: overlay_color(slide_data, "bullet_title_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(bullet.body || ""), {
      x: x_position,
      y: bullet_zone.y + 0.42,
      w: width - 0.22,
      h: 0.38,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_body_font_size", 7.7, { min: 5, max: 15 }),
      color: overlay_color(slide_data, "bullet_body_color", theme.muted),
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_matrix_proof(slide, theme, slide_data, zones) {
  const chart = slide_data.chart || {};
  const labels = Array.isArray(chart.labels) ? chart.labels.slice(0, 4) : [];
  const values = Array.isArray(chart.values) ? chart.values.map(Number).slice(0, 4) : [];
  const chart_zone = zones.chart_zone;
  const colors = overlay_palette(slide_data, "chart_bar_colors", [theme.accent, theme.accent_2, "7D9A8F", "B38E52"]);
  slide.addText(String(chart.title || ""), {
    x: zones.chart_title_zone.x,
    y: zones.chart_title_zone.y,
    w: zones.chart_title_zone.w,
    h: zones.chart_title_zone.h,
    fontFace: theme.font_face,
    fontSize: overlay_number(slide_data, "chart_title_font_size", 11.8, { min: 6, max: 24 }),
    bold: true,
    color: overlay_color(slide_data, "chart_title_color", theme.foreground),
    margin: 0,
    fit: "shrink",
  });
  slide.addShape("line", {
    x: chart_zone.x,
    y: chart_zone.y + chart_zone.h / 2,
    w: chart_zone.w,
    h: 0,
    line: { color: overlay_color(slide_data, "chart_grid_color", "B9C2C4"), pt: 1.0, transparency: 35 },
  });
  slide.addShape("line", {
    x: chart_zone.x + chart_zone.w / 2,
    y: chart_zone.y,
    w: 0,
    h: chart_zone.h,
    line: { color: overlay_color(slide_data, "chart_grid_color", "B9C2C4"), pt: 1.0, transparency: 35 },
  });
  labels.forEach((label, index) => {
    const col = index % 2;
    const row = Math.floor(index / 2);
    const x_position = chart_zone.x + col * (chart_zone.w / 2) + 0.35;
    const y_position = chart_zone.y + row * (chart_zone.h / 2) + 0.36;
    const color = colors[index % colors.length];
    slide.addText(String(values[index] || ""), {
      x: x_position,
      y: y_position,
      w: 0.8,
      h: 0.32,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "chart_value_font_size", 13, { min: 6, max: 22 }),
      bold: true,
      color,
      margin: 0,
      fit: "shrink",
    });
    slide.addShape("ellipse", {
      x: x_position + 0.94,
      y: y_position + 0.1,
      w: 0.12,
      h: 0.12,
      fill: { color, transparency: 5 },
      line: { color, transparency: 100 },
    });
    slide.addText(String(label).replace(/\n/g, " / "), {
      x: x_position,
      y: y_position + 0.46,
      w: chart_zone.w / 2 - 0.62,
      h: 0.28,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "chart_label_font_size", 7.2, { min: 4, max: 14 }),
      color: overlay_color(slide_data, "chart_label_color", theme.muted),
      margin: 0,
      fit: "shrink",
    });
  });
  slide.addText(String(chart.source || ""), {
    x: chart_zone.x,
    y: chart_zone.y + chart_zone.h + 0.16,
    w: chart_zone.w,
    h: 0.12,
    fontFace: theme.font_face,
    fontSize: overlay_number(slide_data, "chart_source_font_size", 5.4, { min: 4, max: 10 }),
    color: overlay_color(slide_data, "chart_source_color", theme.muted),
    margin: 0,
    fit: "shrink",
  });
}

function add_reference_future_telemetry(slide, theme, slide_data, zones) {
  const metrics_zone = zones.metrics_zone;
  const metrics = Array.isArray(slide_data.metrics) ? slide_data.metrics.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "metric_value_colors", [theme.accent, theme.accent_2, "16E0B3"]);
  metrics.forEach((metric, index) => {
    const y_position = metrics_zone.y + index * 0.82;
    const color = colors[index % colors.length];
    slide.addText(String(metric.value || ""), {
      x: metrics_zone.x,
      y: y_position,
      w: metrics_zone.w,
      h: 0.32,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_value_font_size", 17.6, { min: 8, max: 34 }),
      bold: true,
      color,
      align: "right",
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(metric.label || ""), {
      x: metrics_zone.x,
      y: y_position + 0.38,
      w: metrics_zone.w,
      h: 0.18,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_label_font_size", 6.8, { min: 5, max: 16 }),
      bold: true,
      color: overlay_color(slide_data, "metric_label_color", theme.foreground),
      align: "right",
      margin: 0,
      fit: "shrink",
    });
    slide.addShape("line", {
      x: metrics_zone.x + metrics_zone.w - 0.58,
      y: y_position + 0.66,
      w: 0.58,
      h: 0,
      line: { color, pt: 1.8 },
    });
  });
}

function add_reference_future_ticker(slide, theme, slide_data, zones) {
  const bullet_zone = zones.bullet_zone;
  const bullets = Array.isArray(slide_data.bullets) ? slide_data.bullets.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "bullet_icon_colors", [theme.accent, theme.accent_2, "16E0B3"]);
  const width = bullet_zone.w / Math.max(bullets.length, 1);
  slide.addShape("line", {
    x: bullet_zone.x,
    y: bullet_zone.y - 0.16,
    w: bullet_zone.w,
    h: 0,
    line: { color: overlay_color(slide_data, "metrics_divider_color", colors[0]), pt: 1.0, transparency: 30 },
  });
  bullets.forEach((bullet, index) => {
    const x_position = bullet_zone.x + index * width;
    const color = colors[index % colors.length];
    slide.addShape("line", {
      x: x_position,
      y: bullet_zone.y,
      w: 0.46,
      h: 0,
      line: { color, pt: 2.0 },
    });
    slide.addText(String(bullet.title || ""), {
      x: x_position,
      y: bullet_zone.y + 0.18,
      w: width - 0.18,
      h: 0.22,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_title_font_size", 10.2, { min: 6, max: 20 }),
      bold: true,
      color: overlay_color(slide_data, "bullet_title_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(bullet.body || ""), {
      x: x_position,
      y: bullet_zone.y + 0.48,
      w: width - 0.25,
      h: 0.24,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_body_font_size", 7.0, { min: 5, max: 14 }),
      color: overlay_color(slide_data, "bullet_body_color", theme.muted),
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_launch_proof(slide, theme, slide_data, zones) {
  const chart = slide_data.chart || {};
  const chart_zone = zones.chart_zone;
  const labels = Array.isArray(chart.labels) ? chart.labels.slice(0, 4) : [];
  const values = Array.isArray(chart.values) ? chart.values.map(Number).slice(0, 4) : [];
  const max_value = Math.max(...values, 100);
  const colors = overlay_palette(slide_data, "chart_bar_colors", [theme.accent, "4E8DFF", theme.accent_2, "16E0B3"]);
  slide.addText(String(chart.title || ""), {
    x: zones.chart_title_zone.x,
    y: zones.chart_title_zone.y,
    w: zones.chart_title_zone.w,
    h: zones.chart_title_zone.h,
    fontFace: theme.font_face,
    fontSize: overlay_number(slide_data, "chart_title_font_size", 11.6, { min: 6, max: 24 }),
    bold: true,
    color: overlay_color(slide_data, "chart_title_color", theme.foreground),
    margin: 0,
    fit: "shrink",
  });
  const slot_w = chart_zone.w / Math.max(values.length, 1);
  values.forEach((value, index) => {
    const x_position = chart_zone.x + index * slot_w + slot_w * 0.26;
    const bar_h = 0.52 + (value / max_value) * 2.35;
    const y_position = chart_zone.y + chart_zone.h - bar_h;
    const color = colors[index % colors.length];
    slide.addShape("rect", {
      x: x_position,
      y: y_position,
      w: slot_w * 0.44,
      h: bar_h,
      fill: { color, transparency: overlay_number(slide_data, "chart_bar_transparency", 14, { min: 0, max: 100 }) },
      line: { color, transparency: 100 },
    });
    slide.addShape("line", {
      x: x_position + slot_w * 0.22,
      y: y_position - 0.2,
      w: 0,
      h: -0.22,
      line: { color, pt: 1.1, transparency: 20 },
    });
    slide.addText(String(value), {
      x: x_position - 0.08,
      y: y_position - 0.48,
      w: slot_w * 0.6,
      h: 0.18,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "chart_value_font_size", 8.5, { min: 4, max: 16 }),
      bold: true,
      color: overlay_color(slide_data, "chart_value_color", theme.foreground),
      align: "center",
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(labels[index] || "").replace(/\n/g, "\n"), {
      x: chart_zone.x + index * slot_w,
      y: chart_zone.y + chart_zone.h + 0.14,
      w: slot_w,
      h: 0.34,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "chart_label_font_size", 7.0, { min: 4, max: 14 }),
      color: overlay_color(slide_data, "chart_label_color", theme.muted),
      align: "center",
      margin: 0,
      fit: "shrink",
    });
  });
  slide.addText(String(chart.source || ""), {
    x: chart_zone.x + 0.2,
    y: chart_zone.y + chart_zone.h + 0.56,
    w: chart_zone.w,
    h: 0.12,
    fontFace: theme.font_face,
    fontSize: overlay_number(slide_data, "chart_source_font_size", 5.2, { min: 4, max: 10 }),
    color: overlay_color(slide_data, "chart_source_color", theme.muted),
    margin: 0,
    fit: "shrink",
  });
}

function add_reference_scroll_metrics(slide, theme, slide_data, zones) {
  const metrics_zone = zones.metrics_zone;
  const metrics = Array.isArray(slide_data.metrics) ? slide_data.metrics.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "metric_value_colors", [theme.accent, theme.accent_2, "1D1D1B"]);
  metrics.forEach((metric, index) => {
    const y_position = metrics_zone.y + index * 0.76;
    const color = colors[index % colors.length];
    slide.addText(String(metric.value || ""), {
      x: metrics_zone.x,
      y: y_position,
      w: metrics_zone.w,
      h: 0.28,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_value_font_size", 15.4, { min: 8, max: 34 }),
      bold: true,
      color,
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(metric.label || ""), {
      x: metrics_zone.x,
      y: y_position + 0.36,
      w: metrics_zone.w,
      h: 0.18,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_label_font_size", 6.8, { min: 5, max: 16 }),
      color: overlay_color(slide_data, "metric_label_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_scroll_columns(slide, theme, slide_data, zones) {
  const bullet_zone = zones.bullet_zone;
  const bullets = Array.isArray(slide_data.bullets) ? slide_data.bullets.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "bullet_icon_colors", [theme.accent, theme.accent_2, "1D1D1B"]);
  bullets.forEach((bullet, index) => {
    const x_position = bullet_zone.x + index * 1.23;
    const color = colors[index % colors.length];
    slide.addShape("line", {
      x: x_position,
      y: bullet_zone.y,
      w: 0,
      h: 2.6,
      line: { color, pt: 0.8, transparency: 35 },
    });
    slide.addText(String(index + 1), {
      x: x_position - 0.12,
      y: bullet_zone.y - 0.02,
      w: 0.3,
      h: 0.2,
      fontFace: theme.font_face,
      fontSize: 8,
      bold: true,
      color,
      margin: 0,
    });
    slide.addText(String(bullet.title || ""), {
      x: x_position + 0.22,
      y: bullet_zone.y + 0.15,
      w: 0.92,
      h: 0.72,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_title_font_size", 11.2, { min: 6, max: 22 }),
      bold: true,
      color: overlay_color(slide_data, "bullet_title_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(bullet.body || ""), {
      x: x_position + 0.22,
      y: bullet_zone.y + 1.02,
      w: 0.92,
      h: 1.26,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_body_font_size", 7.2, { min: 5, max: 14 }),
      color: overlay_color(slide_data, "bullet_body_color", theme.muted),
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_path_proof(slide, theme, slide_data, zones) {
  const chart = slide_data.chart || {};
  const chart_zone = zones.chart_zone;
  const labels = Array.isArray(chart.labels) ? chart.labels.slice(0, 4) : [];
  const values = Array.isArray(chart.values) ? chart.values.map(Number).slice(0, 4) : [];
  const colors = overlay_palette(slide_data, "chart_bar_colors", [theme.accent, theme.accent_2, "C34F33", "B88A3B"]);
  slide.addText(String(chart.title || ""), {
    x: zones.chart_title_zone.x,
    y: zones.chart_title_zone.y,
    w: zones.chart_title_zone.w,
    h: zones.chart_title_zone.h,
    fontFace: theme.font_face,
    fontSize: overlay_number(slide_data, "chart_title_font_size", 10.8, { min: 6, max: 24 }),
    bold: true,
    color: overlay_color(slide_data, "chart_title_color", theme.foreground),
    margin: 0,
    fit: "shrink",
  });
  const slot_w = chart_zone.w / Math.max(values.length, 1);
  const points = values.map((value, index) => ({
    x: chart_zone.x + index * slot_w + slot_w * 0.5,
    y: chart_zone.y + 0.58 - (value / Math.max(...values, 100)) * 0.42,
    value,
    label: labels[index],
  }));
  points.slice(0, -1).forEach((point, index) => {
    const next_point = points[index + 1];
    slide.addShape("line", {
      x: point.x,
      y: point.y,
      w: next_point.x - point.x,
      h: next_point.y - point.y,
      line: { color: overlay_color(slide_data, "chart_accent_color", theme.accent), pt: 1.6 },
    });
  });
  points.forEach((point, index) => {
    const color = colors[index % colors.length];
    slide.addShape("ellipse", {
      x: point.x - 0.09,
      y: point.y - 0.09,
      w: 0.18,
      h: 0.18,
      fill: { color: "FFFFFF" },
      line: { color, pt: 1.2 },
    });
    slide.addText(String(point.value), {
      x: point.x - 0.22,
      y: point.y - 0.36,
      w: 0.44,
      h: 0.16,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "chart_value_font_size", 7.4, { min: 4, max: 16 }),
      bold: true,
      color: overlay_color(slide_data, "chart_value_color", theme.foreground),
      align: "center",
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(point.label || "").replace(/\n/g, "\n"), {
      x: point.x - 0.4,
      y: chart_zone.y + 0.72,
      w: 0.8,
      h: 0.24,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "chart_label_font_size", 6.4, { min: 4, max: 14 }),
      color: overlay_color(slide_data, "chart_label_color", theme.muted),
      align: "center",
      margin: 0,
      fit: "shrink",
    });
  });
  slide.addText(String(chart.source || ""), {
    x: chart_zone.x,
    y: chart_zone.y + chart_zone.h + 0.1,
    w: chart_zone.w,
    h: 0.12,
    fontFace: theme.font_face,
    fontSize: overlay_number(slide_data, "chart_source_font_size", 5.0, { min: 4, max: 10 }),
    color: overlay_color(slide_data, "chart_source_color", theme.muted),
    margin: 0,
    fit: "shrink",
  });
}

function add_reference_feature_story(slide, theme, slide_data, zones) {
  const bullet_zone = zones.bullet_zone;
  const bullets = Array.isArray(slide_data.bullets) ? slide_data.bullets.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "bullet_icon_colors", [theme.accent, theme.accent_2, "6F7E8B"]);
  bullets.forEach((bullet, index) => {
    const y_position = bullet_zone.y + index * 0.68;
    const color = colors[index % colors.length];
    slide.addText(String(index + 1).padStart(2, "0"), {
      x: bullet_zone.x,
      y: y_position,
      w: 0.34,
      h: 0.16,
      fontFace: theme.font_face,
      fontSize: 6.8,
      bold: true,
      color,
      margin: 0,
    });
    slide.addText(String(bullet.title || ""), {
      x: bullet_zone.x + 0.48,
      y: y_position - 0.04,
      w: bullet_zone.w - 0.56,
      h: 0.24,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_title_font_size", 11.2, { min: 6, max: 22 }),
      bold: true,
      color: overlay_color(slide_data, "bullet_title_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(bullet.body || ""), {
      x: bullet_zone.x + 0.48,
      y: y_position + 0.27,
      w: bullet_zone.w - 0.7,
      h: 0.22,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "bullet_body_font_size", 7.2, { min: 5, max: 14 }),
      color: overlay_color(slide_data, "bullet_body_color", theme.muted),
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_feature_metrics(slide, theme, slide_data, zones) {
  const metrics_zone = zones.metrics_zone;
  const metrics = Array.isArray(slide_data.metrics) ? slide_data.metrics.slice(0, 3) : [];
  const colors = overlay_palette(slide_data, "metric_value_colors", [theme.accent_2, theme.foreground, theme.accent]);
  const width = metrics_zone.w / Math.max(metrics.length, 1);
  metrics.forEach((metric, index) => {
    const x_position = metrics_zone.x + index * width;
    const color = colors[index % colors.length];
    slide.addText(String(metric.value || ""), {
      x: x_position,
      y: metrics_zone.y,
      w: width - 0.12,
      h: 0.34,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_value_font_size", 17.5, { min: 8, max: 34 }),
      bold: true,
      color,
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(metric.label || ""), {
      x: x_position,
      y: metrics_zone.y + 0.42,
      w: width - 0.18,
      h: 0.18,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "metric_label_font_size", 6.8, { min: 5, max: 16 }),
      bold: true,
      color: overlay_color(slide_data, "metric_label_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
  });
}

function add_reference_feature_proof(slide, theme, slide_data, zones) {
  const chart = slide_data.chart || {};
  const chart_zone = zones.chart_zone;
  const labels = Array.isArray(chart.labels) ? chart.labels.slice(0, 4) : [];
  const values = Array.isArray(chart.values) ? chart.values.map(Number).slice(0, 4) : [];
  const max_value = Math.max(...values, 100);
  const colors = overlay_palette(slide_data, "chart_bar_colors", [theme.accent, "C45F54", theme.accent_2, "6F7E8B"]);
  slide.addText(String(chart.title || ""), {
    x: zones.chart_title_zone.x,
    y: zones.chart_title_zone.y,
    w: zones.chart_title_zone.w,
    h: zones.chart_title_zone.h,
    fontFace: theme.font_face,
    fontSize: overlay_number(slide_data, "chart_title_font_size", 11.2, { min: 6, max: 24 }),
    bold: true,
    color: overlay_color(slide_data, "chart_title_color", theme.foreground),
    margin: 0,
    fit: "shrink",
  });
  const slot_w = chart_zone.w / Math.max(values.length, 1);
  values.forEach((value, index) => {
    const x_position = chart_zone.x + 1.18;
    const width = chart_zone.w - 1.62;
    const y_position = chart_zone.y + 0.3 + index * 0.42;
    const color = colors[index % colors.length];
    slide.addShape("rect", {
      x: x_position,
      y: y_position,
      w: (value / max_value) * width,
      h: 0.16,
      fill: { color, transparency: overlay_number(slide_data, "chart_bar_transparency", 10, { min: 0, max: 100 }) },
      line: { color, transparency: 100 },
    });
    slide.addText(String(value), {
      x: x_position + (value / max_value) * width + 0.08,
      y: y_position - 0.04,
      w: 0.42,
      h: 0.14,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "chart_value_font_size", 7.2, { min: 4, max: 16 }),
      bold: true,
      color: overlay_color(slide_data, "chart_value_color", theme.foreground),
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(labels[index] || "").replace(/\n/g, " / "), {
      x: chart_zone.x,
      y: y_position - 0.03,
      w: 0.95,
      h: 0.14,
      fontFace: theme.font_face,
      fontSize: overlay_number(slide_data, "chart_label_font_size", 6.2, { min: 4, max: 14 }),
      color: overlay_color(slide_data, "chart_label_color", theme.muted),
      align: "right",
      margin: 0,
      fit: "shrink",
    });
  });
  slide.addText(String(chart.source || ""), {
    x: chart_zone.x,
    y: chart_zone.y + chart_zone.h + 0.16,
    w: chart_zone.w,
    h: 0.12,
    fontFace: theme.font_face,
    fontSize: overlay_number(slide_data, "chart_source_font_size", 5.0, { min: 4, max: 10 }),
    color: overlay_color(slide_data, "chart_source_color", theme.muted),
    margin: 0,
    fit: "shrink",
  });
}

function add_reference_anime_trend_slide(pptx, theme, slide_data, spec_dir, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_reference_background(slide, theme, slide_data, spec_dir);
  const variant = reference_layout_variant(slide_data);
  const defaults = reference_zone_defaults(variant);
  const blueprint = slide_data.coordinate_blueprint || {};
  const zones = {
    title_zone: zone_value(blueprint, "title_zone", defaults.title_zone),
    subtitle_zone: zone_value(blueprint, "subtitle_zone", defaults.subtitle_zone),
    bullet_zone: zone_value(blueprint, "bullet_zone", defaults.bullet_zone),
    metrics_zone: zone_value(blueprint, "metrics_zone", defaults.metrics_zone),
    chart_title_zone: zone_value(blueprint, "chart_title_zone", defaults.chart_title_zone),
    chart_zone: zone_value(blueprint, "chart_zone", defaults.chart_zone),
  };
  add_reference_anime_title(slide, theme, slide_data, zones);
  if (variant === "future_dashboard_focus") {
    add_reference_anime_chart(slide, theme, slide_data, zones);
    add_reference_signal_bullets(slide, theme, slide_data, zones);
    add_reference_future_metrics(slide, theme, slide_data, zones);
  } else if (variant === "boardroom_summary_matrix") {
    add_reference_boardroom_metrics(slide, theme, slide_data, zones);
    add_reference_matrix_proof(slide, theme, slide_data, zones);
    add_reference_boardroom_insights(slide, theme, slide_data, zones);
  } else if (variant === "future_launch_stage") {
    add_reference_launch_proof(slide, theme, slide_data, zones);
    add_reference_future_telemetry(slide, theme, slide_data, zones);
    add_reference_future_ticker(slide, theme, slide_data, zones);
  } else if (variant === "oriental_scroll_narrative") {
    add_reference_scroll_columns(slide, theme, slide_data, zones);
    add_reference_path_proof(slide, theme, slide_data, zones);
    add_reference_scroll_metrics(slide, theme, slide_data, zones);
  } else if (variant === "editorial_feature_spread") {
    add_reference_feature_story(slide, theme, slide_data, zones);
    add_reference_feature_proof(slide, theme, slide_data, zones);
    add_reference_feature_metrics(slide, theme, slide_data, zones);
  } else if (variant === "oriental_vertical_scroll") {
    add_reference_oriental_bullets(slide, theme, slide_data, zones);
    add_reference_anime_chart(slide, theme, slide_data, zones);
    add_reference_vertical_metrics(slide, theme, slide_data, zones);
  } else if (variant === "editorial_feature_story") {
    add_reference_editorial_bullets(slide, theme, slide_data, zones);
    add_reference_anime_chart(slide, theme, slide_data, zones);
    add_reference_editorial_metrics(slide, theme, slide_data, zones);
  } else {
    add_reference_anime_bullets(slide, theme, slide_data, zones);
    add_reference_anime_metrics(slide, theme, slide_data, zones);
    add_reference_anime_chart(slide, theme, slide_data, zones);
  }
  add_footer(slide, theme, slide_index, total_slides);
}

function add_title_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  slide.addShape("rect", {
    x: 0.72,
    y: 0.82,
    w: 0.72,
    h: 0.12,
    fill: { color: theme.accent_2 },
    line: { color: theme.accent_2, transparency: 100 },
  });
  add_title(slide, theme, slide_data.title, {
    x: 0.72,
    y: 1.08,
    w: 6.75,
    h: 1.85,
    font_size: 30,
  });
  add_body(slide, theme, slide_data.subtitle || slide_data.body || "", {
    x: 0.75,
    y: 3.12,
    w: 5.95,
    h: 1.05,
    font_size: 14,
    color: theme.muted,
  });
  slide.addShape("rect", {
    x: 7.95,
    y: 0.9,
    w: 4.05,
    h: 5.35,
    fill: { color: theme.panel, transparency: 9 },
    line: { color: theme.accent, transparency: 45 },
    radius: 0.18,
  });
  const panel_steps = [
    ["01", "确定主题"],
    ["02", "选择风格"],
    ["03", "生成素材"],
    ["04", "交付文件"],
  ];
  panel_steps.forEach((step, index) => {
    const y_position = 1.35 + index * 0.83;
    slide.addShape("ellipse", {
      x: 8.38,
      y: y_position,
      w: 0.42,
      h: 0.42,
      fill: { color: index % 2 === 0 ? theme.accent : theme.accent_2 },
      line: { color: "FFFFFF", pt: 1 },
    });
    slide.addText(step[0], {
      x: 8.42,
      y: y_position + 0.11,
      w: 0.34,
      h: 0.12,
      fontFace: theme.font_face,
      fontSize: 6.5,
      bold: true,
      color: "FFFFFF",
      align: "center",
      margin: 0,
    });
    slide.addText(step[1], {
      x: 9.02,
      y: y_position + 0.08,
      w: 1.65,
      h: 0.22,
      fontFace: theme.font_face,
      fontSize: 11,
      color: theme.foreground,
      bold: true,
      margin: 0,
    });
  });
  slide.addShape("line", {
    x: 8.58,
    y: 1.78,
    w: 0,
    h: 2.42,
    line: { color: theme.accent, pt: 1.2, transparency: 28 },
  });
  slide.addText(slide_data.kicker || "视觉化交付系统", {
    x: 8.38,
    y: 5.15,
    w: 3.1,
    h: 0.32,
    fontFace: theme.font_face,
    fontSize: 11,
    color: theme.foreground,
    bold: true,
    align: "center",
    margin: 0,
  });
  add_footer(slide, theme, slide_index, total_slides);
}

function add_content_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  add_title(slide, theme, slide_data.title);
  add_claim(slide, theme, slide_data.claim, { y: 1.28, w: 6.3 });
  add_body(slide, theme, slide_data.body || "", {
    x: 0.76,
    y: slide_data.claim ? 2.04 : 1.55,
    w: 5.45,
    h: 1.2,
    font_size: 14,
    color: theme.muted,
  });
  add_bullets(slide, theme, slide_data.bullets, {
    x: 0.82,
    y: 3.05,
    w: 5.2,
    h: 2.55,
    font_size: 14,
  });
  slide.addShape("rect", {
    x: 7.0,
    y: 1.48,
    w: 4.9,
    h: 4.55,
    fill: { color: theme.panel, transparency: 7 },
    line: { color: theme.accent, transparency: 58 },
  });
  add_source_note(slide, theme, slide_data.source);
  add_footer(slide, theme, slide_index, total_slides);
}

function add_image_text_slide(pptx, theme, slide_data, spec_dir, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  add_title(slide, theme, slide_data.title);
  add_claim(slide, theme, slide_data.claim, { y: 1.28, w: 6.05 });
  add_body(slide, theme, slide_data.body || "", {
    x: 0.76,
    y: slide_data.claim ? 2.04 : 1.55,
    w: 5.35,
    h: 1.1,
    font_size: 14,
    color: theme.muted,
  });
  add_bullets(slide, theme, slide_data.bullets, {
    x: 0.84,
    y: 2.9,
    w: 4.95,
    h: 2.7,
    font_size: 13.5,
  });
  slide.addShape("rect", {
    x: 6.65,
    y: 1.28,
    w: 5.45,
    h: 5.15,
    fill: { color: theme.panel, transparency: 4 },
    line: { color: "D8DEE9", transparency: 20 },
  });
  add_image(slide, resolve_asset_path(slide_data.image, spec_dir), {
    x: 7.0,
    y: 1.6,
    w: 4.75,
    h: 4.45,
  });
  add_source_note(slide, theme, slide_data.source);
  add_footer(slide, theme, slide_index, total_slides);
}

function add_bar_chart_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  add_title(slide, theme, slide_data.title);
  add_claim(slide, theme, slide_data.claim, { y: 1.22, w: 10.2 });
  add_body(slide, theme, slide_data.body || "", {
    x: 0.76,
    y: slide_data.claim ? 1.98 : 1.45,
    w: 10.6,
    h: 0.55,
    font_size: 13,
    color: theme.muted,
  });
  const chart = slide_data.chart || {};
  const labels = Array.isArray(chart.labels) ? chart.labels : [];
  const values = Array.isArray(chart.values) ? chart.values.map(Number) : [];
  if (labels.length === 0 || values.length === 0 || labels.length !== values.length) {
    throw new Error(`bar_chart slide requires chart.labels and chart.values with same length: ${slide_data.title || ""}`);
  }
  const max_value = Math.max(...values, 1);
  const chart_x = 1.05;
  const chart_y = 2.3;
  const chart_w = 10.95;
  const chart_h = 3.75;
  const gap = 0.28;
  const bar_w = (chart_w - gap * (values.length - 1)) / values.length;
  slide.addShape("line", {
    x: chart_x,
    y: chart_y + chart_h,
    w: chart_w,
    h: 0,
    line: { color: "CBD5E1", pt: 1 },
  });
  values.forEach((value, index) => {
    const bar_h = (value / max_value) * (chart_h - 0.45);
    const x_position = chart_x + index * (bar_w + gap);
    const y_position = chart_y + chart_h - bar_h;
    const fill_color = index % 2 === 0 ? theme.accent : theme.accent_2;
    slide.addShape("rect", {
      x: x_position,
      y: y_position,
      w: bar_w,
      h: bar_h,
      fill: { color: fill_color },
      line: { color: fill_color, transparency: 100 },
    });
    slide.addText(`${value}${chart.unit || ""}`, {
      x: x_position,
      y: y_position - 0.32,
      w: bar_w,
      h: 0.24,
      fontFace: theme.font_face,
      fontSize: 11,
      bold: true,
      color: theme.foreground,
      align: "center",
      margin: 0,
    });
    slide.addText(String(labels[index]), {
      x: x_position,
      y: chart_y + chart_h + 0.18,
      w: bar_w,
      h: 0.28,
      fontFace: theme.font_face,
      fontSize: 10,
      color: theme.muted,
      align: "center",
      margin: 0,
      fit: "shrink",
    });
  });
  add_source_note(slide, theme, chart.source || slide_data.source);
  add_footer(slide, theme, slide_index, total_slides);
}

function add_comparison_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  add_title(slide, theme, slide_data.title);
  add_claim(slide, theme, slide_data.claim, { y: 1.24, w: 10.2 });
  const items = Array.isArray(slide_data.items) ? slide_data.items : [];
  const item_count = Math.max(items.length, 1);
  const card_w = Math.min(3.55, 10.9 / item_count - 0.2);
  items.forEach((item, index) => {
    const x_position = 0.9 + index * (card_w + 0.32);
    slide.addShape("rect", {
      x: x_position,
      y: 1.75,
      w: card_w,
      h: 4.55,
      fill: { color: theme.panel, transparency: 3 },
      line: { color: index % 2 === 0 ? theme.accent : theme.accent_2, transparency: 35 },
    });
    slide.addText(String(item.title || ""), {
      x: x_position + 0.22,
      y: 2.06,
      w: card_w - 0.44,
      h: 0.42,
      fontFace: theme.font_face,
      fontSize: 15,
      bold: true,
      color: theme.foreground,
      margin: 0,
      fit: "shrink",
    });
    add_body(slide, theme, item.body || "", {
      x: x_position + 0.22,
      y: 2.78,
      w: card_w - 0.44,
      h: 2.5,
      font_size: 12,
      color: theme.muted,
    });
  });
  add_source_note(slide, theme, slide_data.source);
  add_footer(slide, theme, slide_index, total_slides);
}

function add_timeline_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  add_title(slide, theme, slide_data.title);
  add_claim(slide, theme, slide_data.claim, { y: 1.24, w: 10.2 });
  const steps = Array.isArray(slide_data.steps) ? slide_data.steps : [];
  slide.addShape("line", {
    x: 1.12,
    y: 3.75,
    w: 10.75,
    h: 0,
    line: { color: theme.accent, pt: 2 },
  });
  steps.forEach((step, index) => {
    const x_position = 1.05 + index * (10.45 / Math.max(steps.length - 1, 1));
    slide.addShape("ellipse", {
      x: x_position - 0.16,
      y: 3.58,
      w: 0.32,
      h: 0.32,
      fill: { color: index % 2 === 0 ? theme.accent : theme.accent_2 },
      line: { color: "FFFFFF", pt: 1 },
    });
    slide.addText(String(step.label || step.title || ""), {
      x: x_position - 0.8,
      y: 4.05,
      w: 1.6,
      h: 0.35,
      fontFace: theme.font_face,
      fontSize: 11,
      bold: true,
      color: theme.foreground,
      align: "center",
      margin: 0,
      fit: "shrink",
    });
    add_body(slide, theme, step.body || "", {
      x: x_position - 0.9,
      y: 4.5,
      w: 1.8,
      h: 0.85,
      font_size: 9,
      color: theme.muted,
    });
  });
  add_source_note(slide, theme, slide_data.source);
  add_footer(slide, theme, slide_index, total_slides);
}

function add_executive_summary_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  add_title(slide, theme, slide_data.title);
  add_claim(slide, theme, slide_data.claim, { y: 1.24, w: 10.4 });
  const points = Array.isArray(slide_data.points) ? slide_data.points : [];
  points.slice(0, 3).forEach((point, index) => {
    const x_position = 0.82 + index * 4.05;
    slide.addShape("rect", {
      x: x_position,
      y: 2.05,
      w: 3.55,
      h: 3.6,
      fill: { color: theme.panel, transparency: 3 },
      line: { color: index % 2 === 0 ? theme.accent : theme.accent_2, transparency: 40 },
    });
    slide.addText(String(point.label || `0${index + 1}`), {
      x: x_position + 0.28,
      y: 2.34,
      w: 0.65,
      h: 0.28,
      fontFace: theme.font_face,
      fontSize: 10,
      bold: true,
      color: index % 2 === 0 ? theme.accent : theme.accent_2,
      margin: 0,
    });
    slide.addText(String(point.title || ""), {
      x: x_position + 0.28,
      y: 2.82,
      w: 2.82,
      h: 0.62,
      fontFace: theme.font_face,
      fontSize: 16,
      bold: true,
      color: theme.foreground,
      margin: 0,
      fit: "shrink",
    });
    add_body(slide, theme, point.body || "", {
      x: x_position + 0.28,
      y: 3.68,
      w: 2.9,
      h: 1.25,
      font_size: 11.5,
      color: theme.muted,
    });
  });
  add_source_note(slide, theme, slide_data.source);
  add_footer(slide, theme, slide_index, total_slides);
}

function add_architecture_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  add_title(slide, theme, slide_data.title);
  add_claim(slide, theme, slide_data.claim, { y: 1.24, w: 10.4 });
  const layers = Array.isArray(slide_data.layers) ? slide_data.layers : [];
  layers.slice(0, 4).forEach((layer, index) => {
    const y_position = 2.0 + index * 1.02;
    slide.addShape("rect", {
      x: 1.0,
      y: y_position,
      w: 10.9,
      h: 0.72,
      fill: { color: index % 2 === 0 ? theme.panel : theme.background, transparency: index % 2 === 0 ? 2 : 0 },
      line: { color: index % 2 === 0 ? theme.accent : theme.accent_2, transparency: 35 },
    });
    slide.addText(String(layer.title || ""), {
      x: 1.26,
      y: y_position + 0.18,
      w: 2.2,
      h: 0.22,
      fontFace: theme.font_face,
      fontSize: 12.5,
      bold: true,
      color: theme.foreground,
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(layer.body || ""), {
      x: 3.72,
      y: y_position + 0.16,
      w: 7.6,
      h: 0.26,
      fontFace: theme.font_face,
      fontSize: 10.5,
      color: theme.muted,
      margin: 0,
      fit: "shrink",
    });
  });
  add_source_note(slide, theme, slide_data.source);
  add_footer(slide, theme, slide_index, total_slides);
}

function add_metrics_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  add_title(slide, theme, slide_data.title);
  add_claim(slide, theme, slide_data.claim, { y: 1.22, w: 10.2 });
  const metrics = Array.isArray(slide_data.metrics) ? slide_data.metrics : [];
  metrics.slice(0, 4).forEach((metric, index) => {
    const x_position = 0.86 + index * 3.05;
    slide.addText(String(metric.value || ""), {
      x: x_position,
      y: 2.35,
      w: 2.4,
      h: 0.58,
      fontFace: theme.font_face,
      fontSize: 24,
      bold: true,
      color: index % 2 === 0 ? theme.accent : theme.accent_2,
      margin: 0,
      fit: "shrink",
    });
    slide.addText(String(metric.label || ""), {
      x: x_position,
      y: 3.0,
      w: 2.35,
      h: 0.28,
      fontFace: theme.font_face,
      fontSize: 10.5,
      bold: true,
      color: theme.foreground,
      margin: 0,
      fit: "shrink",
    });
    add_body(slide, theme, metric.body || "", {
      x: x_position,
      y: 3.42,
      w: 2.35,
      h: 0.75,
      font_size: 9.5,
      color: theme.muted,
    });
  });
  if (slide_data.chart) {
    const chart = slide_data.chart;
    const labels = Array.isArray(chart.labels) ? chart.labels : [];
    const values = Array.isArray(chart.values) ? chart.values.map(Number) : [];
    const max_value = Math.max(...values, 1);
    labels.forEach((label, index) => {
      const x_position = 1.05 + index * 2.1;
      const bar_h = (values[index] / max_value) * 1.05;
      slide.addShape("rect", {
        x: x_position,
        y: 5.75 - bar_h,
        w: 1.15,
        h: bar_h,
        fill: { color: index % 2 === 0 ? theme.accent : theme.accent_2 },
        line: { color: theme.background, transparency: 100 },
      });
      slide.addText(String(label), {
        x: x_position - 0.18,
        y: 5.9,
        w: 1.5,
        h: 0.2,
        fontFace: theme.font_face,
        fontSize: 8.5,
        color: theme.muted,
        align: "center",
        margin: 0,
        fit: "shrink",
      });
    });
  }
  add_source_note(slide, theme, slide_data.source || (slide_data.chart && slide_data.chart.source));
  add_footer(slide, theme, slide_index, total_slides);
}

function add_roadmap_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  add_title(slide, theme, slide_data.title);
  add_claim(slide, theme, slide_data.claim, { y: 1.24, w: 10.2 });
  const phases = Array.isArray(slide_data.phases) ? slide_data.phases : [];
  phases.slice(0, 4).forEach((phase, index) => {
    const x_position = 0.86 + index * 3.05;
    slide.addShape("rect", {
      x: x_position,
      y: 2.15,
      w: 2.55,
      h: 3.7,
      fill: { color: theme.panel, transparency: 5 },
      line: { color: index % 2 === 0 ? theme.accent : theme.accent_2, transparency: 35 },
    });
    slide.addText(String(phase.period || `Phase ${index + 1}`), {
      x: x_position + 0.2,
      y: 2.44,
      w: 2.0,
      h: 0.22,
      fontFace: theme.font_face,
      fontSize: 9.5,
      bold: true,
      color: index % 2 === 0 ? theme.accent : theme.accent_2,
      margin: 0,
    });
    slide.addText(String(phase.title || ""), {
      x: x_position + 0.2,
      y: 2.86,
      w: 2.05,
      h: 0.45,
      fontFace: theme.font_face,
      fontSize: 13,
      bold: true,
      color: theme.foreground,
      margin: 0,
      fit: "shrink",
    });
    add_body(slide, theme, phase.body || "", {
      x: x_position + 0.2,
      y: 3.58,
      w: 2.05,
      h: 1.3,
      font_size: 9.8,
      color: theme.muted,
    });
  });
  add_source_note(slide, theme, slide_data.source);
  add_footer(slide, theme, slide_index, total_slides);
}

function add_risk_next_steps_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  add_title(slide, theme, slide_data.title);
  add_claim(slide, theme, slide_data.claim, { y: 1.24, w: 10.2 });
  const risks = Array.isArray(slide_data.risks) ? slide_data.risks : [];
  const actions = Array.isArray(slide_data.actions) ? slide_data.actions : [];
  slide.addText("主要风险", {
    x: 0.9,
    y: 2.02,
    w: 4.6,
    h: 0.28,
    fontFace: theme.font_face,
    fontSize: 14,
    bold: true,
    color: theme.foreground,
    margin: 0,
  });
  slide.addText("下一步动作", {
    x: 6.85,
    y: 2.02,
    w: 4.6,
    h: 0.28,
    fontFace: theme.font_face,
    fontSize: 14,
    bold: true,
    color: theme.foreground,
    margin: 0,
  });
  add_bullets(slide, theme, risks, { x: 0.95, y: 2.55, w: 4.8, h: 3.1, font_size: 12 });
  add_bullets(slide, theme, actions, { x: 6.9, y: 2.55, w: 4.8, h: 3.1, font_size: 12 });
  slide.addShape("line", {
    x: 6.28,
    y: 2.0,
    w: 0,
    h: 3.9,
    line: { color: theme.accent, pt: 1.2, transparency: 45 },
  });
  add_source_note(slide, theme, slide_data.source);
  add_footer(slide, theme, slide_index, total_slides);
}

function add_closing_slide(pptx, theme, slide_data, slide_index, total_slides) {
  const slide = pptx.addSlide();
  add_background(slide, theme, slide_data);
  slide.addShape("rect", {
    x: 0.75,
    y: 1.25,
    w: 11.2,
    h: 4.8,
    fill: { color: theme.panel, transparency: 5 },
    line: { color: theme.accent, transparency: 45 },
  });
  add_title(slide, theme, slide_data.title, {
    x: 1.15,
    y: 2.1,
    w: 8.8,
    h: 0.95,
    font_size: 30,
  });
  add_body(slide, theme, slide_data.body || "", {
    x: 1.18,
    y: 3.25,
    w: 6.8,
    h: 0.9,
    font_size: 15,
    color: theme.muted,
  });
  add_footer(slide, theme, slide_index, total_slides);
}

function add_slide_by_layout(pptx, theme, slide_data, spec_dir, slide_index, total_slides) {
  const layout = String(slide_data.layout || "content");
  if (layout === "title") {
    add_title_slide(pptx, theme, slide_data, slide_index, total_slides);
  } else if (layout === "image_text") {
    add_image_text_slide(pptx, theme, slide_data, spec_dir, slide_index, total_slides);
  } else if (layout === "bar_chart") {
    add_bar_chart_slide(pptx, theme, slide_data, slide_index, total_slides);
  } else if (layout === "comparison") {
    add_comparison_slide(pptx, theme, slide_data, slide_index, total_slides);
  } else if (layout === "timeline") {
    add_timeline_slide(pptx, theme, slide_data, slide_index, total_slides);
  } else if (layout === "executive_summary") {
    add_executive_summary_slide(pptx, theme, slide_data, slide_index, total_slides);
  } else if (layout === "architecture") {
    add_architecture_slide(pptx, theme, slide_data, slide_index, total_slides);
  } else if (layout === "metrics") {
    add_metrics_slide(pptx, theme, slide_data, slide_index, total_slides);
  } else if (layout === "roadmap") {
    add_roadmap_slide(pptx, theme, slide_data, slide_index, total_slides);
  } else if (layout === "risk_next_steps") {
    add_risk_next_steps_slide(pptx, theme, slide_data, slide_index, total_slides);
  } else if (layout === "reference_anime_trend" || layout === "reference_visual_trend") {
    add_reference_anime_trend_slide(pptx, theme, slide_data, spec_dir, slide_index, total_slides);
  } else if (layout === "closing" || layout === "section") {
    add_closing_slide(pptx, theme, slide_data, slide_index, total_slides);
  } else {
    add_content_slide(pptx, theme, slide_data, slide_index, total_slides);
  }
}

async function build_deck(spec_path, output_path) {
  const spec_dir = path.dirname(path.resolve(spec_path));
  const spec = normalize_spec(read_json(spec_path));
  const absolute_output = ensure_output_path(output_path);
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = spec.author || "Codex";
  pptx.subject = spec.subtitle || spec.title;
  pptx.title = spec.title;
  pptx.company = "Codex";
  pptx.lang = "zh-CN";
  pptx.theme = {
    headFontFace: spec.theme.font_face,
    bodyFontFace: spec.theme.font_face,
    lang: "zh-CN",
  };

  spec.slides.forEach((slide_data, index) => {
    add_slide_by_layout(
      pptx,
      spec.theme,
      slide_data,
      spec_dir,
      index + 1,
      spec.slides.length
    );
  });

  await pptx.writeFile({ fileName: absolute_output, compression: true });
  console.log(
    JSON.stringify(
      {
        ok: true,
        output: absolute_output,
        slide_count: spec.slides.length,
      },
      null,
      2
    )
  );
}

async function main() {
  let args;
  try {
    args = parse_args(process.argv);
  } catch (error) {
    fail(`${error.message}\n\n${usage()}`);
  }
  if (args.help) {
    console.log(usage());
    return;
  }
  try {
    await build_deck(args.spec, args.output);
  } catch (error) {
    fail(error.message);
  }
}

main();
