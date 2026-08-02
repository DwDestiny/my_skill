#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# GEB-L3
# Input: Markdown 文本/文件（+ 可选 metadata JSON、标题）
# Output: render_markdown_file_to_wechat_html() → 内联样式公众号 HTML 文件
# Pos: wxops publish 站引擎层 · 复制自 hermes wechat-publisher
#
# 来源: /Users/dw/Desktop/claude/services/wechat-publisher/scripts/wechat_html_renderer_lib.py
# 复制日期: 2026-08-01（wxops P5 · issue #43）；仅加本头注，行为零变更，hermes 原文件未动
# 已知状态: 排版样式为固定主题（暖橙主色 #e06a2e，源自麦总玩 AI 号），模块级常量硬编码；
#   按账号视觉 tokens 参数化留待后续版本（persona.md 视觉段当前只约束配图，不驱动排版）。
# 纯函数式渲染：零凭证、零网络调用。
"""独立的公众号 HTML 渲染能力。

排版设计：麦总玩 AI · 暖橙主色系
  主色  #e06a2e  暖橙（与系列配图风格一致）
  正文  #333333  深灰（不纯黑，阅读舒适）
  背景  #faf9f7  极浅米白（避免纯白刺眼）
  H2   左竖线装饰（业界最清晰的章节区分方式）
  strong 主色强调，阅读有节奏感
"""

from __future__ import annotations

import json
import re
from html import escape, unescape
from pathlib import Path
from typing import Dict, List


# ── 全局样式变量 ────────────────────────────────────────────────────────────
PRIMARY = "#e06a2e"  # 暖橙主色

page_style = "margin:0; padding:0; background:#faf9f7;"
paragraph_style = (
    "font-size:16px; line-height:1.85; color:#333333; margin:0.7em 0; "
    "letter-spacing:0.05em; text-align:left; "
    "word-break:break-word; overflow-wrap:anywhere;"
)
container_style = (
    "max-width:680px; margin:0 auto; padding:20px 4px 24px; "
    "box-sizing:border-box; word-break:break-word; overflow-wrap:anywhere;"
)
blockquote_style = (
    f"border-left:4px solid {PRIMARY}; padding:14px 14px; margin:24px 0; "
    "background:rgba(224,106,46,0.06); color:#555555; "
    "font-size:15px; line-height:1.85; border-radius:0 8px 8px 0;"
)
cta_block_style = (
    f"border-left:4px solid {PRIMARY}; padding:16px 14px; margin:28px 0; "
    "background:linear-gradient(135deg,rgba(224,106,46,0.10),rgba(255,246,238,0.96)); "
    "border-radius:10px; box-shadow:0 4px 18px rgba(224,106,46,0.08);"
)
cta_primary_style = (
    "font-size:15px; line-height:1.8; color:#555555; margin:0 0 8px; "
    "letter-spacing:0.04em;"
)
cta_secondary_style = (
    f"font-size:16px; line-height:1.8; color:{PRIMARY}; margin:0; "
    "font-weight:bold; font-style:italic; letter-spacing:0.04em;"
)
code_block_style = (
    "background:#f6f7f8; padding:14px 16px; border-radius:6px; "
    "border:1px solid rgba(0,0,0,0.06); "
    "font-family:'Fira Code',Menlo,Consolas,Monaco,monospace; color:#24292e; "
    "font-size:14px; line-height:1.65; margin:20px 0; "
    "overflow-x:auto; white-space:pre-wrap; word-break:break-word; "
    "overflow-wrap:anywhere; box-sizing:border-box;"
)
code_inner_style = (
    "font-family:'Fira Code',Menlo,Consolas,Monaco,monospace; "
    "white-space:pre-wrap; word-break:break-word; overflow-wrap:anywhere;"
)
inline_code_style = (
    "background:rgba(224,106,46,0.08); color:#c0392b; "
    "padding:2px 6px; border-radius:4px; font-size:90%; "
    "font-family:Menlo,Consolas,Monaco,monospace; "
    "word-break:break-word; overflow-wrap:anywhere;"
)
link_style = (
    "color:#576b95; text-decoration:underline; "
    "word-break:break-word; overflow-wrap:anywhere;"
)
table_style = (
    "width:100%; border-collapse:collapse; table-layout:fixed; margin:24px 0; "
    "font-size:14px; color:#333333; word-break:break-word; overflow-wrap:anywhere;"
)
table_header_style = f"background:{PRIMARY}; color:#fff; font-weight:bold;"
table_cell_style = (
    "padding:10px 14px; border:1px solid #e0dbd3; vertical-align:top; "
    "word-break:break-word; overflow-wrap:anywhere;"
)
table_even_row_style = "background:#faf9f7;"
list_style = (
    "margin:14px 0 20px; padding-left:20px; color:#333333; "
    "font-size:16px; line-height:1.85;"
)
image_style = (
    "max-width:100%; height:auto; display:block; margin:0 auto 6px; "
    "border-radius:8px; box-shadow:0 2px 12px rgba(0,0,0,0.08);"
)
hr_style = (
    "border:none; height:1px; margin:2em 0; "
    "background:linear-gradient(to right,rgba(0,0,0,0),rgba(0,0,0,0.1),rgba(0,0,0,0));"
)
heading_styles = {
    1: (
        "font-size:24px; font-weight:bold; color:#1a1a1a; "
        "text-align:center; margin:8px 0 28px; line-height:1.4; "
        "letter-spacing:0.3px;"
    ),
    2: (
        "font-size:21px; font-weight:bold; color:#1a1a1a; "
        f"margin:38px 0 16px; line-height:1.4; text-align:left; "
        f"padding-left:4px; border-left:4px solid {PRIMARY};"
    ),
    3: (
        "font-size:17px; font-weight:bold; color:#2d2d2d; "
        "margin:26px 0 10px; line-height:1.5;"
    ),
}


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def load_metadata_file(metadata_path: Path | None) -> Dict:
    """读取元数据文件。"""
    if metadata_path is None:
        return {}
    resolved = Path(metadata_path)
    if not resolved.exists():
        raise FileNotFoundError(f"缺少元数据文件: {resolved}")
    with open(resolved, "r", encoding="utf-8") as f:
        return json.load(f)


