from __future__ import annotations

from collections import Counter
from statistics import median as _median
from typing import Any

from analyze.stats import median


def classify_quadrant(article: dict[str, Any], benchmark: dict[str, Any]) -> str:
    """四象限定位。x=阅读量 vs read_median, y=分享率 vs share_rate_median。"""
    read_median = benchmark.get("read_median", 0)
    share_rate_median = benchmark.get("share_rate_median", 0)
    reads = article.get("reads", 0) or 0
    share_rate = article.get("share_rate", 0) or 0
    if reads >= read_median and share_rate >= share_rate_median:
        return "爆款"
    if reads >= read_median and share_rate < share_rate_median:
        return "标题党"
    if reads < read_median and share_rate >= share_rate_median:
        return "深度遗珠"
    return "平稳"


def _mode_or_none(values: list[Any]) -> Any:
    if not values:
        return None
    c = Counter(v for v in values if v is not None)
    if not c:
        return None
    return c.most_common(1)[0][0]


def _safe_median(values: list[float | int]) -> float:
    vals = [v for v in values if v is not None]
    if not vals:
        return 0
    try:
        return _median(vals)
    except Exception:
        # fallback in case empty after filter or single
        return float(vals[0]) if len(vals) == 1 else 0


def reverse_viral_formula(stable: list[dict[str, Any]], benchmark: dict[str, Any]) -> dict[str, Any]:
    """从'爆款'象限文章反推可复制公式。"""
    viral_articles = [a for a in stable if classify_quadrant(a, benchmark) == "爆款"]
    sample_count = len(viral_articles)

    if sample_count == 0:
        return {
            "topic": None,
            "title_pattern": None,
            "timing_weekday": None,
            "timing_hour": 0,
            "persona": None,
            "sample_count": 0,
            "evidence_titles": [],
            "reliable": False,
        }

    topics = [a.get("content_type") for a in viral_articles]
    patterns = [a.get("title_primary_pattern") for a in viral_articles]
    weekdays = [a.get("weekday_label") for a in viral_articles]
    personas = [a.get("persona") for a in viral_articles]
    hours = [a.get("hour") for a in viral_articles if a.get("hour") is not None]

    topic = _mode_or_none(topics)
    title_pattern = _mode_or_none(patterns)
    timing_weekday = _mode_or_none(weekdays)
    timing_hour = int(round(_safe_median(hours))) if hours else 0
    persona = _mode_or_none(personas)

    evidence_titles = [a.get("title", "") for a in sorted(viral_articles, key=lambda x: x.get("reads", 0), reverse=True)[:5]]

    reliable = sample_count >= 3

    return {
        "topic": topic,
        "title_pattern": title_pattern,
        "timing_weekday": timing_weekday,
        "timing_hour": timing_hour,
        "persona": persona,
        "sample_count": sample_count,
        "evidence_titles": evidence_titles,
        "reliable": reliable,
    }


def build_viral_genes(stable: list[dict[str, Any]], benchmark: dict[str, Any]) -> dict[str, Any]:
    """组装模块2输出。"""
    # quadrant for every stable article
    quadrant: list[dict[str, Any]] = []
    counts = {"爆款": 0, "标题党": 0, "深度遗珠": 0, "平稳": 0}
    for a in stable:
        q = classify_quadrant(a, benchmark)
        counts[q] = counts.get(q, 0) + 1
        quadrant.append({
            "title": a.get("title", ""),
            "reads": a.get("reads", 0) or 0,
            "share_rate": a.get("share_rate", 0) or 0,
            "quadrant": q,
            "content_type": a.get("content_type", ""),
        })

    viral_articles = [a for a in stable if classify_quadrant(a, benchmark) == "爆款"]
    top_viral = sorted(viral_articles, key=lambda x: x.get("reads", 0), reverse=True)[:8]

    viral_formula = reverse_viral_formula(stable, benchmark)

    deep_pearls = counts.get("深度遗珠", 0)
    title_party = counts.get("标题党", 0)
    viral_n = counts.get("爆款", 0)
    diagnosis_signal = {
        "title_problem": deep_pearls > viral_n,
        "content_problem": title_party > viral_n,
    }

    return {
        "quadrant": quadrant,
        "quadrant_counts": counts,
        "viral_formula": viral_formula,
        "top_viral": top_viral,
        "diagnosis_signal": diagnosis_signal,
    }
