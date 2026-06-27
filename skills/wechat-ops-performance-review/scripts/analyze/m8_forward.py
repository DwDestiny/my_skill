"""m8_forward.py — 向前看引擎（Direction Engine v1）

按 DATA_CONTRACT.md 契约产出 forward_looking 节点。
入口：build_forward_looking(dataset) -> dict

设计原则：
- 纯 Python stdlib，无第三方依赖。
- 价值中立：不判方向优劣，feasibility 只衡量改造成本。
- 置信内化：不输出"置信度"三字，不输出裸英文 key/桶代码。
- demo 不是 spec：题材维度从 CONTENT_TYPES 实际命中项动态生成。
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from statistics import median as _median
from typing import Any


# ───────────────────────────── 常量 ──────────────────────────────────────────

ENGINE_VERSION = "direction-engine-v1"
ENGINE_MODEL_NAME = "动态方向推导引擎（方向 = f(历史文章现状)）"

ARTICLE_THRESHOLD = 15          # 文章数闸门
GAP_THRESHOLD_DAYS = 30         # 断更天数闸门
MISSING_RATE_THRESHOLD = 0.4    # 关键字段缺失率闸门

FIRST_PERSON_WORDS = re.compile(r"[我咱]们?|本人|笔者")
PERSONAL_STORY_PATTERNS = re.compile(
    r"我的|我[曾已]|亲历|亲测|复盘|这一年|踩坑|我踩|我遇|我发现|自己|分享我|记录一下"
)
METHOD_DENSITY_PATTERNS = re.compile(
    r"步骤|方法|案例|拆解|清单|攻略|教程|指南|怎么|如何|思路|路径|流程|手把手"
)
MONETIZATION_KEYWORDS = re.compile(
    r"微信|二维码|加群|扫码|领取|星球|咨询|付费|私信|报名|入门课|训练营"
)

# 七大类底池（固定，不是菜单）
ARCHETYPES = [
    "资讯流量型",
    "人设IP型",
    "知识服务型",
    "垂直专家型",
    "产品品牌型",
    "带货电商型",
    "社群情感型",
]

# 五推导模式
MODES = {
    "顺势放大": "顺势放大",
    "转型升级": "转型升级",
    "收窄聚焦": "收窄聚焦",
    "跨类迁移": "跨类迁移",
    "混合演进": "混合演进",
}

# 固定五角色
MATRIX_ROLES = ["拉新", "养信任", "建专业", "转化", "留存"]


# ───────────────────────── 工具函数 ──────────────────────────────────────────

def _safe_median(values: list[float]) -> float:
    vals = [v for v in values if v is not None]
    if not vals:
        return 0.0
    return float(_median(vals))


def _safe_mean(values: list[float]) -> float:
    vals = [v for v in values if v is not None]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def _days_since(dt_str: str | None, as_of: str | datetime | None = None) -> int | None:
    """返回 dt_str 相对 as_of 的天数；as_of=None 时用真实 now；失败返回 None。"""
    if not dt_str:
        return None
    try:
        from zoneinfo import ZoneInfo
        cn_tz = ZoneInfo("Asia/Shanghai")
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=cn_tz)
        if as_of is None:
            now = datetime.now(tz=cn_tz)
        else:
            if isinstance(as_of, datetime):
                now = as_of
            else:
                now = datetime.fromisoformat(str(as_of).replace("Z", "+00:00"))
            if now.tzinfo is None:
                now = now.replace(tzinfo=cn_tz)
        return max(0, (now.date() - dt.date()).days)
    except Exception:
        # 解析失败时回退真实 now 计算（尽力而为）
        try:
            from zoneinfo import ZoneInfo
            cn_tz = ZoneInfo("Asia/Shanghai")
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=cn_tz)
            now = datetime.now(tz=cn_tz)
            return max(0, (now.date() - dt.date()).days)
        except Exception:
            return None


def _missing_rate(articles: list[dict[str, Any]], fields: list[str]) -> float:
    """关键字段缺失率（任一缺失算缺失）。"""
    if not articles:
        return 1.0
    missing = sum(
        1 for a in articles
        if any(a.get(f) is None for f in fields)
    )
    return missing / len(articles)


def _hhi(distribution: list[float]) -> float:
    """Herfindahl-Hirschman Index，衡量集中度。0-1，越高越集中。"""
    total = sum(distribution)
    if total <= 0:
        return 0.0
    return sum((v / total) ** 2 for v in distribution)


# ───────────────────────── §3 数据充分性闸门 ─────────────────────────────────

def build_data_sufficiency(dataset: dict[str, Any]) -> dict[str, Any]:
    stable = dataset.get("articles", {}).get("stable", [])
    non_deleted = dataset.get("articles", {}).get("all_period", [])

    # 优先用 stable，不足时尝试回退 non_deleted
    article_count = len(stable)
    fallback_note = None
    if article_count < ARTICLE_THRESHOLD and len(non_deleted) >= ARTICLE_THRESHOLD:
        article_count = len(non_deleted)
        fallback_note = f"稳定样本仅 {len(stable)} 篇，已回退到含未成熟文章的全期样本（{article_count} 篇）"

    # 最近发布距今天数 —— 以 meta 的 source_captured_at / generated_at 为基准（fixtures 采集日）
    all_articles = stable or non_deleted
    dates = [a.get("published_at") for a in all_articles if a.get("published_at")]
    recent_gap_days: int | None = None
    meta = dataset.get("meta", {}) or {}
    as_of = meta.get("source_captured_at") or meta.get("generated_at")
    if dates:
        latest_date = max(dates)
        recent_gap_days = _days_since(latest_date, as_of=as_of)

    # 关键字段缺失率
    key_fields = ["reads", "published_at"]
    miss_rate = _missing_rate(stable or non_deleted, key_fields)

    reasons: list[str] = []
    if article_count < ARTICLE_THRESHOLD:
        reasons.append(f"稳定样本仅 {len(stable)} 篇，不足 {ARTICLE_THRESHOLD} 篇")
    if recent_gap_days is not None and recent_gap_days > GAP_THRESHOLD_DAYS:
        reasons.append(f"最近一次发布距今 {recent_gap_days} 天，超过断更阈值 {GAP_THRESHOLD_DAYS} 天")
    if miss_rate > MISSING_RATE_THRESHOLD:
        reasons.append(f"关键字段（reads/published_at）缺失率 {miss_rate:.0%}，超过 {MISSING_RATE_THRESHOLD:.0%}")
    if fallback_note:
        reasons.append(fallback_note)

    passed = len(reasons) == 0

    if passed:
        statement = f"样本充足（{article_count} 篇稳定样本），可进行方向推导。"
    else:
        statement = "样本还太少，先把现状照清楚；补够数据后再推导方向。"

    return {
        "passed": passed,
        "article_count": article_count,
        "threshold": ARTICLE_THRESHOLD,
        "recent_gap_days": recent_gap_days,
        "gap_threshold_days": GAP_THRESHOLD_DAYS,
        "reasons": reasons,
        "statement": statement,
    }


# ───────────────────────── §4 六类信号 ───────────────────────────────────────

def _topic_distribution_signal(dataset: dict[str, Any]) -> dict[str, Any]:
    """4.1 题材分布与集中度（直接可算）。"""
    by_ct = dataset.get("analysis", {}).get("by_content_type", [])
    total = sum(row.get("count", 0) for row in by_ct)

    distribution = []
    for row in by_ct:
        count = row.get("count", 0)
        if count > 0:
            distribution.append({
                "type": row["key"],
                "count": count,
                "share": round(count / total, 3) if total > 0 else 0,
            })

    # 按占比排序
    distribution.sort(key=lambda x: x["share"], reverse=True)

    counts = [d["count"] for d in distribution]
    hhi = round(_hhi(counts), 3)

    main_axis = distribution[0]["type"] if distribution else "未知"
    top_share = distribution[0]["share"] if distribution else 0

    # level 判定：HHI > 0.5 且主轴占比 > 50% → 强；HHI > 0.3 → 中；否则弱
    if hhi > 0.5 and top_share > 0.5:
        level = "强"
    elif hhi > 0.3:
        level = "中"
    else:
        level = "弱"

    return {
        "key": "topic_distribution",
        "name": "题材分布与集中度",
        "reads_as": "这个号实际在写什么、主轴清不清晰",
        "computability": "直接可算",
        "level": level,
        "detail": {
            "distribution": distribution,
            "hhi": hhi,
            "main_axis": main_axis,
            "top_share": top_share,
            "total_articles": total,
        },
    }


def _viral_type_signal(dataset: dict[str, Any]) -> dict[str, Any]:
    """4.2 爆款类型（直接可算，受样本约束）。"""
    vf = dataset.get("viral_genes", {}).get("viral_formula", {})
    sample_count = vf.get("sample_count", 0)
    reliable = vf.get("reliable", False)

    # level：reliable 且 sample_count>=3 → 中；否则弱
    if reliable and sample_count >= 5:
        level = "强"
    elif reliable:
        level = "中"
    else:
        level = "弱"

    return {
        "key": "viral_type",
        "name": "爆款类型",
        "reads_as": "哪类内容在这个号上能打穿推荐流",
        "computability": "直接可算",
        "level": level,
        "detail": {
            "topic": vf.get("topic"),
            "title_pattern": vf.get("title_pattern"),
            "sample_count": sample_count,
            "reliable": reliable,
            "evidence_titles": vf.get("evidence_titles", [])[:3],
        },
    }


def _interaction_signal(dataset: dict[str, Any]) -> dict[str, Any]:
    """4.3 互动结构（直接可算）。"""
    stable = dataset.get("articles", {}).get("stable", [])
    if not stable:
        return {
            "key": "interaction",
            "name": "互动结构",
            "reads_as": "读者以哪种行为回应这个号：传播、评论还是点赞",
            "computability": "直接可算",
            "level": "弱",
            "detail": {"share_rate": 0, "comment_rate": 0, "like_rate": 0, "dominant": "未知"},
        }

    share_rates = [a.get("share_rate", 0) or 0 for a in stable]
    comment_rates = [a.get("comment_rate", 0) or 0 for a in stable]
    like_rates = [a.get("like_rate", 0) or 0 for a in stable]

    avg_share = round(_safe_mean(share_rates), 4)
    avg_comment = round(_safe_mean(comment_rates), 4)
    avg_like = round(_safe_mean(like_rates), 4)

    # 主导项：相对高低
    rates = {"分享": avg_share, "评论": avg_comment, "点赞": avg_like}
    dominant = max(rates, key=lambda k: rates[k])

    # level：分享率均值 > 0.03 → 强（强传播信号）；> 0.015 → 中；否则弱
    if avg_share > 0.03:
        level = "强"
    elif avg_share > 0.015:
        level = "中"
    else:
        level = "弱"

    return {
        "key": "interaction",
        "name": "互动结构",
        "reads_as": "读者以哪种行为回应这个号：传播、评论还是点赞",
        "computability": "直接可算",
        "level": level,
        "detail": {
            "share_rate": avg_share,
            "comment_rate": avg_comment,
            "like_rate": avg_like,
            "dominant": dominant,
        },
    }


def _originality_signal(dataset: dict[str, Any]) -> dict[str, Any]:
    """4.4 原创比例与人味浓度（正则近似）。"""
    stable = dataset.get("articles", {}).get("stable", [])
    # 只在有正文的子集算
    with_text = [a for a in stable if (a.get("article_length_chars") or 0) > 0]
    coverage = len(with_text) / len(stable) if stable else 0

    if not with_text:
        return {
            "key": "originality",
            "name": "原创比例与人味浓度",
            "reads_as": "内容有没有作者本人的判断、经历和立场",
            "computability": "正则近似",
            "level": "弱",
            "detail": {
                "coverage": 0,
                "coverage_note": "无正文匹配，无法估算",
                "first_person_density": "未知（近似）",
                "personal_story_ratio": "未知（近似）",
            },
        }

    # 第一人称密度
    fp_articles = 0
    story_articles = 0
    for a in with_text:
        title = a.get("title", "") or ""
        digest = a.get("digest", "") or ""
        text = title + digest  # digest 作为正文近似替代

        if FIRST_PERSON_WORDS.search(title) or FIRST_PERSON_WORDS.search(digest):
            fp_articles += 1
        if PERSONAL_STORY_PATTERNS.search(title) or PERSONAL_STORY_PATTERNS.search(digest):
            story_articles += 1

    fp_ratio = fp_articles / len(with_text)
    story_ratio = story_articles / len(with_text)

    def _tier(r: float) -> str:
        if r > 0.4:
            return "高（近似）"
        elif r > 0.15:
            return "中（近似）"
        return "低（近似）"

    # level：人味高 → 强；有一定人味 → 中；否则弱
    if fp_ratio > 0.4 or story_ratio > 0.3:
        level = "强"
    elif fp_ratio > 0.15 or story_ratio > 0.1:
        level = "中"
    else:
        level = "弱"

    return {
        "key": "originality",
        "name": "原创比例与人味浓度",
        "reads_as": "内容有没有作者本人的判断、经历和立场",
        "computability": "正则近似",
        "level": level,
        "detail": {
            "coverage": round(coverage, 2),
            "coverage_note": f"仅 {len(with_text)} 篇匹配到正文（占 {coverage:.0%}），结论为近似估算",
            "first_person_density": _tier(fp_ratio),
            "personal_story_ratio": _tier(story_ratio),
        },
    }


def _timeliness_depth_signal(dataset: dict[str, Any]) -> dict[str, Any]:
    """4.5 时效结构与篇幅厚度（正则近似）。"""
    stable = dataset.get("articles", {}).get("stable", [])
    with_text = [a for a in stable if (a.get("article_length_chars") or 0) > 0]

    # 篇幅中位（直接可算）
    lengths = [a["article_length_chars"] for a in with_text]
    median_length = int(_safe_median(lengths)) if lengths else 0

    # 方法/案例密度（正则近似，扫标题+摘要）
    method_hits = 0
    total_for_method = len(stable)
    for a in stable:
        title = a.get("title", "") or ""
        digest = a.get("digest", "") or ""
        if METHOD_DENSITY_PATTERNS.search(title) or METHOD_DENSITY_PATTERNS.search(digest):
            method_hits += 1

    method_ratio = method_hits / total_for_method if total_for_method else 0

    def _method_tier(r: float) -> str:
        if r > 0.4:
            return "高（近似）"
        elif r > 0.2:
            return "中（近似）"
        return "低（近似）"

    # 时效：题材近似——标题含时效词 或 content_type 名称含情报/发布/热点类词（不写死具体桶名）
    timely_keywords = re.compile(r"发布|更新|情报|速递|最新|限时|本周|今日|今天|即将|已上线|新版")
    timely_ct = re.compile(r"情报|发布|热点|更新|限时|最新|风险|额度")
    timely_articles = sum(
        1 for a in stable
        if timely_keywords.search(a.get("title", "") or "")
        or timely_ct.search(a.get("content_type", "") or "")
    )
    hotspot_ratio = round(timely_articles / len(stable), 2) if stable else 0

    # level：厚度≥2000 且方法密度中 → 强；厚度适中 → 中；否则弱
    if median_length >= 2000 and method_ratio > 0.2:
        level = "强"
    elif median_length >= 1000 or method_ratio > 0.2:
        level = "中"
    else:
        level = "弱"

    return {
        "key": "timeliness_depth",
        "name": "时效结构与篇幅厚度",
        "reads_as": "内容是追热点快销还是建方法沉淀",
        "computability": "正则近似",
        "level": level,
        "detail": {
            "median_length": median_length,
            "hotspot_ratio": hotspot_ratio,
            "method_density": _method_tier(method_ratio),
        },
    }


def _capacity_funnel_signal(dataset: dict[str, Any]) -> dict[str, Any]:
    """4.6 产能底盘与变现链路痕迹（正则近似）。"""
    profile = dataset.get("account_profile", {})
    account = dataset.get("account", {})
    stable = dataset.get("articles", {}).get("stable", [])

    posts_per_week = profile.get("publish_frequency", 0) or 0
    fans = account.get("cumulate_user") or profile.get("fans_count")

    # 变现痕迹（正则近似，扫标题+摘要）
    mono_hits = 0
    for a in stable:
        title = a.get("title", "") or ""
        digest = a.get("digest", "") or ""
        if MONETIZATION_KEYWORDS.search(title) or MONETIZATION_KEYWORDS.search(digest):
            mono_hits += 1

    if mono_hits >= 3:
        monetization_trace = "有"
    elif mono_hits >= 1:
        monetization_trace = "疑似"
    else:
        monetization_trace = "无"

    # level：产能稳定(≥3篇/周)且有粉丝基础 → 强；有一定产能 → 中；否则弱
    if posts_per_week >= 3 and fans and fans >= 5000:
        level = "强"
    elif posts_per_week >= 1.5 or (fans and fans >= 1000):
        level = "中"
    else:
        level = "弱"

    return {
        "key": "capacity_funnel",
        "name": "产能底盘与变现链路痕迹",
        "reads_as": "这个号能不能稳定供内容、有没有在试水变现",
        "computability": "正则近似",
        "level": level,
        "detail": {
            "posts_per_week": round(posts_per_week, 1),
            "fans": fans,
            "monetization_trace": monetization_trace,
        },
    }


def build_signals(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """组装六类信号，顺序固定。"""
    return [
        _topic_distribution_signal(dataset),
        _viral_type_signal(dataset),
        _interaction_signal(dataset),
        _originality_signal(dataset),
        _timeliness_depth_signal(dataset),
        _capacity_funnel_signal(dataset),
    ]


# ───────────────────────── §5 照镜子 ─────────────────────────────────────────

def build_mirror(signals: list[dict[str, Any]], dataset: dict[str, Any]) -> dict[str, Any]:
    """§5 照镜子：现状画像。"""
    by_sig = {s["key"]: s for s in signals}
    stable = dataset.get("articles", {}).get("stable", [])
    sample_n = len(stable)

    vf = dataset.get("viral_genes", {}).get("viral_formula", {})
    traffic_topic = vf.get("topic") or "未知"
    traffic_sample = vf.get("sample_count", 0)
    traffic_reliable = vf.get("reliable", False)

    # 主轴
    topic_dist = by_sig["topic_distribution"]["detail"]
    main_axis = topic_dist.get("main_axis", "未知")

    # 变现成熟度
    cap_detail = by_sig["capacity_funnel"]["detail"]
    mono = cap_detail.get("monetization_trace", "无")
    if mono == "有":
        monetization_maturity = "早期"
    else:
        monetization_maturity = "空白"

    # 互动主导
    inter_detail = by_sig["interaction"]["detail"]
    dominant = inter_detail.get("dominant", "分享")

    # 取向：分享率高 → 信任认同；否则 → 流量钩子
    avg_share = inter_detail.get("share_rate", 0)
    orientation_level = "强" if avg_share > 0.025 else "中"

    # 聚焦：HHI 大 → 聚焦
    hhi = topic_dist.get("hhi", 0)
    focus_level = "强" if hhi > 0.45 else ("中" if hhi > 0.3 else "弱")

    # 时效：hotspot_ratio 大 → 偏资讯
    tl_detail = by_sig["timeliness_depth"]["detail"]
    hotspot_ratio = tl_detail.get("hotspot_ratio", 0)
    timeliness_level = "强" if hotspot_ratio > 0.5 else ("中" if hotspot_ratio > 0.25 else "弱")

    # 厚度
    med_len = tl_detail.get("median_length", 0)
    depth_level = "强" if med_len >= 2000 else ("中" if med_len >= 800 else "弱")

    # 人味
    humanity_level = by_sig["originality"]["level"]

    # 情绪：个人经历篇比例 → 情绪共鸣；否则弱
    orig_detail = by_sig["originality"]["detail"]
    story_tier = orig_detail.get("personal_story_ratio", "低（近似）")
    emotion_level = "中" if "高" in story_tier or "中" in story_tier else "弱"

    axes = [
        {
            "key": "orientation",
            "label": "取向",
            "low": "流量钩子",
            "high": "信任认同",
            "level": orientation_level,
            "note": f"{dominant}率偏高" if dominant != "未知" else "",
        },
        {
            "key": "focus",
            "label": "聚焦",
            "low": "泛",
            "high": "单一主轴",
            "level": focus_level,
            "note": "",
        },
        {
            "key": "timeliness",
            "label": "时效",
            "low": "资讯",
            "high": "长青",
            "level": timeliness_level,
            "note": "近似" if hotspot_ratio > 0 else "",
        },
        {
            "key": "depth",
            "label": "厚度",
            "low": "轻薄",
            "high": "厚重方法",
            "level": depth_level,
            "note": "",
        },
        {
            "key": "humanity",
            "label": "人味",
            "low": "资产化",
            "high": "强人设",
            "level": humanity_level,
            "note": "近似",
        },
        {
            "key": "emotion",
            "label": "情绪",
            "low": "信息导向",
            "high": "情绪共鸣",
            "level": emotion_level,
            "note": "",
        },
    ]

    # 不确定注记
    uncertainty_parts = []
    if orig_detail.get("coverage", 0) < 0.5:
        uncertainty_parts.append("人味/厚度为正则近似，正文匹配率低")
    if not traffic_reliable:
        uncertainty_parts.append(f"流量命脉基于 {traffic_sample} 篇样本，属线索级")
    else:
        uncertainty_parts.append(f"流量命脉爆款锚点基于 {traffic_sample} 篇样本")
    uncertainty_note = "；".join(uncertainty_parts) + "。" if uncertainty_parts else ""

    # statement：中立陈述，带样本量和不确定性
    orient_word = "信任取向偏强" if orientation_level == "强" else "流量倾向中等"
    focus_word = "主轴清晰" if focus_level == "强" else ("聚焦中等" if focus_level == "中" else "题材偏散")
    depth_word = "厚度中上" if depth_level in ("强", "中") else "篇幅轻薄"
    humanity_word = f"人味{humanity_level}"
    mono_word = f"变现链路{monetization_maturity}"
    traffic_reliability_word = "" if traffic_reliable else "（样本偏少，仅作线索）"

    statement = (
        f"你现在是一个{focus_word}、{orient_word}、{depth_word}、{humanity_word}的号，"
        f"主轴是{main_axis}，"
        f"流量命脉来自{traffic_topic}{traffic_reliability_word}（基于 {sample_n} 篇样本），"
        f"{mono_word}。"
    )

    return {
        "statement": statement,
        "axes": axes,
        "main_axis": main_axis,
        "traffic_artery": {
            "topic": traffic_topic,
            "sample_count": traffic_sample,
            "reliable": traffic_reliable,
        },
        "monetization_maturity": monetization_maturity,
        "uncertainty_note": uncertainty_note,
    }


# ───────────────────────── §6 亲缘向量 ──────────────────────────────────────

def build_archetype_affinity(
    signals: list[dict[str, Any]],
    mirror: dict[str, Any],
) -> list[dict[str, Any]]:
    """§6 七大类底池亲缘向量。只列 affinity≠无 的原型。"""
    by_sig = {s["key"]: s for s in signals}

    topic_detail = by_sig["topic_distribution"]["detail"]
    viral_detail = by_sig["viral_type"]["detail"]
    inter_detail = by_sig["interaction"]["detail"]
    origin_detail = by_sig["originality"]["detail"]
    cap_detail = by_sig["capacity_funnel"]["detail"]
    tl_detail = by_sig["timeliness_depth"]["detail"]

    hhi = topic_detail.get("hhi", 0)
    distribution = topic_detail.get("distribution", [])
    main_axis = topic_detail.get("main_axis", "")
    top_share = topic_detail.get("top_share", 0)
    avg_share_rate = inter_detail.get("share_rate", 0)
    avg_like_rate = inter_detail.get("like_rate", 0)
    humanity_level = by_sig["originality"]["level"]
    mono_trace = cap_detail.get("monetization_trace", "无")
    posts_per_week = cap_detail.get("posts_per_week", 0)
    fans = cap_detail.get("fans", 0) or 0
    hotspot_ratio = tl_detail.get("hotspot_ratio", 0)
    viral_reliable = viral_detail.get("reliable", False)

    results = []

    # 1. 资讯流量型：主轴偏资讯类型 且 hotspot_ratio 高
    # 资讯特征：追热点题材占比高（用类型名启发式，不写死具体桶名）
    info_ct = re.compile(r"情报|热点|发布|风险|额度|羊毛|效率|工具|模型")
    info_share = sum(d["share"] for d in distribution if info_ct.search(d.get("type", "")))
    if info_share > 0.5:
        info_affinity = "高"
        info_reason = f"资讯/热点类题材占 {info_share:.0%}，更新节奏与资讯流量型吻合"
    elif info_share > 0.25 or hotspot_ratio > 0.3:
        info_affinity = "中"
        info_reason = f"资讯/热点类题材占 {info_share:.0%}，具备部分资讯特征"
    else:
        info_affinity = "无"
        info_reason = ""

    if info_affinity != "无":
        results.append({
            "archetype": "资讯流量型",
            "affinity": info_affinity,
            "adjacent": ["人设IP型"],
            "reason": info_reason,
        })

    # 2. 人设IP型：分享率/点赞率偏高（有认同基础）+ 有一定人味
    ip_signal = (avg_share_rate > 0.02) or (avg_like_rate > 0.05) or (humanity_level in ("强", "中"))
    if avg_share_rate > 0.03 and humanity_level in ("强", "中"):
        ip_affinity = "高"
        ip_reason = f"分享率均值 {avg_share_rate:.3f}，人味{humanity_level}，有认同与人设原料"
    elif ip_signal:
        ip_affinity = "中"
        ip_reason = f"分享率均值 {avg_share_rate:.3f}，具备初步信任资产"
    else:
        ip_affinity = "无"
        ip_reason = ""

    if ip_affinity != "无":
        results.append({
            "archetype": "人设IP型",
            "affinity": ip_affinity,
            "adjacent": ["垂直专家型", "社群情感型", "知识服务型"],
            "reason": ip_reason,
        })

    # 3. 知识服务型：厚度偏高（方法/案例密度中+）且有信任基础
    method_density = tl_detail.get("method_density", "低（近似）")
    med_len = tl_detail.get("median_length", 0)
    if med_len >= 1500 and "高" in method_density:
        ks_affinity = "中"
        ks_reason = f"篇幅中位 {med_len} 字、方法密度{method_density}，具备知识服务原料"
    elif med_len >= 1000 and ("中" in method_density or avg_share_rate > 0.025):
        ks_affinity = "低"
        ks_reason = f"篇幅中位 {med_len} 字，有一定方法积累，但距知识服务型仍有差距"
    else:
        ks_affinity = "无"
        ks_reason = ""

    if ks_affinity != "无":
        results.append({
            "archetype": "知识服务型",
            "affinity": ks_affinity,
            "adjacent": ["垂直专家型", "人设IP型"],
            "reason": ks_reason,
        })

    # 4. 垂直专家型：主轴高度集中（HHI高）且该主轴有方法深度
    if hhi > 0.45 and top_share > 0.5:
        ve_affinity = "中"
        ve_reason = f"主轴集中度高（HHI={hhi:.2f}），{main_axis} 占 {top_share:.0%}"
    elif hhi > 0.3:
        ve_affinity = "低"
        ve_reason = f"有主轴倾向（HHI={hhi:.2f}），但尚未形成专家壁垒"
    else:
        ve_affinity = "无"
        ve_reason = ""

    if ve_affinity != "无":
        results.append({
            "archetype": "垂直专家型",
            "affinity": ve_affinity,
            "adjacent": ["知识服务型", "人设IP型"],
            "reason": ve_reason,
        })

    # 5. 产品品牌型：变现痕迹明确 且 有产品/副业题材（类型名启发式，不写死具体桶名）
    brand_ct = re.compile(r"产品|副业|商业|变现|品牌")
    brand_share = sum(d["share"] for d in distribution if brand_ct.search(d.get("type", "")))
    if mono_trace == "有" and brand_share > 0.2:
        pb_affinity = "中"
        pb_reason = f"变现痕迹明确，产品/副业题材占 {brand_share:.0%}"
    elif mono_trace in ("有", "疑似") and brand_share > 0:
        pb_affinity = "低"
        pb_reason = f"有变现线索，产品/副业题材占 {brand_share:.0%}"
    else:
        pb_affinity = "无"
        pb_reason = ""

    if pb_affinity != "无":
        results.append({
            "archetype": "产品品牌型",
            "affinity": pb_affinity,
            "adjacent": ["知识服务型"],
            "reason": pb_reason,
        })

    # 6. 带货电商型：不触发（没有明显带货痕迹判断条件，保守处理）
    # 7. 社群情感型：评论率偏高 或 有强情绪/人设内容
    avg_comment_rate = inter_detail.get("comment_rate", 0)
    if avg_comment_rate > 0.015 and humanity_level == "强":
        se_affinity = "中"
        se_reason = f"评论率均值 {avg_comment_rate:.3f}，情感互动偏强"
    elif avg_comment_rate > 0.01 or humanity_level in ("强", "中"):
        se_affinity = "低"
        se_reason = f"有一定评论互动（均值 {avg_comment_rate:.3f}），具备社群基础"
    else:
        se_affinity = "无"
        se_reason = ""

    if se_affinity != "无":
        results.append({
            "archetype": "社群情感型",
            "affinity": se_affinity,
            "adjacent": ["人设IP型"],
            "reason": se_reason,
        })

    return results


# ───────────────────────── §7 候选方向卡 ─────────────────────────────────────

def _get_top_types(dataset: dict[str, Any], n: int = 3) -> list[dict[str, Any]]:
    """按中位阅读排序，返回前 n 个有文章的内容类型。"""
    by_ct = dataset.get("analysis", {}).get("by_content_type", [])
    return sorted(
        [row for row in by_ct if row.get("count", 0) > 0],
        key=lambda r: (r.get("median", 0), r.get("p75", 0)),
        reverse=True,
    )[:n]


def _get_high_share_type(dataset: dict[str, Any]) -> dict[str, Any] | None:
    """分享率最高的内容类型（样本≥2篇）。"""
    by_ct = dataset.get("analysis", {}).get("by_content_type", [])
    candidates = [row for row in by_ct if row.get("count", 0) >= 2]
    if not candidates:
        return None
    return max(candidates, key=lambda r: r.get("share_rate_avg", 0))


def _compute_feasibility(affinity: str, mode: str, weak_base: bool) -> tuple[str, str | None]:
    """按契约：feasibility 只衡信号距离/改造成本。低档必附中立 note。"""
    aff = affinity or "低"
    if aff == "高":
        base = "顺手"
    elif aff == "中":
        base = "够得着"
    else:
        base = "要改造"

    if weak_base and base == "顺手":
        base = "够得着"
    if weak_base and base == "够得着" and mode in ("收窄聚焦", "混合演进"):
        base = "要改造"

    if mode == "跨类迁移" and base in ("顺手", "够得着"):
        base = "要改造"

    note = None
    if base in ("要改造", "阻力大"):
        note = "改造成本高 ≠ 不推荐，是否值得由你的目的决定"
    return base, note


def _pick_mode_for_archetype(archetype: str, by_sig: dict[str, Any]) -> str:
    """§7.1：被亲缘命中的原型映射到最贴合的 mode。"""
    if archetype == "资讯流量型":
        return "顺势放大"
    if archetype == "人设IP型":
        return "转型升级"
    if archetype in ("知识服务型", "垂直专家型"):
        return "收窄聚焦"
    if archetype == "产品品牌型":
        return "转型升级"
    if archetype == "社群情感型":
        return "混合演进"
    if archetype == "带货电商型":
        return "转型升级"
    return "转型升级"


def _build_one_candidate(
    arch: dict[str, Any],
    mode: str,
    by_sig: dict[str, Any],
    mirror: dict[str, Any],
    dataset: dict[str, Any],
    idx_hint: int,
) -> dict[str, Any]:
    """用该号真实素材把模板重写为具象方向卡。"""
    topic_detail = by_sig.get("topic_distribution", {}).get("detail", {})
    viral_detail = by_sig.get("viral_type", {}).get("detail", {})
    inter_detail = by_sig.get("interaction", {}).get("detail", {})
    cap_detail = by_sig.get("capacity_funnel", {}).get("detail", {})
    tl_detail = by_sig.get("timeliness_depth", {}).get("detail", {})

    main_axis = topic_detail.get("main_axis", "主轴内容")
    top_share = topic_detail.get("top_share", 0)
    hhi = topic_detail.get("hhi", 0)
    viral_topic = viral_detail.get("topic") or main_axis
    viral_reliable = viral_detail.get("reliable", False)
    viral_sample = viral_detail.get("sample_count", 0)
    avg_share_rate = inter_detail.get("share_rate", 0)
    avg_like_rate = inter_detail.get("like_rate", 0)
    avg_comment_rate = inter_detail.get("comment_rate", 0)
    posts_per_week = cap_detail.get("posts_per_week", 0) or 0
    fans = cap_detail.get("fans") or 0
    fans_str = f"{fans} 粉" if fans else "粉丝数未知"
    med_len = tl_detail.get("median_length", 0)

    mono_maturity = mirror.get("monetization_maturity", "空白")
    weak_base = posts_per_week < 2 or (fans and fans < 2000)

    top_types = _get_top_types(dataset, n=3)
    top_type_names = [t["key"] for t in top_types if t.get("count", 0) > 0]
    active_types = [r["key"] for r in dataset.get("analysis", {}).get("by_content_type", []) if r.get("count", 0) > 0]

    feasibility, feas_note = _compute_feasibility(arch.get("affinity", "低"), mode, weak_base)

    # 真实题材提取（绝不写死）
    lead_topic = top_type_names[0] if top_type_names else main_axis
    viral_hint = (
        f"爆款锚点可用（{viral_sample} 篇样本）" if viral_reliable else f"流量命脉疑似来自{viral_topic}（样本偏少，仅作线索）"
    )

    if mode == "顺势放大":
        pull_topics = list(dict.fromkeys([main_axis, viral_topic, lead_topic]))[:3]
        path_name = f"沿{main_axis}主轴做深，把流量引擎放大"
        rationale = (
            f"你 {top_share:.0%} 已是{main_axis}，"
            f"这也是流量命脉所在（{viral_hint}）。"
            f"沿最强信号线扩量，信号改造距离最小。"
        )
        gap = [
            f"更新频率要更稳（当前约 {posts_per_week} 篇/周）",
            "标题更钩子化、选题追该类型热点",
        ]
        if fans and fans < 10000:
            gap.append(f"{fans_str}离规模化门槛还远，前期先把阅读量和粉丝做起来")
        monet = "流量主广告分成为主，覆盖面与更新频率决定收入上限；中期可在高频类型下试探小额增值。"
        matrix_hint = (
            f"拉新桶填入「{'、'.join(pull_topics)}」，配比拉到 55% 以上，节奏调快；"
            f"建专业桶做该主轴的深度解析，占 20% 左右。"
        )
    elif mode == "转型升级":
        trust_ev = []
        if avg_share_rate > 0.02:
            trust_ev.append(f"分享率均值 {avg_share_rate:.3f}")
        if avg_like_rate > 0.04:
            trust_ev.append(f"点赞率均值 {avg_like_rate:.3f}")
        trust_str = "、".join(trust_ev) if trust_ev else "互动信号偏强"
        trust_topics = [main_axis]
        brand_re = re.compile(r"产品|副业|商业|变现")
        if any(brand_re.search(t or "") for t in active_types):
            trust_topics.append("产品/副业相关")
        path_name = f"把{main_axis}的认同升级为可承接的变现链路"
        rationale = (
            f"读者{trust_str}，说明已有信任基础；"
            f"但变现链路{mono_maturity}，认同没有被承接。"
            f"把已有的互动信号转化为具体的变现路径，是当前改造成本最小的升级方向。"
        )
        gap = [
            "需要明确一个最小变现单元（如知识星球/小报童/专属群）",
            "内容结构里加入\"你能帮读者做什么\"的承接钩子",
            f"当前{fans_str}，先把私域阵地建起来再做规模化",
        ]
        monet = "可试水知识付费（精华合集/解读专栏）或私域变现；前期以低价/免费积累用户信任，再逐步提升变现密度。"
        matrix_hint = (
            f"养信任桶配比提升到 35%-45%，填入「{'、'.join(trust_topics[:2])}」类的判断与复盘内容；"
            f"转化桶从零开始试水，加私域承接动作。"
        )
    elif mode == "收窄聚焦":
        focus_type = lead_topic or main_axis
        med = 0
        for t in top_types:
            if t["key"] == focus_type:
                med = t.get("median", 0)
                break
        path_name = f"收窄到{focus_type}，做单一垂直信号点"
        rationale = (
            f"当前题材分散（{len(active_types)} 类均有覆盖），"
            f"但{focus_type}信号相对突出（中位阅读 {int(med) if med else '较高'}）。"
            f"若该信号稳健，收口到单一垂直方向可以更快建立壁垒（前提：先验证更多样本）。"
        )
        gap = [
            f"先验证 {focus_type} 在 5-10 篇样本上的中位阅读是否稳健",
            "逐步减少其他题材占比，不要一次性全切",
            "收窄后内容密度要提升，频率不能下降",
        ]
        monet = "垂直深耕可以建立该细分领域的稀缺性；中期试水垂直知识服务（课程/咨询）或品牌合作。"
        matrix_hint = (
            f"建专业桶大幅提升（配比 50%-60%），全部填入「{focus_type}」的深度解析与案例拆解；"
            f"拉新桶保留少量入门级内容引流，占 20% 左右。"
        )
    elif mode == "跨类迁移":
        path_name = f"借现有受众向相邻原型迁移"
        rationale = (
            f"当前与{arch.get('archetype')}已有亲缘，跨类可借用信任与流量资产。"
            f"改造成本较高，需评估目的后再决定。"
        )
        gap = [
            "需重新定位受众与内容口味",
            "建立新形态的信任信号（人设/方法/社群）",
            "频率与产能需匹配新方向",
        ]
        monet = "迁移后按目标原型常见方式变现；早期以内容+私域验证需求。"
        matrix_hint = f"初期保留拉新桶过渡，逐步把养信任/建专业向新方向倾斜。"
    else:  # 混合演进
        share_l = max(
            (r for r in dataset.get("analysis", {}).get("by_content_type", []) if r.get("count", 0) >= 1),
            key=lambda r: r.get("share_rate_avg", 0),
            default={"key": lead_topic},
        )["key"]
        cmt_l = max(
            (r for r in dataset.get("analysis", {}).get("by_content_type", []) if r.get("count", 0) >= 1),
            key=lambda r: r.get("comment_rate_avg", 0),
            default={"key": main_axis},
        )["key"]
        if share_l == cmt_l:
            cmt_l = (top_type_names[1] if len(top_type_names) > 1 else main_axis)
        path_name = f"按角色分层组合现有内容块"
        rationale = (
            f"现有 {min(3, len(active_types))} 个题材有积累，"
            f"分享与评论信号可拆到不同 role 桶。"
            f"按角色分层比全力押注单一方向更稳健。"
        )
        gap = [
            f"把{share_l}定位为拉新主力，标题向钩子倾斜",
            f"把{cmt_l}定位为留存/互动桶，内容引导评论",
            "两类节奏独立管理",
        ]
        monet = "拉新桶扩大覆盖面，留存桶深化信任；两桶协作后再考虑转化植入。"
        matrix_hint = (
            f"拉新桶「{share_l}」配比 45%-55%，节奏快；"
            f"留存桶「{cmt_l}」配比 25%-35%，引导互动；建专业补充主轴。"
        )

    return {
        "id": f"path-{idx_hint}",
        "path_name": path_name,
        "mode": mode,
        "rationale_from_status": rationale,
        "feasibility": feasibility,
        "feasibility_note": feas_note,
        "gap": gap,
        "monetization": monet,
        "matrix_hint": matrix_hint,
    }


def build_candidate_paths(
    signals: list[dict[str, Any]],
    mirror: dict[str, Any],
    archetype_affinity: list[dict[str, Any]],
    dataset: dict[str, Any],
) -> list[dict[str, Any]]:
    """§7 动态方向卡。严格按契约 §7.1 由 archetype_affinity 驱动。"""
    by_sig = {s["key"]: s for s in signals}

    # 优先级：高/中 → 各映射一个 mode 产一条候选；不足 2 用低亲缘补足；>4 按信号距离升序截断
    # 同一原型只映射一次（已在 high_mid 列表里一个 archetype 一次）
    high_mid = [a for a in archetype_affinity if a.get("affinity") in ("高", "中")]
    low = [a for a in archetype_affinity if a.get("affinity") == "低"]

    selected: list[tuple[dict, str]] = []
    for a in high_mid:
        mode = _pick_mode_for_archetype(a["archetype"], by_sig)
        selected.append((a, mode))

    if len(selected) < 2:
        for a in low:
            if len(selected) >= 2:
                break
            mode = _pick_mode_for_archetype(a["archetype"], by_sig)
            selected.append((a, mode))

    # 构建卡片 + 计算距离（affinity 主导 + 微调）
    raw_paths: list[dict[str, Any]] = []
    for i, (arch, mode) in enumerate(selected, start=1):
        p = _build_one_candidate(arch, mode, by_sig, mirror, dataset, i)
        # 距离：高=近(1)，中=中(2.5)，低=远(4+)；用于超限截断
        dist = {"高": 1.0, "中": 2.5, "低": 4.0}.get(arch.get("affinity", "低"), 5.0)
        p["_dist"] = dist
        raw_paths.append(p)

    # 按信号距离升序（越小越近，优先保留）
    raw_paths.sort(key=lambda x: x.get("_dist", 99.0))

    paths = raw_paths[:4]  # 最多 4 张
    if len(paths) < 2 and len(raw_paths) >= 2:
        paths = raw_paths[:2]

    # 连续重编号
    for i, p in enumerate(paths, start=1):
        p["id"] = f"path-{i}"
        p.pop("_dist", None)

    return paths


# ───────────────────────── §8 内容矩阵 ───────────────────────────────────────

def build_content_matrix(
    paths: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    dataset: dict[str, Any],
) -> dict[str, Any]:
    """§8 内容矩阵两层。"""
    by_sig = {s["key"]: s for s in signals}
    topic_detail = by_sig["topic_distribution"]["detail"]
    distribution = topic_detail.get("distribution", [])
    main_axis = topic_detail.get("main_axis", "")
    cap_detail = by_sig["capacity_funnel"]["detail"]
    posts_per_week = cap_detail.get("posts_per_week", 0) or 2.0
    by_ct = dataset.get("analysis", {}).get("by_content_type", [])
    active_types_ordered = [r["key"] for r in by_ct if r.get("count", 0) > 0]  # 保序，by_ct 已按某字段排序
    active_types = set(active_types_ordered)  # 仅用于 in 判断，不迭代

    # 分享率最高类型（适合拉新）
    share_leader_rows = sorted(
        [r for r in by_ct if r.get("count", 0) >= 1],
        key=lambda r: r.get("share_rate_avg", 0), reverse=True
    )
    share_leader = share_leader_rows[0]["key"] if share_leader_rows else main_axis

    # 阅读量最高类型（适合建专业/传播）
    read_leader_rows = sorted(
        [r for r in by_ct if r.get("count", 0) >= 1],
        key=lambda r: r.get("median", 0), reverse=True
    )
    read_leader = read_leader_rows[0]["key"] if read_leader_rows else main_axis

    def _cadence(ppw: float) -> str:
        if ppw >= 5:
            return f"每周 {int(ppw)} 更"
        elif ppw >= 3:
            return f"每周 {int(ppw)}-{int(ppw)+1} 更"
        elif ppw >= 1:
            return f"每周 {max(2, int(ppw*2))} 更"
        return "每周 2 更"

    base_cadence = _cadence(posts_per_week)
    faster_cadence = _cadence(posts_per_week * 1.4)

    by_direction: dict[str, Any] = {}

    for path in paths:
        path_id = path["id"]
        mode = path.get("mode", "")
        path_name = path.get("path_name", "")

        # 根据 mode 动态配比
        if mode == "顺势放大":
            # 拉新为主，快节奏
            pull_topics = list(dict.fromkeys([share_leader, main_axis]))[:2]
            buckets = [
                {
                    "role": "拉新",
                    "topics": pull_topics,
                    "weight": 0.55,
                    "horizon": "本周可发",
                    "rhythm": "节奏调快，标题钩子化",
                },
                {
                    "role": "建专业",
                    "topics": [main_axis],
                    "weight": 0.25,
                    "horizon": "本周可发",
                    "rhythm": "深度解析，每篇有方法框架",
                },
                {
                    "role": "养信任",
                    "topics": [main_axis],
                    "weight": 0.15,
                    "horizon": "需积累",
                    "rhythm": "加入作者判断与视角",
                },
                {
                    "role": "留存",
                    "topics": [t for t in active_types_ordered if t not in {main_axis, share_leader}][:1] or [main_axis],
                    "weight": 0.05,
                    "horizon": "需积累",
                    "rhythm": "互动引导，引发评论",
                },
            ]
            schedule = [
                {
                    "phase": "第 1-2 周",
                    "focus": "稳定更新频率，标题钩子化",
                    "cadence": base_cadence,
                    "topics": pull_topics,
                },
                {
                    "phase": "第 3-4 周",
                    "focus": "追热点选题，拉新桶配比拉满",
                    "cadence": faster_cadence,
                    "topics": pull_topics + [main_axis],
                },
            ]
        elif mode == "转型升级":
            # 养信任为主，建立变现承接
            trust_topics = [main_axis]
            buckets = [
                {
                    "role": "养信任",
                    "topics": trust_topics,
                    "weight": 0.45,
                    "horizon": "本周可发",
                    "rhythm": "加入作者判断、复盘与立场",
                },
                {
                    "role": "拉新",
                    "topics": [share_leader],
                    "weight": 0.30,
                    "horizon": "本周可发",
                    "rhythm": "保持流量入口，引流到信任内容",
                },
                {
                    "role": "建专业",
                    "topics": [main_axis],
                    "weight": 0.15,
                    "horizon": "本周可发",
                    "rhythm": "建立专业壁垒",
                },
                {
                    "role": "转化",
                    "topics": [main_axis],
                    "weight": 0.10,
                    "horizon": "需积累",
                    "rhythm": "小额试水，加私域承接动作",
                },
            ]
            schedule = [
                {
                    "phase": "第 1-2 周",
                    "focus": "加大养信任内容比例，建立私域阵地",
                    "cadence": base_cadence,
                    "topics": trust_topics + [share_leader],
                },
                {
                    "phase": "第 3-4 周",
                    "focus": "试水转化动作，加入承接钩子",
                    "cadence": base_cadence,
                    "topics": trust_topics + [main_axis],
                },
            ]
        elif mode == "收窄聚焦":
            # 建专业为主
            focus_type = path_name.split("收窄到")[-1].split("，")[0].strip() if "收窄到" in path_name else main_axis
            if focus_type not in active_types:
                focus_type = main_axis
            buckets = [
                {
                    "role": "建专业",
                    "topics": [focus_type],
                    "weight": 0.55,
                    "horizon": "本周可发",
                    "rhythm": "深度拆解，每篇有可操作方法",
                },
                {
                    "role": "拉新",
                    "topics": [focus_type],
                    "weight": 0.25,
                    "horizon": "本周可发",
                    "rhythm": "入门级内容，降低进入门槛",
                },
                {
                    "role": "养信任",
                    "topics": [focus_type],
                    "weight": 0.15,
                    "horizon": "需积累",
                    "rhythm": "作者视角与判断，差异化表达",
                },
                {
                    "role": "留存",
                    "topics": [focus_type],
                    "weight": 0.05,
                    "horizon": "需积累",
                    "rhythm": "社群互动，深度用户引导",
                },
            ]
            schedule = [
                {
                    "phase": "第 1-2 周",
                    "focus": f"验证{focus_type}更多样本的稳健性",
                    "cadence": base_cadence,
                    "topics": [focus_type],
                },
                {
                    "phase": "第 3-4 周",
                    "focus": "逐步收窄其他题材，提升垂直密度",
                    "cadence": base_cadence,
                    "topics": [focus_type],
                },
            ]
        else:
            # 混合演进：均衡分配
            all_active = active_types_ordered[:4]
            if not all_active:
                all_active = [main_axis]
            buckets = [
                {
                    "role": "拉新",
                    "topics": [share_leader],
                    "weight": 0.45,
                    "horizon": "本周可发",
                    "rhythm": "高分享类型钩子化，快节奏",
                },
                {
                    "role": "留存",
                    "topics": all_active[:2],
                    "weight": 0.30,
                    "horizon": "本周可发",
                    "rhythm": "引导评论互动，深化用户关系",
                },
                {
                    "role": "建专业",
                    "topics": [main_axis],
                    "weight": 0.15,
                    "horizon": "本周可发",
                    "rhythm": "主轴深度内容，建立壁垒",
                },
                {
                    "role": "养信任",
                    "topics": [main_axis],
                    "weight": 0.10,
                    "horizon": "需积累",
                    "rhythm": "作者判断与复盘",
                },
            ]
            schedule = [
                {
                    "phase": "第 1-2 周",
                    "focus": "明确每类内容的角色定位",
                    "cadence": base_cadence,
                    "topics": [share_leader, main_axis],
                },
                {
                    "phase": "第 3-4 周",
                    "focus": "按角色配比优化，减少角色混淆",
                    "cadence": faster_cadence,
                    "topics": all_active[:3],
                },
            ]

        # 去掉 topics 为空的桶，最多 6 桶
        valid_buckets = [b for b in buckets if b.get("topics")][:6]

        by_direction[path_id] = {
            "buckets": valid_buckets,
            "schedule": schedule,
        }

    return {
        "model_name": "方向参数化内容矩阵（role 维度固定 / 题材维度动态）",
        "roles": MATRIX_ROLES,
        "by_direction": by_direction,
    }


# ───────────────────────── 入口函数 ──────────────────────────────────────────

def build_forward_looking(dataset: dict[str, Any]) -> dict[str, Any]:
    """主入口：产出 forward_looking 节点。

    契约 §2：
        engine_version, model_name,
        data_sufficiency, signals, mirror,
        archetype_affinity, candidate_paths,
        candidate_cap, content_matrix
    """
    data_sufficiency = build_data_sufficiency(dataset)
    signals = build_signals(dataset)
    mirror = build_mirror(signals, dataset)

    if data_sufficiency["passed"]:
        archetype_affinity = build_archetype_affinity(signals, mirror)
        candidate_paths = build_candidate_paths(signals, mirror, archetype_affinity, dataset)
        by_direction = build_content_matrix(candidate_paths, signals, dataset)["by_direction"]
    else:
        archetype_affinity = []
        candidate_paths = []
        by_direction = {}

    content_matrix = {
        "model_name": "方向参数化内容矩阵（role 维度固定 / 题材维度动态）",
        "roles": MATRIX_ROLES,
        "by_direction": by_direction,
    }

    return {
        "engine_version": ENGINE_VERSION,
        "model_name": ENGINE_MODEL_NAME,
        "data_sufficiency": data_sufficiency,
        "signals": signals,
        "mirror": mirror,
        "archetype_affinity": archetype_affinity,
        "candidate_paths": candidate_paths,
        "candidate_cap": {
            "min": 2,
            "max": 4,
            "note": "方向卡数量取决于信号强度，2-4 张；并列方向不分高下、平铺展示。",
        },
        "content_matrix": content_matrix,
    }
