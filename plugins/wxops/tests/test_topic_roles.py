# GEB-L3
# Input: maizong/health 锚点题材统计 fixture + niche 包；assign_topic_roles / build_analysis_sections / build_action_items
# Output: 角色归属、零样本守卫、无 AI 字样、recommendations 可选与 ai-tools 等值断言
# Pos: plugins/wxops/tests/test_topic_roles.py
"""issue #60：题材角色驱动结论层 + 赛道叙事解耦。"""
from __future__ import annotations

import json
from pathlib import Path

from analyze.niche_loader import load_niche, reset_active, set_active
from analyze.topic_roles import MIN_TOPIC_SAMPLES, assign_topic_roles
from build_wechat_ops_report import build_action_items, build_analysis_sections

PLUGIN_ROOT = Path(__file__).resolve().parents[1]

# 迁移前硬编码 recommendations（零行为变更锚点）
LEGACY_AI_TOOLS_RECOMMENDATIONS = {
    "topic_ratio": [
        {"label": "AI 编程/Agent 工作流", "ratio": 0.40, "role": "IP 主线"},
        {"label": "风险/账号/额度焦虑", "ratio": 0.25, "role": "推荐流入口"},
        {"label": "价格/额度/羊毛情报", "ratio": 0.20, "role": "转化与收藏入口"},
        {"label": "模型发布/能力解读", "ratio": 0.10, "role": "热点解释与判断"},
        {"label": "泛 AI 热点/效率工具", "ratio": 0.05, "role": "拓圈与轻量内容"},
    ],
    "publish_windows": [
        {"window": "09:00-10:30", "best_for": "刚需工具、价格/额度更新"},
        {"window": "12:00-12:45", "best_for": "强风险、强利益短通知"},
        {"window": "15:00-17:30", "best_for": "模型发布、官方更新、二次解读"},
        {"window": "22:00-22:45", "best_for": "深度判断、争议复盘、工作流文章"},
    ],
    "headline_rules": [
        "风险文标题先写直接损失，再写对象：谁今天会被卡、会少什么、要检查什么。",
        "羊毛文标题必须写清免费/额度/价格和适用人群，不写泛泛的“福利来了”。",
        "工作流文标题不要讲项目意义，先讲用户少翻多少文件、少花多少 token、少踩什么坑。",
        "模型发布文必须绑定可用性：谁能用、哪里免费、能不能替代当前方案。",
    ],
}

MAIZONG = [
    {
        "key": "风险/账号/额度焦虑",
        "count": 22,
        "avg": 2402.64,
        "median": 178.0,
        "p75": 1727.25,
        "max": 18403,
        "total_reads": 52858,
        "share_rate_avg": 0.0461,
        "comment_rate_avg": 0.0059,
    },
    {
        "key": "价格/额度/羊毛情报",
        "count": 29,
        "avg": 1064.03,
        "median": 68.0,
        "p75": 160.0,
        "max": 22603,
        "total_reads": 30857,
        "share_rate_avg": 0.0522,
        "comment_rate_avg": 0.002,
    },
    {
        "key": "模型发布/能力解读",
        "count": 16,
        "avg": 1007.81,
        "median": 165.0,
        "p75": 688.75,
        "max": 6691,
        "total_reads": 16125,
        "share_rate_avg": 0.0453,
        "comment_rate_avg": 0.0008,
    },
    {
        "key": "AI 编程/Agent 工作流",
        "count": 59,
        "avg": 291.59,
        "median": 71.0,
        "p75": 153.0,
        "max": 4980,
        "total_reads": 17204,
        "share_rate_avg": 0.0589,
        "comment_rate_avg": 0.0034,
    },
    {
        "key": "产品/副业/商业化",
        "count": 4,
        "avg": 85.75,
        "median": 40.0,
        "p75": 103.25,
        "max": 254,
        "total_reads": 343,
        "share_rate_avg": 0.0476,
        "comment_rate_avg": 0.0057,
    },
    {
        "key": "泛 AI 热点/效率工具",
        "count": 12,
        "avg": 186.0,
        "median": 12.0,
        "p75": 28.5,
        "max": 1064,
        "total_reads": 2232,
        "share_rate_avg": 0.0472,
        "comment_rate_avg": 0.0006,
    },
]
MAIZONG_ACCOUNT_SHARE = 0.0463

