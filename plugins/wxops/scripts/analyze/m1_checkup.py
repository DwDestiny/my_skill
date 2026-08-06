# GEB-L3
# Input: stable 文章列表 + benchmark（m7）+ audience raw（粉丝/净增/取关）+ 可选 metric_availability
# Output: health_score/dependency/interaction/fans + verdict/action/voice 体检 dict（含 chart_payload）
# Pos: plugins/wxops/scripts/analyze/m1_checkup.py
from __future__ import annotations

from typing import Any

from analyze.confidence import (
    action_basket_for_confidence,
    confidence_for_records,
    emphasis_for_confidence,
    voice_for_confidence,
)
from analyze.rates import median_rate

# 互动原权重；不可得维度不参与，满分 25 在可得维度间按原比例重分配（issue #61）
_INTER_WEIGHTS = {
    "zaikan": 9.0,
    "share": 9.0,
    "comment": 7.0,
}
_INTER_MAX = 25.0


def _dim_status(metric_availability: dict[str, Any] | None, key: str) -> str:
    """缺省 available：直接调用方未传注册表时保持旧行为。"""
    if not metric_availability:
        return "available"
    entry = metric_availability.get(key) or {}
    status = entry.get("status")
    return str(status) if status else "available"


def _is_available(status: str) -> bool:
    return status == "available"


def build_checkup(
    stable: list[dict[str, Any]],
    benchmark: dict[str, Any],
    audience: dict[str, Any],
    metric_availability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    zaikan_status = _dim_status(metric_availability, "zaikan")
    # share/comment 在注册表里叫 shares/comments
    share_status = _dim_status(metric_availability, "shares")
    comment_status = _dim_status(metric_availability, "comments")

    if not stable:
        conf = confidence_for_records([], note="checkup")
        voice = voice_for_confidence(conf)
        inter: dict[str, Any] = {
            "zaikan_rate": None if not _is_available(zaikan_status) else 0,
            "share_rate": None if not _is_available(share_status) else 0,
            "comment_rate": None if not _is_available(comment_status) else 0,
            "healthy": False,
            "zaikan_status": zaikan_status,
            "share_status": share_status,
            "comment_status": comment_status,
        }
        return {
            "health_score": 0,
            "dependency": {"avg_ratio": 0, "skew_ratio": 0, "is_dependent": False},
            "interaction": inter,
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

    # interaction medians：min_reads 过滤后的中位数（issue #59；原先无最小分母保护）
    zaikan_m = median_rate(stable, "zaikan_rate")["value"] if _is_available(zaikan_status) else None
    share_m = median_rate(stable, "share_rate")["value"] if _is_available(share_status) else None
    comment_m = median_rate(stable, "comment_rate")["value"] if _is_available(comment_status) else None

    zaikan_healthy = bool(zaikan_m is not None and zaikan_m > 0.03)
    share_healthy = bool(share_m is not None and share_m > 0.02)
    comment_healthy = bool(comment_m is not None and comment_m > 0.005)

    # 不可得维度不参与 inter_healthy
    healthy_flags: list[bool] = []
    if _is_available(zaikan_status):
        healthy_flags.append(zaikan_healthy)
    if _is_available(share_status):
        healthy_flags.append(share_healthy)
    if _is_available(comment_status):
        healthy_flags.append(comment_healthy)
    inter_healthy = bool(healthy_flags) and all(healthy_flags)

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

    # interaction: 满分 25，在可得维度间按原权重比例重分配（issue #61）
    avail_weights: dict[str, float] = {}
    if _is_available(zaikan_status):
        avail_weights["zaikan"] = _INTER_WEIGHTS["zaikan"]
    if _is_available(share_status):
        avail_weights["share"] = _INTER_WEIGHTS["share"]
    if _is_available(comment_status):
        avail_weights["comment"] = _INTER_WEIGHTS["comment"]

    if not avail_weights:
        inter_score = 0.0
    else:
        w_sum = sum(avail_weights.values())
        inter_points = 0.0
        if "zaikan" in avail_weights and zaikan_healthy:
            inter_points += _INTER_MAX * avail_weights["zaikan"] / w_sum
        if "share" in avail_weights and share_healthy:
            inter_points += _INTER_MAX * avail_weights["share"] / w_sum
        if "comment" in avail_weights and comment_healthy:
            inter_points += _INTER_MAX * avail_weights["comment"] / w_sum
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

    # analysis：不可得维度不打印百分比（issue #61）
    analysis = _build_interaction_analysis(
        read_median=read_median,
        read_avg=read_avg,
        read_max=read_max,
        share_m=share_m,
        zaikan_m=zaikan_m,
        comment_m=comment_m,
        share_status=share_status,
        zaikan_status=zaikan_status,
        comment_status=comment_status,
        avail_weights=avail_weights,
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
            "zaikan_status": zaikan_status,
            "share_status": share_status,
            "comment_status": comment_status,
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
            "inter_score": inter_score,
        },
    }


def _status_reason(status: str) -> str:
    if status == "platform_not_provided":
        return "平台未提供"
    if status == "fetch_missing":
        return "本次未采到"
    if status == "not_applicable":
        return "不适用"
    return status


def _build_interaction_analysis(
    *,
    read_median: float,
    read_avg: float,
    read_max: float,
    share_m: float | None,
    zaikan_m: float | None,
    comment_m: float | None,
    share_status: str,
    zaikan_status: str,
    comment_status: str,
    avail_weights: dict[str, float],
) -> str:
    head = f"中位{int(read_median)}、均值{int(read_avg)}、最大{int(read_max)}；"
    parts: list[str] = []
    missing: list[str] = []

    if _is_available(share_status) and share_m is not None:
        parts.append(f"分享中位{share_m * 100:.1f}%")
    else:
        missing.append(f"分享{_status_reason(share_status)}")

    if _is_available(comment_status) and comment_m is not None:
        parts.append(f"评论{comment_m * 100:.1f}%")
    else:
        missing.append(f"评论{_status_reason(comment_status)}")

    if _is_available(zaikan_status) and zaikan_m is not None:
        parts.append(f"在看{zaikan_m * 100:.1f}%")
    else:
        missing.append(f"在看{_status_reason(zaikan_status)}")

    if not avail_weights:
        body = "互动维度整体不可得，互动分不计分。"
    else:
        body = "、".join(parts)
        if missing:
            if body:
                body += f"；{'、'.join(missing)}。"
            else:
                body = "、".join(missing) + "。"
        elif body:
            body += "。"
        else:
            body = "互动样本不足。"

    return head + body
