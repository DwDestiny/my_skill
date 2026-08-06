# GEB-L3
# Input: 文章 dict 列表 + 分子字段名列表/单篇率字段名 + 可选分母字段/min_reads
# Output: aggregate_rate 返回 ratio-of-means 聚合包；median_rate 返回带 min_reads 过滤的中位数包
# Pos: plugins/wxops/scripts/analyze/rates.py
"""互动率聚合唯一入口（issue #59）。

- 账号级/分组级平均率：ratio of means（总分子 / 总分母），禁止 mean of ratios。
- 典型文章率：逐篇率中位数，先按 min_reads 过滤防小分母。
"""
from __future__ import annotations

from statistics import median
from typing import Any, Sequence

# 与 m7_standards.py / stats.py 现有口径一致
MIN_READS_FOR_RATE_MEDIAN = 30


def aggregate_rate(
    articles: Sequence[dict[str, Any]],
    numerator_fields: Sequence[str],
    denominator_field: str = "reads",
) -> dict[str, Any]:
    """账号级/分组级聚合互动率 = 总分子 / 总分母（ratio of means）。

    不做最小分母过滤——ratio-of-means 天然按阅读量加权，
    1 阅读的文章只贡献 1 个分母，不会失真。

    numerator_fields 是字段名列表，多个字段求和（点赞要 likes+old_likes+moment_likes）。
    分母为 0 时 value=0.0，不抛异常。
    """
    if not articles:
        return {
            "value": 0.0,
            "numerator": 0,
            "denominator": 0,
            "sample_count": 0,
            "method": "ratio_of_means",
        }

    numerator = 0
    denominator = 0
    for article in articles:
        for field in numerator_fields:
            numerator += int(article.get(field, 0) or 0)
        denominator += int(article.get(denominator_field, 0) or 0)

    value = round(numerator / denominator, 4) if denominator > 0 else 0.0
    return {
        "value": float(value),
        "numerator": int(numerator),
        "denominator": int(denominator),
        "sample_count": len(articles),
        "method": "ratio_of_means",
    }


def median_rate(
    articles: Sequence[dict[str, Any]],
    rate_field: str,
    min_reads: int = MIN_READS_FOR_RATE_MEDIAN,
) -> dict[str, Any]:
    """典型文章的率 = 逐篇率的中位数，先按最小阅读数过滤。

    中位数是等权统计，必须防小分母，所以这里需要 min_reads 过滤。
    过滤后样本 <3 篇时回落到全量，并标注 fallback=True。
    （回落规则对齐 m7_standards 的「样本不足则用全量」意图，并明确 <3 门槛。）
    """
    if not articles:
        return {
            "value": 0.0,
            "sample_count": 0,
            "excluded_count": 0,
            "fallback": False,
            "min_reads": min_reads,
        }

    filtered = [
        a for a in articles if (a.get("reads", 0) or 0) >= min_reads
    ]
    excluded_count = len(articles) - len(filtered)

    fallback = False
    used = filtered
    if len(filtered) < 3:
        used = list(articles)
        fallback = True
        excluded_count = 0  # 回落后未排除任何样本

    values = [float(a.get(rate_field, 0) or 0) for a in used]
    value = round(median(values), 4) if values else 0.0
    return {
        "value": float(value),
        "sample_count": len(used),
        "excluded_count": excluded_count,
        "fallback": fallback,
        "min_reads": min_reads,
    }
