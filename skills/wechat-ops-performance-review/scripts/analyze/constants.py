from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo


CN_TZ = ZoneInfo("Asia/Shanghai")

CONTENT_TYPES = [
    "风险/账号/额度焦虑",
    "价格/额度/羊毛情报",
    "模型发布/能力解读",
    "AI 编程/Agent 工作流",
    "产品/副业/商业化",
    "泛 AI 热点/效率工具",
]

PAIN_POINTS = [
    "账号安全与权限焦虑",
    "成本、额度与订阅压力",
    "工具选择与效率落地",
    "模型能力判断",
    "副业产品化与变现",
    "热点信息差与谈资",
]

PERSONAS = [
    "Claude/Codex/GPT 重度用户",
    "AI 编程/Agent 实践者",
    "省钱党与套餐比较用户",
    "产品经理/独立开发者",
    "非技术效率工具用户",
    "AI 新闻观察者",
]

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

TITLE_PATTERN_KEYS = [
    "风险损失型",
    "价格福利型",
    "模型发布型",
    "对比替代型",
    "教程清单型",
    "疑问反常识型",
    "工作流案例型",
    "普通资讯型",
]

TITLE_LENGTH_BUCKETS = ["16字内", "17-24字", "25-34字", "35字以上"]
ARTICLE_LENGTH_BUCKETS = ["1200字内", "1200-2200字", "2200-3500字", "3500字以上", "未匹配正文"]
