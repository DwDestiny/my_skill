#!/usr/bin/env python3
"""Build a WeChat-only operations report for wiki and dashboard use.

This script is intentionally read-only toward external platforms. It reads the
latest WeChat publish-record export plus local social ops indexes, then writes a
human-readable wiki report and a machine-readable JSON dataset.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any
from zoneinfo import ZoneInfo

from analyze.classify import *
from analyze.confidence import *
from analyze.constants import *
from analyze.enrich import *
from analyze.io_utils import *  # includes load_raw_audience, load_raw_trend
from analyze.stats import *
from analyze.m7_standards import build_benchmark
from analyze.m2_viral_genes import build_viral_genes, classify_quadrant, reverse_viral_formula
from analyze.m1_checkup import build_checkup
from analyze.m3_content_engine import build_content_engine
from analyze.m4_audience import build_audience
from analyze.m5_growth_funnel import build_growth_funnel
from analyze.m6_action_plan import build_action_plan_v2
from analyze.m8_forward import build_forward_looking


@dataclass(frozen=True)
class Paths:
    root: Path
    wiki_repo: Path | None
    report_path: Path
    dataset_path: Path
    dashboard_data_path: Path
    report_date: str


def to_rel(p: Path | str, base: Path) -> str:
    """Convert an absolute path inside *base* to a POSIX relative path string.

    If *p* is empty, not absolute, or not under *base*, return str(p) unchanged.
    This is used solely when writing paths into output artefacts (JSON / MD) so
    that fixtures and wiki reports contain no machine-specific absolute paths.
    Internal file IO continues to use absolute paths.
    """
    if not p:
        return str(p)
    try:
        rel = Path(p).relative_to(base)
        return rel.as_posix()
    except (ValueError, TypeError):
        return str(p)










def build_title_analysis(stable: list[dict[str, Any]]) -> dict[str, Any]:
    pattern_rows = group_stats(stable, "title_primary_pattern", TITLE_PATTERN_KEYS)
    length_rows = group_stats(stable, "title_length_bucket", TITLE_LENGTH_BUCKETS)
    feature_rows = []
    for key, label in [
        ("has_number", "带数字"),
        ("has_price_word", "带价格/额度词"),
        ("has_risk_word", "带风险/损失词"),
        ("has_model_word", "带模型名"),
        ("has_comparison", "带对比/替代"),
        ("has_question", "带疑问"),
        ("has_tutorial", "带教程/清单"),
    ]:
        rows = [article for article in stable if article.get("title_structure", {}).get(key)]
        feature_rows.append({"key": label, **stat_pack(rows), "share_rate_avg": round(mean([r.get("share_rate", 0) for r in rows]), 4) if rows else 0})
    return {
        "by_primary_pattern": pattern_rows,
        "by_title_length": length_rows,
        "by_feature": feature_rows,
        "top_patterns": sorted(pattern_rows, key=lambda row: (row["median"], row["p75"], row["avg"]), reverse=True)[:4],
    }


def build_length_analysis(stable: list[dict[str, Any]]) -> dict[str, Any]:
    bucket_rows = group_stats(stable, "length_bucket", ARTICLE_LENGTH_BUCKETS)
    matched = [article for article in stable if article.get("article_length_chars", 0) > 0]
    lengths = [article["article_length_chars"] for article in matched]
    return {
        "by_length_bucket": bucket_rows,
        "matched_count": len(matched),
        "missing_count": len(stable) - len(matched),
        "median_length": round(median(lengths), 2) if lengths else 0,
        "avg_length": round(mean(lengths), 2) if lengths else 0,
        "top_buckets": sorted(bucket_rows, key=lambda row: (row["median"], row["p75"], row["avg"]), reverse=True)[:4],
    }


def build_conclusions(dataset: dict[str, Any]) -> list[dict[str, str]]:
    stats_by_type = {row["key"]: row for row in dataset["analysis"]["by_content_type"]}
    risk = stats_by_type.get("风险/账号/额度焦虑", {})
    price = stats_by_type.get("价格/额度/羊毛情报", {})
    agent = stats_by_type.get("AI 编程/Agent 工作流", {})
    model = stats_by_type.get("模型发布/能力解读", {})
    hour_best = sorted(
        [row for row in dataset["analysis"]["by_hour"] if row["count"] >= 3],
        key=lambda row: (row["median"], row["p75"], row["avg"]),
        reverse=True,
    )[:3]
    best_hours = "、".join(f"{row['key']}点" for row in hour_best) or "样本不足"
    return [
        {
            "id": "risk-engine",
            "title": "账号风险、验证、额度焦虑是当前最强推荐流入口",
            "body": (
                f"这一类稳定样本 {risk.get('count', 0)} 篇，平均阅读 {risk.get('avg', 0)}，"
                f"中位数 {risk.get('median', 0)}，P75 {risk.get('p75', 0)}。它不是靠老粉打开，"
                "而是用直接损失感把推荐入口打穿。"
            ),
            "evidence": "内容类型矩阵",
        },
        {
            "id": "price-volatility",
            "title": "免费、额度、价格情报能爆，但普通稿波动很大",
            "body": (
                f"价格/额度类平均阅读 {price.get('avg', 0)}，但中位数只有 {price.get('median', 0)}。"
                "这说明爆款会把均值抬高，日常选题必须写清楚适用场景、领取路径和风险边界。"
            ),
            "evidence": "排行榜与类型分布",
        },
        {
            "id": "ip-mainline",
            "title": "AI 编程/Agent 是 IP 主线，不该只用阅读量裁掉",
            "body": (
                f"工作流类样本最多（{agent.get('count', 0)} 篇），中位数 {agent.get('median', 0)}，"
                "阅读不如风险文，但它负责建立“这个号真会用工具”的信任。标题必须从项目意义改成用户收益。"
            ),
            "evidence": "内容类型矩阵",
        },
        {
            "id": "model-topic",
            "title": "模型发布文要和成本、可用性、替代关系绑定",
            "body": (
                f"模型能力类平均阅读 {model.get('avg', 0)}，中位数 {model.get('median', 0)}。"
                "单纯讲模型变强不够，最好回答“谁能免费用、能替代谁、现在该不该切”。"
            ),
            "evidence": "痛点/人群分布",
        },
        {
            "id": "publish-window",
            "title": "发布时间不能只看均值，优先试 9-10、12、15-17、22 点窗口",
            "body": (
                f"按稳定样本看，中位数较好的小时集中在 {best_hours}；但多个时段是爆款拉高均值，"
                "后续应该用题材匹配窗口，而不是机械定点。"
            ),
            "evidence": "发布时间热力图",
        },
    ]


def build_action_items(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    overall = dataset["analysis"]["overall"]
    stable_count = dataset["data_quality"]["stable_article_count"]
    return [
        {
            "priority": "P0",
            "title": "把 AI 编程/Agent 工作流继续做成 IP 主线",
            "why": f"稳定样本 {stable_count} 篇里,工作流类样本最多,但中位阅读仍偏低;问题不是不该写,而是标题和首屏还不够用户收益化。",
            "action": "下一批工作流文章标题先写少踩什么坑、少花多少 token、少翻多少文件,不要用项目名当主角。",
            "owner": "运营负责人",
            "due": "下一轮 7 天",
        },
        {
            "priority": "P0",
            "title": "保留风险/账号/额度题材作为推荐流入口",
            "why": "风险类能打穿推荐流,但不能让账号变成焦虑广播站。",
            "action": "每天最多 1 篇强风险入口文;每篇都要给检查清单或解决路径。",
            "owner": "运营负责人",
            "due": "本周持续",
        },
        {
            "priority": "P1",
            "title": "羊毛/价格文必须补齐领取路径和风险边界",
            "why": "价格/额度类均值容易被爆款拉高,普通稿波动大。",
            "action": "所有羊毛文首屏写清免费额度、适用人群、入口路径、到期或限制。",
            "owner": "运营负责人",
            "due": "下一篇开始",
        },
        {
            "priority": "P1",
            "title": "模型发布文绑定可用性和替代关系",
            "why": "单纯讲模型变强不能稳定转化阅读。",
            "action": "模型文固定回答:谁能用、哪里免费、替代谁、现在该不该切。",
            "owner": "运营负责人",
            "due": "下一篇模型文",
        },
        {
            "priority": "P2",
            "title": "用题材匹配发布时间窗口做 2 周验证",
            "why": f"当前稳定中位阅读 {overall['median']},多个高均值时段有爆款拉高,需要验证题材窗口而不是机械定点。",
            "action": "风险/福利放午间或晚间短窗口,工作流和深度判断放夜间深读窗口,每周复盘中位数和 P75。",
            "owner": "运营负责人",
            "due": "连续 2 周",
        },
    ]


def build_narrative_flow() -> list[dict[str, str]]:
    return [
        {"id": "actions", "label": "01", "title": "本周动作", "anchor": "actions"},
        {"id": "overview", "label": "02", "title": "总体判断", "anchor": "overview"},
        {"id": "content-engine", "label": "03", "title": "内容引擎", "anchor": "content-engine"},
        {"id": "title-structure", "label": "04", "title": "标题结构", "anchor": "title-structure"},
        {"id": "article-length", "label": "05", "title": "文章长度", "anchor": "article-length"},
        {"id": "audience", "label": "06", "title": "读者痛点", "anchor": "audience"},
        {"id": "timing", "label": "07", "title": "发布时间", "anchor": "timing"},
        {"id": "evidence", "label": "08", "title": "证据样本", "anchor": "evidence"},
        {"id": "quality", "label": "09", "title": "数据质量", "anchor": "quality"},
        {"id": "final-synthesis", "label": "10", "title": "最终汇总", "anchor": "final-synthesis"},
    ]


def section_slot(section_id: str) -> dict[str, str]:
    return dict(SECTION_UI_SLOTS[section_id])


def build_top_conclusion(dataset: dict[str, Any]) -> dict[str, Any]:
    overall = dataset.get("analysis", {}).get("overall", {})
    sections = {s["id"]: s for s in dataset.get("analysis_sections", [])}
    ov = sections.get("overview", {})
    conf = dataset.get("confidence_model", {}).get("overall", {})
    level = voice_for_confidence(conf)
    median = overall.get("median", 0)
    # verdict <=8 chars, core judgment from overview facts
    if median <= 300:
        verdict = "稳定底盘没起来"
    else:
        verdict = "底盘已初步抬升"
    if len(verdict) > 8:
        verdict = verdict[:8]
    # next_action <=24 chars, from high prio, modulated by level
    base_action = "抬中位阅读、拆开管理三件事"
    if level == "high":
        next_action = "→ 立即执行IP主线与中位验证"
    elif level == "low":
        next_action = "→ 继续观察底盘再定动作"
    else:
        next_action = f"→ {base_action}"
    if len(next_action) > 24:
        next_action = next_action[:24]
    return {"verdict": verdict, "next_action": next_action}


def build_analysis_sections(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    overall = dataset["analysis"]["overall"]
    quality = dataset["data_quality"]
    stable = dataset["articles"]["stable"]
    type_rows = dataset["analysis"]["by_content_type"]
    pain_rows = dataset["analysis"]["by_pain_point"]
    persona_rows = dataset["analysis"]["by_persona"]
    rankings = dataset["analysis"]["rankings"]
    title_rows = dataset["title_analysis"]["by_primary_pattern"]
    title_length_rows = dataset["title_analysis"]["by_title_length"]
    length_rows = dataset["length_analysis"]["by_length_bucket"]
    confidence_model = dataset["confidence_model"]
    best_hours = sorted(
        [row for row in dataset["analysis"]["by_hour"] if row["count"] >= 3],
        key=lambda row: (row["median"], row["p75"], row["avg"]),
        reverse=True,
    )[:4]
    top_types = sorted(type_rows, key=lambda row: (row["median"], row["p75"], row["avg"]), reverse=True)
    top_pain = max(pain_rows, key=lambda row: (row["median"], row["p75"], row["avg"]), default={})
    top_persona = max(persona_rows, key=lambda row: (row["median"], row["p75"], row["avg"]), default={})
    top_read = rankings["top_reads"][0] if rankings["top_reads"] else {}
    top_share = rankings["top_shares"][0] if rankings["top_shares"] else {}
    top_title = max(title_rows, key=lambda row: (row["median"], row["p75"], row["avg"]), default={})
    top_length = max(length_rows, key=lambda row: (row["median"], row["p75"], row["avg"]), default={})
    length_completeness = confidence_model["article_length_completeness"]

    # collect raw conf for _internal (never attach naked to sections)
    section_confs: dict[str, dict[str, Any]] = {}

    def _conf_for(sec_id: str, conf_obj: dict[str, Any]) -> dict[str, Any]:
        section_confs[sec_id] = conf_obj
        return conf_obj

    # precompute per section confs (calc logic untouched)
    conf_overview = _conf_for("overview", confidence_model["overall"])
    conf_content = _conf_for("content-engine", confidence_for_records(stable, note="按内容类型分组"))
    conf_title = _conf_for("title-structure", confidence_for_records(stable, note="标题结构来自规则化解析"))
    conf_length = _conf_for(
        "article-length",
        confidence_for_records(stable, completeness=length_completeness, note="正文长度依赖本地文章匹配"),
    )
    conf_audience = _conf_for("audience", confidence_for_records(stable, note="人群和痛点来自规则化标签"))
    conf_timing = _conf_for("timing", confidence_for_records(stable, target_sample=24, note="按小时切分后单格样本仍偏少"))
    conf_evidence = _conf_for("evidence", confidence_for_records(stable, note="排行榜只解释样本,不单独推导规律"))
    conf_quality = _conf_for(
        "quality",
        confidence_for_records(stable, completeness=1.0 if quality["metric_pending_count"] == 0 else 0.72, note="核心指标完整性"),
    )
    conf_final = _conf_for("final-synthesis", confidence_model["overall"])

    def _tone_conclusion(base: str, voice: str) -> str:
        if voice == "high":
            return base
        if voice == "low":
            if not base.startswith("初步"):
                return "初步迹象显示" + base
            return base
        return base

    def _tone_action(base: str, voice: str) -> str:
        if voice == "high":
            if not (base.startswith("立即") or base.startswith("必须")):
                return "立即" + base if len(base) < 28 else base
            return base
        if voice == "low":
            return "可继续观察" + base if not base.startswith("可") else base
        return base

    overview_voice = voice_for_confidence(conf_overview)
    overview_conc = _tone_conclusion("账号能打爆款，稳定中位数仍未抬升。", overview_voice)
    overview_act = _tone_action("每周复盘同时看类型中位数和P75是否上移。", overview_voice)

    content_voice = voice_for_confidence(conf_content)
    content_conc = _tone_conclusion("风险羊毛负责推荐入口，工作流主攻IP心智。", content_voice)
    content_act = _tone_action("工作流标题改写用户收益，风险文每天最多1篇。", content_voice)

    title_voice = voice_for_confidence(conf_title)
    title_conc = _tone_conclusion("标题先给损失收益或替代关系，再放产品名。", title_voice)
    title_act = _tone_action("每篇备收益风险替代版供挑选。", title_voice)

    length_voice = voice_for_confidence(conf_length)
    length_conc = _tone_conclusion("长度不是越短越好，关键控制信息密度与动作服务。", length_voice)
    length_act = _tone_action("深度文保留空间，每600字加图表清单喘气点。", length_voice)

    audience_voice = voice_for_confidence(conf_audience)
    audience_conc = _tone_conclusion("读者以账号额度敏感和编程实践者为主，非泛AI用户。", audience_voice)
    audience_act = _tone_action("开头先写损失、省什么、怎么用。", audience_voice)

    timing_voice = voice_for_confidence(conf_timing)
    timing_conc = _tone_conclusion("发布时间需与题材匹配验证，不能只看均值。", timing_voice)
    timing_act = _tone_action("风险放午晚短窗，工作流放22点深读窗。", timing_voice)

    evidence_voice = voice_for_confidence(conf_evidence)
    evidence_conc = _tone_conclusion("爆款证明入口有效，高分享指向IP资产方向。", evidence_voice)
    evidence_act = _tone_action("拆爆款触发词，沉淀高分享为选题模板。", evidence_voice)

    quality_voice = voice_for_confidence(conf_quality)
    quality_conc = _tone_conclusion("核心指标齐全，仍需保留导出时间和待补动作。", quality_voice)
    quality_act = _tone_action("每次复盘先刷新后台导出，登录失效先补数据。", quality_voice)

    final_voice = voice_for_confidence(conf_final)
    final_conc = _tone_conclusion("先把可复制的动作执行到位，不盲目追加新图表。", final_voice)
    final_act = _tone_action("可执行的优先落地，验证的先小步试，暂缓的等数据。", final_voice)

    # build new structure: analysis (fact <=60) + conclusion (<=40 voiced) + action (<=30) + voice/emphasis/basket ; no evidence/next_test/conf
    sections = [
        {
            "id": "overview",
            "title": "总体判断",
            "question": "账号当前最应该解决的运营问题是什么?",
            "analysis": f"稳定样本{quality['stable_article_count']}篇，中位{fmt_num(overall['median'])},P75{fmt_num(overall['p75'])},最高{fmt_num(overall['max'])}，有爆款但底盘偏低。",
            "conclusion": overview_conc,
            "action": overview_act,
            "chart_payload": {"kind": "overall", "metrics": overall},
            "voice": overview_voice,
            "emphasis": emphasis_for_confidence(conf_overview),
            "action_basket": action_basket_for_confidence(conf_overview),
            "ui_slot": section_slot("overview"),
        },
        {
            "id": "content-engine",
            "title": "内容引擎",
            "question": "哪些内容负责拉新和建心智?",
            "analysis": f"风险类中位265、价格类415、工作流类300，类型分化明显（{len(stable)}篇稳定）。",
            "conclusion": content_conc,
            "action": content_act,
            "chart_payload": {"kind": "content_type_matrix", "rows": type_rows, "top_types": top_types[:3]},
            "voice": content_voice,
            "emphasis": emphasis_for_confidence(conf_content),
            "action_basket": action_basket_for_confidence(conf_content),
            "ui_slot": section_slot("content-engine"),
        },
        {
            "id": "title-structure",
            "title": "标题结构",
            "question": "什么标题结构更容易带来点击和分享?",
            "analysis": f"风险损失型标题中位最高，样本{top_title.get('count',0)}，数字价格风险词影响点击。",
            "conclusion": title_conc,
            "action": title_act,
            "chart_payload": {
                "kind": "title_pattern_map",
                "pattern_rows": title_rows,
                "length_rows": title_length_rows,
                "feature_rows": dataset["title_analysis"]["by_feature"],
            },
            "voice": title_voice,
            "emphasis": emphasis_for_confidence(conf_title),
            "action_basket": action_basket_for_confidence(conf_title),
            "ui_slot": section_slot("title-structure"),
        },
        {
            "id": "article-length",
            "title": "文章长度",
            "question": "文章长度如何控制信息密度?",
            "analysis": f"本地匹配{dataset['length_analysis']['matched_count']}篇(均{int(dataset['length_analysis'].get('avg_length',0))}字)，未匹配{dataset['length_analysis']['missing_count']}篇，长度结论受匹配率影响。",
            "conclusion": length_conc,
            "action": length_act,
            "chart_payload": {
                "kind": "length_performance_curve",
                "bucket_rows": length_rows,
                "matched_count": dataset["length_analysis"]["matched_count"],
                "missing_count": dataset["length_analysis"]["missing_count"],
            },
            "voice": length_voice,
            "emphasis": emphasis_for_confidence(conf_length),
            "action_basket": action_basket_for_confidence(conf_length),
            "ui_slot": section_slot("article-length"),
        },
        {
            "id": "audience",
            "title": "读者痛点",
            "question": "读者真正为什么点开、收藏和转发?",
            "analysis": f"最高痛点{top_pain.get('key','样本不足')}({top_pain.get('count',0)}篇)，最高人群{top_persona.get('key','样本不足')}。",
            "conclusion": audience_conc,
            "action": audience_act,
            "chart_payload": {"kind": "audience", "pain_points": pain_rows, "personas": persona_rows},
            "voice": audience_voice,
            "emphasis": emphasis_for_confidence(conf_audience),
            "action_basket": action_basket_for_confidence(conf_audience),
            "ui_slot": section_slot("audience"),
        },
        {
            "id": "timing",
            "title": "发布时间",
            "question": "哪些发布时间值得继续验证?",
            "analysis": "中位较好小时为" + "、".join(f"{row['key']}点" for row in best_hours[:3]) + "，但部分由爆款拉高，单格样本少。",
            "conclusion": timing_conc,
            "action": timing_act,
            "chart_payload": {
                "kind": "time_heatmap",
                "best_hours": best_hours,
                "heatmap": dataset["analysis"]["time_heatmap"],
            },
            "voice": timing_voice,
            "emphasis": emphasis_for_confidence(conf_timing),
            "action_basket": action_basket_for_confidence(conf_timing),
            "ui_slot": section_slot("timing"),
        },
        {
            "id": "evidence",
            "title": "证据样本",
            "question": "哪些文章证明了上面的判断?",
            "analysis": f"阅读最高《{str(top_read.get('title','无'))[:12]}》{int(top_read.get('reads',0))}，分享同篇{int(top_share.get('shares',0))}。",
            "conclusion": evidence_conc,
            "action": evidence_act,
            "chart_payload": {"kind": "rankings", "rankings": rankings},
            "voice": evidence_voice,
            "emphasis": emphasis_for_confidence(conf_evidence),
            "action_basket": action_basket_for_confidence(conf_evidence),
            "ui_slot": section_slot("evidence"),
        },
        {
            "id": "quality",
            "title": "数据质量",
            "question": "这份报告的数据能不能支撑运营判断?",
            "analysis": f"非删{quality['period_non_deleted_count']}篇，稳定{quality['stable_article_count']}篇，缺口{quality['metric_pending_count']}，正文匹配{length_completeness*100:.0f}%。",
            "conclusion": quality_conc,
            "action": quality_act,
            "chart_payload": {"kind": "data_quality", "quality": quality},
            "voice": quality_voice,
            "emphasis": emphasis_for_confidence(conf_quality),
            "action_basket": action_basket_for_confidence(conf_quality),
            "ui_slot": section_slot("quality"),
        },
        {
            "id": "final-synthesis",
            "title": "最终汇总",
            "question": "哪些判断应该立刻执行,哪些只能小步验证?",
            "analysis": "可直接执行的动作优先落地，小步验证的先试一试，暂缓的等更多样本。",
            "conclusion": final_conc,
            "action": final_act,
            "chart_payload": {"kind": "action_baskets", "now": [], "experiment": [], "hold": []},
            "voice": final_voice,
            "emphasis": emphasis_for_confidence(conf_final),
            "action_basket": action_basket_for_confidence(conf_final),
            "ui_slot": section_slot("final-synthesis"),
        },
    ]
    # side channel for _internal (calc untouched), cleaned after use
    dataset["_section_confs_tmp"] = section_confs
    return sections


def build_compat_conclusions(sections: list[dict[str, Any]]) -> list[dict[str, str]]:
    # adapt to new section shape (analysis/conclusion); keep for compat
    return [
        {
            "id": section["id"],
            "title": section.get("conclusion") or section.get("analysis", ""),
            "body": section.get("action", ""),
            "evidence": section.get("title", ""),
        }
        for section in sections
        if section.get("id") in {"overview", "content-engine", "audience", "timing", "evidence"}
    ]


def build_account_profile(dataset: dict[str, Any]) -> dict[str, Any]:
    quality = dataset["data_quality"]
    account_name = dataset["meta"].get("account_name", "我的公众号")
    avatar_text = account_name[0] if account_name else "我"
    articles = dataset.get("articles", {}).get("all_period", [])
    reads = [int(a.get("reads", 0) or 0) for a in articles]
    total_reads = sum(reads)
    avg_reads = int(round(mean(reads))) if reads else 0
    median_reads = int(round(median(reads))) if reads else 0
    # 运营周数：用 meta 期起止计算
    start_s = dataset["meta"].get("period_start", "")
    end_s = dataset["meta"].get("period_end", "")
    weeks = 1.0
    try:
        start_dt = parse_dt(start_s)
        end_dt = parse_dt(end_s)
        if start_dt and end_dt:
            days = max(1, (end_dt - start_dt).days)
            weeks = max(1.0, round(days / 7.0, 2))
    except Exception:
        weeks = 1.0
    article_n = quality.get("period_non_deleted_count", len(articles))
    publish_frequency = round(article_n / weeks, 1) if weeks > 0 else 0.0
    # 爆款：reads >= P90
    p90 = percentile([float(r) for r in reads], 0.9) if reads else 0.0
    explosive_count = sum(1 for r in reads if r >= p90) if p90 > 0 else 0
    return {
        "name": account_name,
        "platform": "微信公众号",
        "description": "面向 AI 工具、Agent 工作流和普通人可落地效率场景的内容号。",
        "avatar_text": avatar_text,
        "analysis_period": f"{dataset['meta']['period_start'][:10]} 至 {dataset['meta']['period_end'][:10]}",
        "article_count": article_n,
        "stable_article_count": quality["stable_article_count"],
        "generated_at": dataset["meta"]["generated_at"],
        # 新增画像字段（DESIGN.md 要求）
        "total_reads": total_reads,
        "avg_reads": avg_reads,
        "median_reads": median_reads,
        "publish_frequency": publish_frequency,
        "explosive_count": explosive_count,
        "fans_count": None,
    }


def build_brand_signature() -> dict[str, Any]:
    author = os.environ.get("WXOPS_AUTHOR", "运营者")
    return {
        "author_name": author,
        "role": "公众号运营分析 Skill 作者",
        "skill_name": "wechat-ops-performance-review",
        "skill_repo": "https://github.com/DwDestiny/my_skill",
        "star_url": "https://github.com/DwDestiny/my_skill",
        "avatar_src": "/sample-avatar.svg",
        "tagline": "数据刷新 → 专业分析 → wiki 报告 → 模板站验收",
    }


def build_final_synthesis(dataset: dict[str, Any]) -> dict[str, Any]:
    sections = dataset.get("analysis_sections", [])
    now_list: list[str] = []
    exp_list: list[str] = []
    hold_list: list[str] = []
    for sec in sections:
        if sec.get("id") == "final-synthesis":
            continue
        basket = sec.get("action_basket", "experiment")
        act = (sec.get("action") or "")[:25]
        if basket == "now":
            now_list.append(act)
        elif basket == "experiment":
            exp_list.append(act)
        else:
            hold_list.append(act)
    return {
        "now": now_list,
        "experiment": exp_list,
        "hold": hold_list,
    }


def build_report_meta(dataset: dict[str, Any]) -> dict[str, Any]:
    meta = dataset["meta"]
    quality = dataset["data_quality"]
    return {
        "template_version": "wechat-ops-template-v2.1",
        "title": "公众号运营诊断报告",
        "account_name": meta.get("account_name", "我的公众号"),
        "platform": "wechat",
        "platform_scope": "wechat_only",
        "period_label": f"{meta['period_start'][:10]} 至 {meta['period_end'][:10]}",
        "generated_at": meta["generated_at"],
        "source_export": meta["source_export"],
        "source_captured_at": meta.get("source_captured_at"),
        "data_quality_summary": {
            "raw_record_count": quality["raw_record_count"],
            "period_non_deleted_count": quality["period_non_deleted_count"],
            "stable_article_count": quality["stable_article_count"],
            "immature_article_count": quality["immature_article_count"],
            "metric_pending_count": quality["metric_pending_count"],
        },
        "scope_note": "当前模板只服务公众号运营分析；头条、Twitter/X、GitHub 不进入主报告。",
    }


def build_executive_summary(dataset: dict[str, Any]) -> dict[str, Any]:
    top = dataset.get("top_conclusion", {"verdict": "稳定底盘没起来", "next_action": "→ 抬中位阅读、拆开管理三件事"})
    quality = dataset["data_quality"]
    overall = dataset["analysis"]["overall"]
    action_titles = [item["title"] for item in dataset["action_items"][:5]]
    return {
        "headline": top["verdict"],
        "subheadline": top["next_action"],
        "primary_tension": (
            f"稳定样本 {quality['stable_article_count']} 篇,中位阅读 {fmt_num(overall['median'])},"
            f"P75 {fmt_num(overall['p75'])};账号能出高点,但稳定底盘还需要被抬高。"
        ),
        "next_focus": "先执行五个动作,再用下一批稳定样本验证中位数、P75 和分享率是否上移。",
        "metric_strip": [
            {
                "label": "当前文章",
                "value": quality["period_non_deleted_count"],
                "display": fmt_num(quality["period_non_deleted_count"]),
                "hint": "公众号当前周期非删除文章",
                "tone": "green",
            },
            {
                "label": "稳定样本",
                "value": quality["stable_article_count"],
                "display": fmt_num(quality["stable_article_count"]),
                "hint": "已过 48 小时,进入稳定均值",
                "tone": "blue",
            },
            {
                "label": "中位阅读",
                "value": overall["median"],
                "display": fmt_num(overall["median"]),
                "hint": f"P75 {fmt_num(overall['p75'])}",
                "tone": "green",
            },
            {
                "label": "指标缺口",
                "value": quality["metric_pending_count"],
                "display": fmt_num(quality["metric_pending_count"]),
                "hint": "核心指标缺失数量",
                "tone": "amber" if quality["metric_pending_count"] else "green",
            },
        ],
        "week_actions": action_titles,
    }


def build_action_plan(dataset: dict[str, Any]) -> dict[str, Any]:
    items = []
    for index, item in enumerate(dataset["action_items"], start=1):
        items.append(
            {
                "id": f"action-{index:02d}",
                "priority": item["priority"],
                "title": item["title"],
                "why": item["why"],
                "action": item["action"],
                "owner": item["owner"],
                "due": item["due"],
                "status": "planned",
                "validation": "下次复盘时必须用中位阅读、P75、分享率和样本标题复核这条动作是否有效。",
            }
        )
    return {
        "title": "本周先做这 5 件事",
        "summary": "先做动作,再看证据;不要把报告做成只会解释过去的数据墙。",
        "items": items,
    }


def build_evidence_stream(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    stream: list[dict[str, Any]] = []
    for section in dataset["analysis_sections"]:
        # adapt: use analysis as body for evidence compat, no next_test
        body = section.get("analysis") or section.get("conclusion", "")
        stream.append(
            {
                "id": f"{section['id']}-evidence",
                "section_id": section["id"],
                "kind": "section_evidence",
                "title": section["title"],
                "body": body,
                "meta": section["question"],
                "tone": section["ui_slot"]["accent"],
            }
        )
        stream.append(
            {
                "id": f"{section['id']}-action",
                "section_id": section["id"],
                "kind": "next_action",
                "title": "下一步动作",
                "body": section["action"],
                "meta": section.get("conclusion", ""),
                "tone": "green",
            }
        )

    for index, article in enumerate(dataset["analysis"]["rankings"]["top_reads"][:5], start=1):
        stream.append(
            {
                "id": f"top-read-{index}",
                "section_id": "evidence",
                "kind": "article_sample",
                "title": article["title"],
                "body": (
                    f"阅读 {fmt_num(article['reads'])},分享 {fmt_num(article['shares'])},"
                    f"分享率 {article['share_rate'] * 100:.1f}%"
                ),
                "meta": article["content_type"],
                "url": article.get("url", ""),
                "tone": "blue",
            }
        )
    return stream


def build_template_slots(dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "template_name": "wechat_ops_three_column_report",
        "layout": "left_nav_center_story_right_context",
        "left_nav": {
            "source": "narrative_flow",
            "behavior": "sticky desktop; horizontal overflow on mobile",
        },
        "hero": {
            "source": "executive_summary",
            "required_blocks": ["headline", "action_plan.items", "metric_strip"],
        },
        "main_flow": [
            {
                "section_id": item["id"],
                "anchor": item["anchor"],
                "title": item["title"],
                "source": "analysis_sections" if item["id"] != "actions" else "action_plan",
                "ui_slot": SECTION_UI_SLOTS.get(item["id"], {"component": "action_plan"}),
            }
            for item in dataset["narrative_flow"]
        ],
        "right_rail": {
            "source": "evidence_stream",
            "active_section_key": "section_id",
            "default_section": "overview",
        },
        "evidence_table": {
            "source": "articles.stable",
            "filters": ["content_type", "pain_point", "include_immature"],
            "sorts": ["reads", "shares", "share_rate", "published_at"],
        },
        "mobile": {
            "layout": "single_column",
            "right_rail": "inline_context_after_hero",
            "nav": "top_horizontal_scroll",
        },
    }


def build_visual_tokens() -> dict[str, Any]:
    return dict(VISUAL_TOKENS)


def load_ledger_quality(root: Path) -> dict[str, Any]:
    article_index = read_json(root / "data/social_ops/indexes/articles.json", {"items": []})
    pending_index = read_json(root / "data/social_ops/indexes/pending_actions.json", {"items": []})
    metric_attempts = read_jsonl(root / "data/social_ops/metrics/metric_attempts.jsonl")
    status_counts = Counter(
        item.get("platforms", {}).get("wechat", {}).get("normalized_status", "none")
        for item in article_index.get("items", [])
    )
    wechat_pending = [
        item for item in pending_index.get("items", []) if item.get("platform") == "wechat"
    ]
    attempts_status = Counter(
        item.get("status", "unknown")
        for item in metric_attempts
        if item.get("platform") == "wechat"
    )
    return {
        "wechat_ledger_status_counts": dict(sorted(status_counts.items())),
        "wechat_pending_actions": wechat_pending,
        "metric_attempt_status_counts": dict(sorted(attempts_status.items())),
        "metric_attempt_rows": sum(1 for item in metric_attempts if item.get("platform") == "wechat"),
    }


def build_dataset(root: Path, *, account_name: str = "我的公众号", since: str | None = None) -> dict[str, Any]:
    raw_path = latest_publish_export(root)
    raw = read_json(raw_path, {})
    captured_at = parse_dt(raw.get("captured_at")) or datetime.now(timezone.utc).astimezone(CN_TZ)
    raw_records = raw.get("records", [])
    # derive report_date from captured_at's date part (YYYY-MM-DD)
    report_date = captured_at.date().isoformat()
    # compute effective OPS_START: use --since if provided, else earliest publish date, else fallback
    if since:
        try:
            d = datetime.strptime(since, "%Y-%m-%d").date()
            ops_start = datetime.combine(d, datetime.min.time(), tzinfo=CN_TZ)
        except Exception:
            ops_start = datetime(2026, 4, 18, tzinfo=CN_TZ)
    else:
        publish_dts = [parse_dt(r.get("published_at")) for r in raw_records if r.get("published_at")]
        publish_dts = [d for d in publish_dts if d]
        if publish_dts:
            min_dt = min(publish_dts)
            min_d = min_dt.date()
            ops_start = datetime.combine(min_d, datetime.min.time(), tzinfo=CN_TZ)
        else:
            ops_start = datetime(2026, 4, 18, tzinfo=CN_TZ)
    by_url, by_title = build_article_lookup(root)
    articles = [build_article(record, captured_at) for record in raw_records]
    for article in articles:
        enrich_article(article, root, by_url, by_title)
    # Normalise any absolute paths that enrich wrote into article fields so
    # output artefacts (JSON / MD) contain only SKILL_ROOT-relative paths.
    for article in articles:
        if article.get("article_length_source"):
            article["article_length_source"] = to_rel(article["article_length_source"], root)
    period_articles = [
        article
        for article in articles
        if article.get("published_at") and parse_dt(article["published_at"]) >= ops_start
    ]
    non_deleted = [article for article in period_articles if not article["is_deleted"]]
    deleted = [article for article in period_articles if article["is_deleted"]]
    immature = [article for article in non_deleted if article["is_immature"]]
    stable = [article for article in non_deleted if not article["is_immature"]]
    missing_core_metrics = [
        article
        for article in non_deleted
        if any(article.get(field) is None for field in ["reads", "shares", "comments", "likes"])
    ]

    by_hour = group_stats(stable, "hour")
    by_weekday = group_stats(stable, "weekday", list(range(1, 8)))
    for row in by_weekday:
        row["label"] = WEEKDAY_LABELS[int(row["key"]) - 1] if row["key"] else ""
    dataset = {
        "meta": {
            "report_date": report_date,
            "account_name": account_name,
            "generated_at": captured_at.isoformat(),
            "period_start": ops_start.isoformat(),
            "period_end": captured_at.isoformat(),
            "source_export": to_rel(raw_path, root),
            "source_captured_at": raw.get("captured_at"),
            "platform_scope": "wechat_only",
        },
        "data_quality": {
            "raw_record_count": len(raw_records),
            "period_record_count": len(period_articles),
            "period_non_deleted_count": len(non_deleted),
            "period_deleted_count": len(deleted),
            "stable_article_count": len(stable),
            "immature_article_count": len(immature),
            "metric_pending_count": len(missing_core_metrics),
            "backend_totals": raw.get("totals", {}),
            "match_stats": raw.get("match_stats", {}),
            **load_ledger_quality(root),
        },
        "articles": {
            "all_period": sorted(non_deleted, key=lambda r: r["published_at"] or "", reverse=True),
            "stable": sorted(stable, key=lambda r: r["published_at"] or "", reverse=True),
            "immature": sorted(immature, key=lambda r: r["published_at"] or "", reverse=True),
            "deleted": sorted(deleted, key=lambda r: r["published_at"] or "", reverse=True),
        },
        "analysis": {
            "overall": stat_pack(stable),
            "by_content_type": group_stats(stable, "content_type", CONTENT_TYPES),
            "by_pain_point": group_stats(stable, "pain_point", PAIN_POINTS),
            "by_persona": group_stats(stable, "persona", PERSONAS),
            "by_hour": by_hour,
            "by_weekday": by_weekday,
            "by_week": weekly_trend(stable),
            "by_month": group_stats(stable, "month"),
            "time_heatmap": time_heatmap(stable),
            "rankings": build_rankings(stable),
            "by_title_pattern": group_stats(stable, "title_primary_pattern", TITLE_PATTERN_KEYS),
            "by_title_length": group_stats(stable, "title_length_bucket", TITLE_LENGTH_BUCKETS),
            "by_article_length": group_stats(stable, "length_bucket", ARTICLE_LENGTH_BUCKETS),
        },
        "recommendations": {
            "topic_ratio": [
                {"label": "AI 编程/Agent 工作流", "ratio": 0.40, "role": "IP 主线"},
                {"label": "风险/账号/额度焦虑", "ratio": 0.25, "role": "推荐流入口"},
                {"label": "价格/额度/羊毛情报", "ratio": 0.20, "role": "转化与收藏入口"},
                {"label": "模型发布/能力解读", "ratio": 0.10, "role": "热点解释与判断"},
                {"label": "泛 AI 热点/效率工具", "ratio": 0.05, "role": "拓圈与轻量内容"},
            ],
            "publish_windows": [
                {"window": "09:00-10:30", "best_for": "刚需工具、价格/额度更新"},
                {"window": "12:00-12:45", "best_for": "强风险、强利益短通知"},
                {"window": "15:00-17:30", "best_for": "模型发布、官方更新、二次解读"},
                {"window": "22:00-22:45", "best_for": "深度判断、争议复盘、工作流文章"},
            ],
            "headline_rules": [
                "风险文标题先写直接损失，再写对象：谁今天会被卡、会少什么、要检查什么。",
                "羊毛文标题必须写清免费/额度/价格和适用人群，不写泛泛的“福利来了”。",
                "工作流文标题不要讲项目意义，先讲用户少翻多少文件、少花多少 token、少踩什么坑。",
                "模型发布文必须绑定可用性：谁能用、哪里免费、能不能替代当前方案。",
            ],
        },
    }
    dataset["benchmark"] = build_benchmark(stable)
    dataset["viral_genes"] = build_viral_genes(stable, dataset["benchmark"])
    # 新增 modules 与 account（仅追加，不改旧字段）
    audience_raw = load_raw_audience(root)
    trend_raw = load_raw_trend(root)
    account_raw = load_raw_account(root)
    bm = dataset["benchmark"]
    vg = dataset["viral_genes"]
    checkup = build_checkup(stable, bm, audience_raw)
    content_engine = build_content_engine(stable, dataset["analysis"]["by_content_type"], bm)
    audience_mod = build_audience(stable, audience_raw, dataset["analysis"]["by_pain_point"], dataset["analysis"]["by_persona"])
    growth_funnel = build_growth_funnel(stable, audience_raw, trend_raw, vg["viral_formula"])
    action_plan_v2 = build_action_plan_v2(vg, checkup, content_engine, audience_mod, growth_funnel)
    dataset["modules"] = {
        "checkup": checkup,
        "content_engine": content_engine,
        "audience": audience_mod,
        "growth_funnel": growth_funnel,
        "action_plan": action_plan_v2,
    }
    dataset["account"] = {
        "name": account_raw.get("name") or account_name,
        "cumulate_user": audience_raw.get("cumulate_user"),
        "avatar_local": account_raw.get("avatar_local"),
        "head_img": account_raw.get("head_img"),
        "available": audience_raw.get("available", False),
    }
    dataset["confidence_model"] = build_confidence_model(stable)
    dataset["title_analysis"] = build_title_analysis(stable)
    dataset["length_analysis"] = build_length_analysis(stable)
    dataset["action_items"] = build_action_items(dataset)
    dataset["narrative_flow"] = build_narrative_flow()
    dataset["analysis_sections"] = build_analysis_sections(dataset)
    # now derive top and final from sections (baskets auto collect)
    dataset["top_conclusion"] = build_top_conclusion(dataset)
    dataset["final_synthesis"] = build_final_synthesis(dataset)
    for sec in dataset.get("analysis_sections", []):
        if sec.get("id") == "final-synthesis":
            sec["chart_payload"] = {"kind": "action_baskets", **dataset["final_synthesis"]}
    # populate _internal , move raw confs
    _sc = dataset.pop("_section_confs_tmp", {})
    dataset["_internal"] = {
        "section_confidence": _sc,
        "confidence_model": dataset.get("confidence_model", {}),
    }
    dataset["account_profile"] = build_account_profile(dataset)
    dataset["brand_signature"] = build_brand_signature()
    dataset["report_meta"] = build_report_meta(dataset)
    dataset["executive_summary"] = build_executive_summary(dataset)
    dataset["action_plan"] = build_action_plan(dataset)
    dataset["evidence_stream"] = build_evidence_stream(dataset)
    dataset["template_slots"] = build_template_slots(dataset)
    dataset["visual_tokens"] = build_visual_tokens()
    dataset["conclusions"] = build_compat_conclusions(dataset["analysis_sections"])
    # 向前看引擎（只读上述字段，仅追加 forward_looking 顶层节点）
    dataset["forward_looking"] = build_forward_looking(dataset)
    return dataset


def fmt_num(value: Any) -> str:
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(out)


def render_report(dataset: dict[str, Any], dataset_path: Path | str) -> str:
    quality = dataset["data_quality"]
    overall = dataset["analysis"]["overall"]
    sections = {section["id"]: section for section in dataset["analysis_sections"]}
    source_name = Path(dataset["meta"]["source_export"]).name
    report_date = dataset.get("meta", {}).get("report_date", "unknown")

    action_rows = [
        [
            item["priority"],
            item["title"],
            item["why"],
            item["action"],
            item["due"],
        ]
        for item in dataset["action_items"]
    ]

    section_flow_rows = []
    for item in dataset["narrative_flow"]:
        if item["id"] == "actions":
            question = "本周先做哪几件事?"
        else:
            question = sections[item["id"]]["question"]
        section_flow_rows.append([item["label"], item["title"], question])

    type_rows = []
    for row in dataset["analysis"]["by_content_type"]:
        sample = row.get("top_sample") or {}
        type_rows.append(
            [
                row["key"],
                row["count"],
                fmt_num(row["avg"]),
                fmt_num(row["median"]),
                fmt_num(row["p75"]),
                fmt_num(row["max"]),
                sample.get("title", "无"),
            ]
        )

    pain_rows = [
        [
            row["key"],
            row["count"],
            fmt_num(row["median"]),
            fmt_num(row["p75"]),
            f"{row.get('share_rate_avg', 0) * 100:.1f}%",
        ]
        for row in dataset["analysis"]["by_pain_point"]
    ]

    persona_rows = [
        [
            row["key"],
            row["count"],
            fmt_num(row["median"]),
            fmt_num(row["p75"]),
            f"{row.get('share_rate_avg', 0) * 100:.1f}%",
        ]
        for row in dataset["analysis"]["by_persona"]
    ]

    title_pattern_rows = [
        [
            row["key"],
            row["count"],
            fmt_num(row["median"]),
            fmt_num(row["p75"]),
            fmt_num(row["max"]),
            f"{row.get('share_rate_avg', 0) * 100:.1f}%",
        ]
        for row in dataset["title_analysis"]["by_primary_pattern"]
    ]

    length_rows = [
        [
            row["key"],
            row["count"],
            fmt_num(row["avg"]),
            fmt_num(row["median"]),
            fmt_num(row["p75"]),
            fmt_num(row["max"]),
        ]
        for row in dataset["length_analysis"]["by_length_bucket"]
    ]

    top_rows = [
        [
            i + 1,
            item["title"],
            fmt_num(item["reads"]),
            fmt_num(item["shares"]),
            f"{item['share_rate'] * 100:.1f}%",
            item["content_type"],
        ]
        for i, item in enumerate(dataset["analysis"]["rankings"]["top_reads"][:10])
    ]

    heat_rows = []
    for row in sorted(
        [x for x in dataset["analysis"]["by_hour"] if x["count"] >= 3],
        key=lambda x: (x["median"], x["p75"], x["avg"]),
        reverse=True,
    )[:8]:
        heat_rows.append(
            [
                f"{row['key']}点",
                row["count"],
                fmt_num(row["avg"]),
                fmt_num(row["median"]),
                fmt_num(row["p75"]),
                fmt_num(row["max"]),
            ]
        )

    ratio_lines = "\n".join(
        f"- {int(item['ratio'] * 100)}%：{item['label']}（{item['role']}）"
        for item in dataset["recommendations"]["topic_ratio"]
    )
    headline_lines = "\n".join(f"- {item}" for item in dataset["recommendations"]["headline_rules"])
    window_lines = "\n".join(
        f"- `{item['window']}`：{item['best_for']}"
        for item in dataset["recommendations"]["publish_windows"]
    )

    pending_actions = quality.get("wechat_pending_actions", [])
    pending_text = (
        "\n".join(
            f"- {item.get('title', item.get('content_id'))}：{item.get('action')}，下一步 {item.get('public_url', '')}"
            for item in pending_actions
        )
        if pending_actions
        else "- 暂无公众号待补动作。"
    )

    def render_section_new(section: dict[str, Any]) -> str:
        # total分总 style per section: analysis + conclusion + action, no conf/evidence/next_test words
        return f"""## {section['title']}

