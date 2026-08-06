# GEB-L3
# Input: stable 文章列表（reads/share_rate/zaikan_rate）
# Output: 本号相对论 benchmark（中位/p75/爆款阈值/topic_select_rate/sample_size）
# Pos: plugins/wxops/scripts/analyze/m7_standards.py
from __future__ import annotations

from typing import Any

from analyze.rates import median_rate
from analyze.stats import stat_pack


def build_benchmark(stable: list[dict[str, Any]]) -> dict[str, Any]:
    """全局相对论基准。看本号相对值,不看绝对值。"""
    if not stable:
        return {
            "read_median": 0,
            "read_p75": 0,
            "read_trimmed_mean": 0,
            "read_avg": 0,
            "read_max": 0,
            "share_rate_median": 0,
            "zaikan_rate_median": 0,
            "viral_read_threshold": 0,
            "viral_share_threshold": 0,
            "viral_zaikan_threshold": 0.05,
            "topic_select_rate": 0,
            "sample_size": 0,
        }

    # reads stats via stat_pack (reuses existing)
    pack = stat_pack(stable, field="reads")
    read_median = pack.get("median", 0)
    read_p75 = pack.get("p75", 0)
    read_trimmed_mean = pack.get("trimmed_mean", 0)
    read_avg = pack.get("avg", 0)
    read_max = pack.get("max", 0)

    # 典型文章率：median + reads>=30 过滤 + 样本不足回落全量（issue #59 → rates.median_rate）
    share_rate_median = median_rate(stable, "share_rate")["value"]
    zaikan_rate_median = median_rate(stable, "zaikan_rate")["value"]

    # thresholds
    viral_read_threshold = round(read_avg * 1.5)
    viral_share_threshold = round(share_rate_median * 2, 4)
    viral_zaikan_threshold = 0.05

    # topic_select_rate: fraction of articles with reads > read_median (strictly above)
    total = len(stable)
    above_median = sum(1 for a in stable if (a.get("reads", 0) or 0) > read_median)
    topic_select_rate = round(above_median / total, 4) if total > 0 else 0.0

    return {
        "read_median": read_median,
        "read_p75": read_p75,
        "read_trimmed_mean": read_trimmed_mean,
        "read_avg": read_avg,
        "read_max": read_max,
        "share_rate_median": share_rate_median,
        "zaikan_rate_median": zaikan_rate_median,
        "viral_read_threshold": viral_read_threshold,
        "viral_share_threshold": viral_share_threshold,
        "viral_zaikan_threshold": viral_zaikan_threshold,
        "topic_select_rate": topic_select_rate,
        "sample_size": total,
    }
