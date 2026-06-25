from __future__ import annotations

from typing import Any


def build_action_plan_v2(
    viral_genes: dict[str, Any],
    checkup: dict[str, Any],
    content_engine: dict[str, Any],
    audience_mod: dict[str, Any],
    growth_funnel: dict[str, Any],
) -> dict[str, Any]:
    now: list[str] = []
    experiment: list[str] = []
    hold: list[str] = []

    for mod in (checkup, content_engine, audience_mod, growth_funnel):
        basket = mod.get("action_basket", "experiment")
        act = (mod.get("action") or "")[:25]
        if not act:
            continue
        if basket == "now":
            now.append(act)
        elif basket == "experiment":
            experiment.append(act)
        else:
            hold.append(act)

    # also consider viral_genes implicitly via next
    vf = (viral_genes or {}).get("viral_formula", {}) or {}
    topic = vf.get("topic") or "风险/账号/额度焦虑"
    pat = vf.get("title_pattern") or "风险损失型"
    hr = vf.get("timing_hour") or 10
    reliable = bool(vf.get("reliable", False))
    suffix = "" if reliable else " (待验证)"
    next_topics = [
        f"{topic}{suffix} + {pat}标题 + {hr}点窗口",
        "工作流深读文 + 22点验证",
    ][:2]

    analysis = "按各模块篮子归集行动；下周选题来自 viral_formula。"
    chart_payload = {
        "kind": "action_baskets_v2",
        "now": now,
        "experiment": experiment,
        "hold": hold,
    }

    return {
        "now": now,
        "experiment": experiment,
        "hold": hold,
        "next_topics": next_topics,
        "analysis": analysis,
        "chart_payload": chart_payload,
    }
