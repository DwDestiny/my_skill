from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean, median
from typing import Any

from analyze.constants import WEEKDAY_LABELS
from analyze.io_utils import parse_dt


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    idx = (len(ordered) - 1) * pct
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return float(ordered[lo])
    return float(ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo))


def trimmed_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) < 5:
        return float(mean(ordered))
    trim = max(1, int(len(ordered) * 0.1))
    middle = ordered[trim:-trim] or ordered
    return float(mean(middle))


def stat_pack(records: list[dict[str, Any]], field: str = "reads") -> dict[str, Any]:
    values = [float(r.get(field, 0) or 0) for r in records]
    return {
        "count": len(values),
        "avg": round(mean(values), 2) if values else 0,
        "median": round(median(values), 2) if values else 0,
        "p75": round(percentile(values, 0.75), 2) if values else 0,
        "max": int(max(values)) if values else 0,
        "trimmed_mean": round(trimmed_mean(values), 2) if values else 0,
    }


def group_stats(records: list[dict[str, Any]], key: str, fixed_keys: list[str] | None = None) -> list[dict[str, Any]]:
    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[record.get(key)].append(record)
    keys = fixed_keys if fixed_keys is not None else sorted(groups.keys())
    output = []
    for group_key in keys:
        rows = groups.get(group_key, [])
        stats = stat_pack(rows)
        top = max(rows, key=lambda r: r.get("reads", 0), default=None)
        total_reads = sum(r.get("reads", 0) for r in rows)
        output.append(
            {
                "key": group_key,
                **stats,
                "total_reads": total_reads,
                "share_rate_avg": round(mean([r.get("share_rate", 0) for r in rows]), 4)
                if rows
                else 0,
                "comment_rate_avg": round(mean([r.get("comment_rate", 0) for r in rows]), 4)
                if rows
                else 0,
                "top_sample": {
                    "title": top.get("title"),
                    "reads": top.get("reads"),
                    "url": top.get("url"),
                }
                if top
                else None,
            }
        )
    return output


def time_heatmap(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        weekday = record.get("weekday")
        hour = record.get("hour")
        if weekday is not None and hour is not None:
            groups[(weekday, hour)].append(record)
    cells = []
    for weekday in range(1, 8):
        for hour in range(0, 24):
            rows = groups.get((weekday, hour), [])
            stats = stat_pack(rows)
            cells.append(
                {
                    "weekday": weekday,
                    "weekday_label": WEEKDAY_LABELS[weekday - 1],
                    "hour": hour,
                    **stats,
                }
            )
    return cells


def weekly_trend(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("iso_week"):
            groups[record["iso_week"]].append(record)
    rows = []
    for week in sorted(groups):
        records_for_week = groups[week]
        dates = [parse_dt(r.get("published_at")) for r in records_for_week if r.get("published_at")]
        week_start = min(dates).date().isoformat() if dates else ""
        rows.append({"week": week, "week_start": week_start, **stat_pack(records_for_week)})
    return rows


def top_n(records: list[dict[str, Any]], key: str, n: int = 12) -> list[dict[str, Any]]:
    return [
        {
            "title": record["title"],
            "url": record["url"],
            "published_at": record["published_at"],
            "reads": record["reads"],
            "shares": record["shares"],
            "comments": record["comments"],
            "share_rate": record["share_rate"],
            "content_type": record["content_type"],
            "pain_point": record["pain_point"],
            "persona": record["persona"],
        }
        for record in sorted(records, key=lambda r: r.get(key, 0), reverse=True)[:n]
    ]


def build_rankings(records: list[dict[str, Any]]) -> dict[str, Any]:
    reads = [r["reads"] for r in records]
    read_median = median(reads) if reads else 0
    share_rate_candidates = [r["share_rate"] for r in records if r["reads"] >= 30]
    share_rate_p75 = percentile(share_rate_candidates, 0.75) if share_rate_candidates else 0
    potential = [
        r
        for r in records
        if r["reads"] <= max(read_median * 2, 80)
        and r["reads"] >= 30
        and r["share_rate"] >= share_rate_p75
    ]
    return {
        "top_reads": top_n(records, "reads"),
        "top_shares": top_n(records, "shares"),
        "top_share_rate": top_n([r for r in records if r["reads"] >= 30], "share_rate"),
        "low_read_high_share_potential": top_n(potential, "shares"),
    }


def rate(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)