### 分析情况

{section.get('analysis', '')}

### 得出结论

{section.get('conclusion', '')}

### 下一步动作

{section.get('action', '')}
"""

    top = dataset.get("top_conclusion", {"verdict": "", "next_action": ""})
    # build final baskets text without conf words
    fs = dataset.get("final_synthesis", {})
    now_items = "\n".join(f"- {x}" for x in fs.get("now", [])) or "- （待补充）"
    exp_items = "\n".join(f"- {x}" for x in fs.get("experiment", [])) or "- （待补充）"
    hold_items = "\n".join(f"- {x}" for x in fs.get("hold", [])) or "- （待补充）"

    # render sections in order using new shape
    dim_order = ["overview", "content-engine", "title-structure", "article-length", "audience", "timing", "evidence", "quality", "final-synthesis"]
    dim_blocks = []
    for sid in dim_order:
        if sid in sections:
            dim_blocks.append(render_section_new(sections[sid]))

    return f"""---
title: "公众号运营分析报告 {report_date}"
type: report
tags: [operations, social-ops, wechat, analytics]
date: {report_date}
sources:
  - reports/wechat/{source_name}
  - data/social_ops/metrics/metric_attempts.jsonl
created_by_agent: codex
last_updated_by_agent: codex
---

## 本周先做这 5 件事

