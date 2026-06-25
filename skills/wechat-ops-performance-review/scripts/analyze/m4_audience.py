from __future__ import annotations

from typing import Any

from analyze.confidence import (
    action_basket_for_confidence,
    confidence_for_records,
    emphasis_for_confidence,
    voice_for_confidence,
)


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

    if not available:
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
        fans_portrait_available = False
    else:
        city = (audience_raw.get("city") or [])[:10]
        age = audience_raw.get("age") or []
        gender = audience_raw.get("gender") or {}
        user_source = audience_raw.get("user_source") or []
        analysis = f"粉丝主要城市{city[0]['name'] if city else '未知'}，年龄段{age[0]['range'] if age else '未知'}占比高。"
        if voice == "high":
            conclusion = "画像集中高线城市与中青年，来源搜索与分享为主。"
        else:
            conclusion = "画像以中青年搜索用户为主，内容匹配搜索意图。"
        action = "标题与封面强化搜索词与本地化标签。"
        fans_portrait_available = True

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