def strip_frontmatter(markdown_text: str) -> str:
    """移除 markdown frontmatter。"""
    m = re.match(r"^---\s*\n[\s\S]*?\n---\s*\n", markdown_text)
    return markdown_text[m.end():] if m else markdown_text


def extract_title(markdown_text: str, metadata: Dict) -> str:
    """从 metadata 或 markdown 中提取标题。"""
    wechat_title = str(metadata.get("wechat", {}).get("title", "")).strip()
    if wechat_title:
        return wechat_title
    m = re.search(r"^\s*#\s+(.+?)\s*$", markdown_text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return str(metadata.get("title", "")).strip() or "未命名"


def split_markdown_blocks(markdown_text: str) -> List[str]:
    """按空行拆分 markdown。"""
    normalized = markdown_text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    blocks: List[str] = []
    current: List[str] = []
    in_fenced_code = False

    for raw_line in normalized.split("\n"):
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            current.append(raw_line)
            in_fenced_code = not in_fenced_code
            if not in_fenced_code:
                blocks.append("\n".join(current).strip())
                current = []
            continue

        if in_fenced_code:
            current.append(raw_line)
            continue

        if not stripped:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue

        current.append(raw_line)

    if current:
        blocks.append("\n".join(current).strip())
    return blocks


def render_inline_markdown(text: str) -> str:
    """渲染行内 markdown（链接 / strong / em / code）。"""
    rendered = escape(text, quote=True)

    # 行内代码 `code` — 先处理，避免被 ** 误匹配
    rendered = re.sub(
        r"`([^`]+)`",
        lambda m: f'<code style="{inline_code_style}">{m.group(1)}</code>',
        rendered,
    )
    # 链接
    rendered = re.sub(
        r"\[([^\]]+)\]\(((?:[^()]|\([^)]*\))+)\)",
        lambda m: (
            f'<a href="{escape(unescape(m.group(2).strip()), quote=True)}" '
            f'style="{link_style}">'
            f'{escape(unescape(m.group(1).strip()))}</a>'
        ),
        rendered,
    )
    # 粗体（主色强调）
    rendered = re.sub(
        r"\*\*(.+?)\*\*",
        lambda m: f'<strong style="color:{PRIMARY}; font-weight:bold;">{m.group(1)}</strong>',
        rendered,
    )
    # 斜体
    rendered = re.sub(
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
        r"<em>\1</em>",
        rendered,
    )
    return rendered


# ── 块级渲染 ─────────────────────────────────────────────────────────────────

def render_image_block(block_text: str) -> str | None:
    """渲染图片块。"""
    m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)$", block_text.strip())
    if not m:
        return None
    alt = escape(m.group(1).strip(), quote=True)
    src = escape(m.group(2).strip(), quote=True)
    return (
        '<p style="text-align:center; margin:24px 0 8px;">'
        f'<img src="{src}" alt="{alt}" style="{image_style}" />'
        "</p>"
    )