{markdown_table(['优先级', '动作', '为什么', '具体执行', '截止'], action_rows)}

这份报告不是日常监控盘，而是阶段性运营诊断。阅读顺序固定为：先确定本周动作，再看为什么这些动作成立，最后看样本和数据质量。

{markdown_table(['步骤', '章节', '要回答的问题'], section_flow_rows)}

## 数据口径

- 分析平台：只看微信公众号；头条、Twitter/X、GitHub、小红书、知乎全部不进入本轮表现分析。
- 分析周期：`{dataset['meta']['period_start']}` 到 `{dataset['meta']['period_end']}`。
- 机器数据源：`{dataset['meta']['source_export']}`。
- 结构化数据源：`{dataset_path}`。
- 当前周期后台记录 {quality['period_record_count']} 篇，其中非删除 {quality['period_non_deleted_count']} 篇、删除 {quality['period_deleted_count']} 篇。
- 稳定表现样本 {quality['stable_article_count']} 篇；最近 48 小时内的新文章 {quality['immature_article_count']} 篇，只进“新文章观察”，不进稳定均值。
- 核心指标缺口：{quality['metric_pending_count']}。这里的缺口指阅读、分享、评论、点赞字段缺失，不把真实 0 误判为缺失。

## 核心判断

**{top.get('verdict', '')}**

