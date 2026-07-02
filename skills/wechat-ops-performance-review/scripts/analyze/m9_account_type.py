"""m9_account_type.py — 账号类型识别与分析路由引擎（account-type-router-v1）

从已抓取数据（发文频率、题材时效性、人味浓度、方法密度、变现痕迹、互动结构、
粉丝城市集中度）自动推断公众号类型，并给出该类型的诊断 playbook 与 m1–m8 路由权重。

设计原则：
- 只增不删：产出挂 dataset["account_type"] 顶层新节点，不改任何现有字段。
- 置信内化：置信不足回退通用链路（general），不硬判类型；
  所有可渲染字符串不出现"置信度"等禁词。
- 价值中立：类型之间不判优劣，playbook 只描述"该类型看什么、怎么读、往哪使劲"。
- 方法论长文见 references/account-type-playbooks.md，本文件只放判定逻辑与精炼口径。
"""
from __future__ import annotations

import re
from typing import Any

ENGINE_VERSION = "account-type-router-v1"

# 六大类型 + 通用回退（顺序即 scores 输出顺序）
ACCOUNT_TYPES = [
    "media_news",
    "personal_ip",
    "knowledge_service",
    "conversion_sales",
    "brand_org",
    "local_life",
    "general",
]

# m1–m8 模块键（与 dataset["modules"] + viral_genes/standards/forward_looking 对齐）
MODULE_KEYS_ORDERED = [
    "checkup",
    "viral_genes",
    "content_engine",
    "audience",
    "growth_funnel",
    "action_plan",
    "standards",
    "forward_looking",
]

# ───────────────────────── 特征正则 ──────────────────────────────────────────

# 时效/资讯特征（刻意不含"限时/福利"等促销词，避免与转化号混淆）
HOTSPOT_RE = re.compile(r"快讯|速递|今日|今天|本周|最新|刚刚|突发|发布|上线|官宣|资讯|日报|周报")
# 人味/个人叙事
FIRST_PERSON_RE = re.compile(r"[我咱]们?|本人|笔者")
STORY_RE = re.compile(r"我的|我[曾已踩遇]|亲历|亲测|复盘|这一年|踩坑|我发现|聊聊|判断|立场|取舍")
# 方法/教学
METHOD_RE = re.compile(r"步骤|方法|案例|拆解|清单|攻略|教程|指南|手把手|一文|讲透|保姆级|完整版|实操")
# 变现/转化钩子
MONETIZATION_RE = re.compile(r"二维码|加群|扫码|领取|星球|付费|私信|报名|训练营|下单|购买|带货|佣金|返现|会员价")
# 促销福利词（转化号的标题特征）
BENEFIT_RE = re.compile(r"免费|福利|优惠|限时|折扣|秒杀|特价|羊毛|名额")
# 机构口吻（企业品牌号）
ORG_RE = re.compile(r"我司|本公司|我们团队|官方|旗下|品牌方|新品发布会|周年庆|荣获|喜报|招聘")
# 本地生活
LOCAL_RE = re.compile(r"探店|门店|到店|同城|本地|商圈|打卡|外卖|开业|堂食|营业时间|地铁|附近")


def _hit_ratio(articles: list[dict[str, Any]], pattern: re.Pattern[str]) -> float:
    """标题+摘要命中 pattern 的文章占比。"""
    if not articles:
        return 0.0
    hits = sum(
        1 for a in articles
        if pattern.search((a.get("title") or "") + (a.get("digest") or ""))
    )
    return hits / len(articles)


def _avg(values: list[float]) -> float:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


def _median(values: list[float]) -> float:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return 0.0
    n = len(vals)
    mid = n // 2
    return float(vals[mid]) if n % 2 else (vals[mid - 1] + vals[mid]) / 2.0