def render_hr_block(block_text: str) -> str | None:
    """渲染分割线 --- / *** / ___。"""
    if re.match(r"^(\-{3,}|\*{3,}|_{3,})$", block_text.strip()):
        return f'<hr style="{hr_style}" />'
    return None


def render_heading_block(block_text: str) -> str | None:
    """渲染标题块。"""
    m = re.match(r"^(#{1,6})\s+(.+)$", block_text.strip())
    if not m:
        return None
    level = min(len(m.group(1)), 3)
    tag = f"h{level}"
    text = render_inline_markdown(m.group(2).strip())
    return f'<{tag} style="{heading_styles[level]}">{text}</{tag}>'


def render_blockquote_block(block_text: str) -> str | None:
    """渲染引用块。"""
    lines = [l.strip() for l in block_text.splitlines() if l.strip()]
    if not lines or any(not l.startswith(">") for l in lines):
        return None
    quote_lines = [render_inline_markdown(l.lstrip(">").strip()) for l in lines]
    return f'<blockquote style="{blockquote_style}">{"<br>".join(quote_lines)}</blockquote>'


def render_article_cta_block(block_text: str) -> str | None:
    """渲染文末关注 + 项目咨询轻转化块。"""
    lines = []
    for raw_line in block_text.splitlines():
        line = raw_line.strip()
        if line.startswith(">"):
            line = line.lstrip(">").strip()
        if line:
            lines.append(line)

    if not lines:
        return None

    plain_text = re.sub(r"\s+", "", "".join(lines))
    has_follow = "关注我" in plain_text and "AI资讯" in plain_text and "AI知识" in plain_text
    has_project_cta = "大小项目开发" in plain_text and "方案咨询" in plain_text and "交流" in plain_text
    if not has_follow or not has_project_cta:
        return None

    primary_line = lines[0]
    secondary_lines = lines[1:] if len(lines) > 1 else []

    secondary_html = ""
    for line in secondary_lines:
        secondary_html += f'<p style="{cta_secondary_style}">{render_inline_markdown(line)}</p>'

    return (
        f'<section data-role="article-cta" style="{cta_block_style}">'
        f'<p style="{cta_primary_style}">{render_inline_markdown(primary_line)}</p>'
        f'{secondary_html}'
        "</section>"
    )


def render_code_block(block_text: str) -> str | None:
    """渲染代码块（``` 或缩进式）。"""
    fenced = re.match(r"^```(\w*)\s*\n([\s\S]*?)\n```$", block_text.strip())
    if fenced:
        code = escape(fenced.group(2).strip("\n"), quote=True)
        return (
            f'<pre data-role="code-block" style="{code_block_style}">'
            f'<code style="{code_inner_style}">{code}</code></pre>'
        )

    lines = block_text.strip().split("\n")
    if all(l.startswith("    ") or l.startswith("\t") for l in lines if l):
        stripped = [l[4:] if l.startswith("    ") else l[1:] for l in lines]
        code = escape("\n".join(stripped), quote=True)
        return (
            f'<pre data-role="code-block" style="{code_block_style}">'
            f'<code style="{code_inner_style}">{code}</code></pre>'
        )

    return None


