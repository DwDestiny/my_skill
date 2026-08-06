# GEB-L3
# Input: TYPE_PLAYBOOKS 模板 + 构造 metric_availability + fixtures dataset
# Output: issue #69 m9 metric-aware playbook 渲染契约（registry 防复发、槽位一致、degraded 铁律、降级/全量/去重/旧数据集/模板不污染/报告口径校正）
# Pos: plugins/wxops/tests/test_m9_metric_aware.py
"""Issue #69: m9 TYPE_PLAYBOOKS 按 metric_availability 渲染，不推荐拿不到数的指标。"""
from __future__ import annotations

import re
from pathlib import Path

from analyze.m9_account_type import (
    TYPE_PLAYBOOKS,
    _render_playbook,
    build_account_type,
)
from analyze.metric_registry import METRIC_DIMENSIONS
from build_wechat_ops_report import build_dataset, render_report

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

_REGISTRY_KEYS = {d["key"] for d in METRIC_DIMENSIONS}

# degraded 文案禁止引用的不可得词（core 以外 / 采集器未覆盖）
_FORBIDDEN_IN_DEGRADED = (
    "在看",
    "收藏",
    "完读",
    "复访",
    "钩子点击",
    "阅读来源",
    "粉丝净增",
    "城市分布",
    "打开率",
)


def _all_available() -> dict[str, dict]:
    return {
        d["key"]: {"status": "available", "label": d["label"]}
        for d in METRIC_DIMENSIONS
    }


def _mk_article(
    title: str,
    digest: str = "",
    *,
    reads: int = 500,
    share_rate: float = 0.03,
    comment_rate: float = 0.012,
    like_rate: float = 0.06,
    length: int = 1800,
) -> dict:
    shares = round(reads * share_rate)
    comments = round(reads * comment_rate)
    likes = round(reads * like_rate)
    return {
        "title": title,
        "digest": digest,
        "reads": reads,
        "shares": shares,
        "comments": comments,
        "likes": likes,
        "old_likes": 0,
        "moment_likes": 0,
        "share_rate": share_rate,
        "comment_rate": comment_rate,
        "like_rate": like_rate,
        "article_length_chars": length,
        "content_type": "泛内容",
        "published_at": "2026-06-01T10:00:00+08:00",
    }


def _ip_dataset(*, availability: dict | None = None) -> dict:
    arts = [
        _mk_article(
            f"我踩坑一年后的第 {i} 条判断",
            "我的亲历复盘,聊聊我自己的取舍和立场。",
        )
        for i in range(16)
    ]
    ds: dict = {
        "articles": {"stable": arts, "all_period": arts},
        "account_profile": {"publish_frequency": 2.0},
        "account": {"cumulate_user": 3000},
        "modules": {"audience": {"city": []}},
    }
    if availability is not None:
        ds["metric_availability"] = availability
    return ds


def _iter_declared_dicts(pb: dict):
    """遍历 playbook 里所有带声明的 dict 项（north_star / diagnosis_focus / slots）。"""
    for field in ("north_star", "diagnosis_focus"):
        for item in pb.get(field) or []:
            if isinstance(item, dict):
                yield field, item
    for slot_name, slot_def in (pb.get("reading_guide_slots") or {}).items():
        if isinstance(slot_def, dict):
            yield f"reading_guide_slots.{slot_name}", slot_def


def test_all_declared_metrics_exist_in_registry():
    """防复发：声明的 metrics key 必须在 METRIC_DIMENSIONS 内，且 metrics/not_collected 至少有一。"""
    for type_key, pb in TYPE_PLAYBOOKS.items():
        for loc, item in _iter_declared_dicts(pb):
            metrics = item.get("metrics") or []
            has_nc = bool(item.get("not_collected"))
            assert metrics or has_nc, (
                f"{type_key}.{loc} 必须至少有 metrics 或 not_collected 之一"
            )
            for key in metrics:
                assert key in _REGISTRY_KEYS, (
                    f"{type_key}.{loc} 引用了 registry 中不存在的维度 key={key!r}"
                )


def test_all_slots_declared_in_template():
    """reading_guide 里的 {槽位} 与 reading_guide_slots 键双向一致。"""
    for type_key, pb in TYPE_PLAYBOOKS.items():
        guide = pb.get("reading_guide") or ""
        slots = pb.get("reading_guide_slots") or {}
        used = set(re.findall(r"\{([^}]+)\}", guide))
        declared = set(slots.keys())
        assert used == declared, (
            f"{type_key}: 模板槽位 {used} 与 slots 键 {declared} 不一致"
        )


def test_degraded_only_references_core_metrics():
    """所有 degraded 文案不得含不可得词。"""
    for type_key, pb in TYPE_PLAYBOOKS.items():
        for field in ("north_star", "diagnosis_focus"):
            for i, item in enumerate(pb.get(field) or []):
                if not isinstance(item, dict):
                    continue
                degraded = item.get("degraded")
                if degraded is None:
                    continue
                for word in _FORBIDDEN_IN_DEGRADED:
                    assert word not in degraded, (
                        f"{type_key}.{field}[{i}] degraded 含禁词 {word!r}: {degraded!r}"
                    )
        for slot_name, slot_def in (pb.get("reading_guide_slots") or {}).items():
            degraded = slot_def.get("degraded")
            assert degraded is not None, (
                f"{type_key}.reading_guide_slots.{slot_name} degraded 不许为 None"
            )
            for word in _FORBIDDEN_IN_DEGRADED:
                assert word not in degraded, (
                    f"{type_key}.reading_guide_slots.{slot_name} degraded 含禁词 "
                    f"{word!r}: {degraded!r}"
                )


