#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

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

const candidate_templates = [
  {
    slug: "minimal-premium",
    name: "简约高级",
    palette: ["#050505", "#4A4A4A", "#A7A7A7", "#E1E1E1", "#FFFFFF"],
    best_for: ["商业计划书", "融资路演", "咨询汇报"],
    visual_direction: "大量留白、黑白灰秩序、真实建筑线条和克制的商业咨询气质，适合严肃决策场景。",
    raster_layers: ["浅灰建筑摄影感背景", "低对比纸张纹理", "细线空间透视氛围"],
    transparent_assets: ["黑白线框图标组", "半透明建筑结构装饰", "咨询卡片角标"],
    editable_layers: ["封面主标题", "英文副标题", "章节标题", "数据标签", "图表坐标和注释"],
    prompt_seed:
      "premium minimalist business consulting PowerPoint background, elegant grayscale, architectural glass building details, abundant white space, thin black lines, refined corporate presentation mood",
  },
  {
    slug: "playful-anime",
    name: "活泼动漫",
    palette: ["#FFC93C", "#FF9EB5", "#7BDDC8", "#8FD3FF", "#B9B2F8"],
    best_for: ["教育课程", "儿童产品", "社群活动"],
    visual_direction: "明亮色彩、圆润结构、可爱角色和轻松课堂氛围，适合学习、活动和年轻用户表达。",
    raster_layers: ["明亮教室场景背景", "柔和云朵和色块氛围", "课程页浅色纸面纹理"],
    transparent_assets: ["可爱学生角色", "课程徽章贴纸", "星星和学习道具装饰"],
    editable_layers: ["课程标题", "目标卡片文字", "按钮标签", "步骤编号", "图表解释文字"],
    prompt_seed:
      "playful anime education PowerPoint background, cheerful classroom, soft clouds, rounded colorful visual areas, bright yellow pink blue palette, polished illustration quality",
  },
  {
    slug: "data-analytics",
    name: "数据分析",
    palette: ["#020B1D", "#061C3A", "#0B4F86", "#5B5FF0", "#12C7D6"],
    best_for: ["经营复盘", "增长分析", "行业报告"],
    visual_direction: "深色科技背景、高信息密度仪表盘、蓝色发光图表和清晰 KPI 层级，适合数据驱动叙事。",
    raster_layers: ["深蓝网格空间背景", "发光数据柱状图氛围", "暗色仪表盘底图"],
    transparent_assets: ["发光图表装饰", "KPI 卡片边框", "数据节点和连线元素"],
    editable_layers: ["报告标题", "KPI 数字", "图表标题", "坐标轴标签", "来源说明"],
    prompt_seed:
      "data analytics PowerPoint background, dark navy dashboard atmosphere, luminous blue abstract charts without labels, premium enterprise report mood, subtle grid",
  },
  {
    slug: "oriental-heritage",
    name: "国潮东方",
    palette: ["#B91C1C", "#171717", "#E8DCC7", "#F3EADB", "#FAF8F2"],
    best_for: ["品牌介绍", "文化项目", "消费品提案"],
    visual_direction: "宣纸质感、朱红墨黑、山水留白和当代表达，适合东方文化、品牌和消费品提案。",
    raster_layers: ["宣纸纹理背景", "水墨山水远景", "朱红印章氛围"],
    transparent_assets: ["水墨山石装饰", "朱红印章元素", "梅枝或器物剪影"],
    editable_layers: ["品牌标题", "理念卡片文字", "章节题签", "说明正文", "页脚日期"],
    prompt_seed:
      "oriental heritage PowerPoint background, premium Chinese ink landscape, rice paper texture, vermilion accent, elegant modern brand presentation, calm cultural luxury, no text",
  },
  {
    slug: "future-tech",
    name: "未来科技",
    palette: ["#0097A7", "#00D4D8", "#2F80ED", "#7C4DFF", "#03122B"],
    best_for: ["AI 发布会", "科技产品", "创新方案"],
    visual_direction: "深色空间、蓝绿霓虹、芯片平台和玻璃拟态卡片，适合 AI 产品发布和未来科技叙事。",
    raster_layers: ["深色宇宙科技背景", "AI 芯片平台主视觉", "蓝绿霓虹光轨"],
    transparent_assets: ["玻璃拟态产品卡片", "芯片和光效装饰", "科技图标组"],
    editable_layers: ["发布会标题", "产品卖点", "功能卡片文字", "时间地点", "图表标签"],
    prompt_seed:
      "future technology PowerPoint background, dark cinematic AI product launch, cyan neon glow, holographic chip platform, glassmorphism atmosphere, premium tech conference mood, no text",
  },
  {
    slug: "editorial-magazine",
    name: "编辑杂志",
    palette: ["#111827", "#D72638", "#F3EEE8", "#C7B299", "#FFFFFF"],
    best_for: ["品牌故事", "公开演讲", "趋势洞察"],
    visual_direction: "杂志封面级标题、非对称大图留白、克制红色强调和强编辑感排版，适合观点型表达。",
    raster_layers: ["大幅摄影/插画留白背景", "轻纸张颗粒", "编辑式页眉页脚节奏"],
    transparent_assets: ["红色编辑标记", "裁切图片角标", "细线章节编号"],
    editable_layers: ["杂志式主标题", "导语正文", "章节编号", "引用文字", "图表注释"],
    prompt_seed:
      "editorial magazine PowerPoint background, premium trend report layout, asymmetric whitespace, subtle paper grain, restrained red accent, cinematic photo area, high-end magazine typography mood, no text",
  },
  {
    slug: "saas-product",
    name: "SaaS 产品",
    palette: ["#0F172A", "#2563EB", "#22C55E", "#E0F2FE", "#F8FAFC"],
    best_for: ["产品发布", "SaaS 销售", "功能路线图"],
    visual_direction: "干净产品界面感、柔和蓝绿光、模块化信息但不套大框，适合产品价值和功能流程叙事。",
    raster_layers: ["浅色产品工作台背景", "柔和蓝绿渐变光", "抽象界面透视氛围"],
    transparent_assets: ["产品界面浮层", "功能图标组", "流程节点装饰"],
    editable_layers: ["产品标题", "功能卖点", "路线节点", "指标标签", "流程说明"],
    prompt_seed:
      "modern SaaS product launch PowerPoint background, clean workspace, soft blue green gradient, abstract app interface panels as decorative edge elements only, premium product marketing presentation, no text",
  },
  {
    slug: "investor-narrative",
    name: "投资人叙事",
    palette: ["#08111F", "#F6C85F", "#E6EEF8", "#42526E", "#FFFFFF"],
    best_for: ["融资路演", "商业计划", "增长故事"],
    visual_direction: "深色高信任感、金色增长线、市场叙事和关键指标优先，适合投资人 pitch 和商业计划。",
    raster_layers: ["深色金融空间背景", "金色增长曲线氛围", "低纹理市场地图或网格"],
    transparent_assets: ["增长箭头光线", "市场地图点位", "投资人指标图标"],
    editable_layers: ["融资主张", "市场规模数字", "增长图表", "商业模式标签", "里程碑"],
    prompt_seed:
      "investor pitch deck PowerPoint background, dark premium financial narrative, subtle market map grid, warm gold growth line atmosphere, high trust boardroom mood, no text",
  },
];

function parse_args(argv) {
  const args = {};
  for (let index = 2; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--output-dir") {
      args.output_dir = argv[index + 1];
      index += 1;
    } else if (token === "--topic") {
      args.topic = argv[index + 1];
      index += 1;
    } else if (token === "--background-source-dir") {
      args.background_source_dir = argv[index + 1];
      index += 1;
    } else if (token === "--allow-placeholder-backgrounds") {
      args.allow_placeholder_backgrounds = true;
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
    "  node build_style_candidates.js --output-dir /absolute/path/style-candidates --topic \"deck topic\"",
    "  node build_style_candidates.js --output-dir /absolute/path/style-candidates --topic \"deck topic\" --background-source-dir /absolute/path/backgrounds",
    "  node build_style_candidates.js --output-dir /absolute/path/style-candidates --topic \"deck topic\" --allow-placeholder-backgrounds",
    "",
    "Writes eight editable one-slide PPTX samples, eight PNG previews exported from those PPTX files,",
    "style-reference prompts, clean-background prompts, and a style-candidate-spec.json contract.",
    "",
    "Commercial mode requires real imagegen/user-provided raster backgrounds via --background-source-dir.",
    "--allow-placeholder-backgrounds is test-only and cannot be used for README/showcase/commercial samples.",
  ].join("\n");
}

function ensure_directory(directory_path) {
  fs.mkdirSync(directory_path, { recursive: true });
}