def _extract_features(dataset: dict[str, Any]) -> dict[str, Any]:
    stable = dataset.get("articles", {}).get("stable", []) or []
    profile = dataset.get("account_profile", {}) or {}
    account = dataset.get("account", {}) or {}
    audience_mod = (dataset.get("modules", {}) or {}).get("audience", {}) or {}

    city = audience_mod.get("city") or []
    city_top_share = 0.0
    if isinstance(city, list) and city:
        values = [float(c.get("value", 0) or 0) for c in city if isinstance(c, dict)]
        total = sum(values)
        if total > 0 and values:
            city_top_share = max(values) / total

    return {
        "sample_count": len(stable),
        "posts_per_week": float(profile.get("publish_frequency", 0) or 0),
        "fans": account.get("cumulate_user"),
        "hotspot_ratio": _hit_ratio(stable, HOTSPOT_RE),
        "story_ratio": _hit_ratio(stable, STORY_RE),
        "first_person_ratio": _hit_ratio(stable, FIRST_PERSON_RE),
        "method_ratio": _hit_ratio(stable, METHOD_RE),
        "monetization_ratio": _hit_ratio(stable, MONETIZATION_RE),
        "benefit_ratio": _hit_ratio(stable, BENEFIT_RE),
        "org_ratio": _hit_ratio(stable, ORG_RE),
        "local_ratio": _hit_ratio(stable, LOCAL_RE),
        "avg_share_rate": _avg([a.get("share_rate", 0) or 0 for a in stable]),
        "avg_comment_rate": _avg([a.get("comment_rate", 0) or 0 for a in stable]),
        "avg_like_rate": _avg([a.get("like_rate", 0) or 0 for a in stable]),
        "median_length": _median([
            float(a.get("article_length_chars") or 0)
            for a in stable if (a.get("article_length_chars") or 0) > 0
        ]),
        "city_top_share": city_top_share,
    }


# ───────────────────────── 类型打分 ──────────────────────────────────────────

def _score_types(f: dict[str, Any]) -> dict[str, float]:
    """六类型各打 0–1 分。加权特征命中，阈值宁保守勿硬判。"""
    ppw = f["posts_per_week"]
    humanity_low = f["first_person_ratio"] < 0.15 and f["story_ratio"] < 0.15
    dominant_share = f["avg_share_rate"] >= max(f["avg_comment_rate"], f["avg_like_rate"])

    media = 0.0
    media += 0.30 if ppw >= 4 else (0.15 if ppw >= 2.5 else 0.0)
    media += 0.30 if f["hotspot_ratio"] >= 0.5 else (0.15 if f["hotspot_ratio"] >= 0.3 else 0.0)
    media += 0.15 if humanity_low else 0.0
    media += 0.15 if 0 < f["median_length"] < 1200 else 0.0
    media += 0.10 if dominant_share else 0.0

    ip = 0.0
    ip += 0.35 if f["story_ratio"] >= 0.4 or f["first_person_ratio"] >= 0.5 else (
        0.20 if f["story_ratio"] >= 0.2 or f["first_person_ratio"] >= 0.25 else 0.0)
    ip += 0.20 if f["avg_like_rate"] > 0.04 or f["avg_share_rate"] > 0.025 else 0.0
    ip += 0.15 if f["avg_comment_rate"] > 0.008 else 0.0
    ip += 0.10 if f["hotspot_ratio"] < 0.2 else 0.0
    ip += 0.10 if f["median_length"] >= 1500 else 0.0
    ip += 0.10 if 0 < ppw <= 3 else 0.0

    ks = 0.0
    ks += 0.35 if f["method_ratio"] >= 0.4 else (0.18 if f["method_ratio"] >= 0.2 else 0.0)
    ks += 0.30 if f["median_length"] >= 2200 else (0.15 if f["median_length"] >= 1500 else 0.0)
    ks += 0.10 if f["avg_share_rate"] > 0.02 else 0.0
    ks += 0.10 if f["hotspot_ratio"] < 0.2 else 0.0
    ks += 0.10 if f["story_ratio"] < 0.2 else 0.0

    cs = 0.0
    cs += 0.45 if f["monetization_ratio"] >= 0.3 else (0.22 if f["monetization_ratio"] >= 0.1 else 0.0)
    cs += 0.20 if f["monetization_ratio"] >= 0.6 else 0.0
    cs += 0.15 if f["benefit_ratio"] >= 0.3 else 0.0
    cs += 0.10 if ppw >= 3 else 0.0

    brand = 0.0
    brand += 0.40 if f["org_ratio"] >= 0.3 else (0.20 if f["org_ratio"] >= 0.1 else 0.0)
    brand += 0.20 if humanity_low else 0.0
    brand += 0.15 if f["avg_share_rate"] < 0.01 and f["avg_comment_rate"] < 0.005 else 0.0

    local = 0.0
    local += 0.40 if f["local_ratio"] >= 0.3 else (0.20 if f["local_ratio"] >= 0.1 else 0.0)
    local += 0.30 if f["city_top_share"] >= 0.4 else (0.15 if f["city_top_share"] >= 0.25 else 0.0)
    local += 0.10 if f["benefit_ratio"] >= 0.2 else 0.0

    return {
        "media_news": round(min(1.0, media), 3),
        "personal_ip": round(min(1.0, ip), 3),
        "knowledge_service": round(min(1.0, ks), 3),
        "conversion_sales": round(min(1.0, cs), 3),
        "brand_org": round(min(1.0, brand), 3),
        "local_life": round(min(1.0, local), 3),
    }


