# GEB-L3
# Input: 合成文章列表（小分母极端值 / 多字段点赞 / 全 0 分母 / 空列表）
# Output: rates.aggregate_rate 与 median_rate 的 pytest 断言（issue #59 ratio-of-means）
# Pos: plugins/wxops/tests/test_rates.py
"""互动率聚合入口单测（issue #59）。

覆盖：ratio-of-means 抗小分母失真、多字段分子、分母全 0、空列表、
median_rate 的 min_reads 过滤与样本不足回落。
"""
from __future__ import annotations

from analyze.rates import aggregate_rate, median_rate, MIN_READS_FOR_RATE_MEDIAN


def test_aggregate_rate_ratio_of_means_not_mean_of_ratios():
    """1 阅读 1 赞 ×10 + 10000 阅读 100 赞 ×1 → ≈110/10010，而非 mean-of-ratios ~0.909。"""
    articles = [
        {"reads": 1, "likes": 1, "old_likes": 0, "moment_likes": 0}
        for _ in range(10)
    ] + [
        {"reads": 10000, "likes": 100, "old_likes": 0, "moment_likes": 0},
    ]
    result = aggregate_rate(articles, ["likes", "old_likes", "moment_likes"])
    expected = round(110 / 10010, 4)
    assert result["value"] == expected
    assert abs(result["value"] - 0.011) < 0.0001
    # 明确不是 mean-of-ratios
    assert result["value"] < 0.1
    assert result["numerator"] == 110
    assert result["denominator"] == 10010
    assert result["sample_count"] == 11
    assert result["method"] == "ratio_of_means"


def test_aggregate_rate_multi_field_numerator():
    """likes + old_likes + moment_likes 三字段求和。"""
    articles = [
        {"reads": 1000, "likes": 10, "old_likes": 5, "moment_likes": 3},
        {"reads": 1000, "likes": 2, "old_likes": 0, "moment_likes": 0},
    ]
    result = aggregate_rate(articles, ["likes", "old_likes", "moment_likes"])
    # 分子 = 10+5+3 + 2+0+0 = 20；分母 = 2000
    assert result["numerator"] == 20
    assert result["denominator"] == 2000
    assert result["value"] == round(20 / 2000, 4)
    assert result["value"] == 0.01


def test_aggregate_rate_zero_denominator():
    """分母全 0：value=0.0 且不抛异常。"""
    articles = [
        {"reads": 0, "shares": 1},
        {"reads": 0, "shares": 2},
    ]
    result = aggregate_rate(articles, ["shares"])
    assert result["value"] == 0.0
    assert result["numerator"] == 3
    assert result["denominator"] == 0
    assert result["sample_count"] == 2


def test_aggregate_rate_empty_list():
    """空列表：value=0.0, sample_count=0。"""
    result = aggregate_rate([], ["shares"])
    assert result["value"] == 0.0
    assert result["sample_count"] == 0
    assert result["numerator"] == 0
    assert result["denominator"] == 0
    assert result["method"] == "ratio_of_means"


def test_median_rate_min_reads_filter_excludes_low_reads():
    """低阅读的极端值被 min_reads 过滤掉。"""
    articles = [
        # 低阅读极端值：若等权中位会把中位拉高
        {"reads": 1, "share_rate": 1.0},
        {"reads": 2, "share_rate": 1.0},
        # 足够阅读的正常值
        {"reads": 100, "share_rate": 0.01},
        {"reads": 200, "share_rate": 0.02},
        {"reads": 300, "share_rate": 0.03},
    ]
    result = median_rate(articles, "share_rate", min_reads=MIN_READS_FOR_RATE_MEDIAN)
    assert result["fallback"] is False
    assert result["sample_count"] == 3
    assert result["excluded_count"] == 2
    assert result["value"] == 0.02  # median of 0.01, 0.02, 0.03
    assert result["min_reads"] == 30


def test_median_rate_fallback_when_filtered_insufficient():
    """过滤后样本 <3 时回落全量，fallback=True。"""
    articles = [
        {"reads": 100, "share_rate": 0.01},
        {"reads": 200, "share_rate": 0.02},
        # 其余 reads 不足
        {"reads": 5, "share_rate": 0.50},
        {"reads": 1, "share_rate": 1.0},
        {"reads": 2, "share_rate": 0.80},
    ]
    result = median_rate(articles, "share_rate", min_reads=30)
    assert result["fallback"] is True
    assert result["sample_count"] == 5  # 全量
    assert result["excluded_count"] == 0  # 回落后未排除
    # 全量中位数：0.01, 0.02, 0.50, 0.80, 1.0 → 0.50
    assert result["value"] == 0.5
