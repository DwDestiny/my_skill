"""m9_account_type 账号类型识别与路由引擎测试。

覆盖:各类型合成场景识别、置信不足回退通用链路、playbook 完整性、
契约只增不删(report.json 向后兼容)、渲染红线(不出现"置信度"字样)。
"""
from __future__ import annotations

import json
from pathlib import Path

from analyze.m9_account_type import (
    ACCOUNT_TYPES,
    TYPE_PLAYBOOKS,
    build_account_type,
)
from build_wechat_ops_report import build_dataset

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

MODULE_KEYS = {
    "checkup",
    "viral_genes",
    "content_engine",
    "audience",
    "growth_funnel",
    "action_plan",
    "standards",
    "forward_looking",
}


def _mk_article(
    title: str,
    digest: str = "",
    *,
    reads: int = 500,
    share_rate: float = 0.01,
    comment_rate: float = 0.003,
    like_rate: float = 0.01,
    length: int = 1500,
) -> dict:
    return {
        "title": title,
        "digest": digest,
        "reads": reads,
        "share_rate": share_rate,
        "comment_rate": comment_rate,
        "like_rate": like_rate,
        "article_length_chars": length,
        "content_type": "泛内容",
        "published_at": "2026-06-01T10:00:00+08:00",
    }


def _mk_dataset(articles: list[dict], *, posts_per_week: float = 3.0, fans: int | None = 3000, city: list | None = None) -> dict:
    return {
        "articles": {"stable": articles, "all_period": articles},
        "account_profile": {"publish_frequency": posts_per_week},
        "account": {"cumulate_user": fans},
        "modules": {"audience": {"city": city or []}},
    }


def _media_dataset() -> dict:
    arts = [
        _mk_article(
            f"今日快讯:某大厂发布第 {i} 号新品",
            "最新动态速递,今天上线,本周更新汇总。",
            share_rate=0.02,
            like_rate=0.005,
            length=800,
        )
        for i in range(20)
    ]
    return _mk_dataset(arts, posts_per_week=6.0)


def _ip_dataset() -> dict:
    arts = [
        _mk_article(
            f"我踩坑一年后的第 {i} 条判断",
            "我的亲历复盘,聊聊我自己的取舍和立场。",
            share_rate=0.03,
            comment_rate=0.012,
            like_rate=0.06,
            length=1800,
        )
        for i in range(16)
    ]
    return _mk_dataset(arts, posts_per_week=2.0)


def _knowledge_dataset() -> dict:
    arts = [
        _mk_article(
            f"一文讲透第 {i} 类场景:保姆级教程与清单",
            "分步骤拆解方法,附完整攻略和操作指南。",
            share_rate=0.025,
            like_rate=0.02,
            length=3200,
        )
        for i in range(15)
    ]
    return _mk_dataset(arts, posts_per_week=1.5)


def _conversion_dataset() -> dict:
    arts = [
        _mk_article(
            f"限时福利第 {i} 波:免费领取名额有限",
            "扫码加群领取优惠,付费社群报名通道已开。",
            share_rate=0.012,
            like_rate=0.008,
            length=900,
        )
        for i in range(15)
    ]
    return _mk_dataset(arts, posts_per_week=4.0)


# ───────────────────────── 类型识别 ─────────────────────────


def test_media_news_recognized():
    result = build_account_type(_media_dataset())
    assert result["primary"]["key"] == "media_news"
    assert result["fallback_to_general"] is False
    assert result["evidence"], "识别必须给出依据"


def test_personal_ip_recognized():
    result = build_account_type(_ip_dataset())
    assert result["primary"]["key"] == "personal_ip"
    assert result["evidence"]


def test_knowledge_service_recognized():
    result = build_account_type(_knowledge_dataset())
    assert result["primary"]["key"] == "knowledge_service"


def test_conversion_sales_recognized():
    result = build_account_type(_conversion_dataset())
    assert result["primary"]["key"] == "conversion_sales"


# ───────────────────────── 回退与置信 ─────────────────────────


def test_small_sample_falls_back_to_general():
    """稳定样本 < 8 篇时不硬判类型,回退通用链路。"""
    arts = [_mk_article(f"随笔 {i}") for i in range(5)]
    result = build_account_type(_mk_dataset(arts))
    assert result["primary"]["key"] == "general"
    assert result["fallback_to_general"] is True
    assert result["confidence"] == "low"
    # 回退时依然给出通用 playbook 与路由
    assert result["playbook"]["module_weights"]
    assert result["routing"]["chain"]


def test_weak_signals_fall_back_to_general():
    """信号全弱(无明显类型特征)时回退通用,不硬凑。"""
    arts = [
        _mk_article(f"一些内容 {i}", "普通描述文字。", share_rate=0.005, like_rate=0.004, length=1400)
        for i in range(12)
    ]
    result = build_account_type(_mk_dataset(arts, posts_per_week=1.0, fans=500))
    assert result["primary"]["key"] == "general"
    assert result["fallback_to_general"] is True


def test_confidence_and_scores_shape():
    result = build_account_type(_media_dataset())
    assert result["confidence"] in {"high", "medium", "low"}
    assert set(result["scores"].keys()) == {t for t in ACCOUNT_TYPES if t != "general"}
    for v in result["scores"].values():
        assert 0.0 <= v <= 1.0


# ───────────────────────── playbook 与路由 ─────────────────────────


def test_playbooks_complete_for_all_types():
    for key in ACCOUNT_TYPES:
        pb = TYPE_PLAYBOOKS[key]
        assert pb["name"]
        assert pb["north_star"], key
        assert pb["diagnosis_focus"], key
        assert pb["reading_guide"], key
        assert pb["action_bias"], key
        assert set(pb["module_weights"].keys()) == MODULE_KEYS, key
        assert all(v in {"高", "中", "低"} for v in pb["module_weights"].values()), key


def test_routing_chain_orders_by_weight():
    result = build_account_type(_media_dataset())
    chain = result["routing"]["chain"]
    assert set(chain) == MODULE_KEYS
    weights = result["playbook"]["module_weights"]
    order = {"高": 0, "中": 1, "低": 2}
    ranks = [order[weights[m]] for m in chain]
    assert ranks == sorted(ranks), "路由链路必须按权重从高到低排列"


# ───────────────────────── 契约与红线 ─────────────────────────


def test_dataset_mounts_account_type_and_keeps_old_keys():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    # 新节点存在且结构完整
    at = dataset["account_type"]
    assert at["engine_version"]
    assert at["primary"]["key"] in ACCOUNT_TYPES
    assert isinstance(at["evidence"], list)
    assert at["playbook"]["module_weights"]
    # 旧顶层键全部保留(只增不删)
    for key in [
        "meta", "data_quality", "articles", "analysis", "benchmark",
        "viral_genes", "modules", "account", "confidence_model",
        "title_analysis", "length_analysis", "analysis_sections",
        "top_conclusion", "final_synthesis", "account_profile",
        "executive_summary", "action_plan", "forward_looking",
    ]:
        assert key in dataset, f"旧顶层键 {key} 丢失"


def test_account_type_strings_obey_redline():
    """account_type 节点所有字符串不得出现置信类禁词。"""
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    blob = json.dumps(dataset["account_type"], ensure_ascii=False)
    for word in ["置信度", "高置信", "中置信", "低置信"]:
        assert word not in blob