# ───────────────────────── 类型 playbook ─────────────────────────────────────

TYPE_PLAYBOOKS: dict[str, dict[str, Any]] = {
    "media_news": {
        "name": "媒体资讯号",
        "north_star": ["打开率与阅读量", "时效命中率(热点跟进速度)", "发文频率稳定性"],
        "diagnosis_focus": [
            "发文节奏是否稳定且够快(资讯号断更即掉量)",
            "爆款是否可复制:哪类快讯题材+钩子标题能打穿推荐流",
            "阅读依赖是否过度集中在个别热点",
        ],
        "module_weights": {
            "checkup": "高", "viral_genes": "高", "content_engine": "高",
            "audience": "低", "growth_funnel": "中", "action_plan": "高",
            "standards": "中", "forward_looking": "中",
        },
        "reading_guide": "资讯号先看量与速度:阅读中位、发文频率、热点响应窗口比互动率更要紧;分享率是破圈信号,评论率偏低属正常,不必按人设号口径焦虑。",
        "action_bias": [
            "优先提升发文频率与热点响应速度,固化每日选题流程",
            "标题钩子化实验放最高优先级,快速迭代",
            "互动类动作(引导评论/社群)后置,先把覆盖面做大",
        ],
    },
    "personal_ip": {
        "name": "内容IP/个人品牌号",
        "north_star": ["在看率与分享率(认同强度)", "粉丝忠诚与复访", "人设一致性"],
        "diagnosis_focus": [
            "人设是否一致:题材漂移会稀释信任",
            "认同信号(在看/评论)是否持续,而非只看阅读量",
            "信任资产有没有承接口(私域/专栏),避免认同空转",
        ],
        "module_weights": {
            "checkup": "中", "viral_genes": "中", "content_engine": "中",
            "audience": "高", "growth_funnel": "高", "action_plan": "高",
            "standards": "低", "forward_looking": "高",
        },
        "reading_guide": "IP号先看认同不看流量:在看率、评论质量、粉丝净增的口碑成分比阅读中位更要紧;单篇低阅读高在看是资产不是失败,不必按资讯号口径追热点。",
        "action_bias": [
            "优先巩固人设主线,砍掉稀释人设的杂题材",
            "把高认同内容沉淀为系列/专栏,建立复访理由",
            "追热点动作降级:只追与人设强相关的热点",
        ],
    },
    "knowledge_service": {
        "name": "知识服务/教育号",
        "north_star": ["收藏与分享率(工具性价值)", "方法内容密度", "教程系列完成度"],
        "diagnosis_focus": [
            "方法密度与篇幅厚度是否撑得起专业心智",
            "教程/清单类是否形成体系,而非零散单篇",
            "深度遗珠象限占比:好内容标题不行是知识号最常见病",
        ],
        "module_weights": {
            "checkup": "中", "viral_genes": "高", "content_engine": "高",
            "audience": "中", "growth_funnel": "中", "action_plan": "高",
            "standards": "高", "forward_looking": "中",
        },
        "reading_guide": "知识号先看留存价值:分享率与长文完读比阅读峰值更要紧;深度遗珠(低读高享)多说明标题拖后腿而非内容问题,优化方向是标题不是选题。",
        "action_bias": [
            "优先把深度遗珠的标题重做,存量内容二次分发",
            "把散篇方法整合成系列/合集,建立体系感",
            "发文频率可低但必须稳,厚度不减",
        ],
    },
    "conversion_sales": {
        "name": "私域转化/带货号",
        "north_star": ["引流-转化漏斗通畅度", "私域承接动作密度", "转化内容配比"],
        "diagnosis_focus": [
            "漏斗是否完整:拉新内容→信任内容→转化钩子是否断链",
            "转化钩子密度是否过高反噬阅读(全是广告没人看)",
            "粉丝净增与转化动作的节奏是否匹配",
        ],
        "module_weights": {
            "checkup": "高", "viral_genes": "中", "content_engine": "高",
            "audience": "高", "growth_funnel": "高", "action_plan": "高",
            "standards": "低", "forward_looking": "中",
        },
        "reading_guide": "转化号先看漏斗不看单篇:拉新篇的阅读、信任篇的互动、转化篇的钩子点击要分开评估;阅读中位偏低但转化链路通畅是健康状态,不必按媒体号口径冲量。",
        "action_bias": [
            "优先梳理漏斗断点:哪一环内容缺配比就补哪环",
            "控制转化钩子密度,保持拉新与转化内容配比",
            "粉丝画像与来源分析权重拉高,精准比规模重要",
        ],
    },
    "brand_org": {
        "name": "企业品牌号",
        "north_star": ["品牌内容与业务关联度", "发布稳定性", "有效触达(非僵尸阅读)"],
        "diagnosis_focus": [
            "内容是否只有官宣没有用户价值(自嗨风险)",
            "互动全低时要区分:触达失败还是内容无关",
            "品牌调性与平台内容生态的适配度",
        ],
        "module_weights": {
            "checkup": "高", "viral_genes": "低", "content_engine": "高",
            "audience": "高", "growth_funnel": "中", "action_plan": "高",
            "standards": "中", "forward_looking": "低",
        },
        "reading_guide": "品牌号先看有效触达:阅读来自目标人群还是员工转发要分开看;爆款公式参考价值低,内容与业务的关联度、用户视角占比才是诊断重点。",
        "action_bias": [
            "优先把官宣类内容改写为用户价值视角",
            "建立固定栏目降低选题成本,保证发布稳定",
            "爆款复制类动作降级,不追平台热点",
        ],
    },
    "local_life": {
        "name": "本地生活号",
        "north_star": ["本地粉丝浓度(城市集中度)", "到店/线下转化钩子", "本地题材覆盖密度"],
        "diagnosis_focus": [
            "粉丝城市集中度是否够高:泛流量对本地号无效",
            "内容是否绑定具体场景(店/商圈/活动)可转化",
            "福利类内容与本地信息类内容的配比",
        ],
        "module_weights": {
            "checkup": "中", "viral_genes": "中", "content_engine": "高",
            "audience": "高", "growth_funnel": "高", "action_plan": "高",
            "standards": "低", "forward_looking": "中",
        },
        "reading_guide": "本地号先看城市浓度:一万泛粉不如三千同城粉;粉丝画像的城市分布是第一诊断指标,阅读量要结合本地人口基数评估而非平台通用基准。",
        "action_bias": [
            "优先做本地强绑定选题(探店/活动/政策),提城市浓度",
            "每篇内容带可执行的线下动作钩子",
            "跨城泛流量内容降配比,不为阅读量稀释定位",
        ],
    },
    "general": {
        "name": "通用链路",
        "north_star": ["阅读中位稳定性", "互动结构健康度", "选题有效率"],
        "diagnosis_focus": [
            "类型信号尚不清晰:先按通用诊断把现状照清楚",
            "积累样本后重新识别,再切换差异化链路",
        ],
        "module_weights": {
            "checkup": "高", "viral_genes": "高", "content_engine": "高",
            "audience": "中", "growth_funnel": "中", "action_plan": "高",
            "standards": "中", "forward_looking": "高",
        },
        "reading_guide": "类型特征还不明显,按通用口径解读:先看底盘健康与爆款基因,等样本与信号积累后自动切换到对应类型链路。",
        "action_bias": [
            "按通用诊断执行,不预设类型化打法",
            "持续积累样本,让类型信号自然显影",
        ],
    },
}


