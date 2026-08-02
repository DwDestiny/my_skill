# GEB-L3
# Input: 文章 record/title/正文 str + get_active() 赛道包（content_types/pain_points/personas/title_patterns）
# Output: 题材（含 terms|fallback 来源）、痛点、人设；标题结构 dict；正文去 MD 后字数与 length_bucket
# Pos: plugins/wxops/scripts/analyze/classify.py
from __future__ import annotations

import re
from typing import Any

from analyze.constants import (
    TITLE_PATTERN_COMPARISON,
    TITLE_PATTERN_GENERIC,
    TITLE_PATTERN_QUESTION,
    TITLE_PATTERN_TUTORIAL,
)
from analyze.io_utils import has_any, text_blob
from analyze.niche_loader import get_active


def classify_content_with_source(record: dict[str, Any]) -> tuple[str, str]:
    """题材分类 + 命中来源。source ∈ {"terms", "fallback"}（契约 §3.1 / §5）。"""
    text = text_blob(record)
    title = str(record.get("title", "")).lower()
    ct = get_active().content_types

    for rule in ct.rules:
        if has_any(text, rule.terms):
            return rule.type, "terms"
    # fallback：title_regex 命中与否殊途同归都返回 fallback.type（契约 §3.1 / 现状语义）
    # 两条路径均计为 fallback（覆盖率分母，契约 §5）
    if ct.fallback_title_re is not None:
        ct.fallback_title_re.search(title)
    return ct.fallback_type, "fallback"


def classify_content(record: dict[str, Any]) -> str:
    """旧签名 wrapper：只返回题材名，行为与 with_source 第一元一致。"""
    return classify_content_with_source(record)[0]


def classify_pain(record: dict[str, Any], content_type: str) -> str:
    text = text_blob(record)
    pp = get_active().pain_points
    mapped = pp.by_content_type.get(content_type)
    if mapped is not None:
        return mapped
    for rule in pp.term_rules:
        if has_any(text, rule.terms):
            return rule.pain
    return pp.default


def classify_persona(record: dict[str, Any], content_type: str, pain: str) -> str:
    text = text_blob(record)
    pe = get_active().personas
    for rule in pe.rules:
        if rule.if_terms_any is not None and not has_any(text, rule.if_terms_any):
            continue
        if rule.if_content_type is not None and content_type != rule.if_content_type:
            continue
        if rule.if_pain is not None and pain != rule.if_pain:
            continue
        return rule.then
    return pe.default


def title_length_bucket(title: str) -> str:
    length = len(title.strip())
    if length <= 16:
        return "16字内"
    if length <= 24:
        return "17-24字"
    if length <= 34:
        return "25-34字"
    return "35字以上"


def title_structure(title: str) -> dict[str, Any]:
    text = title.lower()
    slots = get_active().title_patterns

    has_number = bool(re.search(r"\d|一|二|三|四|五|六|七|八|九|十|百|千|万|亿", title))
    has_price_word = has_any(text, slots.price.terms)
    has_risk_word = has_any(text, slots.risk.terms)
    has_model_word = has_any(text, slots.release.subject_terms)
    # 通用结构特征留引擎（契约 §3.4）
    has_comparison = bool(re.search(r"vs|比|对比|替代|不如|超过|打败|拿下|第一", text))
    has_question = bool(re.search(r"[?？]|为什么|怎么|能不能|是不是|到底|凭什么", title))
    has_tutorial = has_any(text, ["教程", "指南", "手把手", "完整", "附", "清单", "步骤", "一文"])
    has_workflow = has_any(text, slots.workflow.terms)

    patterns: list[str] = []
    # 求值序：risk → price → release → 对比 → 教程|数字 → 疑问 → workflow → 普通
    if has_risk_word:
        patterns.append(slots.risk.label)
    if has_price_word:
        patterns.append(slots.price.label)
    if has_model_word and has_any(text, slots.release.action_terms):
        patterns.append(slots.release.label)
    if has_comparison:
        patterns.append(TITLE_PATTERN_COMPARISON)
    if has_tutorial or has_number:
        patterns.append(TITLE_PATTERN_TUTORIAL)
    if has_question:
        patterns.append(TITLE_PATTERN_QUESTION)
    if has_workflow:
        patterns.append(slots.workflow.label)
    if not patterns:
        patterns.append(TITLE_PATTERN_GENERIC)

    return {
        "length": len(title.strip()),
        "length_bucket": title_length_bucket(title),
        "primary_pattern": patterns[0],
        "patterns": patterns,
        "has_number": has_number,
        "has_price_word": has_price_word,
        "has_risk_word": has_risk_word,
        "has_model_word": has_model_word,
        "has_comparison": has_comparison,
        "has_question": has_question,
        "has_tutorial": has_tutorial,
    }


def strip_markdown_for_length(text: str) -> str:
    text = re.sub(r"(?s)^---.*?---", "", text, count=1)
    text = re.sub(r"(?s)```.*?```", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[#>*_`~\-|]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def count_article_chars(text: str) -> int:
    clean = strip_markdown_for_length(text)
    cjk = re.findall(r"[\u4e00-\u9fff]", clean)
    ascii_words = re.findall(r"[A-Za-z0-9][A-Za-z0-9+._/-]*", clean)
    return len(cjk) + sum(len(word) for word in ascii_words)


def length_bucket(length: int) -> str:
    if length <= 0:
        return "未匹配正文"
    if length < 1200:
        return "1200字内"
    if length < 2200:
        return "1200-2200字"
    if length < 3500:
        return "2200-3500字"
    return "3500字以上"