def render_table_block(block_text: str) -> str | None:
    """渲染 Markdown 表格。"""
    lines = block_text.strip().split("\n")
    if len(lines) < 3 or not all("|" in l for l in lines):
        return None

    headers = [h.strip() for h in lines[0].strip().split("|") if h.strip()]
    if not headers:
        return None
    if not any(re.match(r"^\|?[\s\-:]+\|", l) for l in lines[1:3] if l.strip()):
        return None

    header_html = "".join(
        f'<th style="{table_cell_style} {table_header_style}">{escape(h)}</th>'
        for h in headers
    )
    rows = [f"<tr>{header_html}</tr>"]

    for idx, line in enumerate(lines[2:], start=2):
        if not line.strip() or re.match(r"^\|?[\s\-:]+\|", line):
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if cells:
            row_style = table_even_row_style if idx % 2 == 0 else ""
            row_html = "".join(
                f'<td style="{table_cell_style} {row_style}">{escape(c)}</td>'
                for c in cells
            )
            rows.append(f"<tr>{row_html}</tr>")

    return f'<table style="{table_style}">{"".join(rows)}</table>'


def render_list_block(block_text: str) -> str | None:
    """渲染列表块。"""
    lines = [l.strip() for l in block_text.splitlines() if l.strip()]
    if not lines:
        return None

    unordered = all(re.match(r"^[-*]\s+.+$", l) for l in lines)
    ordered = all(re.match(r"^\d+\.\s+.+$", l) for l in lines)
    if not unordered and not ordered:
        return None

    tag = "ol" if ordered else "ul"
    items = []
    for line in lines:
        item_text = re.sub(r"^[-*]\s+|^\d+\.\s+", "", line).strip()
        items.append(f"<li>{render_inline_markdown(item_text)}</li>")
    return f'<{tag} style="{list_style}">{"".join(items)}</{tag}>'


def render_paragraph_block(block_text: str) -> str:
    """渲染普通段落。"""
    lines = [render_inline_markdown(l.strip()) for l in block_text.splitlines() if l.strip()]
    return f'<p style="{paragraph_style}">{"<br>".join(lines)}</p>'


# ── 主渲染函数 ────────────────────────────────────────────────────────────────

def render_markdown_to_wechat_html(markdown_text: str, title: str) -> str:
    """将 markdown 文本渲染为公众号 HTML。"""
    body_blocks: List[str] = []
    normalized = strip_frontmatter(markdown_text)

    blocks_iter = iter(split_markdown_blocks(normalized))
    # 公众号标题字段已单独设置，跳过正文首个 H1 避免重复渲染
    first = next(blocks_iter, None)
    if first is not None and not re.match(r"^#\s+", first.strip()):
        blocks_iter = (b for b in [first, *blocks_iter])  # 不是 H1 则保留

    for block_text in blocks_iter:
        rendered = (
            render_image_block(block_text)
            or render_hr_block(block_text)
            or render_heading_block(block_text)
            or render_article_cta_block(block_text)
            or render_blockquote_block(block_text)
            or render_code_block(block_text)
            or render_table_block(block_text)
            or render_list_block(block_text)
            or render_paragraph_block(block_text)
        )
        body_blocks.append(rendered)

    body_html = "\n\n".join(body_blocks)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '    <meta charset="UTF-8">\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"    <title>{escape(title)}</title>\n"
        "</head>\n"
        f'<body style="{page_style}">\n\n'
        f'<div style="{container_style}">\n\n{body_html}\n\n</div>\n'
        "</body>\n"
        "</html>\n"
    )


def render_markdown_file_to_wechat_html(
    markdown_path: Path,
    output_html_path: Path | None = None,
    metadata_path: Path | None = None,
    title: str = "",
) -> Path:
    """将任意 markdown 文件渲染为公众号 HTML。"""
    resolved = Path(markdown_path)
    if not resolved.exists():
        raise FileNotFoundError(f"缺少 markdown 文件: {resolved}")

    metadata = load_metadata_file(metadata_path)
    markdown_text = resolved.read_text(encoding="utf-8")
    final_title = title.strip() or extract_title(markdown_text, metadata)
    html_content = render_markdown_to_wechat_html(markdown_text, final_title)

    out_path = (
        Path(output_html_path)
        if output_html_path is not None
        else resolved.with_suffix(".html")
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_content, encoding="utf-8")
    return out_path.resolve()
