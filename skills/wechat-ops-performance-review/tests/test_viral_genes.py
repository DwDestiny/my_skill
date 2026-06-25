"""Tests for new benchmark and viral_genes modules."""
from pathlib import Path
from statistics import mean

import pytest

from build_wechat_ops_report import build_dataset
from analyze.m7_standards import build_benchmark
from analyze.m2_viral_genes import (
    build_viral_genes,
    classify_quadrant,
    reverse_viral_formula,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_classify_quadrant_four_quadrants():
    """Construct 4 articles to hit all 4 quadrants exactly."""
    benchmark = {
        "read_median": 100,
        "share_rate_median": 0.05,
    }
    # 爆款: reads >=100 and share >=0.05
    a1 = {"title": "爆款", "reads": 150, "share_rate": 0.06}
    assert classify_quadrant(a1, benchmark) == "爆款"

    # 标题党: reads >=100 and share <0.05
    a2 = {"title": "标题党", "reads": 120, "share_rate": 0.01}
    assert classify_quadrant(a2, benchmark) == "标题党"

    # 深度遗珠: reads <100 and share >=0.05
    a3 = {"title": "深度遗珠", "reads": 50, "share_rate": 0.10}
    assert classify_quadrant(a3, benchmark) == "深度遗珠"

    # 平稳: reads <100 and share <0.05
    a4 = {"title": "平稳", "reads": 30, "share_rate": 0.02}
    assert classify_quadrant(a4, benchmark) == "平稳"

    # boundary exact median should count as high side
    a5 = {"title": "边界读数", "reads": 100, "share_rate": 0.05}
    assert classify_quadrant(a5, benchmark) == "爆款"


def test_build_benchmark_thresholds_and_select_rate():
    """viral_read_threshold == round(avg*1.5) and topic_select_rate correct."""
    # Use real fixture data via build_dataset
    dataset = build_dataset(FIXTURES, account_name="测试")
    stable = dataset["articles"]["stable"]
    bm = dataset["benchmark"]

    reads = [a.get("reads", 0) or 0 for a in stable]
    avg = mean(reads) if reads else 0
    expected_threshold = round(avg * 1.5)
    assert bm["viral_read_threshold"] == expected_threshold

    # topic_select_rate: fraction with reads > read_median
    read_median = bm["read_median"]
    total = len(stable)
    above = sum(1 for r in reads if r > read_median)
    expected_rate = round(above / total, 4) if total else 0
    assert bm["topic_select_rate"] == expected_rate
    assert bm["sample_size"] == total

    # fixture 应有稳定样本(不写死具体篇数,避免 fixtures 调整即脆断)
    assert bm["sample_size"] > 0
    assert bm["read_median"] > 0
    assert bm["share_rate_median"] > 0


def test_reverse_viral_formula_reliable_and_mode():
    """reliable=True iff >=3 viral; topic is the mode when >=3."""
    # 3 high + 2 low: for odd count, median lands on the smallest of the high group -> all 3 qualify as viral
    articles = [
        {"title": "low1", "reads": 40, "share_rate": 0.01, "content_type": "泛 AI 热点/效率工具", "title_primary_pattern": "普通资讯型", "weekday_label": "周三", "hour": 8, "persona": "非技术效率工具用户"},
        {"title": "low2", "reads": 60, "share_rate": 0.02, "content_type": "泛 AI 热点/效率工具", "title_primary_pattern": "普通资讯型", "weekday_label": "周三", "hour": 8, "persona": "非技术效率工具用户"},
        {"title": "v1", "reads": 400, "share_rate": 0.10, "content_type": "风险/账号/额度焦虑", "title_primary_pattern": "风险损失型", "weekday_label": "周一", "hour": 9, "persona": "AI 新闻观察者"},
        {"title": "v2", "reads": 500, "share_rate": 0.12, "content_type": "风险/账号/额度焦虑", "title_primary_pattern": "风险损失型", "weekday_label": "周一", "hour": 10, "persona": "AI 新闻观察者"},
        {"title": "v3", "reads": 600, "share_rate": 0.11, "content_type": "风险/账号/额度焦虑", "title_primary_pattern": "风险损失型", "weekday_label": "周二", "hour": 11, "persona": "AI 新闻观察者"},
    ]
    bm = build_benchmark(articles)
    formula = reverse_viral_formula(articles, bm)
    assert formula["sample_count"] >= 3
    assert formula["reliable"] is True
    assert formula["topic"] == "风险/账号/额度焦虑"  # the mode
    assert len(formula["evidence_titles"]) <= 5

    # Now <3 viral case (only 1 viral)
    articles2 = [
        {"title": "v1", "reads": 400, "share_rate": 0.10, "content_type": "风险/账号/额度焦虑", "title_primary_pattern": "风险损失型", "weekday_label": "周一", "hour": 9, "persona": "AI 新闻观察者"},
        {"title": "low1", "reads": 50, "share_rate": 0.01, "content_type": "泛 AI 热点/效率工具", "title_primary_pattern": "普通资讯型", "weekday_label": "周三", "hour": 8, "persona": "非技术效率工具用户"},
        {"title": "low2", "reads": 60, "share_rate": 0.02, "content_type": "泛 AI 热点/效率工具", "title_primary_pattern": "普通资讯型", "weekday_label": "周三", "hour": 8, "persona": "非技术效率工具用户"},
    ]
    bm2 = build_benchmark(articles2)
    formula2 = reverse_viral_formula(articles2, bm2)
    assert formula2["sample_count"] < 3
    assert formula2["reliable"] is False


def test_build_viral_genes_quadrant_length_matches_stable():
    """After mount to dataset, quadrant list length == stable count."""
    dataset = build_dataset(FIXTURES, account_name="测试")
    stable = dataset["articles"]["stable"]
    vg = dataset["viral_genes"]
    assert len(vg["quadrant"]) == len(stable)
    assert "爆款" in vg["quadrant_counts"]
    assert "标题党" in vg["quadrant_counts"]
    assert "深度遗珠" in vg["quadrant_counts"]
    assert "平稳" in vg["quadrant_counts"]
    assert "viral_formula" in vg
    assert "top_viral" in vg
    assert "diagnosis_signal" in vg
    assert isinstance(vg["diagnosis_signal"]["title_problem"], bool)
    assert isinstance(vg["diagnosis_signal"]["content_problem"], bool)
