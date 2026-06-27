from __future__ import annotations

from typing import Any

from analyze.confidence import (
    action_basket_for_confidence,
    confidence_for_records,
    emphasis_for_confidence,
    voice_for_confidence,
)


def build_content_engine(
    stable: list[dict[str, Any]], by_content_type: list[dict[str, Any]], benchmark: dict[str, Any]
) -> dict[str, Any]:
    if not by_content_type or not stable:
        conf = confidence_for_records([], note="content_engine")
        voice = voice_for_confidence(conf)
        return {
            "by_topic": [],
            "pull_topics": [],
            "mind_topics": [],
            "recommended_ratio": [],
            "analysis": "无稳定样本或分组数据。",
            "conclusion": "样本不足，无法给出内容引擎建议。",
            "action": "积累更多文章后复盘类型表现。",
            "voice": voice,
            "emphasis": emphasis_for_confidence(voice),
            "action_basket": action_basket_for_confidence(voice),
            "chart_payload": {"kind": "content_engine", "by_topic": []},
        }

    # enrich by_topic from input
    by_topic = []
    for row in by_content_type:
        by_topic.append({
            "key": row.get("key"),
            "median": row.get("median", 0),
            "share_rate_avg": row.get("share_rate_avg", 0),
            "comment_rate_avg": row.get("comment_rate_avg", 0),
            "count": row.get("count", 0),
        })

    # pull new: top by share_rate_avg (拉新)
    sorted_share = sorted(by_topic, key=lambda r: (r["share_rate_avg"], r["median"]), reverse=True)
    pull_topics = [r["key"] for r in sorted_share[:3] if r["share_rate_avg"] > 0][:3]
    if not pull_topics:
        pull_topics = [r["key"] for r in sorted_share[:2]]

    # mind build: top by comment_rate or median as proxy (建心智)
    sorted_comment = sorted(by_topic, key=lambda r: (r["comment_rate_avg"], r["median"]), reverse=True)
    mind_topics = [r["key"] for r in sorted_comment[:3] if r.get("comment_rate_avg", 0) > 0][:3]
    if not mind_topics:
        mind_topics = [r["key"] for r in sorted(by_topic, key=lambda r: r["median"], reverse=True)[:2]]

    # recommended_ratio: based on median performance, normalize
    medians = [(r["key"], max(0.0, float(r.get("median", 0) or 0))) for r in by_topic]
    total_med = sum(m for _, m in medians) or 1.0
    recommended_ratio = []
    for key, m in sorted(medians, key=lambda x: x[1], reverse=True):
        ratio = round(m / total_med, 4) if total_med > 0 else 0
        recommended_ratio.append({"topic": key, "ratio": ratio})

    # conf
    conf = confidence_for_records(stable, note="content_engine")
    voice = voice_for_confidence(conf)
    emphasis = emphasis_for_confidence(voice)
    basket = action_basket_for_confidence(voice)

    # conclusion / analysis
    top_pull = pull_topics[0] if pull_topics else "未知"
    # 心智题材取评论率最高且与拉新题材不同的(避免同一题材既当拉新又当心智,结论矛盾)
    _mind_diff = [r["key"] for r in sorted_comment if r["key"] != top_pull]
    top_mind = _mind_diff[0] if _mind_diff else (mind_topics[0] if mind_topics else "未知")
    analysis = f"拉新靠分享率高的{top_pull}，心智靠评论高的{top_mind}。"
    if voice == "high":
        conclusion = f"把{top_pull}当拉新入口，{top_mind}当心智主线。"
    elif voice == "low":
        conclusion = "初步迹象显示分享高与评论高的题材值得多配比。"
    else:
        conclusion = f"建议拉新题材优先{top_pull}，建心智题材优先{top_mind}。"

    if voice == "high":
        action = "按推荐配比调整下周内容比例，追踪分享率。"
    else:
        action = "小步验证分享率高的题材配比，提升1-2周。"

    return {
        "by_topic": by_topic,
        "pull_topics": pull_topics,
        "mind_topics": mind_topics,
        "recommended_ratio": recommended_ratio,
        "analysis": analysis,
        "conclusion": conclusion,
        "action": action,
        "voice": voice,
        "emphasis": emphasis,
        "action_basket": basket,
        "chart_payload": {
            "kind": "content_engine",
            "pull_topics": pull_topics,
            "mind_topics": mind_topics,
            "recommended_ratio": recommended_ratio,
        },
    }