# share_rate_avg 为 #59 ratio-of-means 真值（非 mean-of-ratios 旧报告抄值）
HEALTH = [
    {
        "key": "节气饮食",
        "count": 7,
        "avg": 21.14,
        "median": 2.0,
        "p75": 11.5,
        "max": 119,
        "total_reads": 148,
        "share_rate_avg": 0.0405,
        "comment_rate_avg": 0.0,
    },
    {
        "key": "运动与作息",
        "count": 6,
        "avg": 30.33,
        "median": 12.0,
        "p75": 26.75,
        "max": 125,
        "total_reads": 182,
        "share_rate_avg": 0.0165,
        "comment_rate_avg": 0.0,
    },
    {
        "key": "清淡饮食与体重管理",
        "count": 5,
        "avg": 4671.2,
        "median": 4.0,
        "p75": 82.0,
        "max": 23265,
        "total_reads": 23356,
        "share_rate_avg": 0.0072,
        "comment_rate_avg": 0.0001,
    },
    {
        "key": "食品安全与成分核查",
        "count": 20,
        "avg": 8.35,
        "median": 1.0,
        "p75": 2.25,
        "max": 103,
        "total_reads": 167,
        "share_rate_avg": 0.0299,
        "comment_rate_avg": 0.0,
    },
    {
        "key": "常见误区辟谣",
        "count": 4,
        "avg": 8.25,
        "median": 5.0,
        "p75": 9.75,
        "max": 21,
        "total_reads": 33,
        "share_rate_avg": 0.0303,
        "comment_rate_avg": 0.0,
    },
    {
        "key": "生活习惯改善",
        "count": 14,
        "avg": 46.71,
        "median": 9.0,
        "p75": 102.75,
        "max": 109,
        "total_reads": 654,
        "share_rate_avg": 0.0183,
        "comment_rate_avg": 0.0,
    },
]
HEALTH_ACCOUNT_SHARE = 0.0079

AI_FORBIDDEN = ("AI 编程", "Agent 工作流", "羊毛", "额度焦虑", "模型发布")


def _roles_map(by_type: list[dict], account_share: float) -> dict[str, str]:
    return {r["role"]: r["key"] for r in assign_topic_roles(by_type, account_share)}


def _minimal_dataset(
    by_content_type: list[dict],
    *,
    stable: list[dict] | None = None,
    by_hour: list[dict] | None = None,
    stable_count: int | None = None,
    median_reads: float = 0,
    max_reads: float = 0,
    persona_key: str = "样本人群",
    pain_key: str = "样本痛点",
) -> dict:
    """构造 build_analysis_sections / build_action_items 所需最小 dataset。"""
    if stable is None:
        stable = []
    n = stable_count if stable_count is not None else len(stable)
    conf = {
        "level": "medium",
        "score": 0.6,
        "sample_size": n,
        "completeness": 1.0,
        "note": "test",
    }
    return {
        "analysis": {
            "by_content_type": by_content_type,
            "by_hour": by_hour or [],
            "by_pain_point": [{"key": pain_key, "count": max(1, n), "median": 1, "p75": 1, "avg": 1}],
            "by_persona": [{"key": persona_key, "count": max(1, n), "median": 1, "p75": 1, "avg": 1}],
            "rankings": {"top_reads": [], "top_shares": []},
            "overall": {
                "median": median_reads,
                "p75": 0,
                "avg": 0,
                "max": max_reads,
                "count": n,
            },
            "time_heatmap": [],
        },
        "articles": {"stable": stable},
        "data_quality": {
            "stable_article_count": n,
            "period_non_deleted_count": n,
            "metric_pending_count": 0,
        },
        "title_analysis": {
            "by_primary_pattern": [{"key": "教程清单型", "count": 1, "median": 1, "p75": 1, "avg": 1}],
            "by_title_length": [],
            "by_feature": [],
        },
        "length_analysis": {
            "by_length_bucket": [],
            "matched_count": 0,
            "missing_count": n,
            "avg_length": 0,
        },
        "confidence_model": {
            "overall": conf,
            "article_length_completeness": 0.0,
        },
        "modules": {"audience": {"fans_portrait_available": False}},
    }


def _stable_for_share(account_share: float, n: int = 100) -> list[dict]:
    """构造 ratio-of-means 精确等于 account_share 的稳定样本（reads 足够大）。"""
    reads = 10000
    shares = int(round(account_share * reads))
    return [{"reads": reads, "shares": shares} for _ in range(n)]


def _content_engine_section(dataset: dict) -> dict:
    sections = build_analysis_sections(dataset)
    return next(s for s in sections if s["id"] == "content-engine")


def test_maizong_role_assignment():
    roles = _roles_map(MAIZONG, MAIZONG_ACCOUNT_SHARE)
    assert roles["workhorse"] == "AI 编程/Agent 工作流"
    assert roles["volatile"] == "价格/额度/羊毛情报"
    assert roles["reach_entry"] == "风险/账号/额度焦虑"
    assert roles["loyalty_base"] == "产品/副业/商业化"
    assert set(roles) == {"workhorse", "volatile", "reach_entry", "loyalty_base"}


def test_health_role_assignment_reach_entry_absent():
    """冷启动：reach_entry 缺席是正确行为，不是硬凑。"""
    roles = _roles_map(HEALTH, HEALTH_ACCOUNT_SHARE)
    assert roles["workhorse"] == "食品安全与成分核查"
    assert roles["volatile"] == "清淡饮食与体重管理"
    assert "reach_entry" not in roles
    assert roles["loyalty_base"] == "节气饮食"
    assert set(roles) == {"workhorse", "volatile", "loyalty_base"}