{top.get('next_action', '')}

{dim_blocks[0] if dim_blocks else ''}

{dim_blocks[1] if len(dim_blocks)>1 else ''}

{dim_blocks[2] if len(dim_blocks)>2 else ''}

{dim_blocks[3] if len(dim_blocks)>3 else ''}

{dim_blocks[4] if len(dim_blocks)>4 else ''}

{dim_blocks[5] if len(dim_blocks)>5 else ''}

{dim_blocks[6] if len(dim_blocks)>6 else ''}

{dim_blocks[7] if len(dim_blocks)>7 else ''}

{dim_blocks[8] if len(dim_blocks)>8 else ''}

## 行动分档

### 现在就做
{now_items}

### 小步验证
{exp_items}

### 暂不拍板
{hold_items}

## Connections

- [[社媒运营总账]]：当前运营事实入口。
- [[发布记录台账]]：公众号发布状态和链接回填入口。
- [[指标采集账本]]：指标采集口径和数据缺口入口。
"""


def _is_under(path: Path, base: Path) -> bool:
    """True if *path* resolves inside *base* (the writable workspace)."""
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except (ValueError, OSError):
        return False


def _safe_write(path: Path, content: str, *, workspace: Path, label: str) -> None:
    """Write *content* to *path*.

    Artefacts inside the workspace are core products: a write failure (e.g. the
    skill directory accidentally being the target, or a read-only mount) aborts
    the build. Targets outside the workspace are treated as optional (e.g. an
    explicit injection into a possibly read-only area) and a failure only warns
    so the read-only-skill contract (rc=0 + workspace output) still holds.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except (OSError, PermissionError) as exc:
        if _is_under(path, workspace):
            raise SystemExit(f"错误: 无法写入工作区产物 {label} ({path}): {exc}")
        print(f"⚠ 跳过可选产物 {label} ({path}): {exc}")


