from __future__ import annotations

from typing import Any

from analyze.confidence import (
    action_basket_for_confidence,
    confidence_for_records,
    emphasis_for_confidence,
    voice_for_confidence,
)
from analyze.stats import median


def _approx_weekly_shares(stable: list[dict[str, Any]]) -> float:
    if not stable:
        return 0.0
    total = sum(int(r.get("shares", 0) or 0) for r in stable)
    # approximate weeks: use rough 4-5 based on typical; fallback count-based
    n = len(stable)
    weeks = max(1.0, n / 5.0)
    return round(total / weeks, 1)


def build_growth_funnel(
    stable: list[dict[str, Any]],
    audience_raw: dict[str, Any],
    trend_raw: dict[str, Any],
    viral_formula: dict[str, Any],
) -> dict[str, Any]:
    aud_avail = bool(audience_raw.get("available"))
    trend_avail = bool(trend_raw.get("available"))
    data_available = aud_avail and trend_avail

    conf = confidence_for_records(stable, note="growth_funnel")
    voice = voice_for_confidence(conf)
    emphasis = emphasis_for_confidence(voice)
    basket = action_basket_for_confidence(voice)

    netgain_trend: list[dict[str, Any]] = []
    if aud_avail:
        for d in audience_raw.get("daily", []) or []:
            netgain_trend.append({
                "date": d.get("date"),
                "netgain": int(d.get("netgain", 0) or 0),
                "cumulate": int(d.get("cumulate", 0) or 0),
            })

    # share_to_fan approx
    net_7d = int((audience_raw.get("summary") or {}).get("netgain_7d", 0) or 0) if aud_avail else 0
    weekly_share_approx = _approx_weekly_shares(stable)
    if weekly_share_approx > 0:
        share_to_fan_rate = round(net_7d / weekly_share_approx, 4)
    else:
        share_to_fan_rate = 0.0

    # open_rate_approx
    total_reads = sum(int(r.get("reads", 0) or 0) for r in stable) if stable else 0
    cumulate = int(audience_raw.get("cumulate_user", 0) or 0) if aud_avail else 0
    if cumulate > 0:
        open_rate_approx = round(total_reads / cumulate, 4)
    else:
        open_rate_approx = 0.0

    # startup_plan 4 weeks, use viral + median target
    read_median = 0
    if stable:
        reads = [int(r.get("reads", 0) or 0) for r in stable]
        read_median = int(median(reads)) if reads else 0
    topic = viral_formula.get("topic") or "风险/账号/额度焦虑"
    pattern = viral_formula.get("title_pattern") or "风险损失型"
    hour = viral_formula.get("timing_hour") or 10
    reliable = bool(viral_formula.get("reliable"))
    focus_base = topic
    if not reliable:
        focus_base = f"{topic}(待验证)"

    startup_plan = []
    targets = [read_median, int(read_median * 1.1), int(read_median * 1.2), int(read_median * 1.15)]
    for i in range(1, 5):
        wk = {
            "week": i,
            "focus": focus_base,
            "topics": f"{topic} + {pattern}标题，{hour}点附近",
            "target": max(50, targets[i-1]) if targets[i-1] else 120,
        }
        startup_plan.append(wk)

    # analysis etc
    if not data_available:
        analysis = "audience 或 trend 数据缺失，漏斗仅用文章数据近似。"
        conclusion = "启动计划基于历史中位，待数据补全后校准。"
        action = "补充 raw 数据后重跑，验证转化。"
    else:
        analysis = f"7天净增{net_7d}，近似分享转化率{share_to_fan_rate:.2%}；打开率近似{open_rate_approx:.2%}。"
        if voice == "high":
            conclusion = "分享→净增转化可追踪，启动计划按爆款公式排。"
        else:
            conclusion = "净增与分享口径近似，建议持续跟踪。"
        action = "按4周计划执行，复盘净增与分享率。"

    return {
        "data_available": data_available,
        "share_to_fan_rate": share_to_fan_rate,
        "netgain_trend": netgain_trend,
        "open_rate_approx": open_rate_approx,
        "startup_plan": startup_plan,
        "analysis": analysis,
        "conclusion": conclusion,
        "action": action,
        "voice": voice,
        "emphasis": emphasis,
        "action_basket": basket,
        "chart_payload": {
            "kind": "growth_funnel",
            "data_available": data_available,
            "netgain_trend_len": len(netgain_trend),
            "startup_plan": startup_plan,
        },
    }