def test_personal_ip_degrades_when_zaikan_missing():
    """zaikan/fans_portrait 不可得时 personal_ip 口径降级。"""
    avail = _all_available()
    avail["zaikan"] = {
        "status": "platform_not_provided",
        "label": "在看数",
    }
    avail["fans_portrait"] = {
        "status": "fetch_missing",
        "label": "粉丝画像",
    }
    # comments 保持 available
    rendered, _lenses = _render_playbook(TYPE_PLAYBOOKS["personal_ip"], avail)
    guide = rendered["reading_guide"]
    ns = rendered["north_star"]
    assert "在看" not in guide
    assert "分享率与评论数" in guide
    assert "粉丝忠诚与复访" not in ns
    assert "分享率(认同强度)" in ns


def test_personal_ip_full_when_all_available():
    """十维全 available 时 zaikan 类依赖回满；not_collected 类仍撤下——两条正交降级通道。"""
    rendered, lenses = _render_playbook(
        TYPE_PLAYBOOKS["personal_ip"], _all_available()
    )
    guide = rendered["reading_guide"]
    ns = rendered["north_star"]
    # zaikan 类：快照全 available 时回到完整主口径
    assert "在看率、评论质量、粉丝净增" in guide
    assert "在看率与分享率(认同强度)" in ns
    # not_collected 类：采集器未覆盖，与快照可得性无关，永远撤下
    assert "粉丝忠诚与复访" not in ns
    assert lenses == [
        {
            "label": "复访率",
            "reason": "collector_not_implemented",
            "action": "",
        }
    ]


def test_unavailable_lenses_dedup_and_reason():
    """同一维度被多条引用时 label 去重；reason 分三类。"""
    avail = _all_available()
    avail["zaikan"] = {
        "status": "platform_not_provided",
        "label": "在看数",
    }
    avail["fans_portrait"] = {
        "status": "fetch_missing",
        "label": "粉丝画像",
    }
    _rendered, lenses = _render_playbook(TYPE_PLAYBOOKS["personal_ip"], avail)
    labels = [x["label"] for x in lenses]
    assert labels.count("在看数") == 1
    by_label = {x["label"]: x for x in lenses}
    assert by_label["在看数"]["reason"] == "platform_not_provided"
    assert by_label["粉丝画像"]["reason"] == "fetch_missing"
    assert by_label["复访率"]["reason"] == "collector_not_implemented"


def test_missing_availability_behaves_as_all_available():
    """缺 availability 不等于采集失败：旧数据集与全 available 输出完全一致，且 lenses 只许 collector_not_implemented。"""
    ds_missing = _ip_dataset()
    ds_full = _ip_dataset(availability=_all_available())
    r1 = build_account_type(ds_missing)
    r2 = build_account_type(ds_full)
    # 无 metric_availability 与十维全 available 输出完全一致（含 playbook 三字段与 unavailable_lenses）
    assert r1 == r2
    # 修正 2 门禁：旧数据集不能被诬告成采集失败
    for lens in r1["unavailable_lenses"]:
        assert lens["reason"] == "collector_not_implemented"
        assert lens["reason"] not in ("fetch_missing", "platform_not_provided")
    for lens in r2["unavailable_lenses"]:
        assert lens["reason"] == "collector_not_implemented"
        assert lens["reason"] not in ("fetch_missing", "platform_not_provided")


def test_template_not_mutated():
    """不同 availability 连续调用不得污染 TYPE_PLAYBOOKS 模板。"""
    empty_avail = {
        d["key"]: {"status": "fetch_missing", "label": d["label"]}
        for d in METRIC_DIMENSIONS
    }
    # 额外把 zaikan 标成 platform_not_provided，确保走降级
    empty_avail["zaikan"] = {
        "status": "platform_not_provided",
        "label": "在看数",
    }
    r1 = build_account_type(_ip_dataset(availability=empty_avail))
    r2 = build_account_type(_ip_dataset(availability=_all_available()))
    # 第二次必须是完整文案
    assert "在看率、评论质量、粉丝净增" in r2["playbook"]["reading_guide"]
    assert "在看率与分享率(认同强度)" in r2["playbook"]["north_star"]
    # 第一次应是降级文案，且第二次不被带偏
    assert "在看" not in r1["playbook"]["reading_guide"]
    assert r1["playbook"]["reading_guide"] != r2["playbook"]["reading_guide"]


def test_report_renders_correction_line():
    """render_report 在 unavailable_lenses 非空时输出口径校正，空时不出现。"""
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    assert dataset.get("account_type", {}).get("primary")

    dataset["account_type"]["unavailable_lenses"] = [
        {
            "label": "在看数",
            "reason": "platform_not_provided",
            "action": "",
        },
        {
            "label": "粉丝画像",
            "reason": "fetch_missing",
            "action": "跑 wxops accounts check 确认登录态后重新 analyze",
        },
    ]
    md = render_report(dataset, "datasets/wechat-ops-report-test.json")
    assert "口径校正：" in md
    assert "微信后台不提供" in md
    assert "上面的口径已按可得数据改写。" in md

    dataset["account_type"]["unavailable_lenses"] = []
    md_empty = render_report(dataset, "datasets/wechat-ops-report-test.json")
    assert "口径校正" not in md_empty
