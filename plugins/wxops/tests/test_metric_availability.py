# GEB-L3
# Input: 构造 raw_records / stable 样本 + fixtures；m1/m7/probe 直接调用
# Output: issue #61 指标可得性契约（四态、真零、core pending、权重重分配、阈值短路、防回归）
# Pos: plugins/wxops/tests/test_metric_availability.py
"""Issue #61: 指标可得性缺失不得当作真零。"""
from __future__ import annotations

import json
from pathlib import Path

from analyze.m1_checkup import build_checkup
from analyze.m7_standards import build_benchmark
from analyze.metric_registry import (
    METRIC_DIMENSIONS,
    core_pending_count,
    probe_availability,
)
from build_wechat_ops_report import build_dataset

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _rec(**fields):
    """最小原始记录骨架。"""
    base = {
        "title": "t",
        "published_at": "2026-01-01T10:00:00+08:00",
        "is_deleted": False,
    }
    base.update(fields)
    return base


def test_platform_not_provided_zaikan():
    records = [
        _rec(read_num=10, share_num=1, comment_num=0, like_num=0),
        _rec(read_num=20, share_num=2, comment_num=1, like_num=1),
    ]
    avail = probe_availability(records)
    assert avail["zaikan"]["status"] == "platform_not_provided"
    assert avail["zaikan"]["coverage"] == 0.0
    assert avail["zaikan"]["all_zero"] is None


def test_true_zero_available_reprint():
    """字段存在且值全 0 = 真零，status 必须 available（本单核心守门）。"""
    records = [
        _rec(read_num=10, share_num=0, comment_num=0, like_num=0, reprint_num=0),
        _rec(read_num=20, share_num=0, comment_num=0, like_num=0, reprint_num=0),
        _rec(read_num=30, share_num=1, comment_num=0, like_num=0, reprint_num=0),
    ]
    avail = probe_availability(records)
    assert avail["reprints"]["status"] == "available"
    assert avail["reprints"]["all_zero"] is True
    assert avail["reprints"]["coverage"] == 1.0


def test_partial_coverage_available():
    records = []
    for i in range(59):
        r = _rec(read_num=i + 1, share_num=0, comment_num=0, like_num=0)
        if i < 12:
            r["moment_like_num"] = 0
        records.append(r)
    avail = probe_availability(records)
    assert avail["moment_likes"]["status"] == "available"
    assert avail["moment_likes"]["coverage"] == round(12 / 59, 4)


def test_empty_records_all_raw_fetch_missing():
    avail = probe_availability([])
    for dim in METRIC_DIMENSIONS:
        if dim["probe"] != "raw_field":
            continue
        entry = avail[dim["key"]]
        assert entry["status"] == "fetch_missing", dim["key"]
        assert entry["coverage"] == 0.0


def test_derived_dimensions_passthrough_and_not_applicable():
    records = [_rec(read_num=1, share_num=0, comment_num=0, like_num=0)]
    avail = probe_availability(
        records,
        derived={
            "article_length_chars": {
                "status": "fetch_missing",
                "coverage": 0.0,
                "detail": "matched/total=0/1",
            }
        },
    )
    assert avail["article_length_chars"]["status"] == "fetch_missing"
    assert avail["article_length_chars"]["coverage"] == 0.0
    # 未传入的 derived → not_applicable
    assert avail["fans_portrait"]["status"] == "not_applicable"


def test_core_missing_raises_pending_count():
    """缺 read_num → metric_pending_count == 1；证明不再是死代码。"""
    records = [
        _rec(share_num=1, comment_num=0, like_num=0),  # 无 read_num
        _rec(share_num=2, comment_num=1, like_num=1),
    ]
    avail = probe_availability(records)
    assert avail["reads"]["status"] == "platform_not_provided"
    assert avail["shares"]["status"] == "available"
    assert core_pending_count(avail) == 1