def test_zero_sample_guard_roles_and_content_engine():
    tiny = [
        {
            "key": "A",
            "count": 2,
            "avg": 10,
            "median": 5,
            "p75": 8,
            "max": 20,
            "share_rate_avg": 0.01,
        },
        {
            "key": "B",
            "count": 1,
            "avg": 3,
            "median": 3,
            "p75": 3,
            "max": 3,
            "share_rate_avg": 0.02,
        },
    ]
    assert assign_topic_roles(tiny, 0.01) == []
    ds = _minimal_dataset(tiny, stable=[], stable_count=3, median_reads=1)
    ce = _content_engine_section(ds)
    assert "题材角色暂不可判断" in ce["conclusion"]
    assert str(MIN_TOPIC_SAMPLES)  # 阈值常量仍存在，供 action_items 守卫使用
    items = build_action_items(ds)
    assert len(items) == 5
    assert str(MIN_TOPIC_SAMPLES) in items[0]["why"]
    assert items[0]["priority"] == "P0"
    assert "稳定样本" in items[0]["title"]


def test_health_output_has_no_ai_literals():
    """防回归闸门：health 角色结论/建议不得泄漏 AI 赛道硬编码文案。"""
    stable = [{"reads": 10000, "shares": 79} for _ in range(10)]
    ds = _minimal_dataset(
        HEALTH,
        stable=stable,
        stable_count=56,
        median_reads=3.0,
        max_reads=23265,
        by_hour=[{"key": 10, "count": 5, "median": 12, "p75": 20, "avg": 15}],
        persona_key="50-70岁养生读者",
        pain_key="节气该吃什么不知道",
    )
    text = json.dumps(
        {
            "analysis_sections": build_analysis_sections(ds),
            "action_items": build_action_items(ds),
        },
        ensure_ascii=False,
    )
    for needle in AI_FORBIDDEN:
        assert needle not in text, f"forbidden AI literal leaked: {needle!r}"


def test_health_content_engine_uses_topic_roles():
    """content-engine 章结论应由角色驱动，出现 health 题材名而非 AI 硬编码。"""
    stable = [{"reads": 10000, "shares": 79} for _ in range(10)]
    ds = _minimal_dataset(
        HEALTH,
        stable=stable,
        stable_count=56,
        median_reads=3.0,
        max_reads=23265,
        persona_key="50-70岁养生读者",
        pain_key="节气该吃什么不知道",
    )
    ce = _content_engine_section(ds)
    # workhorse 在场、reach 缺席 → 产能集中或 loyalty 句
    assert "食品安全与成分核查" in ce["analysis"] or "食品安全与成分核查" in ce["conclusion"] or "食品安全与成分核查" in ce["action"]
    assert "节气饮食" in ce["conclusion"]  # loyalty_base（ROM 分享率题材内最高）
    assert "风险羊毛" not in ce["conclusion"]
    assert "工作流" not in ce["conclusion"]
    assert "265" not in ce["analysis"]
    assert "415" not in ce["analysis"]


def test_generic_recommendations_missing_is_none():
    reset_active()
    try:
        spec = load_niche("_generic")
        assert spec.recommendations is None
    finally:
        reset_active()


def test_ai_tools_recommendations_match_legacy():
    reset_active()
    try:
        spec = load_niche("ai-tools")
        assert spec.recommendations is not None
        rec = {
            "topic_ratio": list(spec.recommendations.topic_ratio),
            "publish_windows": list(spec.recommendations.publish_windows),
            "headline_rules": list(spec.recommendations.headline_rules),
        }
        assert rec == LEGACY_AI_TOOLS_RECOMMENDATIONS
    finally:
        reset_active()


def test_empty_roles_action_items_filled_to_five():
    """全题材 count < MIN_TOPIC_SAMPLES → 零角色；P0 守卫 + filler 补齐恒 5 条。"""
    tiny = [
        {
            "key": "节气饮食",
            "count": 2,
            "avg": 10,
            "median": 5,
            "p75": 8,
            "max": 20,
            "share_rate_avg": 0.01,
        },
        {
            "key": "运动与作息",
            "count": 1,
            "avg": 3,
            "median": 3,
            "p75": 3,
            "max": 3,
            "share_rate_avg": 0.02,
        },
        {
            "key": "食品安全与成分核查",
            "count": 2,
            "avg": 4,
            "median": 2,
            "p75": 3,
            "max": 8,
            "share_rate_avg": 0.015,
        },
    ]
    assert assign_topic_roles(tiny, 0.01) == []
    ds = _minimal_dataset(tiny, stable=[], stable_count=5, median_reads=0)
    items = build_action_items(ds)
    assert len(items) == 5
    assert items[0]["priority"] == "P0"
    assert "稳定样本" in items[0]["title"]
    assert "可分析量级" in items[0]["title"]
    blob = json.dumps(items, ensure_ascii=False)
    for topic in ("节气饮食", "运动与作息", "食品安全与成分核查"):
        assert topic not in blob, f"zero-role filler must not name topic {topic!r}"
