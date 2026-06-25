from __future__ import annotations

from typing import Any

from analyze.stats import stat_pack


def confidence_for_records(
    records: list[dict[str, Any]],
    *,
    completeness: float = 1.0,
    target_sample: int = 18,
    note: str = "",
) -> dict[str, Any]:
    count = len(records)
    stats = stat_pack(records)
    median_value = float(stats["median"] or 0)
    max_value = float(stats["max"] or 0)
    avg_value = float(stats["avg"] or 0)
    sample_score = min(1.0, count / target_sample) if target_sample else 1.0
    skew_ratio = max_value / median_value if median_value else (8.0 if max_value else 1.0)
    avg_ratio = avg_value / median_value if median_value else (3.0 if avg_value else 1.0)
    distribution_score = 1.0
    reasons: list[str] = []
    if skew_ratio > 8 or avg_ratio > 2.6:
        distribution_score = 0.45
        reasons.append("存在单篇爆款明显拉高均值")
    elif skew_ratio > 5 or avg_ratio > 1.8:
        distribution_score = 0.68
        reasons.append("分布有一定长尾,结论需同时看中位数")
    else:
        reasons.append("分布相对稳定")
    if count < 6:
        reasons.append("样本量偏少")
    elif count < target_sample:
        reasons.append("样本量中等,适合做下一轮验证")
    else:
        reasons.append("样本量足够支撑阶段性判断")
    if completeness < 0.92:
        reasons.append("存在本地正文或指标匹配缺口")
    if note:
        reasons.append(note)
    score = round(
        max(0.0, min(1.0, sample_score * 0.42 + distribution_score * 0.34 + completeness * 0.24)),
        2,
    )
    if score >= 0.74:
        level = "high"
    elif score >= 0.52:
        level = "medium"
    else:
        level = "low"
    return {
        "level": level,
        "score": score,
        "sample_size": count,
        "completeness": round(completeness, 3),
        "distribution_skew": round(skew_ratio, 2),
        "reasons": reasons[:4],
    }


def voice_for_confidence(confidence: dict[str, Any] | str) -> str:
    if isinstance(confidence, dict):
        level = confidence.get("level", "medium")
    else:
        level = str(confidence) if confidence else "medium"
    if level not in ("high", "medium", "low"):
        level = "medium"
    return level


def emphasis_for_confidence(confidence: dict[str, Any] | str) -> str:
    level = voice_for_confidence(confidence)
    return {"high": "hero", "medium": "primary", "low": "secondary"}.get(level, "primary")


def action_basket_for_confidence(confidence: dict[str, Any] | str) -> str:
    level = voice_for_confidence(confidence)
    return {"high": "now", "medium": "experiment", "low": "hold"}.get(level, "experiment")


def build_confidence_model(stable: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [article for article in stable if article.get("article_length_chars", 0) > 0]
    completeness = len(matched) / len(stable) if stable else 0
    return {
        "levels": {
            "high": "可以直接进入本周动作,但仍要用下一批文章复核。",
            "medium": "适合做 A/B 或小批量验证,不要一口气改全局策略。",
            "low": "只作为观察线索,不写成运营规律。",
        },
        "drivers": [
            "样本量",
            "均值是否被单篇爆款拉高",
            "指标和本地正文匹配完整度",
            "48 小时成熟窗口",
        ],
        "overall": confidence_for_records(stable, completeness=completeness, note="全局稳定样本"),
        "article_length_completeness": round(completeness, 3),
    }
