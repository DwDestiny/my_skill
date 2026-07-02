from __future__ import annotations

from typing import Any

from analyze.confidence import (
    action_basket_for_confidence,
    confidence_for_records,
    emphasis_for_confidence,
    voice_for_confidence,
)


def _first_name(items: Any) -> str | None:
    """Return items[0]['name'] only if items is non-empty list of dicts with str name, else None."""
    if isinstance(items, list) and len(items) > 0 and isinstance(items[0], dict):
        name = items[0].get("name")
        if isinstance(name, str):
            return name
    return None


def _first_range(items: Any) -> str | None:
    """Return items[0]['range'] only if items is non-empty list of dicts with str range, else None."""
    if isinstance(items, list) and len(items) > 0 and isinstance(items[0], dict):
        rng = items[0].get("range")
        if isinstance(rng, str):
            return rng
    return None


def build_audience(
    stable: list[dict[str, Any]],
    audience_raw: dict[str, Any],
    by_pain: list[dict[str, Any]],
    by_persona: list[dict[str, Any]],
) -> dict[str, Any]:
    available = bool(audience_raw.get("available"))

    conf = confidence_for_records(stable, note="audience")
    voice = voice_for_confidence(conf)
    emphasis = emphasis_for_confidence(voice)
    basket = action_basket_for_confidence(voice)

    # 先做类型规整：畸形数据（JS 代码字符串、非 dict 条目）一律过滤掉
    raw_city = audience_raw.get("city")
    raw_age = audience_raw.get("age")
    raw_user_source = audience_raw.get("user_source")
    city = [c for c in (raw_city if isinstance(raw_city, list) else []) if isinstance(c, dict)][:10]
    age = [a for a in (raw_age if isinstance(raw_age, list) else []) if isinstance(a, dict)]
    gender = audience_raw.get("gender") if isinstance(audience_raw.get("gender"), dict) else {}
    user_source = [u for u in (raw_user_source if isinstance(raw_user_source, list) else []) if isinstance(u, dict)]

    # #27: "有画像"定义为过滤后至少一个维度非空,而非信任原始 available 标志
    has_renderable_dim = bool(city or age or gender or user_source)
    fans_portrait_available = available and has_renderable_dim

    if not fans_portrait_available:
        # degrade, use article side only
        if voice != "low":
            emphasis = "secondary"
        city = []
        age = []
        gender = {}
        user_source = []
        analysis = "粉丝后台数据不可得，仅用文章标签推断人群。"
        conclusion = "以文章标签人群为主，补充粉丝来源数据后可细化。"
        action = "通过登录后台补充 audience 抓取，复盘真实画像。"
    else:
        c0 = _first_name(city)
        a0 = _first_range(age)
        analysis = f"粉丝主要城市{c0 if c0 else '未知'}，年龄段{a0 if a0 else '未知'}占比高。"
        if voice == "high":
            conclusion = "画像集中高线城市与中青年，来源搜索与分享为主。"
        else:
            conclusion = "画像以中青年搜索用户为主，内容匹配搜索意图。"
        action = "标题与封面强化搜索词与本地化标签。"

    # article side always
    pain_points = [{"key": r.get("key"), "count": r.get("count"), "median": r.get("median"), "share_rate_avg": r.get("share_rate_avg")} for r in (by_pain or [])]
    personas = [{"key": r.get("key"), "count": r.get("count"), "median": r.get("median"), "share_rate_avg": r.get("share_rate_avg")} for r in (by_persona or [])]

    return {
        "fans_portrait_available": fans_portrait_available,
        "city": city,
        "age": age,
        "gender": gender,
        "user_source": user_source,
        "pain_points": pain_points,
        "personas": personas,
        "analysis": analysis,
        "conclusion": conclusion,
        "action": action,
        "voice": voice,
        "emphasis": emphasis,
        "action_basket": basket,
        "chart_payload": {
            "kind": "audience",
            "fans_portrait_available": fans_portrait_available,
            "city": city,
            "age": age,
            "gender": gender,
            "user_source": user_source,
        },
    }