def _routing_chain(module_weights: dict[str, str]) -> list[str]:
    """按权重高→中→低排,同档保持 m1–m8 canonical 顺序。"""
    order = {"高": 0, "中": 1, "低": 2}
    return sorted(MODULE_KEYS_ORDERED, key=lambda m: (order.get(module_weights.get(m, "中"), 1), MODULE_KEYS_ORDERED.index(m)))


def _build_evidence(key: str, f: dict[str, Any]) -> list[str]:
    """识别依据,引用真实特征值(中文可渲染,不含禁词)。"""
    ev: list[str] = []
    if key == "media_news":
        ev.append(f"发文频率约 {f['posts_per_week']:.1f} 篇/周,时效类题材占 {f['hotspot_ratio']:.0%}")
        if f["median_length"]:
            ev.append(f"篇幅中位 {int(f['median_length'])} 字,偏轻快资讯形态")
    elif key == "personal_ip":
        ev.append(f"个人叙事类内容占 {f['story_ratio']:.0%},第一人称出现率 {f['first_person_ratio']:.0%}")
        ev.append(f"点赞率均值 {f['avg_like_rate']:.3f}、评论率均值 {f['avg_comment_rate']:.3f},认同信号明显")
    elif key == "knowledge_service":
        ev.append(f"方法/教程类内容占 {f['method_ratio']:.0%},篇幅中位 {int(f['median_length'])} 字")
    elif key == "conversion_sales":
        ev.append(f"变现/转化钩子出现在 {f['monetization_ratio']:.0%} 的内容中,福利促销词占 {f['benefit_ratio']:.0%}")
    elif key == "brand_org":
        ev.append(f"机构口吻内容占 {f['org_ratio']:.0%},人称叙事弱")
    elif key == "local_life":
        ev.append(f"本地生活类内容占 {f['local_ratio']:.0%},粉丝头部城市占比 {f['city_top_share']:.0%}")
    else:
        ev.append(f"稳定样本 {f['sample_count']} 篇,类型特征信号均未达判定阈值,走通用链路")
    return ev


