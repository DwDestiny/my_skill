from __future__ import annotations

from typing import Any

from analyze.confidence import (
    action_basket_for_confidence,
    confidence_for_records,
    emphasis_for_confidence,
    voice_for_confidence,
)
from analyze.stats import median


def _median_of_field(records: list[dict[str, Any]], field: str) -> float:
    vals = [float(r.get(field, 0) or 0) for r in records]
    return median(vals) if vals else 0.0


def build_checkup(stable: list[dict[str, Any]], benchmark: dict[str, Any], audience: dict[str, Any]) -> dict[str, Any]:
    if not stable:
        conf = confidence_for_records([], note="checkup")
        voice = voice_for_confidence(conf)
        return {
            "health_score": 0,
            "dependency": {"avg_ratio": 0, "skew_ratio": 0, "is_dependent": False},
            "interaction": {"zaikan_rate": 0, "share_rate": 0, "comment_rate": 0, "healthy": False},
            "fans": {"netgain_7d": 0, "cancel_rate": 0, "available": False},
            "verdict": "样本不足，暂无诊断",
            "analysis": "稳定样本为空，无法计算体检。",
            "action": "先积累稳定样本再复盘。",
            "voice": voice,
            "emphasis": emphasis_for_confidence(voice),
            "action_basket": action_basket_for_confidence(voice),
            "chart_payload": {"kind": "checkup", "health_score": 0},
        }

    # dependency from benchmark
    read_avg = float(benchmark.get("read_avg", 0) or 0)
    read_median = float(benchmark.get("read_median", 0) or 0)
    read_max = float(benchmark.get("read_max", 0) or 0)
    avg_ratio = round(read_avg / read_median, 2) if read_median > 0 else (3.0 if read_avg > 0 else 0)
    skew_ratio = round(read_max / read_median, 2) if read_median > 0 else (8.0 if read_max > 0 else 0)
    is_dependent = (avg_ratio > 2.6) or (skew_ratio > 8)

    # interaction medians
    zaikan_m = round(_median_of_field(stable, "zaikan_rate"), 4)
    share_m = round(_median_of_field(stable, "share_rate"), 4)
    comment_m = round(_median_of_field(stable, "comment_rate"), 4)
    zaikan_healthy = zaikan_m > 0.03
    share_healthy = share_m > 0.02
    comment_healthy = comment_m > 0.005
    inter_healthy = zaikan_healthy and share_healthy and comment_healthy

    # fans
    fans_available = bool(audience.get("available"))
    netgain_7d = int(audience.get("summary", {}).get("netgain_7d", 0) or 0) if fans_available else 0
    cumulate = int(audience.get("cumulate_user", 0) or 0) if fans_available else 0
    cancel_7d = int(audience.get("summary", {}).get("cancel_user_7d", 0) or 0) if fans_available else 0
    cancel_rate = round(cancel_7d / cumulate, 4) if fans_available and cumulate > 0 else 0.0

    # health_score components (0-100)
    # base: median / target 250 cap at 100, *40 weight -> 0-40
    base_raw = min(100.0, (read_median / 250.0) * 100.0) if read_median else 0
    base_score = round(base_raw * 0.40, 1)

    # anti-dependency: if not dependent 20, else if mild 10, low 0; weight -> up to ~20
    if not is_dependent:
        anti_dep = 20.0
    elif avg_ratio > 2.0 or skew_ratio > 5:
        anti_dep = 8.0
    else:
        anti_dep = 14.0
    anti_score = round(anti_dep, 1)  # already scaled

    # interaction: each healthy gives points, max 25
    inter_points = 0.0
    if zaikan_healthy:
        inter_points += 9
    if share_healthy:
        inter_points += 9
    if comment_healthy:
        inter_points += 7
    inter_score = round(inter_points, 1)

    # fans netgain: if available, netgain_7d >0 gives points, higher better, cap ~15; also penalize high cancel
    fan_score = 0.0
    if fans_available:
        if netgain_7d > 0:
            fan_score += min(10.0, netgain_7d / 30.0)  # ~10 for 300+
        if cancel_rate < 0.01:
            fan_score += 5.0
        elif cancel_rate < 0.03:
            fan_score += 2.0
    fan_score = round(fan_score, 1)

    health_score = int(round(max(0.0, min(100.0, base_score + anti_score + inter_score + fan_score))))

    # conf and voice
    conf = confidence_for_records(stable, note="checkup")
    voice = voice_for_confidence(conf)
    emphasis = emphasis_for_confidence(voice)
    basket = action_basket_for_confidence(voice)

    # verdict one sentence, voice modulated, no conf num
    if health_score >= 75:
        base_ver = "账号底盘健康，依赖风险低。"
    elif health_score >= 55:
        base_ver = "底盘中等，需防爆款依赖。"
    else:
        base_ver = "底盘偏弱，依赖爆款明显。"
    if voice == "high":
        verdict = base_ver
    elif voice == "low":
        verdict = "初步迹象显示" + base_ver if not base_ver.startswith("初步") else base_ver
    else:
        verdict = base_ver

    # analysis short
    analysis = (
        f"中位{int(read_median)}、均值{int(read_avg)}、最大{int(read_max)}；"
        f"分享中位{share_m*100:.1f}%、在看{zaikan_m*100:.1f}%、评论{comment_m*100:.1f}%。"
    )

    # action voice modulated
    if voice == "high":
        action = "优先做中位验证，控每天风险文上限。"
    elif voice == "low":
        action = "可继续观察中位与净增，再定优先级。"
    else:
        action = "复盘中位与分享率，限制强依赖题材频次。"

    return {
        "health_score": health_score,
        "dependency": {
            "avg_ratio": avg_ratio,
            "skew_ratio": skew_ratio,
            "is_dependent": is_dependent,
        },
        "interaction": {
            "zaikan_rate": zaikan_m,
            "share_rate": share_m,
            "comment_rate": comment_m,
            "healthy": inter_healthy,
        },
        "fans": {
            "netgain_7d": netgain_7d,
            "cancel_rate": cancel_rate,
            "available": fans_available,
        },
        "verdict": verdict,
        "analysis": analysis,
        "action": action,
        "voice": voice,
        "emphasis": emphasis,
        "action_basket": basket,
        "chart_payload": {
            "kind": "checkup",
            "health_score": health_score,
            "dependency": is_dependent,
            "interaction_healthy": inter_healthy,
        },
    }
