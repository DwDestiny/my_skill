# GEB-L3
# Input: 无运行时入参（纯常量模块）
# Output: CN_TZ/星期标签、SECTION_UI_SLOTS 与 VISUAL_TOKENS、引擎四型标题标签、覆盖率阈值、标题/正文字数分桶
# Pos: plugins/wxops/scripts/analyze/constants.py
from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo


CN_TZ = ZoneInfo("Asia/Shanghai")

WEEKDAY_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

SECTION_UI_SLOTS: dict[str, dict[str, str]] = {
    "overview": {
        "component": "summary_metrics",
        "rail_focus": "operating_tension",
        "accent": "green",
    },
    "content-engine": {
        "component": "content_type_matrix",
        "rail_focus": "topic_ratio",
        "accent": "blue",
    },
    "title-structure": {
        "component": "title_pattern_map",
        "rail_focus": "headline_strategy",
        "accent": "coral",
    },
    "article-length": {
        "component": "length_performance_curve",
        "rail_focus": "reading_depth",
        "accent": "violet",
    },
    "audience": {
        "component": "audience_split",
        "rail_focus": "reader_motivation",
        "accent": "green",
    },
    "timing": {
        "component": "time_window_trend",
        "rail_focus": "publish_experiment",
        "accent": "amber",
    },
    "evidence": {
        "component": "evidence_table",
        "rail_focus": "sample_review",
        "accent": "blue",
    },
    "quality": {
        "component": "data_quality",
        "rail_focus": "data_integrity",
        "accent": "amber",
    },
    "final-synthesis": {
        "component": "confidence_action_board",
        "rail_focus": "final_decision",
        "accent": "green",
    },
}

VISUAL_TOKENS: dict[str, Any] = {
    "layout": "three_column_report_shell",
    "background": "#f4f6fb",
    "surface": "#ffffff",
    "surface_muted": "#f8fafc",
    "ink": "#101828",
    "muted": "#667085",
    "line": "#e7ebf0",
    "accent_green": "#2f9f7b",
    "accent_blue": "#5f98f2",
    "accent_amber": "#e7a13d",
    "accent_coral": "#f26d6d",
    "accent_violet": "#8b7cf6",
    "radius_shell": 26,
    "radius_control": 8,
    "shadow": "0 28px 70px rgba(32, 41, 63, 0.12)",
    "density": "low",
    "screen_rule": "one_claim_one_visual_one_action",
}

# 引擎固定的通用四型标题套路标签（不进 niche 包，见契约 §3.4）
TITLE_PATTERN_COMPARISON = "对比替代型"
TITLE_PATTERN_TUTORIAL = "教程清单型"
TITLE_PATTERN_QUESTION = "疑问反常识型"
TITLE_PATTERN_GENERIC = "普通资讯型"
ENGINE_TITLE_PATTERN_LABELS = frozenset(
    {
        TITLE_PATTERN_COMPARISON,
        TITLE_PATTERN_TUTORIAL,
        TITLE_PATTERN_QUESTION,
        TITLE_PATTERN_GENERIC,
    }
)

# 覆盖率闸门阈值（契约 §5；v1 不做包级覆写）
NICHE_COVERAGE_ALERT_THRESHOLD = 0.6

TITLE_LENGTH_BUCKETS = ["16字内", "17-24字", "25-34字", "35字以上"]
ARTICLE_LENGTH_BUCKETS = ["1200字内", "1200-2200字", "2200-3500字", "3500字以上", "未匹配正文"]