MIN_SAMPLE_FOR_TYPING = 8
PRIMARY_THRESHOLD = 0.45
HIGH_THRESHOLD = 0.6
HIGH_GAP = 0.15


def build_account_type(dataset: dict[str, Any]) -> dict[str, Any]:
    """主入口:识别账号类型并给出诊断路由。挂 dataset["account_type"]。"""
    f = _extract_features(dataset)
    scores = _score_types(f)

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_key, top_score = ranked[0]
    second_key, second_score = ranked[1]

    if f["sample_count"] < MIN_SAMPLE_FOR_TYPING:
        primary_key, confidence, fallback = "general", "low", True
        reason = f"稳定样本仅 {f['sample_count']} 篇,不足 {MIN_SAMPLE_FOR_TYPING} 篇,类型判定暂不启用"
    elif top_score < PRIMARY_THRESHOLD:
        primary_key, confidence, fallback = "general", "low", True
        reason = "各类型特征信号均偏弱,不硬判类型"
    elif top_score >= HIGH_THRESHOLD and (top_score - second_score) >= HIGH_GAP:
        primary_key, confidence, fallback = top_key, "high", False
        reason = "类型特征清晰且与次优类型拉开差距"
    else:
        primary_key, confidence, fallback = top_key, "medium", False
        reason = "类型特征基本成立,建议积累样本后复核"

    playbook = TYPE_PLAYBOOKS[primary_key]
    secondary = None
    if not fallback and second_score >= PRIMARY_THRESHOLD:
        secondary = {
            "key": second_key,
            "name": TYPE_PLAYBOOKS[second_key]["name"],
            "score": second_score,
        }

    evidence = _build_evidence(primary_key, f)

    return {
        "engine_version": ENGINE_VERSION,
        "primary": {
            "key": primary_key,
            "name": playbook["name"],
            "score": scores.get(primary_key, 0.0) if primary_key != "general" else None,
        },
        "secondary": secondary,
        "confidence": confidence,
        "fallback_to_general": fallback,
        "decision_note": reason,
        "scores": scores,
        "evidence": evidence,
        "features": {
            "sample_count": f["sample_count"],
            "posts_per_week": round(f["posts_per_week"], 1),
            "hotspot_ratio": round(f["hotspot_ratio"], 2),
            "story_ratio": round(f["story_ratio"], 2),
            "method_ratio": round(f["method_ratio"], 2),
            "monetization_ratio": round(f["monetization_ratio"], 2),
            "org_ratio": round(f["org_ratio"], 2),
            "local_ratio": round(f["local_ratio"], 2),
            "city_top_share": round(f["city_top_share"], 2),
            "median_length": int(f["median_length"]),
        },
        "playbook": {
            "name": playbook["name"],
            "north_star": playbook["north_star"],
            "diagnosis_focus": playbook["diagnosis_focus"],
            "module_weights": playbook["module_weights"],
            "reading_guide": playbook["reading_guide"],
            "action_bias": playbook["action_bias"],
        },
        "routing": {
            "chain": _routing_chain(playbook["module_weights"]),
            "note": (
                "诊断阅读顺序按该类型的模块权重排列;权重低的模块仍产出,"
                "只是解读与行动建议按 reading_guide 口径降权。"
            ),
        },
    }
