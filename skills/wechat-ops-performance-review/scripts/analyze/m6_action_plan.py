from __future__ import annotations

from typing import Any


def build_action_plan_v2(
    viral_genes: dict[str, Any],
    checkup: dict[str, Any],
    content_engine: dict[str, Any],
    audience_mod: dict[str, Any],
    growth_funnel: dict[str, Any],
) -> dict[str, Any]:
    """构建 v2 行动计划三栏。

    红线：
    - 键名固定为 now/experiment/hold（dashboard 硬依赖：现在就做/小步验证/暂不拍板）
    - 置信度只内化，不外显；lane 是行动时间/试探档位
    - 确定性：使用位置角色 + 显式处理顺序，不依赖 set/dict 迭代

    lane 分配规则（按模块角色定基准，置信度只能下调至更试探方向，不能上调）：
    - checkup（健康度/风险，即时行动）：基准 "now"；低置信 → "experiment"
    - content_engine（内容配比）：高置信 → "now"，否则 "experiment"
    - audience_mod（标题/封面/搜索词，可测试微调）：基准 "experiment"；低置信 → "hold"
    - growth_funnel（多周计划，长周期）：基准 "hold"
    置信档从模块的 action_basket 反推：now=高 / experiment=中 / hold=低。
    因此全高置信时也必然跨 ≥2 条 lane（growth 恒 hold、audience 基准 experiment）。
    """
    now: list[str] = []
    experiment: list[str] = []
    hold: list[str] = []

    def _infer_conf_tier(mod: dict[str, Any]) -> str:
        """从模块保留的 action_basket 反推置信档（不改变模块自身数据）。"""
        b = mod.get("action_basket", "experiment")
        if b == "now":
            return "high"
        if b == "hold":
            return "low"
        return "medium"

    def _decide_lane(role: str, mod: dict[str, Any]) -> str:
        tier = _infer_conf_tier(mod)
        if role == "checkup":
            # 即时 → 基准 now，低才下调
            return "experiment" if tier == "low" else "now"
        if role == "content_engine":
            # 配比 → 高才 now，否则 experiment
            return "now" if tier == "high" else "experiment"
        if role == "audience_mod":
            # 可微调测试 → 基准 experiment，低才 hold
            return "hold" if tier == "low" else "experiment"
        if role == "growth_funnel":
            # 长周期 → 恒 hold
            return "hold"
        return "experiment"

    # 显式按角色顺序处理（位置已知角色），保证确定性与跨 lane
    role_mod_pairs: list[tuple[str, dict[str, Any]]] = [
        ("checkup", checkup),
        ("content_engine", content_engine),
        ("audience_mod", audience_mod),
        ("growth_funnel", growth_funnel),
    ]
    for role, mod in role_mod_pairs:
        act = (mod.get("action") or "")[:25]
        if not act:
            continue
        lane = _decide_lane(role, mod)
        if lane == "now":
            now.append(act)
        elif lane == "experiment":
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

    analysis = "按各模块篮子归集行动；下周选题由爆款基因反推得出。"
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