def test_m1_weight_redistribution_zaikan_missing():
    """zaikan 不可得 + share healthy + comment 不 healthy → inter_score == 14.1。"""
    stable = [
        {
            "reads": 100,
            "share_rate": 0.04,
            "comment_rate": 0.0,
            "zaikan_rate": 0.0,
        }
        for _ in range(5)
    ]
    bm = {
        "read_avg": 100,
        "read_median": 100,
        "read_max": 100,
    }
    audience = {"available": False}
    metric_availability = {
        "zaikan": {"status": "platform_not_provided"},
        "shares": {"status": "available"},
        "comments": {"status": "available"},
    }
    chk = build_checkup(stable, bm, audience, metric_availability=metric_availability)
    # 25 * 9/16 = 14.0625 → round 1 位 = 14.1
    assert chk["chart_payload"]["inter_score"] == 14.1
    assert chk["interaction"]["zaikan_rate"] is None
    assert chk["interaction"]["zaikan_status"] == "platform_not_provided"
    assert abs(float(chk["interaction"]["share_rate"]) - 0.04) < 1e-9

    # 三项全不可得 → inter_score 0，25 分不挪到 base/anti/fan
    all_missing = {
        "zaikan": {"status": "platform_not_provided"},
        "shares": {"status": "platform_not_provided"},
        "comments": {"status": "platform_not_provided"},
    }
    chk2 = build_checkup(stable, bm, audience, metric_availability=all_missing)
    assert chk2["chart_payload"]["inter_score"] == 0.0
    assert chk2["health_score"] == 36  # 16+20+0+0
    assert chk2["interaction"]["share_rate"] is None
    assert chk2["interaction"]["comment_rate"] is None
    assert chk2["interaction"]["zaikan_rate"] is None
    assert "互动维度整体不可得" in chk2["analysis"]


def test_m7_zaikan_threshold_none_when_unavailable():
    stable = [{"reads": 100, "share_rate": 0.03, "zaikan_rate": 0.0}] * 5
    metric_availability = {"zaikan": {"status": "platform_not_provided"}}
    bm = build_benchmark(stable, metric_availability=metric_availability)
    assert bm["viral_zaikan_threshold"] is None
    assert bm["zaikan_rate_median"] is None

    # 零样本分支同样
    bm0 = build_benchmark([], metric_availability=metric_availability)
    assert bm0["viral_zaikan_threshold"] is None
    assert bm0["zaikan_rate_median"] is None


def test_regression_no_fake_zaikan_zero_pct_in_report_text():
    """health 形态：无 zaikan 源字段 → 序列化文本不得出现「在看0.0%」。"""
    # 用 fixture 跑完整报告，再把 raw 形态模拟成无 zaikan 键需要真实路径；
    # fixture 含 wow_num，因此改用构造：直接 build_checkup + 序列化 analysis
    stable = [
        {"reads": 50, "share_rate": 0.0, "comment_rate": 0.0, "zaikan_rate": 0.0}
        for _ in range(5)
    ]
    bm = {"read_avg": 50, "read_median": 50, "read_max": 50}
    metric_availability = {
        "zaikan": {"status": "platform_not_provided"},
        "shares": {"status": "available"},
        "comments": {"status": "available"},
    }
    chk = build_checkup(stable, bm, {"available": False}, metric_availability=metric_availability)
    text = json.dumps(chk, ensure_ascii=False)
    assert "在看0.0%" not in text
    assert "在看0%" not in chk["analysis"]
    assert "平台未提供" in chk["analysis"] or "不可得" in chk["analysis"]


def test_build_dataset_exposes_metric_availability_and_pending_zero():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    assert "metric_availability" in dataset
    ma = dataset["metric_availability"]
    # fixture 含核心四字段
    for key in ("reads", "shares", "comments", "likes"):
        assert ma[key]["status"] == "available"
    assert dataset["data_quality"]["metric_pending_count"] == 0
    # fixture 有 wow_num → zaikan available
    assert ma["zaikan"]["status"] == "available"
    # fans_portrait 来自 m4 探测器
    assert ma["fans_portrait"]["status"] in {"available", "fetch_missing"}