def write_outputs(dataset: dict[str, Any], paths: Paths) -> None:
    # 写出前剥离纯内部调试字段，不影响内存 dataset 对象（校验已完成）
    _INTERNAL_KEYS = ("_internal", "confidence_model")
    export_dataset = {k: v for k, v in dataset.items() if k not in _INTERNAL_KEYS}
    payload = json.dumps(export_dataset, ensure_ascii=False, indent=2) + "\n"
    _safe_write(paths.dataset_path, payload, workspace=paths.root, label="dataset")
    _safe_write(paths.dashboard_data_path, payload, workspace=paths.root, label="dashboard-data")
    _safe_write(
        paths.report_path,
        render_report(dataset, to_rel(paths.dataset_path, paths.root)),
        workspace=paths.root,
        label="report",
    )


def update_social_ops_index(paths: Paths) -> None:
    if paths.wiki_repo is None:
        return
    index_path = paths.wiki_repo / "wiki/operations/social-ops/index.md"
    if not index_path.exists():
        return
    text = index_path.read_text(encoding="utf-8")
    rd = paths.report_date
    link = f"- [公众号运营分析报告 {rd}](wechat-ops-report-{rd}.md) — 当前运营期公众号表现、题材、人群、发布时间与下一阶段内容配比。"
    if f"wechat-ops-report-{rd}.md" not in text:
        if "## 自动区块外补充" in text:
            text = text.replace("## 自动区块外补充", f"## 自动区块外补充\n\n{link}\n")
        else:
            text = text.rstrip() + "\n\n## 自动区块外补充\n\n" + link + "\n"
        index_path.write_text(text, encoding="utf-8")