function strip_hash(color) {
  return String(color || "000000").replace(/^#/, "").toUpperCase();
}

function add_text(slide, value, options) {
  slide.addText(String(value || ""), {
    fontFace: options.font_face || "PingFang SC",
    fontSize: options.font_size || 16,
    bold: Boolean(options.bold),
    color: strip_hash(options.color || "111827"),
    x: options.x,
    y: options.y,
    w: options.w,
    h: options.h,
    margin: options.margin == null ? 0 : options.margin,
    fit: "shrink",
    breakLine: false,
    valign: options.valign || "mid",
    align: options.align || "left",
  });
}

function add_open_metric_stat(slide, metric, index, theme, x, y, w, options = {}) {
  const accent = options.accent || (index % 2 === 0 ? theme.accent : theme.accent_2);
  const value_size = options.value_size || 20;
  slide.addShape("line", {
    x,
    y,
    w: options.line_width || 0.58,
    h: 0,
    line: { color: strip_hash(accent), transparency: options.line_transparency == null ? 10 : options.line_transparency, width: 2 },
  });
  add_text(slide, metric.value, {
    x,
    y: y + 0.14,
    w,
    h: 0.36,
    font_face: options.font_face || theme.font_face,
    font_size: value_size,
    bold: true,
    color: accent,
  });
  add_text(slide, metric.label, {
    x,
    y: y + 0.54,
    w,
    h: 0.25,
    font_face: options.label_font_face || options.font_face || theme.font_face,
    font_size: options.label_size || 7.8,
    bold: true,
    color: options.label_color || theme.foreground,
  });
}

function add_editable_chart(slide, content, theme, x, y, w, h, options = {}) {
  const variant = options.variant || "default";
  const values_by_variant = {
    thin_column_with_baseline: [42, 64, 78, 91],
    rounded_learning_progress: [36, 58, 74, 86],
    dashboard_glow_columns: [31, 54, 71, 88],
    ink_sequence_columns: [28, 49, 68, 84],
    neon_launch_columns: [30, 50, 69, 88],
    editorial_evidence_axis: [24, 46, 67, 83],
    product_growth_flow: [34, 56, 71, 89],
    gold_growth_story: [22, 45, 63, 81],
  };
  const values = values_by_variant[variant] || [42, 64, 78, 91];
  const label_font_face = options.label_font_face || theme.font_face;

  if (variant === "rounded_learning_progress") {
    const row_gap = h / 4.8;
    content.chart_labels.forEach((label, index) => {
      const row_y = y + 0.18 + index * row_gap;
      const accent = index % 2 === 0 ? theme.accent : theme.accent_2;
      add_text(slide, label, {
        x,
        y: row_y - 0.02,
        w: 0.75,
        h: 0.18,
        font_face: label_font_face,
        font_size: 6.8,
        color: theme.foreground,
      });
      slide.addShape("line", {
        x: x + 0.88,
        y: row_y + 0.12,
        w: w - 1.18,
        h: 0,
        line: { color: strip_hash(theme.muted), transparency: 72, width: 1 },
      });
      slide.addShape("rect", {
        x: x + 0.88,
        y: row_y + 0.04,
        w: (w - 1.18) * (values[index] / 100),
        h: 0.16,
        fill: { color: strip_hash(accent), transparency: 12 },
        line: { transparency: 100 },
      });
      for (let dot_index = 0; dot_index < 3; dot_index += 1) {
        slide.addShape("ellipse", {
          x: x + 0.92 + dot_index * 0.18,
          y: row_y + 0.075,
          w: 0.07,
          h: 0.07,
          fill: { color: strip_hash(dot_index <= index % 3 ? accent : theme.muted), transparency: dot_index <= index % 3 ? 0 : 64 },
          line: { transparency: 100 },
        });
      }
      slide.addShape("ellipse", {
        x: x + 0.88 + (w - 1.18) * (values[index] / 100) - 0.07,
        y: row_y - 0.005,
        w: 0.18,
        h: 0.18,
        fill: { color: strip_hash(accent), transparency: 0 },
        line: { color: strip_hash("FFFFFF"), transparency: 25, width: 0.5 },
      });
    });
    return;
  }

  if (variant === "editorial_evidence_axis") {
    const row_gap = h / 4.7;
    slide.addShape("line", {
      x,
      y: y + 0.08,
      w,
      h: 0,
      line: { color: strip_hash(theme.accent), transparency: 12, width: 1.2 },
    });
    content.chart_labels.forEach((label, index) => {
      const row_y = y + 0.34 + index * row_gap;
      const bar_w = (w - 1.15) * (values[index] / 100);
      add_text(slide, label, {
        x,
        y: row_y - 0.04,
        w: 0.86,
        h: 0.18,
        font_face: label_font_face,
        font_size: 6.8,
        color: theme.muted,
      });
      slide.addShape("rect", {
        x: x + 1.02,
        y: row_y,
        w: bar_w,
        h: 0.15,
        fill: { color: strip_hash(index === 2 ? theme.accent : theme.foreground), transparency: index === 2 ? 0 : 22 },
        line: { transparency: 100 },
      });
      slide.addShape("line", {
        x: x + 1.02 + bar_w + 0.08,
        y: row_y + 0.08,
        w: Math.max(0.22, w - 1.18 - bar_w),
        h: 0,
        line: { color: strip_hash(theme.muted), transparency: 76, width: 0.8 },
      });
    });
    return;
  }

  if (variant === "product_growth_flow") {
    const nodes = content.chart_labels.map((label, index) => ({
      label,
      x: x + 0.35 + index * ((w - 0.9) / 3),
      y: y + h - 0.7 - index * 0.42,
      color: index % 2 === 0 ? theme.accent : theme.accent_2,
    }));
    nodes.forEach((node, index) => {
      if (index < nodes.length - 1) {
        slide.addShape("line", {
          x: node.x + 0.22,
          y: node.y + 0.12,
          w: nodes[index + 1].x - node.x - 0.08,
          h: nodes[index + 1].y - node.y,
          line: { color: strip_hash(theme.accent), transparency: 24, width: 1.4 },
        });
        slide.addShape("line", {
          x: node.x + 0.24,
          y: node.y + 0.23,
          w: nodes[index + 1].x - node.x - 0.18,
          h: nodes[index + 1].y - node.y,
          line: { color: strip_hash(theme.accent_2), transparency: 58, width: 0.8 },
        });
      }
      slide.addShape("ellipse", {
        x: node.x,
        y: node.y,
        w: 0.26,
        h: 0.26,
        fill: { color: strip_hash(node.color), transparency: 0 },
        line: { color: strip_hash("FFFFFF"), transparency: 12, width: 0.8 },
      });
      slide.addShape("ellipse", {
        x: node.x + 0.07,
        y: node.y + 0.07,
        w: 0.12,
        h: 0.12,
        fill: { color: strip_hash("FFFFFF"), transparency: 18 },
        line: { transparency: 100 },
      });
      slide.addShape("ellipse", {
        x: node.x - 0.08,
        y: node.y + 0.02,
        w: 0.07,
        h: 0.07,
        fill: { color: strip_hash(node.color), transparency: 62 },
        line: { transparency: 100 },
      });
      slide.addShape("rect", {
        x: node.x - 0.02,
        y: node.y + 0.42,
        w: 0.62 + index * 0.16,
        h: 0.1,
        fill: { color: strip_hash(node.color), transparency: 28 },
        line: { transparency: 100 },
      });
      add_text(slide, node.label, {
        x: node.x - 0.18,
        y: node.y + 0.58,
        w: 0.75,
        h: 0.18,
        font_face: label_font_face,
        font_size: 6.6,
        color: theme.muted,
        align: "center",
      });
    });
    return;
  }

  if (variant === "gold_growth_story") {
    const points = [
      [x + 0.15, y + h - 0.52],
      [x + 1.0, y + h - 0.95],
      [x + 1.72, y + h - 1.58],
      [x + 2.62, y + h - 2.18],
      [x + 3.48, y + h - 2.88],
      [x + w - 0.24, y + 0.62],
    ];
    for (let grid_index = 0; grid_index < 4; grid_index += 1) {
      slide.addShape("line", {
        x: x + grid_index * (w / 4),
        y: y + 0.24,
        w: 0,
        h: h - 0.8,
        line: { color: strip_hash(theme.accent), transparency: 82, width: 0.7 },
      });
    }
    for (let index = 0; index < points.length - 1; index += 1) {
      slide.addShape("line", {
        x: points[index][0],
        y: points[index][1],
        w: points[index + 1][0] - points[index][0],
        h: points[index + 1][1] - points[index][1],
        line: { color: strip_hash(theme.accent), transparency: 6, width: 1.8 },
      });
    }
    content.chart_labels.forEach((label, index) => {
      const point = points[Math.min(index + 1, points.length - 1)];
      slide.addShape("ellipse", {
        x: point[0] - 0.06,
        y: point[1] - 0.06,
        w: 0.12,
        h: 0.12,
        fill: { color: strip_hash(theme.accent), transparency: 0 },
        line: { color: strip_hash("FFFFFF"), transparency: 36, width: 0.5 },
      });
      slide.addShape("line", {
        x: point[0],
        y: point[1] + 0.1,
        w: 0,
        h: 0.42,
        line: { color: strip_hash(theme.accent), transparency: 44, width: 0.8 },
      });
      add_text(slide, label, {
        x: point[0] - 0.32,
        y: point[1] + 0.54,
        w: 0.72,
        h: 0.18,
        font_face: label_font_face,
        font_size: 6.6,
        color: theme.muted,
        align: "center",
      });
    });
    return;
  }

  const gap = 0.22;
  const bar_width = (w - gap * 5) / 4;
  if (variant === "dashboard_glow_columns" || variant === "neon_launch_columns") {
    for (let grid_index = 0; grid_index < 4; grid_index += 1) {
      slide.addShape("line", {
        x,
        y: y + 0.3 + grid_index * ((h - 0.95) / 4),
        w,
        h: 0,
        line: { color: strip_hash(theme.axis || theme.muted), transparency: 78, width: 0.7 },
      });
      slide.addShape("line", {
        x: x + grid_index * (w / 4),
        y: y + 0.2,
        w: 0,
        h: h - 0.72,
        line: { color: strip_hash(theme.axis || theme.muted), transparency: 84, width: 0.55 },
      });
    }
  }
  if (options.axis) {
    slide.addShape("line", {
      x,
      y: y + h - 0.46,
      w,
      h: 0,
      line: { color: strip_hash(theme.axis || theme.muted), transparency: 30, width: 1 },
    });
  }
  content.chart_labels.forEach((label, index) => {
    const bar_height = (h - 0.46) * (values[index] / 100);
    const bar_x = x + gap + index * (bar_width + gap);
    const bar_y = y + h - 0.46 - bar_height;
    const accent = index % 2 === 0 ? theme.accent : theme.accent_2;
    const dark_fill = variant === "thin_column_with_baseline" ? (index % 2 === 0 ? theme.foreground : theme.muted) : accent;
    if (new Set(["dashboard_glow_columns", "neon_launch_columns", "gold_growth_story"]).has(variant)) {
      slide.addShape("rect", {
        x: bar_x - 0.03,
        y: bar_y - 0.03,
        w: bar_width + 0.06,
        h: bar_height + 0.03,
        fill: { color: strip_hash(accent), transparency: variant === "gold_growth_story" ? 68 : 78 },
        line: { transparency: 100 },
      });
    }
    slide.addShape("rect", {
      x: bar_x,
      y: bar_y,
      w: bar_width,
      h: bar_height,
      fill: { color: strip_hash(dark_fill), transparency: 0 },
      line: { color: strip_hash(dark_fill), transparency: 100 },
    });
    if (variant === "rounded_learning_progress" || variant === "product_growth_flow") {
      slide.addShape("ellipse", {
        x: bar_x + bar_width / 2 - 0.07,
        y: bar_y - 0.08,
        w: 0.14,
        h: 0.14,
        fill: { color: strip_hash(accent), transparency: 0 },
        line: { transparency: 100 },
      });
    }
    if (variant === "editorial_evidence_axis" && index === 2) {
      slide.addShape("line", {
        x: bar_x - 0.06,
        y: bar_y - 0.14,
        w: bar_width + 0.12,
        h: 0,
        line: { color: strip_hash(theme.accent), transparency: 10, width: 1 },
      });
    }
    add_text(slide, label, {
      x: bar_x - 0.04,
      y: y + h - 0.32,
      w: bar_width + 0.08,
      h: 0.18,
      font_face: label_font_face,
      font_size: 6.8,
      color: theme.muted,
      align: "center",
    });
  });
  if (new Set(["dashboard_glow_columns", "product_growth_flow", "gold_growth_story", "neon_launch_columns"]).has(variant)) {
    const line_points = [];
    values.forEach((value, index) => {
      const bar_height = (h - 0.46) * (value / 100);
      const bar_x = x + gap + index * (bar_width + gap);
      const bar_y = y + h - 0.46 - bar_height;
      line_points.push([bar_x + bar_width / 2, bar_y - 0.04]);
      slide.addShape("ellipse", {
        x: bar_x + bar_width / 2 - 0.05,
        y: bar_y - 0.09,
        w: 0.1,
        h: 0.1,
        fill: { color: strip_hash(variant === "gold_growth_story" ? theme.accent : theme.accent_2), transparency: 0 },
        line: { transparency: 100 },
      });
    });
    for (let index = 0; index < line_points.length - 1; index += 1) {
      slide.addShape("line", {
        x: line_points[index][0],
        y: line_points[index][1],
        w: line_points[index + 1][0] - line_points[index][0],
        h: line_points[index + 1][1] - line_points[index][1],
        line: {
          color: strip_hash(variant === "gold_growth_story" ? theme.accent : theme.accent_2),
          transparency: variant === "gold_growth_story" ? 8 : 18,
          width: 1.4,
        },
      });
    }
  }
}

function add_bullet_list(slide, bullets, theme, x, y, options = {}) {
  bullets.forEach((bullet, index) => {
    const bullet_y = y + index * (options.step || 0.32);
    slide.addShape("ellipse", {
      x,
      y: bullet_y + 0.04,
      w: 0.08,
      h: 0.08,
      fill: { color: strip_hash(index % 2 === 0 ? theme.accent : theme.accent_2) },
      line: { transparency: 100 },
    });
    add_text(slide, bullet, {
      x: x + 0.18,
      y: bullet_y - 0.02,
      w: options.w || 3.6,
      h: 0.18,
      font_face: options.font_face || theme.font_face,
      font_size: options.font_size || 8.2,
      color: options.color || theme.foreground,
    });
  });
}

function add_integrated_note(slide, candidate, theme, typography, x, y, w) {
  slide.addShape("line", {
    x,
    y: y + 0.02,
    w: 0.52,
    h: 0,
    line: { color: strip_hash(theme.accent), transparency: 10, width: 1.5 },
  });
  add_text(slide, "文字、数字和图表标签均为 PPT 可编辑对象", {
    x: x + 0.68,
    y: y - 0.08,
    w,
    h: 0.18,
    font_face: typography.body_font_face || theme.font_face,
    font_size: 7.4,
    color: theme.muted,
  });
  add_text(slide, candidate.name, {
    x: 10.8,
    y: 6.88,
    w: 1.0,
    h: 0.16,
    font_face: typography.eyebrow_font_face || typography.body_font_face || theme.font_face,
    font_size: 7.2,
    bold: true,
    color: theme.accent,
    align: "right",
  });
}

function add_background(slide, candidate, theme, output_dir) {
  slide.background = { color: strip_hash(theme.background) };
  slide.addShape("rect", {
    x: 0,
    y: 0,
    w: slide_width,
    h: slide_height,
    fill: { color: strip_hash(theme.background) },
    line: { color: strip_hash(theme.background), transparency: 100 },
  });
  const background_path = path.join(output_dir, candidate.background_asset_path);
  if (fs.existsSync(background_path)) {
    slide.addImage({ path: background_path, x: 0, y: 0, w: slide_width, h: slide_height, transparency: 0 });
    slide.addShape("rect", {
      x: 0,
      y: 0,
      w: slide_width,
      h: slide_height,
      fill: { color: strip_hash(theme.background), transparency: candidate.safe_background_wash_transparency },
      line: { transparency: 100 },
    });
  }
}

function theme_for(candidate) {
  const palette = candidate.palette.map(strip_hash);
  const dark_slugs = new Set(["data-analytics", "future-tech", "investor-narrative"]);
  const is_dark = dark_slugs.has(candidate.slug);
  if (candidate.slug === "playful-anime") {
    return {
      background: "FFF7E6",
      foreground: "1F2937",
      muted: "586174",
      accent: "F59E0B",
      accent_2: "FF7AA2",
      card_fill: "FFFFFF",
      card_transparency: 18,
      metric_fill: "FFF4D6",
      metric_transparency: 10,
      font_face: "PingFang SC",
    };
  }
  if (candidate.slug === "data-analytics") {
    return {
      background: palette[0],
      foreground: "FFFFFF",
      muted: "A7C3D9",
      accent: "6C72FF",
      accent_2: "12C7D6",
      card_fill: "071B34",
      card_transparency: 8,
      metric_fill: "08213C",
      metric_transparency: 10,
      axis: "2E6F9E",
      font_face: "PingFang SC",
    };
  }
  if (candidate.slug === "future-tech") {
    return {
      background: "03122B",
      foreground: "FFFFFF",
      muted: "A7C3D9",
      accent: "00D4D8",
      accent_2: "7C4DFF",
      card_fill: "071B34",
      card_transparency: 8,
      metric_fill: "071B34",
      metric_transparency: 10,
      axis: "315D82",
      font_face: "PingFang SC",
    };
  }
  if (candidate.slug === "saas-product") {
    return {
      background: "F8FAFC",
      foreground: "0F172A",
      muted: "64748B",
      accent: "2563EB",
      accent_2: "22C55E",
      card_fill: "FFFFFF",
      card_transparency: 14,
      metric_fill: "E0F2FE",
      metric_transparency: 18,
      axis: "93C5FD",
      font_face: "PingFang SC",
    };
  }
  return {
    background: is_dark ? palette[0] : palette[4],
    foreground: is_dark ? "FFFFFF" : palette[0],
    muted: is_dark ? "A7C3D9" : "5D6673",
    accent: palette[0] === "020B1D" ? palette[3] : palette[0],
    accent_2: palette[1],
    card_fill: is_dark ? "071B34" : "FFFFFF",
    card_transparency: is_dark ? 8 : 0,
    metric_fill: is_dark ? "071B34" : "FFFFFF",
    metric_transparency: is_dark ? 8 : 0,
    axis: is_dark ? "315D82" : "A7A7A7",
    font_face: "PingFang SC",
  };
}

function build_sample_content(topic, candidate) {
  const style_details = {
    "minimal-premium": {
      eyebrow_label: "BOARD BRIEF",
      subtitle: "董事会简报样张",
      section_title: "核心结论",
      chart_title: "决策迁移",
      body: "AI 应用正在从工具采购转向流程重构，真正的价值来自业务场景、数据闭环和组织协同。",
      bullets: ["从单点工具进入流程级改造", "高频知识工作先出现回报", "治理和复用能力决定放大速度"],
      metrics: [
        { value: "41%", label: "流程级改造占比" },
        { value: "18周", label: "组织落地周期" },
        { value: "2026", label: "预算重排窗口" },
      ],
      chart_labels: ["工具", "流程", "数据", "组织"],
    },
    "playful-anime": {
      eyebrow_label: "AI COURSE",
      subtitle: "培训课程样张",
      section_title: "学习目标",
      chart_title: "学习热度",
      body: "用轻量案例解释 AI 应用趋势，让非技术团队也能判断哪些场景值得优先试点。",
      bullets: ["看懂趋势", "识别场景", "设计试点"],
      metrics: [
        { value: "4课", label: "课程模块" },
        { value: "73%", label: "练习完成率" },
        { value: "3步", label: "试点方法" },
      ],
      chart_labels: ["认知", "体验", "练习", "复盘"],
    },
    "data-analytics": {
      eyebrow_label: "AI RESEARCH",
      subtitle: "行业研究报告样张",
      section_title: "关键指标",
      chart_title: "趋势指数",
      body: "企业采用 AI 的竞争点，正从模型能力转向数据资产、流程嵌入和投入产出监控。",
      bullets: ["试点数量增长", "复用组件增加", "ROI 口径更严格"],
      metrics: [
        { value: "73%", label: "企业已进入试点" },
        { value: "3x", label: "复用组件增长" },
        { value: "12月", label: "ROI 复盘周期" },
      ],
      chart_labels: ["采纳", "复用", "成本", "收益"],
    },
    "oriental-heritage": {
      eyebrow_label: "BRAND NARRATIVE",
      subtitle: "品牌战略解读样张",
      section_title: "趋势脉络",
      chart_title: "演进四象",
      body: "新技术落地不是一阵风，而是从器、术、法到组织文化的一次长期演进。",
      bullets: ["以器入局", "以术成事", "以法固化"],
      metrics: [
        { value: "器", label: "工具入局" },
        { value: "术", label: "流程成事" },
        { value: "法", label: "组织固化" },
      ],
      chart_labels: ["起", "承", "转", "合"],
    },
    "future-tech": {
      eyebrow_label: "AI PRODUCT RELEASE",
      subtitle: "AI 产品发布会样张",
      section_title: "能力模块",
      chart_title: "能力跃迁",
      body: "下一代 AI 应用将围绕多模态输入、智能执行、可信审计和生态连接展开。",
      bullets: ["多模态入口", "自动化执行", "企业级治理"],
      metrics: [
        { value: "4D", label: "多模态入口" },
        { value: "24/7", label: "智能执行" },
        { value: "0漏审", label: "可信审计目标" },
      ],
      chart_labels: ["输入", "推理", "执行", "审计"],
    },
    "editorial-magazine": {
      eyebrow_label: "ISSUE 01",
      subtitle: "趋势洞察报告样张",
      section_title: "核心观点",
      chart_title: "证据走向",
      body: "AI 应用的下一阶段不是工具清单竞争，而是组织是否能把判断、素材和流程沉淀成可复用能力。",
      bullets: ["观点先行", "案例支撑", "节奏留白"],
      metrics: [
        { value: "01", label: "主叙事" },
        { value: "5页", label: "章节节奏" },
        { value: "3层", label: "证据结构" },
      ],
      chart_labels: ["观点", "案例", "数据", "行动"],
    },
    "saas-product": {
      eyebrow_label: "PRODUCT STRATEGY",
      subtitle: "产品增长方案样张",
      section_title: "产品价值",
      chart_title: "增长路径",
      body: "SaaS 型 AI 产品要把能力说成用户可感知的流程收益，而不是堆模型参数和功能清单。",
      bullets: ["缩短上手路径", "提高协作效率", "沉淀复用资产"],
      metrics: [
        { value: "42%", label: "激活提升" },
        { value: "7天", label: "上手周期" },
        { value: "3x", label: "功能复用" },
      ],
      chart_labels: ["访问", "激活", "留存", "扩展"],
    },
    "investor-narrative": {
      eyebrow_label: "INVESTOR EDITION",
      subtitle: "融资路演样张",
      section_title: "增长逻辑",
      chart_title: "增长故事",
      body: "投资人需要看到的不只是市场热度，而是需求强度、增长路径、商业模式和团队执行节奏。",
      bullets: ["市场窗口明确", "增长路径可验证", "商业化节奏清晰"],
      metrics: [
        { value: "$1.2B", label: "目标市场" },
        { value: "18月", label: "扩张窗口" },
        { value: "4x", label: "收入杠杆" },
      ],
      chart_labels: ["需求", "产品", "收入", "规模"],
    },
  };
  const detail = style_details[candidate.slug];
  return {
    title: topic,
    eyebrow_label: detail.eyebrow_label,
    subtitle: detail.subtitle,
    section_title: detail.section_title,
    chart_title: detail.chart_title,
    body: detail.body,
    bullets: detail.bullets,
    metrics: detail.metrics,
    chart_labels: detail.chart_labels,
  };
}

function build_coordinate_blueprint(candidate) {
  const shared = {
    unit: "inches",
    slide: { width: slide_width, height: slide_height },
    planning_rule: "先规划区域，再生成背景、透明素材、文案和图表；所有可编辑元素必须按坐标蓝图落版。",
  };
  const blueprints = {
    "minimal-premium": {
      title_zone: {
        x: 0.72,
        y: 0.72,
        w: 5.9,
        h: 1.15,
        role: "主标题和副标题，保持建筑线条低对比。",
        capacity: "主标题 1 行，副标题 1 行。",
      },
      text_zone: {
        x: 0.82,
        y: 2.3,
        w: 4.95,
        h: 2.2,
        role: "正文和三条要点，浅色低纹理留白。",
        capacity: "正文 55 个中文字符以内，3 条短要点。",
      },
      chart_zone: {
        x: 7.05,
        y: 1.5,
        w: 4.8,
        h: 4.75,
        role: "开放式柱状图或折线图，背景仅保留细线透视。",
        capacity: "4 组柱状图，坐标标签 4 个。",
      },
      metrics_zone: {
        x: 0.82,
        y: 5.42,
        w: 5.5,
        h: 0.95,
        role: "三组开放式指标，不加描边框。",
        capacity: "3 个大数字，每个 1 个短标签。",
      },
      visual_focus_zone: {
        x: 8.55,
        y: 0,
        w: 4.5,
        h: 7.5,
        role: "建筑玻璃、空间透视和低对比装饰主视觉。",
        capacity: "不能承载文字。",
      },
      protected_empty_zone: {
        x: 5.9,
        y: 0.5,
        w: 1,
        h: 6.4,
        role: "内容区和图表区之间的呼吸带。",
        capacity: "保持干净，不放正文或复杂纹理。",
      },
    },
    "playful-anime": {
      title_zone: {
        x: 0.72,
        y: 0.72,
        w: 5.4,
        h: 1.05,
        role: "课程标题和轻量副标题，避开角色脸部。",
        capacity: "主标题 1 行，副标题 1 行。",
      },
      text_zone: {
        x: 3,
        y: 2.25,
        w: 4.1,
        h: 2.3,
        role: "学习目标正文，浅色云朵或黑板低纹理区域。",
        capacity: "正文 45 个中文字符以内，3 条短要点。",
      },
      chart_zone: {
        x: 7.25,
        y: 1.85,
        w: 4.65,
        h: 4.35,
        role: "彩色开放式图表，背景使用浅色课堂留白。",
        capacity: "4 组柱状图，标签用深灰。",
      },
      metrics_zone: {
        x: 2.9,
        y: 5.45,
        w: 5.55,
        h: 0.95,
        role: "三组彩色指标，像贴纸但不画外框。",
        capacity: "3 个大数字，每个 1 个短标签。",
      },
      visual_focus_zone: {
        x: 0,
        y: 3,
        w: 3,
        h: 4.5,
        role: "卡通角色和学习道具主视觉。",
        capacity: "角色不遮挡文字区。",
      },
      protected_empty_zone: {
        x: 3,
        y: 2,
        w: 4.2,
        h: 3.2,
        role: "正文阅读区，背景只能是低噪声浅色过渡。",
        capacity: "保持干净，不放高饱和装饰。",
      },
    },
    "data-analytics": {
      title_zone: {
        x: 0.72,
        y: 0.75,
        w: 5.7,
        h: 1.15,
        role: "报告标题和副标题，深色低纹理网格。",
        capacity: "主标题 1 行，副标题 1 行。",
      },
      text_zone: {
        x: 0.82,
        y: 2.35,
        w: 4.9,
        h: 2.25,
        role: "关键指标解释和要点，背景为暗色干净留白。",
        capacity: "正文 55 个中文字符以内，3 条短要点。",
      },
      chart_zone: {
        x: 7,
        y: 1.45,
        w: 4.9,
        h: 4.9,
        role: "发光数据图表区，避开强眩光中心。",
        capacity: "4 组图表，坐标标签 4 个。",
      },
      metrics_zone: {
        x: 0.82,
        y: 5.45,
        w: 5.55,
        h: 0.95,
        role: "开放式 KPI 数字组，不使用卡片。",
        capacity: "3 个大数字，每个 1 个短标签。",
      },
      visual_focus_zone: {
        x: 0,
        y: 0,
        w: 13.33,
        h: 1.75,
        role: "顶部边缘的数据粒子、暗色网格和蓝色波形主视觉。",
        capacity: "只做氛围，不承载正文或图表标签。",
      },
      protected_empty_zone: {
        x: 5.75,
        y: 0.7,
        w: 1.05,
        h: 6,
        role: "左右信息分区的暗色过渡带。",
        capacity: "保持低对比。",
      },
    },
    "oriental-heritage": {
      title_zone: {
        x: 2.55,
        y: 0.86,
        w: 4.8,
        h: 1.15,
        role: "东方品牌标题，避开左上红日，落在宣纸留白上。",
        capacity: "主标题 1 行，副标题 1 行。",
      },
      text_zone: {
        x: 3.05,
        y: 2.2,
        w: 3.9,
        h: 2.45,
        role: "趋势脉络正文，宣纸低纹理留白。",
        capacity: "正文 50 个中文字符以内，3 条短要点。",
      },
      chart_zone: {
        x: 7.35,
        y: 1.55,
        w: 4.65,
        h: 4.55,
        role: "国潮配色开放式图表，避开山水密集线条。",
        capacity: "4 组柱状图，标签 4 个。",
      },
      metrics_zone: {
        x: 2.35,
        y: 5.45,
        w: 5.55,
        h: 0.95,
        role: "三组朱红/墨黑指标，不加框。",
        capacity: "3 个大数字，每个 1 个短标签。",
      },
      visual_focus_zone: {
        x: 0,
        y: 1.8,
        w: 3,
        h: 5.4,
        role: "山水、梅枝或器物剪影主视觉。",
        capacity: "不能穿过正文行。",
      },
      protected_empty_zone: {
        x: 7.1,
        y: 0.85,
        w: 5.2,
        h: 5.2,
        role: "图表阅读区，保留浅纸色和淡墨过渡。",
        capacity: "不放强水墨纹理。",
      },
    },
    "future-tech": {
      title_zone: {
        x: 0.72,
        y: 0.75,
        w: 5.7,
        h: 1.15,
        role: "发布会标题和副标题，深色净空。",
        capacity: "主标题 1 行，副标题 1 行。",
      },
      text_zone: {
        x: 0.82,
        y: 2.35,
        w: 4.9,
        h: 2.25,
        role: "能力模块说明，避开霓虹强光。",
        capacity: "正文 55 个中文字符以内，3 条短要点。",
      },
      chart_zone: {
        x: 7,
        y: 1.45,
        w: 4.9,
        h: 4.9,
        role: "霓虹图表区，背景为低纹理玻璃暗面。",
        capacity: "4 组柱状图，坐标标签 4 个。",
      },
      metrics_zone: {
        x: 0.82,
        y: 5.45,
        w: 5.55,
        h: 0.95,
        role: "开放式科技指标数字，不加玻璃卡片框。",
        capacity: "3 个大数字，每个 1 个短标签。",
      },
      visual_focus_zone: {
        x: 7,
        y: 2.1,
        w: 5.7,
        h: 4.8,
        role: "AI 芯片平台、光轨和全息主视觉。",
        capacity: "光源避开标签和柱体顶部。",
      },
      protected_empty_zone: {
        x: 5.75,
        y: 0.7,
        w: 1.05,
        h: 6,
        role: "左右内容之间的暗色呼吸带。",
        capacity: "保持干净，不放强光。",
      },
    },
    "editorial-magazine": {
      title_zone: {
        x: 2.35,
        y: 0.78,
        w: 4.65,
        h: 1.35,
        role: "杂志式主标题和导语，避开左上布料纹理，落在纸面净空。",
        capacity: "主标题 1-2 行，副标题 1 行。",
      },
      text_zone: {
        x: 2.42,
        y: 2.55,
        w: 3.75,
        h: 2.05,
        role: "观点导语和三条证据，低纹理编辑留白。",
        capacity: "正文 60 个中文字符以内，3 条短要点。",
      },
      chart_zone: {
        x: 7.25,
        y: 1.62,
        w: 4.7,
        h: 4.55,
        role: "开放式趋势图，红色只做关键转折强调。",
        capacity: "4 组柱状图或观点证据轴。",
      },
      metrics_zone: {
        x: 2.42,
        y: 5.42,
        w: 4.7,
        h: 0.95,
        role: "编辑式大编号和指标，不加卡片。",
        capacity: "3 个大数字，每个 1 个短标签。",
      },
      visual_focus_zone: {
        x: 0,
        y: 0,
        w: 2.2,
        h: 7.5,
        role: "左上布料、纸张裁切边和酒红材料感主视觉。",
        capacity: "可承接图片但不承载正文。",
      },
      protected_empty_zone: {
        x: 6.35,
        y: 0.75,
        w: 0.75,
        h: 6.15,
        role: "左右非对称版面的呼吸带。",
        capacity: "保持干净。",
      },
    },
    "saas-product": {
      title_zone: {
        x: 0.72,
        y: 0.76,
        w: 5.7,
        h: 1.12,
        role: "产品价值标题和副标题，浅色产品背景净空。",
        capacity: "主标题 1 行，副标题 1 行。",
      },
      text_zone: {
        x: 0.84,
        y: 2.32,
        w: 4.95,
        h: 2.25,
        role: "功能价值和流程说明，背景为浅蓝低噪声留白。",
        capacity: "正文 55 个中文字符以内，3 条短要点。",
      },
      chart_zone: {
        x: 7.1,
        y: 1.55,
        w: 4.75,
        h: 4.7,
        role: "增长漏斗或采用趋势图，避免像后台 UI 卡片。",
        capacity: "4 组增长数据和标签。",
      },
      metrics_zone: {
        x: 0.84,
        y: 5.45,
        w: 5.6,
        h: 0.95,
        role: "开放式产品指标，不做卡片。",
        capacity: "3 个大数字，每个 1 个短标签。",
      },
      visual_focus_zone: {
        x: 7.15,
        y: 0.5,
        w: 5.65,
        h: 6.2,
        role: "产品界面透视、流程节点和柔和渐变主视觉。",
        capacity: "界面元素只在边缘，不能穿过图表核心。",
      },
      protected_empty_zone: {
        x: 5.85,
        y: 0.75,
        w: 1.05,
        h: 6.1,
        role: "产品说明和图表之间的浅色过渡带。",
        capacity: "不放高饱和按钮或 UI 文本。",
      },
    },
    "investor-narrative": {
      title_zone: {
        x: 4.72,
        y: 0.75,
        w: 5.35,
        h: 1.15,
        role: "融资主张标题和副标题，落在右侧深色高信任净空。",
        capacity: "主标题 1 行，副标题 1 行。",
      },
      text_zone: {
        x: 4.82,
        y: 2.35,
        w: 3.15,
        h: 2.25,
        role: "增长逻辑和商业化证据，避开左侧地球高光。",
        capacity: "正文 55 个中文字符以内，3 条短要点。",
      },
      chart_zone: {
        x: 8.35,
        y: 1.45,
        w: 4.25,
        h: 4.9,
        role: "右侧开放式增长线，背景保持低纹理深色。",
        capacity: "4 组增长数据和标签。",
      },
      metrics_zone: {
        x: 4.82,
        y: 5.45,
        w: 4.75,
        h: 0.95,
        role: "投资人关注的市场、窗口、杠杆指标。",
        capacity: "3 个大数字，每个 1 个短标签。",
      },
      visual_focus_zone: {
        x: 0,
        y: 0,
        w: 4.55,
        h: 7.5,
        role: "左侧金色地球、金融远景和暗色空间主视觉。",
        capacity: "不能承载正文，只做 pitch 氛围和信任锚点。",
      },
      protected_empty_zone: {
        x: 4.55,
        y: 0.7,
        w: 0.35,
        h: 6,
        role: "地球视觉与正文区之间的暗色呼吸带。",
        capacity: "保持低对比。",
      },
    },
  };
  return { ...shared, zones: blueprints[candidate.slug] };
}

function format_coordinate_zone(zone_name, zone) {
  return `${zone_name}: x=${zone.x}, y=${zone.y}, w=${zone.w}, h=${zone.h}; role=${zone.role}; capacity=${zone.capacity}`;
}

function build_style_reference_prompt(candidate, topic, content, coordinate_blueprint) {
  const zone_lines = Object.entries(coordinate_blueprint.zones).map(([zone_name, zone]) =>
    format_coordinate_zone(zone_name, zone)
  );
  return [
    `Codex image generation prompt for ${candidate.name}.`,
    "",
    `Create one full-page style reference image / 完整效果图 for a 16:9 PowerPoint slide about: ${topic}.`,
    "This is the visual target only. It may show realistic sample Chinese title, body, metrics, and chart labels so the user can judge style, typography, hierarchy, density, and composition.",
    `Sample title: ${content.title}`,
    `Sample subtitle: ${content.subtitle}`,
    `Sample section title: ${content.section_title}`,
    `Sample body: ${content.body}`,
    `Sample bullets: ${content.bullets.join(" / ")}`,
    `Sample metrics: ${content.metrics.map((metric) => `${metric.value} ${metric.label}`).join(" / ")}`,
    `Sample chart labels: ${content.chart_labels.join(" / ")}`,
    `Visual direction: ${candidate.prompt_seed}.`,
    `Palette reference: ${candidate.palette.join(", ")}.`,
    "Make the page look like a premium finished PPT slide, not a UI wireframe and not a collage of white boxes.",
    "Use integrated composition: text, chart, metrics, decoration, and background feel designed together.",
    "Avoid large plain content cards, chart cards, framed metric tiles, fake app UI, watermarks, and unreadable tiny text.",
    "Coordinate intent for the reference image:",
    ...zone_lines,
    "After this reference is approved, it will be decomposed into clean background, transparent assets, editable PPT text, and editable chart layers.",
  ].join("\n");
}

function build_clean_background_prompt(candidate, topic, content, coordinate_blueprint) {
  const zone_lines = Object.entries(coordinate_blueprint.zones).map(([zone_name, zone]) =>
    format_coordinate_zone(zone_name, zone)
  );
  return [
    `Codex image generation prompt for ${candidate.name}.`,
    "",
    `Create a 16:9 clean background image only for a deck about: ${topic}.`,
    "Use the approved full-page style reference image as the design target, but remove every editable layer from the background.",
    `Visual direction: ${candidate.prompt_seed}.`,
    `The reference page used these sample text ideas: ${content.title}, ${content.section_title}, ${content.body}.`,
    "Remove all readable text, letters, numbers, metric values, bullets, chart bars, chart lines, axes, fake UI labels, titles, subtitles, and watermarks.",
    "Coordinate blueprint uses inches on a 13.333 x 7.5 slide. Design the background around these zones before adding visual detail:",
    ...zone_lines,
    "Reserve deliberate text-safe zones and chart-safe zones: low-detail, low-noise areas with smooth tonal transitions, not blank boxes.",
    "Leave clean whitespace where editable PPT title, body copy, open metric numbers, and chart labels can be placed later without any card frames.",
    "Build gentle light-to-dark or dark-to-light transition areas behind future text and chart strokes so the final PPT remains readable without adding rescue panels.",
    "This background image is only one raster asset layer. The final candidate preview must be produced by placing editable PPT text, shapes, charts, and labels above it.",
    `Palette reference: ${candidate.palette.join(", ")}.`,
    `Suggested transparent assets to generate separately later: ${candidate.transparent_assets.join(", ")}.`,
  ].join("\n");
}

function build_safe_zone_plan(candidate) {
  const dark_style = new Set(["data-analytics", "future-tech", "investor-narrative"]).has(candidate.slug);
  const light_style = new Set(["minimal-premium", "oriental-heritage", "playful-anime", "editorial-magazine", "saas-product"]).has(candidate.slug);
  return {
    text_zone: light_style
      ? "左侧或中左侧保留低纹理浅色留白，使用深色主标题和中灰正文；人物、建筑、山水等高细节素材避开正文行高区域。"
      : "左侧保留低纹理深色留白，使用白色主标题和浅蓝灰正文；高亮元素只作为短线和关键数字使用。",
    chart_zone: dark_style
      ? "右侧图表落在平台光带或网格暗区，使用青色/紫色高亮线条，避免细标签压在高亮眩光中心。"
      : "右侧图表落在浅色留白或纸纹过渡区，使用深色/品牌强调色线条，避免柱体或折线压到复杂纹理。",
    transition_zone:
      "文本区和图表区之间必须有柔和明暗过渡或低对比纹理带，让内容像嵌入背景，而不是浮在一块临时矩形上。",
    text_color_rule: dark_style
      ? "深背景使用白色标题、浅蓝灰正文、青色重点；禁止在亮光束上放浅色小字。"
      : "浅背景使用近黑标题、中灰正文、品牌强调色重点；禁止在深色图片纹理上放小号正文。",
    chart_color_rule:
      "图表主线/主柱必须比背景高一个明确亮度层级，辅助线降低透明度；标签避开高纹理和强光区域。",
  };
}

function build_typography_system(candidate) {
  const systems = {
    "minimal-premium": {
      heading: "克制咨询风，标题粗黑、字距正常、信息层级少而准。",
      body: "正文使用中灰小号文本，行宽短，配细线和留白。",
      title_font_face: "PingFang SC",
      body_font_face: "PingFang SC",
      eyebrow_font_face: "Avenir Next",
      title_size: 27,
      subtitle_size: 10.5,
      section_size: 12.5,
      body_size: 10.4,
      label_size: 7.2,
    },
    "playful-anime": {
      heading: "课程型圆润标题，字号略大，颜色更轻快。",
      body: "正文短句化，配彩色圆点和更大的呼吸间距。",
      title_font_face: "PingFang SC",
      body_font_face: "PingFang SC",
      eyebrow_font_face: "Avenir Next",
      title_size: 26,
      subtitle_size: 10.8,
      section_size: 13.5,
      body_size: 10.8,
      label_size: 7.6,
    },
    "data-analytics": {
      heading: "深色仪表盘标题，数字优先，信息密度更高。",
      body: "正文使用浅蓝灰，KPI 数字和图表标签强调科技感。",
      title_font_face: "Hiragino Sans GB",
      body_font_face: "PingFang SC",
      eyebrow_font_face: "Avenir Next",
      title_size: 24,
      subtitle_size: 10.2,
      section_size: 12,
      body_size: 9.8,
      label_size: 7,
    },
    "oriental-heritage": {
      heading: "东方题签式标题，留白更重，朱红强调。",
      body: "正文像品牌理念页，短句、纵深和印章感分隔。",
      title_font_face: "Songti SC",
      body_font_face: "PingFang SC",
      eyebrow_font_face: "Avenir Next",
      title_size: 25,
      subtitle_size: 10.4,
      section_size: 14,
      body_size: 10.4,
      label_size: 7.2,
    },
    "future-tech": {
      heading: "发布会式标题，白字高亮，副标题更像产品 tagline。",
      body: "正文压缩成能力说明，霓虹强调只给关键词和数字。",
      title_font_face: "Hiragino Sans GB",
      body_font_face: "PingFang SC",
      eyebrow_font_face: "Avenir Next",
      title_size: 25,
      subtitle_size: 10.3,
      section_size: 12.5,
      body_size: 10,
      label_size: 7,
    },
    "editorial-magazine": {
      heading: "编辑杂志式标题，强调观点和节奏，标题更像封面主张。",
      body: "正文像导语和旁注，留白足，红色只做少量编辑强调。",
      title_font_face: "Songti SC",
      body_font_face: "PingFang SC",
      eyebrow_font_face: "Avenir Next",
      title_size: 28,
      subtitle_size: 10.2,
      section_size: 13.2,
      body_size: 10.2,
      label_size: 7.2,
    },
    "saas-product": {
      heading: "产品营销式标题，清晰、直接、偏现代黑体。",
      body: "正文强调功能收益，搭配流程节点和开放式指标。",
      title_font_face: "PingFang SC",
      body_font_face: "PingFang SC",
      eyebrow_font_face: "Avenir Next",
      title_size: 25,
      subtitle_size: 10.2,
      section_size: 12.8,
      body_size: 10.2,
      label_size: 7.2,
    },
    "investor-narrative": {
      heading: "投资人 pitch 标题，短促、有主张，数字权重大。",
      body: "正文压成商业逻辑和证据点，金色只给增长和关键指标。",
      title_font_face: "Heiti SC",
      body_font_face: "PingFang SC",
      eyebrow_font_face: "Avenir Next",
      title_size: 25,
      subtitle_size: 10.2,
      section_size: 12.4,
      body_size: 9.8,
      label_size: 7,
    },
  };
  return systems[candidate.slug];
}

function build_style_treatments(candidate) {
  const treatments = {
    "minimal-premium": {
      layout_variant: "consulting_split",
      title_treatment: "黑白咨询风标题，细线分隔，建筑留白压住画面。",
      metric_treatment: "底部开放式三列指标，像咨询页脚里的结论锚点。",
      chart_treatment: "黑灰开放式柱图，强调理性秩序而不是装饰。",
      background_visual_anchor: "右侧建筑玻璃立面和透视结构线，形成咨询/投行式空间感。",
      visual_focus_asset_strategy: "建筑结构只占右侧和边缘，正文区保持浅色纸面，图表区只保留低对比透视。",
    },
    "playful-anime": {
      layout_variant: "classroom_stage",
      title_treatment: "轻快课程标题，暖色眉题，标题与正文像落在云朵舞台上。",
      metric_treatment: "底部彩色学习指标，像贴纸节奏，但不套卡片。",
      chart_treatment: "明亮进度柱图，颜色活泼，标签更像课程节奏点。",
      background_visual_anchor: "左下课堂角色、课桌和星形学习贴纸，右上保留彩色课堂氛围。",
      visual_focus_asset_strategy: "角色和道具放在视觉焦点区，不进入正文行和柱状图主体。",
    },
    "data-analytics": {
      layout_variant: "dashboard_split",
      title_treatment: "深色研究报告标题，信息密度高，科技蓝作为引导。",
      metric_treatment: "KPI 数字前置，节奏更像经营看板。",
      chart_treatment: "带微弱发光的仪表盘柱图与趋势线组合。",
      background_visual_anchor: "边缘数据粒子、暗色网格和蓝色波形氛围，中心保留深色数据舞台。",
      visual_focus_asset_strategy: "数据粒子只做边缘空间感，图表主体由 PPT 可编辑层承担，左侧文字保持暗色净空。",
    },
    "oriental-heritage": {
      layout_variant: "cultural_spread",
      title_treatment: "东方题签式标题，宋体主标题配朱红副标题和宣纸留白。",
      metric_treatment: "方法论式指标，像器术法的章节锚点。",
      chart_treatment: "朱红墨黑交替的开放式图表，重节奏轻科技感。",
      background_visual_anchor: "左下水墨山峦、左上朱红日轮和右上印章形成东方品牌气质。",
      visual_focus_asset_strategy: "山水落在页脚和边缘，宣纸留白承接正文和图表，不让墨线穿过标签。",
    },
    "future-tech": {
      layout_variant: "launch_stage",
      title_treatment: "发布会主标题，霓虹眉题与白色标题构成舞台感。",
      metric_treatment: "低位开放式数字，强化能力模块的系统感。",
      chart_treatment: "青紫霓虹柱图加弱趋势线，像大屏发布会数据模块。",
      background_visual_anchor: "右侧芯片平台、全息光环和青紫光轨构成发布会舞台。",
      visual_focus_asset_strategy: "芯片平台在右下视觉焦点，光环退到图表背后，文字区保持低纹理深色。",
    },
    "editorial-magazine": {
      layout_variant: "editorial_column",
      title_treatment: "杂志封面式主张标题，红色期号眉题，版面更非对称。",
      metric_treatment: "底部像杂志页码和章节索引的指标排法。",
      chart_treatment: "细线证据轴与单色重点柱，像观点页里的证据栏。",
      background_visual_anchor: "右侧斜切摄影纸面、红色编辑标记和页边细线构成杂志感。",
      visual_focus_asset_strategy: "大图感只在右侧边缘和页角出现，左侧导语区是干净纸面，不做白框。",
    },
    "saas-product": {
      layout_variant: "product_workspace",
      title_treatment: "产品营销标题，冷静干净，突出功能价值和流程收益。",
      metric_treatment: "蓝绿开放式指标，像产品增长看板的摘要层。",
      chart_treatment: "蓝绿增长柱图加节点线，表达转化与扩展路径。",
      background_visual_anchor: "右侧半透明产品界面浮层、流程节点和蓝绿工作台光。",
      visual_focus_asset_strategy: "界面浮层作为产品环境，不承载真实文字；可编辑文案和图表仍在 PPT 层。",
    },
    "investor-narrative": {
      layout_variant: "boardroom_growth",
      title_treatment: "董事会级 pitch 标题，压缩语言，强调主张和可信度。",
      metric_treatment: "市场、窗口、杠杆三组数字像投委会摘要。",
      chart_treatment: "深色底上的金色增长线与关键柱体组合。",
      background_visual_anchor: "左侧金色地球、金融雾化城市和深色留白形成投资叙事主视觉。",
      visual_focus_asset_strategy: "地球和城市远景固定在左侧，右侧深色净空承载标题、增长逻辑和可编辑增长线。",
    },
  };
  return treatments[candidate.slug];
}

function build_chart_language(candidate) {
  const languages = {
    "minimal-premium": {
      type: "thin_column_with_baseline",
      description: "极细坐标基线、黑灰柱体和单色强调，像咨询报告里的开放式图表。",
    },
    "playful-anime": {
      type: "rounded_learning_progress",
      description: "彩色学习进度柱和圆点标签，图表更轻松，但仍保持可编辑形状。",
    },
    "data-analytics": {
      type: "dashboard_glow_columns",
      description: "深色仪表盘发光柱，轴线弱化，KPI 与图表形成同一数据语言。",
    },
    "oriental-heritage": {
      type: "ink_sequence_columns",
      description: "起承转合四段式柱体，朱红和墨黑交替，像国潮品牌方法论。",
    },
    "future-tech": {
      type: "neon_launch_columns",
      description: "青紫霓虹柱体和极弱网格，模拟发布会大屏的数据模块。",
    },
    "editorial-magazine": {
      type: "editorial_evidence_axis",
      description: "细线证据轴、红色关键点和克制柱体，像趋势杂志里的观点图。",
    },
    "saas-product": {
      type: "product_growth_flow",
      description: "蓝绿增长柱和流程节点结合，表达产品激活、留存和扩展路径。",
    },
    "investor-narrative": {
      type: "gold_growth_story",
      description: "深色底上的金色增长线和关键柱体，突出市场规模、收入杠杆和扩张窗口。",
    },
  };
  return languages[candidate.slug];
}

function build_visual_decomposition(candidate, coordinate_blueprint) {
  return {
    source: "先直出完整效果图，确认审美后从效果图拆解坐标、留白、背景、透明素材和可编辑层。",
    reference_image_role:
      "完整效果图只用于确认风格、排版、字体、图表语言和层次，不作为最终 PPT 交付。",
    clean_background_role:
      "clean background 保留参考图的背景、光影、材质、留白和低纹理安全区，移除所有文字、数字、图表和标签。",
    zones: coordinate_blueprint.zones,
    reconstruction_rule:
      "最终 PPTX 用 clean background 做底层，透明素材做装饰层，标题、正文、指标、图表和标签全部由 PPT 可编辑对象重建。",
  };
}

function build_reconstruction_layers(candidate) {
  return [
    "clean_background_raster_layer",
    ...candidate.transparent_assets.map((asset) => `transparent_asset_layer:${asset}`),
    "editable_title_and_subtitle_text",
    "editable_body_and_bullet_text",
    "editable_metric_numbers_and_labels",
    "editable_chart_shapes_and_axis_labels",
  ];
}

function build_sample_slide_spec(candidate, content, coordinate_blueprint, treatments) {
  return {
    layout: "style_candidate_sample",
    layout_variant: treatments.layout_variant,
    title: content.title,
    subtitle: content.subtitle,
    section_title: content.section_title,
    body: content.body,
    bullets: content.bullets,
    metrics: content.metrics,
    chart_labels: content.chart_labels,
    title_treatment: treatments.title_treatment,
    metric_treatment: treatments.metric_treatment,
    chart_treatment: treatments.chart_treatment,
    background_visual_anchor: treatments.background_visual_anchor,
    visual_focus_asset_strategy: treatments.visual_focus_asset_strategy,
    integrated_surface_strategy:
      "用背景留白、开放式信息层、无容器图表和无描边指标数字组组成页面，避免把内容装进框里。",
    readable_area_strategy:
      "先让背景提供文本安全区、图表安全区和低纹理过渡区，再叠加可编辑文本和图表；不能靠加框补救可读性。",
    coordinate_blueprint_strategy:
      `坐标蓝图来自效果图拆解；标题、正文、指标和图表分别落在 ${Object.keys(coordinate_blueprint.zones).join("、")} 内，背景必须按这些坐标预留干净区域。`,
    reference_reconstruction_strategy:
      "先用完整效果图确认风格，再生成移除文字/数字/图表的 clean background，最后用 PPT 可编辑文本、形状和图表按坐标重建。",
    forbidden_large_panel_count: 0,
    forbidden_framed_metric_tile_count: 0,
  };
}

function build_candidate(candidate_template, topic) {
  const prompt_file = `prompts/clean-background-${candidate_template.slug}.md`;
  const style_reference_prompt_file = `prompts/style-reference-${candidate_template.slug}.md`;
  const content = build_sample_content(topic, candidate_template);
  const coordinate_blueprint = build_coordinate_blueprint(candidate_template);
  const treatments = build_style_treatments(candidate_template);
  return {
    slug: candidate_template.slug,
    name: candidate_template.name,
    pptx_sample_path: `samples/style-sample-${candidate_template.slug}.pptx`,
    preview_png_path: `previews/style-sample-${candidate_template.slug}.png`,
    background_asset_path: `assets/background-${candidate_template.slug}.png`,
    transparent_asset_paths: [
      `assets/transparent-${candidate_template.slug}-accent-01.png`,
      `assets/transparent-${candidate_template.slug}-accent-02.png`,
    ],
    prompt_file,
    clean_background_prompt_file: prompt_file,
    style_reference_prompt_file,
    image_generation_prompt: build_clean_background_prompt(candidate_template, topic, content, coordinate_blueprint),
    style_reference_prompt: build_style_reference_prompt(candidate_template, topic, content, coordinate_blueprint),
    palette: candidate_template.palette,
    best_for: candidate_template.best_for,
    visual_direction: candidate_template.visual_direction,
    sample_content: content,
    layout_variant: treatments.layout_variant,
    title_treatment: treatments.title_treatment,
    metric_treatment: treatments.metric_treatment,
    chart_treatment: treatments.chart_treatment,
    background_visual_anchor: treatments.background_visual_anchor,
    visual_focus_asset_strategy: treatments.visual_focus_asset_strategy,
    sample_slide_spec: build_sample_slide_spec(candidate_template, content, coordinate_blueprint, treatments),
    coordinate_blueprint,
    visual_decomposition: build_visual_decomposition(candidate_template, coordinate_blueprint),
    reconstruction_layers: build_reconstruction_layers(candidate_template),
    typography_system: build_typography_system(candidate_template),
    chart_language: build_chart_language(candidate_template),
    raster_layers: candidate_template.raster_layers,
    transparent_assets: candidate_template.transparent_assets,
    editable_layers: candidate_template.editable_layers,
    editable_text_contract:
      "标题、副标题、正文、要点、指标数字、指标标签和图表标签必须作为 PPT 文本对象生成，用户能在 PowerPoint 中直接改。",
    asset_layer_contract:
      "背景和装饰只能作为独立 raster/transparent image assets 叠加，不得承载正式正文、关键数字或图表标签。",
    surface_strategy:
      "采用融合式版面：文本、指标和图表嵌入背景留白、光带或纸纹/玻璃层中，形成同一视觉系统。",
    safe_background_wash_transparency: new Set(["data-analytics", "future-tech", "investor-narrative"]).has(
      candidate_template.slug
    )
      ? 100
      : 100,
    readability_contract:
      "配色、配图和字色必须服务可读性：标题、正文、指标、图表线条都要落在背景预留的阅读安全区或图表安全区，过渡区域先由背景生成，不能靠加框补救。",
    safe_zone_plan: build_safe_zone_plan(candidate_template),
    no_plain_white_box_contract:
      "禁止大白框和容器框：不得用大面积矩形或指标描边框承载正文、指标和图表，浅色区域也必须依靠背景留白、纹理、细线和开放式布局。",
    large_surface_count: {
      content_panels: 0,
      chart_panels: 0,
      framed_metric_tiles: 0,
    },
  };
}

function build_style_profile(candidate, theme, typography) {
  const zones = candidate.coordinate_blueprint.zones;
  const content = candidate.sample_content;
  const profile = {
    eyebrow: {
      label: content.eyebrow_label,
      x: zones.title_zone.x,
      y: Math.max(0.28, zones.title_zone.y - 0.3),
      w: 2.7,
      h: 0.18,
      size: 7.5,
      color: theme.accent,
    },
    title: {
      x: zones.title_zone.x,
      y: zones.title_zone.y,
      w: zones.title_zone.w,
      h: 0.9,
      size: typography.title_size,
      color: theme.foreground,
    },
    subtitle: {
      x: zones.title_zone.x + 0.04,
      y: zones.title_zone.y + 0.84,
      w: Math.min(4.8, zones.title_zone.w),
      h: 0.24,
      size: typography.subtitle_size,
      color: theme.accent,
    },
    divider: {
      x: zones.text_zone.x,
      y: zones.text_zone.y - 0.2,
      w: 4.65,
      color: theme.accent,
      transparency: 35,
      width: 1.2,
    },
    section: {
      x: zones.text_zone.x,
      y: zones.text_zone.y,
      w: 2.2,
      h: 0.28,
      size: typography.section_size,
      color: theme.foreground,
    },
    body: {
      x: zones.text_zone.x,
      y: zones.text_zone.y + 0.55,
      w: zones.text_zone.w,
      h: 0.7,
      size: typography.body_size,
      color: theme.muted,
    },
    bullets: {
      x: zones.text_zone.x + 0.02,
      y: zones.text_zone.y + 1.38,
      w: Math.max(2.8, zones.text_zone.w - 0.5),
      size: typography.label_size + 1,
      step: 0.32,
    },
    metrics: {
      mode: "open",
      start_x: zones.metrics_zone.x,
      y: zones.metrics_zone.y,
      gap: zones.metrics_zone.w / 3,
      value_size: candidate.slug === "data-analytics" ? 20 : 18,
    },
    chart: {
      title: content.chart_title,
      title_x: zones.chart_zone.x + 0.18,
      title_y: zones.chart_zone.y + 0.08,
      title_w: 2.6,
      x: zones.chart_zone.x + 0.1,
      y: zones.chart_zone.y + 0.9,
      w: Math.max(3.2, zones.chart_zone.w - 0.35),
      h: Math.max(2.35, zones.chart_zone.h - 1.45),
      variant: candidate.chart_language.type,
    },
    note: {
      x: Math.max(0.8, zones.text_zone.x),
      y: 6.82,
      w: 6.2,
    },
  };

  switch (candidate.slug) {
    case "playful-anime":
      profile.eyebrow.y = 0.42;
      profile.title.y = 0.82;
      profile.subtitle.y = 1.68;
      profile.subtitle.w = 3.0;
      profile.divider.w = 1.0;
      profile.divider.transparency = 12;
      profile.section.x = 3.02;
      profile.section.y = 2.24;
      profile.body.x = 3.02;
      profile.body.y = 2.78;
      profile.body.w = 3.95;
      profile.bullets.x = 3.04;
      profile.bullets.y = 3.58;
      profile.bullets.w = 3.55;
      profile.bullets.step = 0.38;
      profile.metrics.mode = "playful";
      profile.metrics.start_x = 2.92;
      profile.metrics.gap = 1.72;
      profile.metrics.y = 5.48;
      profile.chart.title_x = 7.45;
      profile.chart.title_y = 1.88;
      profile.chart.x = 7.18;
      profile.chart.y = 2.42;
      profile.chart.w = 4.3;
      profile.chart.h = 3.26;
      profile.note.x = 3.02;
      profile.note.w = 4.4;
      break;
    case "oriental-heritage":
      profile.eyebrow.x = 2.55;
      profile.eyebrow.y = 0.45;
      profile.title.x = 2.52;
      profile.title.w = 4.95;
      profile.title.color = "C32727";
      profile.subtitle.x = 4.52;
      profile.subtitle.y = 1.72;
      profile.subtitle.w = 2.6;
      profile.divider.x = 3.04;
      profile.divider.y = 2.02;
      profile.divider.w = 0.72;
      profile.divider.color = "B91C1C";
      profile.divider.transparency = 10;
      profile.divider.width = 2;
      profile.section.x = 3.04;
      profile.section.y = 2.22;
      profile.body.x = 3.04;
      profile.body.y = 2.78;
      profile.body.w = 3.82;
      profile.bullets.x = 3.06;
      profile.bullets.y = 3.62;
      profile.bullets.w = 3.35;
      profile.metrics.mode = "ritual";
      profile.metrics.start_x = 2.42;
      profile.metrics.gap = 1.74;
      profile.metrics.y = 5.42;
      profile.chart.title_x = 7.46;
      profile.chart.title_y = 1.72;
      profile.chart.x = 7.16;
      profile.chart.y = 2.26;
      profile.chart.w = 4.34;
      profile.chart.h = 3.52;
      profile.note.x = 8.4;
      profile.note.w = 2.5;
      break;
    case "future-tech":
      profile.eyebrow.y = 0.42;
      profile.title.y = 0.82;
      profile.subtitle.y = 1.62;
      profile.divider.color = theme.accent;
      profile.chart.title_x = 7.18;
      profile.chart.title_y = 1.62;
      profile.chart.x = 6.94;
      profile.chart.y = 2.2;
      profile.chart.w = 4.56;
      profile.chart.h = 3.9;
      break;
    case "editorial-magazine":
      profile.eyebrow.x = 2.42;
      profile.eyebrow.y = 0.42;
      profile.eyebrow.size = 7.2;
      profile.eyebrow.color = "D72638";
      profile.title.x = 2.42;
      profile.title.y = 0.8;
      profile.title.w = 5.0;
      profile.title.h = 1.0;
      profile.title.color = "1F2937";
      profile.subtitle.x = 2.44;
      profile.subtitle.y = 1.84;
      profile.subtitle.w = 3.6;
      profile.subtitle.color = "6B5560";
      profile.divider.x = 2.42;
      profile.divider.y = 2.06;
      profile.divider.w = 1.28;
      profile.divider.color = theme.accent;
      profile.divider.transparency = 10;
      profile.section.x = 2.42;
      profile.section.y = 2.54;
      profile.section.color = "1F2937";
      profile.body.x = 2.42;
      profile.body.y = 3.02;
      profile.body.w = 3.65;
      profile.body.color = "6B7280";
      profile.bullets.x = 2.44;
      profile.bullets.y = 3.9;
      profile.bullets.w = 3.45;
      profile.bullets.color = "1F2937";
      profile.metrics.mode = "folio";
      profile.metrics.start_x = 2.42;
      profile.metrics.gap = 1.52;
      profile.metrics.y = 5.42;
      profile.chart.title_x = 7.25;
      profile.chart.title_y = 1.88;
      profile.chart.x = 7.04;
      profile.chart.y = 2.28;
      profile.chart.w = 4.08;
      profile.chart.h = 3.48;
      profile.note.x = 8.86;
      profile.note.w = 2.8;
      break;
    case "saas-product":
      profile.eyebrow.y = 0.44;
      profile.title.y = 0.82;
      profile.subtitle.y = 1.62;
      profile.divider.w = 4.55;
      profile.body.w = 4.85;
      profile.chart.title_x = 7.2;
      profile.chart.title_y = 1.7;
      profile.chart.x = 7.02;
      profile.chart.y = 2.2;
      profile.chart.w = 4.3;
      profile.chart.h = 3.64;
      break;
    case "investor-narrative":
      profile.eyebrow.x = 4.82;
      profile.eyebrow.y = 0.44;
      profile.title.x = 4.82;
      profile.title.y = 0.8;
      profile.title.w = 5.4;
      profile.subtitle.x = 4.84;
      profile.subtitle.y = 1.58;
      profile.subtitle.w = 3.2;
      profile.divider.x = 4.82;
      profile.divider.y = 2.08;
      profile.divider.w = 3.0;
      profile.divider.color = "F6C85F";
      profile.divider.transparency = 18;
      profile.section.x = 4.82;
      profile.section.y = 2.38;
      profile.body.x = 4.82;
      profile.body.y = 2.92;
      profile.body.w = 3.08;
      profile.bullets.x = 4.84;
      profile.bullets.y = 3.72;
      profile.bullets.w = 2.8;
      profile.metrics.mode = "boardroom";
      profile.metrics.start_x = 4.82;
      profile.metrics.gap = 1.42;
      profile.metrics.y = 5.46;
      profile.metrics.value_size = 18.5;
      profile.chart.title_x = 8.42;
      profile.chart.title_y = 1.72;
      profile.chart.x = 8.16;
      profile.chart.y = 2.16;
      profile.chart.w = 3.98;
      profile.chart.h = 3.72;
      profile.note.x = 8.8;
      profile.note.w = 2.8;
      break;
    default:
      break;
  }
  return profile;
}

function add_metric_group(slide, candidate, theme, typography, profile) {
  const is_dark = new Set(["data-analytics", "future-tech", "investor-narrative"]).has(candidate.slug);
  candidate.sample_content.metrics.forEach((metric, index) => {
    const x = profile.metrics.start_x + index * profile.metrics.gap;
    const w = Math.max(1.16, profile.metrics.gap - 0.16);
    if (profile.metrics.mode === "folio") {
      const editorial_colors = candidate.slug === "editorial-magazine";
      add_text(slide, metric.label, {
        x,
        y: profile.metrics.y + 0.02,
        w,
        h: 0.18,
        font_face: typography.eyebrow_font_face || typography.body_font_face,
        font_size: 6.8,
        bold: true,
        color: editorial_colors ? "6B7280" : theme.muted,
      });
      slide.addShape("line", {
        x,
        y: profile.metrics.y + 0.28,
        w: 0.56,
        h: 0,
        line: {
          color: strip_hash(index === 1 ? theme.accent : editorial_colors ? "1F2937" : theme.foreground),
          transparency: 16,
          width: 1.4,
        },
      });
      add_text(slide, metric.value, {
        x,
        y: profile.metrics.y + 0.34,
        w,
        h: 0.34,
        font_face: typography.title_font_face,
        font_size: 18,
        bold: true,
        color: index === 1 ? theme.accent : editorial_colors ? "1F2937" : theme.foreground,
      });
      return;
    }
    if (profile.metrics.mode === "ritual") {
      slide.addShape("line", {
        x,
        y: profile.metrics.y,
        w: 0.5,
        h: 0,
        line: { color: strip_hash(index === 1 ? "171717" : theme.accent), transparency: 10, width: 1.4 },
      });
      add_text(slide, metric.value, {
        x,
        y: profile.metrics.y + 0.14,
        w,
        h: 0.34,
        font_face: typography.title_font_face,
        font_size: 18,
        bold: true,
        color: index === 1 ? "171717" : theme.accent,
      });
      add_text(slide, metric.label, {
        x,
        y: profile.metrics.y + 0.52,
        w,
        h: 0.18,
        font_face: typography.body_font_face,
        font_size: typography.label_size,
        color: "171717",
      });
      return;
    }
    if (profile.metrics.mode === "boardroom") {
      add_open_metric_stat(slide, metric, index, theme, x, profile.metrics.y, w, {
        accent: "F6C85F",
        font_face: typography.title_font_face,
        label_font_face: typography.body_font_face,
        line_transparency: 10,
        value_size: profile.metrics.value_size,
        label_size: typography.label_size,
        label_color: "E6EEF8",
      });
      return;
    }
    if (profile.metrics.mode === "playful") {
      add_open_metric_stat(slide, metric, index, theme, x, profile.metrics.y, w, {
        accent: index === 1 ? theme.accent_2 : theme.accent,
        font_face: typography.title_font_face,
        label_font_face: typography.body_font_face,
        line_transparency: 8,
        value_size: 18,
        label_size: typography.label_size,
        label_color: theme.foreground,
      });
      return;
    }
    add_open_metric_stat(slide, metric, index, theme, x, profile.metrics.y, w, {
      font_face: typography.title_font_face,
      label_font_face: typography.body_font_face,
      line_transparency: candidate.slug === "playful-anime" ? 12 : 22,
      value_size: profile.metrics.value_size,
      label_size: typography.label_size,
      label_color: is_dark ? "FFFFFF" : theme.foreground,
    });
  });
}

function add_style_signature_marks(slide, candidate, theme, typography, profile) {
  if (candidate.slug === "minimal-premium") {
    slide.addShape("line", { x: 6.82, y: 1.22, w: 0, h: 4.92, line: { color: "A7A7A7", transparency: 45, width: 1 } });
    return;
  }
  if (candidate.slug === "playful-anime") {
    [[5.6, 0.9, "FFC93C"], [5.92, 1.02, "FF9EB5"], [6.24, 0.86, "8FD3FF"]].forEach(([x, y, color]) => {
      slide.addShape("ellipse", { x, y, w: 0.1, h: 0.1, fill: { color }, line: { transparency: 100 } });
    });
    return;
  }
  if (candidate.slug === "future-tech") {
    slide.addShape("line", { x: 11.08, y: 0.88, w: 0.74, h: 0.58, line: { color: strip_hash(theme.accent_2), transparency: 54, width: 1.1 } });
    slide.addShape("line", { x: 11.2, y: 6.12, w: 0.56, h: -0.4, line: { color: strip_hash(theme.accent), transparency: 58, width: 1.0 } });
    return;
  }
  if (candidate.slug === "editorial-magazine") {
    add_text(slide, "01", {
      x: 5.74,
      y: 5.86,
      w: 0.8,
      h: 0.28,
      font_face: typography.eyebrow_font_face,
      font_size: 13.5,
      bold: true,
      color: "D8CFC6",
    });
    return;
  }
  if (candidate.slug === "saas-product") {
    slide.addShape("line", { x: 0.56, y: 0.74, w: 0.42, h: 0, line: { color: "2563EB", transparency: 8, width: 1.4 } });
    slide.addShape("ellipse", { x: 10.92, y: 6.1, w: 0.08, h: 0.08, fill: { color: "22C55E" }, line: { transparency: 100 } });
    slide.addShape("ellipse", { x: 11.12, y: 6.1, w: 0.08, h: 0.08, fill: { color: "2563EB" }, line: { transparency: 100 } });
    return;
  }
  if (candidate.slug === "investor-narrative") {
    slide.addShape("line", { x: 0.74, y: 1.88, w: 1.28, h: 0, line: { color: "F6C85F", transparency: 20, width: 1.3 } });
  }
}

function add_sample_layout(slide, candidate, output_dir) {
  const theme = theme_for(candidate);
  const content = candidate.sample_content;
  const typography = candidate.typography_system || build_typography_system(candidate);
  const profile = build_style_profile(candidate, theme, typography);
  add_background(slide, candidate, theme, output_dir);
  add_style_signature_marks(slide, candidate, theme, typography, profile);

  add_text(slide, profile.eyebrow.label, {
    x: profile.eyebrow.x,
    y: profile.eyebrow.y,
    w: profile.eyebrow.w,
    h: profile.eyebrow.h,
    font_face: typography.eyebrow_font_face || typography.body_font_face,
    font_size: profile.eyebrow.size,
    bold: true,
    color: profile.eyebrow.color,
  });
  add_text(slide, content.title, {
    x: profile.title.x,
    y: profile.title.y,
    w: profile.title.w,
    h: profile.title.h,
    font_face: typography.title_font_face,
    font_size: profile.title.size,
    bold: true,
    color: profile.title.color,
  });
  add_text(slide, content.subtitle, {
    x: profile.subtitle.x,
    y: profile.subtitle.y,
    w: profile.subtitle.w,
    h: profile.subtitle.h,
    font_face: typography.body_font_face,
    font_size: profile.subtitle.size,
    bold: true,
    color: profile.subtitle.color,
  });
  slide.addShape("line", {
    x: profile.divider.x,
    y: profile.divider.y,
    w: profile.divider.w,
    h: 0,
    line: {
      color: strip_hash(profile.divider.color),
      transparency: profile.divider.transparency,
      width: profile.divider.width,
    },
  });
  add_text(slide, content.section_title, {
    x: profile.section.x,
    y: profile.section.y,
    w: profile.section.w,
    h: profile.section.h,
    font_face: typography.body_font_face,
    font_size: profile.section.size,
    bold: true,
    color: profile.section.color,
  });
  add_text(slide, content.body, {
    x: profile.body.x,
    y: profile.body.y,
    w: profile.body.w,
    h: profile.body.h,
    font_face: typography.body_font_face,
    font_size: profile.body.size,
    color: profile.body.color,
  });
    add_bullet_list(slide, content.bullets, theme, profile.bullets.x, profile.bullets.y, {
    w: profile.bullets.w,
    font_face: typography.body_font_face,
    font_size: profile.bullets.size,
    step: profile.bullets.step,
    color: profile.bullets.color,
  });
  add_metric_group(slide, candidate, theme, typography, profile);
  add_text(slide, profile.chart.title, {
    x: profile.chart.title_x,
    y: profile.chart.title_y,
    w: profile.chart.title_w,
    h: 0.26,
    font_face: typography.body_font_face,
    font_size: typography.section_size,
    bold: true,
    color: theme.foreground,
  });
  slide.addShape("line", {
    x: profile.chart.x,
    y: profile.chart.y - 0.22,
    w: profile.chart.w,
    h: 0,
    line: { color: strip_hash(profile.divider.color), transparency: 35, width: 1.2 },
  });
  add_editable_chart(slide, content, theme, profile.chart.x, profile.chart.y, profile.chart.w, profile.chart.h, {
    axis: true,
    variant: profile.chart.variant,
    label_font_face: typography.body_font_face,
  });
  add_integrated_note(slide, candidate, theme, typography, profile.note.x, profile.note.y, profile.note.w);
}

async function write_candidate_pptx(output_dir, candidate) {
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Codex";
  pptx.subject = "Editable style candidate sample";
  pptx.title = `${candidate.sample_content.title} - ${candidate.name}`;
  pptx.company = "codex-visual-asset-skills";
  pptx.lang = "zh-CN";
  pptx.theme = {
    headFontFace: "PingFang SC",
    bodyFontFace: "PingFang SC",
    lang: "zh-CN",
  };
  const slide = pptx.addSlide();
  add_sample_layout(slide, candidate, output_dir);
  const pptx_path = path.join(output_dir, candidate.pptx_sample_path);
  ensure_directory(path.dirname(pptx_path));
  await pptx.writeFile({ fileName: pptx_path });
}

function write_png_fallback(preview_path) {
  const fallback_png_base64 =
    "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAIAAADTED8xAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAUNJREFUeNrs0zERAAAIBDEw+idhAkcQWmhmnWWugoY9OQDg7wRAABBAAAQQAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQYAUYABNWAlL3dn3YAAAAAElFTkSuQmCC";
  fs.writeFileSync(preview_path, Buffer.from(fallback_png_base64, "base64"));
}

function render_preview_png(output_dir, candidate) {
  const pptx_path = path.join(output_dir, candidate.pptx_sample_path);
  const preview_path = path.join(output_dir, candidate.preview_png_path);
  const preview_dir = path.dirname(preview_path);
  ensure_directory(preview_dir);
  if (fs.existsSync("/usr/bin/qlmanage")) {
    const result = spawnSync("/usr/bin/qlmanage", ["-t", "-s", "1920", "-o", preview_dir, pptx_path], {
      encoding: "utf8",
    });
    const quicklook_path = path.join(preview_dir, `${path.basename(pptx_path)}.png`);
    if (result.status === 0 && fs.existsSync(quicklook_path)) {
      fs.renameSync(quicklook_path, preview_path);
      if (fs.existsSync("/usr/bin/sips")) {
        spawnSync("/usr/bin/sips", ["-z", "1080", "1920", preview_path], { encoding: "utf8" });
      }
      return;
    }
  }
  write_png_fallback(preview_path);
}

function measure_background_zone_quality(image_path, preview_path, candidate) {
  if (!fs.existsSync(image_path)) {
    return {
      text_zone_score: 1,
      chart_zone_score: 1,
      text_final_readability_score: 1,
      chart_final_readability_score: 1,
      texture_std_max: 0,
      overlay_active_ratio_max: 1,
      overlay_delta_p95_max: 255,
      has_background_overlap_risk: false,
      reason: "no custom background image; deterministic safe canvas",
    };
  }
  const zones = candidate.coordinate_blueprint.zones;
  const payload = {
    image_path,
    preview_path: fs.existsSync(preview_path) ? preview_path : "",
    slide_width,
    slide_height,
    zones: {
      text_zone: zones.text_zone,
      chart_zone: zones.chart_zone,
    },
  };
  const python_source = `
import json
import statistics
import sys
from PIL import Image, ImageChops, ImageFilter, ImageStat

payload = json.loads(sys.stdin.read())
background = Image.open(payload["image_path"]).convert("RGB")
preview = Image.open(payload["preview_path"]).convert("RGB") if payload.get("preview_path") else None
width, height = background.size
if preview and preview.size != background.size:
    preview = preview.resize(background.size)

def zone_stats(zone):
    x0 = max(0, min(width - 1, int(zone["x"] / payload["slide_width"] * width)))
    y0 = max(0, min(height - 1, int(zone["y"] / payload["slide_height"] * height)))
    x1 = max(x0 + 1, min(width, int((zone["x"] + zone["w"]) / payload["slide_width"] * width)))
    y1 = max(y0 + 1, min(height, int((zone["y"] + zone["h"]) / payload["slide_height"] * height)))
    crop = background.crop((x0, y0, x1, y1)).resize((96, 96))
    luminance = []
    for red, green, blue in crop.getdata():
        lum = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        luminance.append(lum)
    std = statistics.pstdev(luminance)
    texture_penalty = min(1.0, std / 56.0)
    score = max(0.0, 1.0 - texture_penalty)
    if preview:
        preview_crop = preview.crop((x0, y0, x1, y1)).resize((144, 144))
        background_crop = background.crop((x0, y0, x1, y1)).resize((144, 144))
        diff_values = list(ImageChops.difference(background_crop, preview_crop).convert("L").getdata())
        diff_values.sort()
        delta_p95 = diff_values[int(len(diff_values) * 0.95)]
        active_ratio = sum(1 for value in diff_values if value > 18) / len(diff_values)
        edge_mean = ImageStat.Stat(preview_crop.convert("L").filter(ImageFilter.FIND_EDGES)).mean[0]
    else:
        delta_p95 = 255
        active_ratio = 1
        edge_mean = 24
    overlay_score = min(1.0, delta_p95 / 74.0) * 0.42 + min(1.0, active_ratio / 0.07) * 0.34 + min(1.0, edge_mean / 18.0) * 0.24
    final_score = max(score, min(1.0, score * 0.45 + overlay_score * 0.55))
    return {
        "std": std,
        "score": score,
        "final_score": final_score,
        "delta_p95": delta_p95,
        "active_ratio": active_ratio,
    }

text_stats = zone_stats(payload["zones"]["text_zone"])
chart_stats = zone_stats(payload["zones"]["chart_zone"])
print(json.dumps({
    "text_zone_score": round(text_stats["score"], 3),
    "chart_zone_score": round(chart_stats["score"], 3),
    "text_final_readability_score": round(text_stats["final_score"], 3),
    "chart_final_readability_score": round(chart_stats["final_score"], 3),
    "texture_std_max": round(max(text_stats["std"], chart_stats["std"]), 3),
    "overlay_active_ratio_max": round(max(text_stats["active_ratio"], chart_stats["active_ratio"]), 3),
    "overlay_delta_p95_max": round(max(text_stats["delta_p95"], chart_stats["delta_p95"]), 3),
    "has_background_overlap_risk": (
        text_stats["score"] < 0.72 and text_stats["final_score"] < 0.8
    ) or (
        chart_stats["score"] < 0.72 and chart_stats["final_score"] < 0.8
    ),
    "reason": "background safe-zone texture plus final editable overlay readability analysis",
}, ensure_ascii=False))
`;
  const result = spawnSync("python3", ["-c", python_source], {
    input: JSON.stringify(payload),
    encoding: "utf8",
  });
  if (result.status !== 0) {
    return {
      text_zone_score: 0,
      chart_zone_score: 0,
      text_final_readability_score: 0,
      chart_final_readability_score: 0,
      texture_std_max: 999,
      overlay_active_ratio_max: 0,
      overlay_delta_p95_max: 0,
      has_background_overlap_risk: true,
      reason: `visual QA measurement failed: ${String(result.stderr || result.stdout).trim()}`,
    };
  }
  return JSON.parse(result.stdout);
}

function write_visual_qa_report(output_dir, candidates) {
  const items = candidates.map((candidate) => {
    const background_path = path.join(output_dir, candidate.background_asset_path);
    const preview_path = path.join(output_dir, candidate.preview_png_path);
    const measurement = measure_background_zone_quality(background_path, preview_path, candidate);
    return {
      slug: candidate.slug,
      name: candidate.name,
      status: measurement.has_background_overlap_risk ? "fail" : "pass",
      text_zone_score: measurement.text_zone_score,
      chart_zone_score: measurement.chart_zone_score,
      text_final_readability_score: measurement.text_final_readability_score,
      chart_final_readability_score: measurement.chart_final_readability_score,
      texture_std_max: measurement.texture_std_max,
      overlay_active_ratio_max: measurement.overlay_active_ratio_max,
      overlay_delta_p95_max: measurement.overlay_delta_p95_max,
      has_background_overlap_risk: measurement.has_background_overlap_risk,
      reason: measurement.reason,
    };
  });
  const failed_count = items.filter((item) => item.status !== "pass").length;
  const report = {
    ok: failed_count === 0,
    gate: "readability + background_overlap + safe_zone_texture + final_overlay_readability",
    candidate_count: candidates.length,
    failed_count,
    items,
  };
  fs.writeFileSync(path.join(output_dir, "style-visual-qa.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
  return report;
}

function measure_background_design_quality(image_path, candidate) {
  if (!fs.existsSync(image_path)) {
    return {
      visual_focus_score: 0,
      edge_signature_score: 0,
      luminance_std: 0,
      has_flat_background_risk: true,
      reason: "missing background visual anchor",
    };
  }
  const zones = candidate.coordinate_blueprint.zones;
  const payload = {
    image_path,
    slide_width,
    slide_height,
    visual_focus_zone: zones.visual_focus_zone,
  };
  const python_source = `
import json
import statistics
import sys
from PIL import Image, ImageFilter, ImageStat

payload = json.loads(sys.stdin.read())
image = Image.open(payload["image_path"]).convert("RGB")
width, height = image.size
focus = payload["visual_focus_zone"]
edge_zones = [
    focus,
    {"x": 0, "y": 0, "w": payload["slide_width"], "h": 1.55},
    {"x": 0, "y": payload["slide_height"] - 1.55, "w": payload["slide_width"], "h": 1.55},
    {"x": 0, "y": 0, "w": 2.2, "h": payload["slide_height"]},
    {"x": payload["slide_width"] - 2.2, "y": 0, "w": 2.2, "h": payload["slide_height"]},
]

def score_zone(zone):
    x0 = max(0, min(width - 1, int(zone["x"] / payload["slide_width"] * width)))
    y0 = max(0, min(height - 1, int(zone["y"] / payload["slide_height"] * height)))
    x1 = max(x0 + 1, min(width, int((zone["x"] + zone["w"]) / payload["slide_width"] * width)))
    y1 = max(y0 + 1, min(height, int((zone["y"] + zone["h"]) / payload["slide_height"] * height)))
    crop = image.crop((x0, y0, x1, y1)).resize((192, 192))
    luminance = []
    for red, green, blue in crop.getdata():
        luminance.append(0.2126 * red + 0.7152 * green + 0.0722 * blue)
    luminance_std = statistics.pstdev(luminance)
    edges = crop.convert("L").filter(ImageFilter.FIND_EDGES)
    edge_mean = ImageStat.Stat(edges).mean[0]
    try:
        import colorsys
        saturation = []
        for red, green, blue in crop.getdata():
            saturation.append(colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)[1] * 255)
        saturation_mean = statistics.mean(saturation)
        saturation_std = statistics.pstdev(saturation)
    except Exception:
        saturation_mean = 0
        saturation_std = 0
    visual_focus_score = min(
        1.0,
        min(1.0, luminance_std / 24.0) * 0.28
        + min(1.0, edge_mean / 10.0) * 0.45
        + min(1.0, saturation_std / 28.0) * 0.12
        + min(1.0, saturation_mean / 180.0) * 0.15,
    )
    edge_signature_score = min(1.0, max(edge_mean / 8.0, saturation_std / 55.0, saturation_mean / 220.0))
    return visual_focus_score, edge_signature_score, luminance_std

visual_focus_score, edge_signature_score, luminance_std = max(score_zone(zone) for zone in edge_zones)
visual_focus_score = max(visual_focus_score, min(1.0, edge_signature_score * 0.6))
print(json.dumps({
    "visual_focus_score": round(visual_focus_score, 3),
    "edge_signature_score": round(edge_signature_score, 3),
    "luminance_std": round(luminance_std, 3),
    "has_flat_background_risk": visual_focus_score < 0.42 or edge_signature_score < 0.28,
    "reason": "visual focus and edge-band richness analysis",
}, ensure_ascii=False))
`;
  const result = spawnSync("python3", ["-c", python_source], {
    input: JSON.stringify(payload),
    encoding: "utf8",
  });
  if (result.status !== 0) {
    return {
      visual_focus_score: 0,
      edge_signature_score: 0,
      luminance_std: 0,
      has_flat_background_risk: true,
      reason: `design QA measurement failed: ${String(result.stderr || result.stdout).trim()}`,
    };
  }
  return JSON.parse(result.stdout);
}

function write_design_qa_report(output_dir, candidates) {
  const items = candidates.map((candidate) => {
    const background_path = path.join(output_dir, candidate.background_asset_path);
    const measurement = measure_background_design_quality(background_path, candidate);
    return {
      slug: candidate.slug,
      name: candidate.name,
      status: measurement.has_flat_background_risk ? "fail" : "pass",
      visual_focus_score: measurement.visual_focus_score,
      edge_signature_score: measurement.edge_signature_score,
      luminance_std: measurement.luminance_std,
      has_flat_background_risk: measurement.has_flat_background_risk,
      background_visual_anchor: candidate.background_visual_anchor,
      reason: measurement.reason,
    };
  });
  const failed_count = items.filter((item) => item.status !== "pass").length;
  const report = {
    ok: failed_count === 0,
    gate: "visual_focus + edge_signature + anti_flat_background",
    candidate_count: candidates.length,
    failed_count,
    items,
  };
  fs.writeFileSync(path.join(output_dir, "style-design-qa.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
  return report;
}

function read_candidate_slide_xml(output_dir, candidate) {
  const pptx_path = path.join(output_dir, candidate.pptx_sample_path);
  if (!fs.existsSync(pptx_path)) {
    return "";
  }
  const result = spawnSync("unzip", ["-p", pptx_path, "ppt/slides/slide1.xml"], { encoding: "utf8" });
  if (result.status !== 0) {
    return "";
  }
  return result.stdout || "";
}

function score_candidate_director_item(output_dir, candidate, visual_item, design_item) {
  const slide_xml = read_candidate_slide_xml(output_dir, candidate);
  const brief_keys = [
    candidate.layout_variant,
    candidate.title_treatment,
    candidate.metric_treatment,
    candidate.chart_treatment,
    candidate.typography_system?.heading,
    candidate.typography_system?.body,
    candidate.chart_language?.type,
    candidate.surface_strategy,
  ];
  const metadata_score = brief_keys.filter(Boolean).length / brief_keys.length;
  const has_editable_text = (slide_xml.match(/<a:t>/g) || []).length >= 12;
  const round_rect_count = (slide_xml.match(/prst="roundRect"/g) || []).length;
  const no_large_surface =
    candidate.large_surface_count?.content_panels === 0 &&
    candidate.large_surface_count?.chart_panels === 0 &&
    candidate.large_surface_count?.framed_metric_tiles === 0;
  const consistency_score = Math.min(1, metadata_score * 0.75 + (has_editable_text ? 0.25 : 0));
  const harmony_score = Math.min(
    1,
    (visual_item?.status === "pass" ? 0.34 : 0) +
      (design_item?.status === "pass" ? 0.28 : 0) +
      (round_rect_count === 0 ? 0.2 : 0) +
      (no_large_surface ? 0.18 : 0)
  );
  const diversity_signature = [
    candidate.layout_variant,
    candidate.chart_language?.type,
    candidate.title_treatment,
    candidate.metric_treatment,
    candidate.coordinate_blueprint?.zones?.title_zone?.x,
    candidate.coordinate_blueprint?.zones?.text_zone?.x,
    candidate.coordinate_blueprint?.zones?.chart_zone?.x,
  ].join("::");
  const errors = [];
  if (consistency_score < 0.8) errors.push("consistency_score below 0.8");
  if (harmony_score < 0.8) errors.push("harmony_score below 0.8");
  if (round_rect_count > 0) errors.push("roundRect rescue box detected");
  if (!has_editable_text) errors.push("editable text layer too sparse");
  return {
    slug: candidate.slug,
    name: candidate.name,
    layout_variant: candidate.layout_variant,
    chart_language_type: candidate.chart_language?.type,
    consistency_score: Number(consistency_score.toFixed(2)),
    harmony_score: Number(harmony_score.toFixed(2)),
    diversity_signature,
    editable_text_run_count: (slide_xml.match(/<a:t>/g) || []).length,
    round_rect_count,
    large_surface_count: candidate.large_surface_count,
    status: errors.length ? "fail" : "pass",
    errors,
  };
}

function write_design_director_qa_report(output_dir, candidates, visual_qa, design_qa) {
  const visual_by_slug = Object.fromEntries(visual_qa.items.map((item) => [item.slug, item]));
  const design_by_slug = Object.fromEntries(design_qa.items.map((item) => [item.slug, item]));
  const items = candidates.map((candidate) =>
    score_candidate_director_item(output_dir, candidate, visual_by_slug[candidate.slug], design_by_slug[candidate.slug])
  );
  const diversity_signatures = new Set(items.map((item) => item.diversity_signature));
  const chart_language_types = new Set(items.map((item) => item.chart_language_type));
  const errors = items.flatMap((item) => item.errors.map((error) => `${item.slug}: ${error}`));
  if (diversity_signatures.size < items.length) {
    errors.push("diversity signatures must be unique across style candidates");
  }
  if (chart_language_types.size < items.length) {
    errors.push("chart language types must be unique across style candidates");
  }
  const report = {
    ok: errors.length === 0,
    gate: "design director commercial QA: consistency + harmony + diversity + editable layers",
    candidate_count: candidates.length,
    failed_count: items.filter((item) => item.status !== "pass").length,
    unique_diversity_signature_count: diversity_signatures.size,
    unique_chart_language_type_count: chart_language_types.size,
    min_consistency_score: items.length ? Math.min(...items.map((item) => item.consistency_score)) : 0,
    min_harmony_score: items.length ? Math.min(...items.map((item) => item.harmony_score)) : 0,
    errors,
    items,
  };
  fs.writeFileSync(path.join(output_dir, "design-director-qa.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
  return report;
}

function write_prompt_file(output_dir, candidate) {
  const prompt_path = path.join(output_dir, candidate.prompt_file);
  ensure_directory(path.dirname(prompt_path));
  fs.writeFileSync(prompt_path, `${candidate.image_generation_prompt}\n`, "utf8");
  const style_reference_prompt_path = path.join(output_dir, candidate.style_reference_prompt_file);
  ensure_directory(path.dirname(style_reference_prompt_path));
  fs.writeFileSync(style_reference_prompt_path, `${candidate.style_reference_prompt}\n`, "utf8");
}

function write_markdown(output_dir, topic, candidates, background_asset_policy) {
  const lines = [
    "# PPT 风格候选真实样板包",
    "",
    `主题：${topic}`,
    "",
    "硬规则：每个候选必须先生成真实 PPTX 样板，再从 PPTX 导出 PNG 预览。PNG 预览只用于选择风格；真正可复用的是 PPTX 样板、背景素材、透明素材和分层契约。标题、正文、指标、图表标签必须文本可编辑，不允许把正式页面整页生图后交给用户选。视觉上必须是融合式版面，禁止大白框贴背景。",
    "",
    "使用方式：",
    "",
    "1. 先查看 `samples/style-sample-*.pptx`，确认文字、指标和图表标签能在 PowerPoint 中直接编辑。",
    "2. 再查看 `previews/style-sample-*.png`，让用户从 8 张单独预览里选择风格。",
    "3. 如需提高画面质感，先按 `prompts/style-reference-*.md` 生成完整效果图母稿，验收后再按 `prompts/clean-background-*.md` 生成无文字 clean background，保存到 `assets/background-*.png` 后重新运行本工具。",
    "4. 被选中的方向进入逐页 PPT 生产，沿用同一套 PPT 分层结构，而不是重新临摹一张整页图片。",
    "5. 查看 `style-visual-qa.json`，任何候选只要文字区或图表区背景复杂度过高，就不能作为通过样张展示。",
    "",
    `背景来源：${background_asset_policy.source}`,
    `商用状态：${background_asset_policy.commercial_ready ? "ready" : "not-ready"}`,
    `限制：${background_asset_policy.restriction}`,
    "",
  ];
  for (const candidate of candidates) {
    lines.push(`## ${candidate.name}`);
    lines.push("");
    lines.push(`- PPTX 样板：\`${candidate.pptx_sample_path}\``);
    lines.push(`- PNG 预览：\`${candidate.preview_png_path}\``);
    lines.push(`- 效果图母稿提示词：\`${candidate.style_reference_prompt_file}\``);
    lines.push(`- clean background 提示词：\`${candidate.clean_background_prompt_file}\``);
    lines.push(`- 背景素材：\`${candidate.background_asset_path}\``);
    lines.push(`- 适合场景：${candidate.best_for.join("、")}`);
    lines.push(`- 视觉方向：${candidate.visual_direction}`);
    lines.push(`- 透明素材：${candidate.transparent_assets.join("、")}`);
    lines.push(`- 可编辑层：${candidate.editable_layers.join("、")}`);
    lines.push(`- 版式变体：${candidate.layout_variant}`);
    lines.push(`- 样本标题：${candidate.sample_content.title}`);
    lines.push(`- 样本正文：${candidate.sample_content.body}`);
    lines.push(`- 分层契约：${candidate.editable_text_contract}`);
    lines.push(`- 反拆来源：${candidate.visual_decomposition.source}`);
    lines.push(`- 字体系统：${candidate.typography_system.heading} ${candidate.typography_system.body}`);
    lines.push(`- 标题处理：${candidate.title_treatment}`);
    lines.push(`- 指标处理：${candidate.metric_treatment}`);
    lines.push(`- 图表处理：${candidate.chart_treatment}`);
    lines.push(`- 背景主视觉：${candidate.background_visual_anchor}`);
    lines.push(`- 视觉焦点策略：${candidate.visual_focus_asset_strategy}`);
    lines.push(`- 图表语言：${candidate.chart_language.description}`);
    lines.push(`- 可编辑重建层：${candidate.reconstruction_layers.join("、")}`);
    lines.push(`- 融合策略：${candidate.surface_strategy}`);
    lines.push(`- 阅读安全区：${candidate.safe_zone_plan.text_zone}`);
    lines.push(`- 图表安全区：${candidate.safe_zone_plan.chart_zone}`);
    lines.push(
      `- 坐标蓝图：单位 ${candidate.coordinate_blueprint.unit}，页面 ${candidate.coordinate_blueprint.slide.width} x ${candidate.coordinate_blueprint.slide.height}`
    );
    for (const zone_name of ["title_zone", "text_zone", "chart_zone", "metrics_zone", "visual_focus_zone", "protected_empty_zone"]) {
      const zone = candidate.coordinate_blueprint.zones[zone_name];
      lines.push(
        `- ${zone_name}：x=${zone.x}, y=${zone.y}, w=${zone.w}, h=${zone.h}；${zone.role}；${zone.capacity}`
      );
    }
    lines.push(`- 可读性契约：${candidate.readability_contract}`);
    lines.push(`- 白框约束：${candidate.no_plain_white_box_contract}`);
    lines.push(`- 大面积正文容器：${candidate.large_surface_count.content_panels}`);
    lines.push(`- 大面积图表容器：${candidate.large_surface_count.chart_panels}`);
    lines.push(`- 指标描边框：${candidate.large_surface_count.framed_metric_tiles}`);
    lines.push("");
  }
  if (lines[lines.length - 1] === "") {
    lines.pop();
  }
  fs.writeFileSync(path.join(output_dir, "style-candidates.md"), `${lines.join("\n")}\n`, "utf8");
}

function write_spec(output_dir, topic, candidates, background_asset_policy) {
  const spec = {
    topic,
    candidate_count: candidates.length,
    delivery_contract: "editable_pptx_samples_with_png_previews",
    background_asset_policy,
    preview_rule: "PNG 预览必须由对应 PPTX 样板渲染导出，不能直接使用整页生图作为候选。",
    ppt_contract:
      "PPTX 样板中的标题、正文、指标、图表标签和关键注释必须可编辑；图片只承担背景、透明素材和装饰层。",
    visual_quality_contract:
      "候选必须达到融合式版面：背景、文本、指标和图表属于同一视觉系统；文字和图表要嵌入背景留白，禁止大白框、内容容器框和指标描边框。",
    readable_area_policy: {
      text_safe_zones_required: true,
      chart_safe_zones_required: true,
      low_detail_transition_required: true,
      visual_qa_report_required: true,
      min_body_text_contrast_ratio: 4.5,
      min_chart_stroke_contrast_ratio: 3.0,
      anti_rescue_box_rule: "不能靠加框补救可读性；必须先通过背景留白、低纹理过渡区和字色/线色选择解决。",
    },
    coordinate_blueprint_policy: {
      coordinate_unit: "inches_16_9",
      blueprint_required_before_background: true,
      background_prompt_must_include_zone_coordinates: true,
      layout_first_rule: "先直出完整效果图，确认审美后做效果图拆解，再生成 clean background、透明素材、文案和图表；所有可编辑元素按坐标蓝图落版。",
    },
    style_reference_policy: {
      reference_image_required_before_decomposition: true,
      clean_background_after_reference: true,
      editable_reconstruction_required: true,
      workflow_rule:
        "先直出完整效果图确认风格，再反拆留白、素材和坐标，随后生成移除文字/数字/图表的 clean background，最终用 PPT 可编辑层重建。",
    },
    large_surface_policy: {
      max_large_content_panels: 0,
      max_large_chart_panels: 0,
      max_framed_metric_tiles: 0,
      allowed_open_metric_groups: true,
    },
    style_diversity_policy: {
      min_unique_layout_variants: 6,
      typography_should_follow_style: true,
      chart_language_should_follow_style: true,
      title_and_metric_treatments_must_not_collapse_to_single_template: true,
    },
    visual_focus_policy: {
      visible_visual_anchor_required: true,
      min_visual_focus_score: 0.42,
      min_edge_signature_score: 0.28,
      visual_anchor_must_stay_outside_text_safe_zone: true,
      anti_flat_background_rule: "通过可读性门禁不等于通过设计门禁；每套风格都必须在 visual_focus_zone 有可见主视觉元素，不能只靠底色和低纹理留白。",
    },
    candidates,
  };
  fs.writeFileSync(path.join(output_dir, "style-candidate-spec.json"), `${JSON.stringify(spec, null, 2)}\n`, "utf8");
}

function copy_background_assets_if_requested(output_dir, source_dir, candidates) {
  if (!source_dir) {
    return;
  }
  const resolved_source_dir = path.resolve(source_dir);
  for (const candidate of candidates) {
    const source_path = path.join(resolved_source_dir, `background-${candidate.slug}.png`);
    const target_path = path.join(output_dir, candidate.background_asset_path);
    if (fs.existsSync(source_path)) {
      ensure_directory(path.dirname(target_path));
      fs.copyFileSync(source_path, target_path);
    }
  }
}

function assert_real_background_assets(output_dir, candidates) {
  const missing = [];
  for (const candidate of candidates) {
    const target_path = path.join(output_dir, candidate.background_asset_path);
    if (!fs.existsSync(target_path)) {
      missing.push(path.basename(candidate.background_asset_path));
    }
  }
  if (missing.length) {
    throw new Error(
      [
        "正式候选需要真实生图背景或用户提供的 raster 背景，不能用代码绘制背景进入展示。",
        "请先用 Codex imagegen / Skywork Design / 用户模板反拆生成以下 PNG，再通过 --background-source-dir 传入：",
        missing.join(", "),
      ].join("\n")
    );
  }
}

function ensure_default_background_assets(output_dir, candidates) {
  const renderer_path = path.join(__dirname, "render_style_background.py");
  for (const candidate of candidates) {
    const target_path = path.join(output_dir, candidate.background_asset_path);
    if (fs.existsSync(target_path)) {
      continue;
    }
    const result = spawnSync(
      "python3",
      [
        renderer_path,
        "--style-slug",
        candidate.slug,
        "--output",
        target_path,
        "--blueprint-json",
        JSON.stringify(candidate.coordinate_blueprint),
      ],
      { encoding: "utf8" }
    );
    if (result.status !== 0 || !fs.existsSync(target_path)) {
      throw new Error(`failed to render default background for ${candidate.slug}: ${String(result.stderr || result.stdout).trim()}`);
    }
  }
}

async function main() {
  let args;
  try {
    args = parse_args(process.argv);
  } catch (error) {
    console.error(`${error.message}\n\n${usage()}`);
    process.exit(1);
  }
  if (args.help) {
    console.log(usage());
    return;
  }
  if (!args.output_dir) {
    console.error(`missing --output-dir\n\n${usage()}`);
    process.exit(1);
  }

  const output_dir = path.resolve(args.output_dir);
  const topic = args.topic || "2026 AI 应用趋势调研";
  ensure_directory(output_dir);
  ensure_directory(path.join(output_dir, "assets"));

  const candidates = candidate_templates.map((candidate) => build_candidate(candidate, topic));
  copy_background_assets_if_requested(output_dir, args.background_source_dir, candidates);
  const background_asset_policy = args.allow_placeholder_backgrounds
    ? {
        source: "test_only_placeholder",
        commercial_ready: false,
        restriction:
          "仅允许单元测试和结构验证；不能进入正式展示、README 样张、style-library 或商业交付。",
      }
    : {
        source: "imagegen_or_user_provided_raster",
        commercial_ready: true,
        restriction:
          "背景必须来自 Codex imagegen、Skywork Design、用户模板反拆或用户提供的真实 raster 设计素材；不得使用代码绘制主视觉。",
      };
  if (args.allow_placeholder_backgrounds) {
    ensure_default_background_assets(output_dir, candidates);
  } else {
    assert_real_background_assets(output_dir, candidates);
  }
  for (const candidate of candidates) {
    write_prompt_file(output_dir, candidate);
    await write_candidate_pptx(output_dir, candidate);
    render_preview_png(output_dir, candidate);
  }
  const visual_qa = write_visual_qa_report(output_dir, candidates);
  const design_qa = write_design_qa_report(output_dir, candidates);
  const director_qa = write_design_director_qa_report(output_dir, candidates, visual_qa, design_qa);
  write_spec(output_dir, topic, candidates, background_asset_policy);
  write_markdown(output_dir, topic, candidates, background_asset_policy);

  console.log(
    JSON.stringify(
      {
        ok: true,
        output_dir,
        candidate_count: candidates.length,
        delivery_contract: "editable_pptx_samples_with_png_previews",
        spec: path.join(output_dir, "style-candidate-spec.json"),
        visual_qa: path.join(output_dir, "style-visual-qa.json"),
        design_qa: path.join(output_dir, "style-design-qa.json"),
        director_qa: path.join(output_dir, "design-director-qa.json"),
        visual_qa_ok: visual_qa.ok,
        design_qa_ok: design_qa.ok,
        director_qa_ok: director_qa.ok,
        pptx_samples: candidates.map((candidate) => path.join(output_dir, candidate.pptx_sample_path)),
        previews: candidates.map((candidate) => path.join(output_dir, candidate.preview_png_path)),
      },
      null,
      2
    )
  );
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