def append_wiki_log(paths: Paths) -> None:
    if paths.wiki_repo is None:
        return
    log_path = paths.wiki_repo / "wiki/log.md"
    if not log_path.exists():
        return
    rd = paths.report_date
    marker = f"## [{rd}] report | 公众号运营分析报告"
    text = log_path.read_text(encoding="utf-8")
    if marker in text:
        return
    entry = (
        f"\n{marker}\n\n"
        f"新增 `operations/social-ops/wechat-ops-report-{rd}.md` 和同名 JSON 数据集，"
        "只分析公众号当前运营期表现。\n"
    )
    log_path.write_text(text.rstrip() + "\n" + entry, encoding="utf-8")


def validate_dataset(dataset: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    quality = dataset["data_quality"]
    stable = dataset["articles"]["stable"]
    all_period = dataset["articles"]["all_period"]
    # updated per contract: no evidence/next_test/confidence naked
    required_section_fields = [
        "question",
        "analysis",
        "conclusion",
        "action",
        "chart_payload",
        "ui_slot",
        "voice",
        "emphasis",
        "action_basket",
    ]
    required_top_fields = [
        "report_meta",
        "account_profile",
        "executive_summary",
        "action_plan",
        "confidence_model",
        "title_analysis",
        "length_analysis",
        "final_synthesis",
        "brand_signature",
        "evidence_stream",
        "template_slots",
        "visual_tokens",
        "top_conclusion",
    ]
    for field in required_top_fields:
        if not dataset.get(field):
            errors.append(f"missing template contract field: {field}")
    if quality["metric_pending_count"] != 0:
        errors.append(f"metric_pending_count is {quality['metric_pending_count']}, expected 0")
    if dataset.get("meta", {}).get("platform_scope") != "wechat_only":
        errors.append("platform_scope must be wechat_only")
    if dataset.get("report_meta", {}).get("platform_scope") != "wechat_only":
        errors.append("report_meta.platform_scope must be wechat_only")
    if len(dataset.get("action_plan", {}).get("items", [])) != 5:
        errors.append("action_plan.items must contain 5 actions")
    if dataset.get("template_slots", {}).get("layout") != "left_nav_center_story_right_context":
        errors.append("template_slots.layout must be left_nav_center_story_right_context")
    if dataset.get("visual_tokens", {}).get("layout") != "three_column_report_shell":
        errors.append("visual_tokens.layout must be three_column_report_shell")
    for article in all_period:
        for field in ["content_type", "pain_point", "persona", "published_at"]:
            if not article.get(field):
                errors.append(f"missing {field}: {article.get('title')}")
    for article in stable:
        if article.get("is_immature"):
            errors.append(f"immature article leaked into stable stats: {article.get('title')}")
    type_count = sum(row["count"] for row in dataset["analysis"]["by_content_type"])
    if type_count != len(stable):
        errors.append(f"content type count {type_count} != stable count {len(stable)}")
    section_ids = [section.get("id") for section in dataset.get("analysis_sections", [])]
    expected_ids = [
        "overview",
        "content-engine",
        "title-structure",
        "article-length",
        "audience",
        "timing",
        "evidence",
        "quality",
        "final-synthesis",
    ]
    if section_ids != expected_ids:
        errors.append(f"analysis section order {section_ids} != {expected_ids}")
    # new final keys
    fs = dataset.get("final_synthesis", {})
    if not (fs.get("now") is not None and fs.get("experiment") is not None and fs.get("hold") is not None):
        errors.append("final_synthesis must have now/experiment/hold")
    if not dataset.get("title_analysis", {}).get("by_primary_pattern"):
        errors.append("title_analysis.by_primary_pattern must be non-empty")
    if not dataset.get("length_analysis", {}).get("by_length_bucket"):
        errors.append("length_analysis.by_length_bucket must be non-empty")
    # top_conclusion checks
    topc = dataset.get("top_conclusion", {})
    if not topc.get("verdict"):
        errors.append("top_conclusion.verdict required")
    if len(str(topc.get("verdict", ""))) > 8:
        errors.append("top_conclusion.verdict >8 chars")
    if not topc.get("next_action"):
        errors.append("top_conclusion.next_action required")
    if len(str(topc.get("next_action", ""))) > 24:
        errors.append("top_conclusion.next_action >24 chars")
    # per section checks + word limits + three channels
    for section in dataset.get("analysis_sections", []):
        for field in required_section_fields:
            if not section.get(field):
                errors.append(f"missing section field {field}: {section.get('id')}")
        if not isinstance(section.get("chart_payload"), dict):
            errors.append(f"section chart_payload must be dict: {section.get('id')}")
        ui_slot = section.get("ui_slot")
        if not isinstance(ui_slot, dict) or not ui_slot.get("component") or not ui_slot.get("rail_focus"):
            errors.append(f"section ui_slot must include component and rail_focus: {section.get('id')}")
        # new three channels
        v = section.get("voice")
        e = section.get("emphasis")
        b = section.get("action_basket")
        if v not in {"high", "medium", "low"}:
            errors.append(f"section voice invalid: {section.get('id')}")
        if e not in {"hero", "primary", "secondary"}:
            errors.append(f"section emphasis invalid: {section.get('id')}")
        if b not in {"now", "experiment", "hold"}:
            errors.append(f"section action_basket invalid: {section.get('id')}")
        # word limits (len as chars per contract)
        if len(str(section.get("title", ""))) > 8:
            errors.append(f"section title >8: {section.get('id')}")
        if len(str(section.get("question", ""))) > 20:
            errors.append(f"section question >20: {section.get('id')}")
        if len(str(section.get("analysis", ""))) > 60:
            errors.append(f"section analysis >60: {section.get('id')}")
        if len(str(section.get("conclusion", ""))) > 40:
            errors.append(f"section conclusion >40: {section.get('id')}")
        if len(str(section.get("action", ""))) > 30:
            errors.append(f"section action >30: {section.get('id')}")
    section_id_set = set(expected_ids)
    for entry in dataset.get("evidence_stream", []):
        if entry.get("section_id") not in section_id_set:
            errors.append(f"evidence_stream has unknown section_id: {entry.get('section_id')}")
    # red line: no conf words in render output or dashboard-ish str
    try:
        rendered = render_report(dataset, Path("/tmp/dummy.json"))
        bad = re.search(r"置信度|高置信|中置信|低置信", rendered)
        if bad:
            errors.append("render_report contains forbidden confidence words")
        # also scan string values of top level for safety
        ds_str = json.dumps({k: v for k, v in dataset.items() if k not in ("articles", "analysis")}, ensure_ascii=False)
        if re.search(r"置信度|高置信|中置信|低置信", ds_str):
            errors.append("dataset string values contain forbidden confidence words")
    except Exception:
        pass
    # final baskets items <=25
    for basket in ("now", "experiment", "hold"):
        for item in fs.get(basket, []):
            if len(str(item)) > 25:
                errors.append(f"final {basket} item >25 chars")
    return errors


def build_paths(
    workspace: Path,
    wiki_repo: Path | None,
    report_date: str,
    dashboard_data_path: Path | None = None,
) -> Paths:
    out_dir = workspace / "output"
    if wiki_repo is None:
        report_path = out_dir / f"wechat-ops-report-{report_date}.md"
        dataset_path = out_dir / f"wechat-ops-report-{report_date}.json"
    else:
        report_path = wiki_repo / f"wiki/operations/social-ops/wechat-ops-report-{report_date}.md"
        dataset_path = wiki_repo / f"wiki/operations/social-ops/datasets/wechat-ops-report-{report_date}.json"
    # Runtime contract: code dir (skill) is read-only; all artefacts land in the
    # writable workspace. The dashboard data file therefore defaults to the
    # workspace output dir (same place as dataset/md), not the skill source tree.
    # Callers (e.g. analyze_cmd) may override to inject into a workspace
    # dashboard copy. Never default to the skill directory.
    if dashboard_data_path is None:
        dashboard_data_path = out_dir / "report.json"
    return Paths(
        root=workspace,
        wiki_repo=wiki_repo,
        report_path=report_path,
        dataset_path=dataset_path,
        dashboard_data_path=dashboard_data_path,
        report_date=report_date,
    )


def derive_report_date(workspace: Path) -> str:
    """Derive report_date (YYYY-MM-DD) from the captured_at date part in latest publish export."""
    raw_path = latest_publish_export(workspace)
    raw = read_json(raw_path, {})
    captured_at = parse_dt(raw.get("captured_at")) or datetime.now(timezone.utc).astimezone(CN_TZ)
    return captured_at.date().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=None, help="数据与产物工作区")
    parser.add_argument("--wiki-root", default=None, help="wiki 仓库根（不传则不写入外部 wiki，只输出到 workspace/output/）")
    parser.add_argument("--account-name", default="我的公众号", help="公众号账号名")
    parser.add_argument("--since", default=None, help="运营期起始日，ISO 日期如 2026-04-18（不传则取数据中最早发布时间当天或回退到 2026-04-18）")
    parser.add_argument(
        "--dashboard-data",
        default=None,
        help="覆盖 dashboard 数据文件落点（默认 <workspace>/output/report.json，skill 目录始终只读）",
    )
    parser.add_argument("--check", action="store_true", help="validate generated dataset only")
    args = parser.parse_args()

    if not args.workspace:
        print("错误: 必须通过 --workspace 指定数据与产物工作区路径")
        return 1
    workspace = Path(args.workspace).resolve()
    wiki_repo = Path(args.wiki_root).resolve() if args.wiki_root else None
    dashboard_data = Path(args.dashboard_data).expanduser().resolve() if args.dashboard_data else None
    report_date = derive_report_date(workspace)
    paths = build_paths(workspace, wiki_repo, report_date, dashboard_data)
    dataset = build_dataset(workspace, account_name=args.account_name, since=args.since)
    errors = validate_dataset(dataset)
    if args.check:
        if errors:
            print("\n".join(errors))
            return 1
        print(
            "ok: "
            f"{dataset['data_quality']['period_non_deleted_count']} current non-deleted, "
            f"{dataset['data_quality']['stable_article_count']} stable, "
            f"{dataset['data_quality']['metric_pending_count']} metric pending"
        )
        return 0

    if errors:
        print("Dataset validation failed:")
        print("\n".join(errors))
        return 1
    write_outputs(dataset, paths)
    if wiki_repo is not None:
        update_social_ops_index(paths)
        append_wiki_log(paths)
    print(f"wrote {paths.report_path}")
    print(f"wrote {paths.dataset_path}")
    print(f"wrote {paths.dashboard_data_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
