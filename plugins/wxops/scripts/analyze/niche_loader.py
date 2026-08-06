# GEB-L3
# Input: niche_id, WXOPS_HOME / 插件根 niches/<id>/niche.json
# Output: NicheSpec（校验通过的赛道包）；set_active / get_active 会话态
# Pos: plugins/wxops/scripts/analyze/niche_loader.py
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constants import ENGINE_TITLE_PATTERN_LABELS
from .scoring_thresholds import INTERACTION_THRESHOLD_FIELDS, validate_threshold_overrides

_SLOT_NAMES = ("risk", "price", "release", "workflow")
_PERSONA_IF_KEYS = frozenset({"terms_any", "content_type", "pain"})

# 契约 §3 / §8：已知字段集合；未知键警告后忽略
_KNOWN_TOP_LEVEL = frozenset(
    {
        "niche_schema_version",
        "id",
        "name",
        "description",
        "content_types",
        "pain_points",
        "personas",
        "title_patterns",
        "recommendations",  # 可选：静态赛道运营建议（issue #60）
        "scoring",  # 可选：赛道级打分覆写（issue #74）
    }
)
_KNOWN_RECOMMENDATIONS = frozenset({"topic_ratio", "publish_windows", "headline_rules"})
_KNOWN_SCORING = frozenset({"interaction_thresholds"})
_KNOWN_TOPIC_RATIO_ITEM = frozenset({"label", "ratio", "role"})
_KNOWN_PUBLISH_WINDOW_ITEM = frozenset({"window", "best_for"})
_KNOWN_CONTENT_TYPES = frozenset({"names", "rules", "fallback"})
_KNOWN_CT_RULE = frozenset({"type", "terms"})
_KNOWN_CT_FALLBACK = frozenset({"title_regex", "type"})
_KNOWN_PAIN_POINTS = frozenset({"names", "by_content_type", "term_rules", "default"})
_KNOWN_PP_TERM_RULE = frozenset({"terms", "pain"})
_KNOWN_PERSONAS = frozenset({"names", "rules", "default"})
_KNOWN_PE_RULE = frozenset({"if", "then"})
_KNOWN_TITLE_PATTERNS = frozenset({"keys", "slots"})
_KNOWN_SLOT = frozenset({"label", "terms", "subject_terms", "action_terms"})

_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
_active: "NicheSpec | None" = None


class NicheLoadError(Exception):
    """坏包或 _generic 缺失时的硬报错。"""


@dataclass
class ContentTypeRule:
    type: str
    terms: list[str]


@dataclass
class ContentTypesSpec:
    names: list[str]
    rules: list[ContentTypeRule]
    fallback_type: str
    fallback_title_regex: str | None  # raw pattern；None 表示未给出
    fallback_title_re: re.Pattern[str] | None


@dataclass
class PainTermRule:
    terms: list[str]
    pain: str


@dataclass
class PainPointsSpec:
    names: list[str]
    by_content_type: dict[str, str]
    term_rules: list[PainTermRule]
    default: str


@dataclass
class PersonaRule:
    if_terms_any: list[str] | None
    if_content_type: str | None
    if_pain: str | None
    then: str


@dataclass
class PersonasSpec:
    names: list[str]
    rules: list[PersonaRule]
    default: str


@dataclass
class TitleSlot:
    label: str
    terms: list[str] = field(default_factory=list)
    subject_terms: list[str] = field(default_factory=list)
    action_terms: list[str] = field(default_factory=list)


@dataclass
class TitlePatternsSpec:
    keys: list[str]
    risk: TitleSlot
    price: TitleSlot
    release: TitleSlot
    workflow: TitleSlot


@dataclass
class RecommendationsSpec:
    """可选静态赛道运营建议；缺省 None，不回落任何硬编码文案。"""

    topic_ratio: list[dict[str, Any]]
    publish_windows: list[dict[str, Any]]
    headline_rules: list[str]


@dataclass
class ScoringSpec:
    """可选赛道级打分覆写；缺省 None → 全走 scoring_thresholds 里的平台级默认。"""

    interaction_thresholds: dict[str, float] | None = None


@dataclass
class NicheSpec:
    id: str
    name: str
    requested_id: str
    content_types: ContentTypesSpec
    pain_points: PainPointsSpec
    personas: PersonasSpec
    title_patterns: TitlePatternsSpec
    description: str = ""
    recommendations: RecommendationsSpec | None = None
    scoring: ScoringSpec | None = None

    @property
    def content_type_names(self) -> list[str]:
        return list(self.content_types.names)

    @property
    def pain_point_names(self) -> list[str]:
        return list(self.pain_points.names)

    @property
    def persona_names(self) -> list[str]:
        return list(self.personas.names)

    @property
    def title_pattern_keys(self) -> list[str]:
        return list(self.title_patterns.keys)


def _wxops_home() -> Path:
    raw = os.environ.get("WXOPS_HOME")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".wxops"


def _resolve_niche_path(niche_id: str) -> Path | None:
    """用户目录优先，其次内置目录；都不存在返回 None。"""
    user_path = _wxops_home() / "niches" / niche_id / "niche.json"
    if user_path.is_file():
        return user_path
    builtin = _PLUGIN_ROOT / "niches" / niche_id / "niche.json"
    if builtin.is_file():
        return builtin
    return None


def _fail(path: Path, item: str, detail: str = "") -> None:
    msg = f"赛道包校验失败 [{item}]: {path}"
    if detail:
        msg = f"{msg} — {detail}"
    raise NicheLoadError(msg)


def _require_nonempty_str_list(path: Path, item: str, values: Any, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(values, list):
        _fail(path, item, "必须为字符串数组")
    out: list[str] = []
    for i, v in enumerate(values):
        if not isinstance(v, str) or not v:
            _fail(path, item, f"第 {i} 项必须为非空字符串")
        out.append(v)
    if not allow_empty and not out:
        _fail(path, item, "不得为空")
    return out


def _check_names_unique(path: Path, item: str, names: list[str]) -> None:
    if len(names) != len(set(names)):
        _fail(path, item, "存在重复项")


def _warn_unknown_fields(path: Path, scope: str, keys: set[str], known: frozenset[str]) -> None:
    """契约 §8：未知字段警告后忽略。"""
    for key in sorted(keys - known):
        label = f"{scope}.{key}" if scope else key
        print(f"⚠ 赛道包 {path} 含未知字段 {label}，已忽略（schema v1）", file=sys.stderr)


def _validate_and_build(path: Path, data: dict[str, Any], *, requested_id: str, dir_id: str) -> NicheSpec:
    # §8 顶层未知字段
    _warn_unknown_fields(path, "", set(data.keys()), _KNOWN_TOP_LEVEL)

    # §7.1 schema version
    if data.get("niche_schema_version") != 1:
        _fail(path, "niche_schema_version==1", f"得到 {data.get('niche_schema_version')!r}")

    # §7.2 id / name
    niche_id = data.get("id")
    if not isinstance(niche_id, str) or not niche_id:
        _fail(path, "id 非空", f"得到 {niche_id!r}")
    if niche_id != dir_id:
        _fail(path, "id 与目录名一致", f"id={niche_id!r} dir={dir_id!r}")
    name = data.get("name")
    if not isinstance(name, str) or not name:
        _fail(path, "name 非空", f"得到 {name!r}")

    # §7.3 四大组
    for key in ("content_types", "pain_points", "personas", "title_patterns"):
        if key not in data or not isinstance(data[key], dict):
            _fail(path, f"四大组俱全:{key}")

    ct_raw = data["content_types"]
    pp_raw = data["pain_points"]
    pe_raw = data["personas"]
    tp_raw = data["title_patterns"]

    # §8 组内未知键
    _warn_unknown_fields(path, "content_types", set(ct_raw.keys()), _KNOWN_CONTENT_TYPES)
    _warn_unknown_fields(path, "pain_points", set(pp_raw.keys()), _KNOWN_PAIN_POINTS)
    _warn_unknown_fields(path, "personas", set(pe_raw.keys()), _KNOWN_PERSONAS)
    _warn_unknown_fields(path, "title_patterns", set(tp_raw.keys()), _KNOWN_TITLE_PATTERNS)

    ct_names = _require_nonempty_str_list(path, "content_types.names", ct_raw.get("names"))
    _check_names_unique(path, "content_types.names 无重复", ct_names)
    pp_names = _require_nonempty_str_list(path, "pain_points.names", pp_raw.get("names"))
    _check_names_unique(path, "pain_points.names 无重复", pp_names)
    pe_names = _require_nonempty_str_list(path, "personas.names", pe_raw.get("names"))
    _check_names_unique(path, "personas.names 无重复", pe_names)
    tp_keys = _require_nonempty_str_list(path, "title_patterns.keys", tp_raw.get("keys"))
    _check_names_unique(path, "title_patterns.keys 无重复", tp_keys)

    # content_types rules + fallback
    rules_raw = ct_raw.get("rules")
    if not isinstance(rules_raw, list):
        _fail(path, "content_types.rules 为数组")
    ct_rules: list[ContentTypeRule] = []
    for i, rule in enumerate(rules_raw):
        if not isinstance(rule, dict):
            _fail(path, f"content_types.rules[{i}] 为对象")
        _warn_unknown_fields(path, f"content_types.rules[{i}]", set(rule.keys()), _KNOWN_CT_RULE)
        rtype = rule.get("type")
        if not isinstance(rtype, str) or rtype not in ct_names:
            _fail(path, "content_types.rules[*].type ∈ names", f"rules[{i}].type={rtype!r}")
        terms = _require_nonempty_str_list(
            path, f"content_types.rules[{i}].terms", rule.get("terms"), allow_empty=False
        )
        ct_rules.append(ContentTypeRule(type=rtype, terms=terms))

    fb = ct_raw.get("fallback")
    if not isinstance(fb, dict):
        _fail(path, "content_types.fallback 为对象")
    _warn_unknown_fields(path, "content_types.fallback", set(fb.keys()), _KNOWN_CT_FALLBACK)
    fb_type = fb.get("type")
    if not isinstance(fb_type, str) or fb_type not in ct_names:
        _fail(path, "content_types.fallback.type ∈ names", f"得到 {fb_type!r}")
    fb_regex_raw = fb.get("title_regex")
    fb_re: re.Pattern[str] | None = None
    fb_regex: str | None = None
    if fb_regex_raw is not None:
        if not isinstance(fb_regex_raw, str) or not fb_regex_raw:
            _fail(path, "title_regex 为非空字符串", f"得到 {fb_regex_raw!r}")
        try:
            fb_re = re.compile(fb_regex_raw)
        except re.error as e:
            _fail(path, "title_regex 可 re.compile", str(e))
        fb_regex = fb_regex_raw

    content_types = ContentTypesSpec(
        names=ct_names,
        rules=ct_rules,
        fallback_type=fb_type,
        fallback_title_regex=fb_regex,
        fallback_title_re=fb_re,
    )

    # pain_points
    by_ct = pp_raw.get("by_content_type")
    if not isinstance(by_ct, dict):
        _fail(path, "pain_points.by_content_type 为对象")
    by_content_type: dict[str, str] = {}
    for k, v in by_ct.items():
        if not isinstance(k, str) or k not in ct_names:
            _fail(path, "pain_points.by_content_type 键 ∈ content_types.names", f"键={k!r}")
        if not isinstance(v, str) or v not in pp_names:
            _fail(path, "pain_points.by_content_type 值 ∈ pain_points.names", f"{k}→{v!r}")
        by_content_type[k] = v

    tr_raw = pp_raw.get("term_rules")
    if not isinstance(tr_raw, list):
        _fail(path, "pain_points.term_rules 为数组")
    term_rules: list[PainTermRule] = []
    for i, rule in enumerate(tr_raw):
        if not isinstance(rule, dict):
            _fail(path, f"pain_points.term_rules[{i}] 为对象")
        _warn_unknown_fields(path, f"pain_points.term_rules[{i}]", set(rule.keys()), _KNOWN_PP_TERM_RULE)
        pain = rule.get("pain")
        if not isinstance(pain, str) or pain not in pp_names:
            _fail(path, "pain_points.term_rules[*].pain ∈ names", f"term_rules[{i}].pain={pain!r}")
        terms = _require_nonempty_str_list(
            path, f"pain_points.term_rules[{i}].terms", rule.get("terms"), allow_empty=False
        )
        term_rules.append(PainTermRule(terms=terms, pain=pain))

    pp_default = pp_raw.get("default")
    if not isinstance(pp_default, str) or pp_default not in pp_names:
        _fail(path, "pain_points.default ∈ names", f"得到 {pp_default!r}")

    pain_points = PainPointsSpec(
        names=pp_names,
        by_content_type=by_content_type,
        term_rules=term_rules,
        default=pp_default,
    )

    # personas
    pe_rules_raw = pe_raw.get("rules")
    if not isinstance(pe_rules_raw, list):
        _fail(path, "personas.rules 为数组")
    pe_rules: list[PersonaRule] = []
    for i, rule in enumerate(pe_rules_raw):
        if not isinstance(rule, dict):
            _fail(path, f"personas.rules[{i}] 为对象")
        _warn_unknown_fields(path, f"personas.rules[{i}]", set(rule.keys()), _KNOWN_PE_RULE)
        then = rule.get("then")
        if not isinstance(then, str) or then not in pe_names:
            _fail(path, "personas.rules[*].then ∈ names", f"rules[{i}].then={then!r}")
        if_obj = rule.get("if")
        if not isinstance(if_obj, dict) or not if_obj:
            _fail(path, "personas.rules[*].if 至少一键", f"rules[{i}]")
        # §7.6 if 键必须 ∈ 已知集合；未知键硬报错（与 §8 组级 warn 不同）
        unknown = set(if_obj.keys()) - _PERSONA_IF_KEYS
        if unknown:
            _fail(path, "personas.rules[*].if 键 ∈ {terms_any,content_type,pain}", f"rules[{i}] 未知键 {unknown}")
        terms_any: list[str] | None = None
        if "terms_any" in if_obj:
            terms_any = _require_nonempty_str_list(
                path, f"personas.rules[{i}].if.terms_any", if_obj.get("terms_any"), allow_empty=False
            )
        if_ct = if_obj.get("content_type") if "content_type" in if_obj else None
        if if_ct is not None:
            if not isinstance(if_ct, str) or if_ct not in ct_names:
                _fail(path, "personas.rules[*].if.content_type ∈ content_types.names", f"rules[{i}]={if_ct!r}")
        if_pain = if_obj.get("pain") if "pain" in if_obj else None
        if if_pain is not None:
            if not isinstance(if_pain, str) or if_pain not in pp_names:
                _fail(path, "personas.rules[*].if.pain ∈ pain_points.names", f"rules[{i}]={if_pain!r}")
        pe_rules.append(
            PersonaRule(
                if_terms_any=terms_any,
                if_content_type=if_ct if isinstance(if_ct, str) else None,
                if_pain=if_pain if isinstance(if_pain, str) else None,
                then=then,
            )
        )

    pe_default = pe_raw.get("default")
    if not isinstance(pe_default, str) or pe_default not in pe_names:
        _fail(path, "personas.default ∈ names", f"得到 {pe_default!r}")

    personas = PersonasSpec(names=pe_names, rules=pe_rules, default=pe_default)

    # title_patterns slots
    slots_raw = tp_raw.get("slots")
    if not isinstance(slots_raw, dict):
        _fail(path, "title_patterns.slots 为对象")
    missing_slots = [s for s in _SLOT_NAMES if s not in slots_raw]
    if missing_slots:
        _fail(path, "title_patterns 四槽俱全", f"缺少 {missing_slots}")

    def _parse_slot(slot_name: str) -> TitleSlot:
        raw = slots_raw[slot_name]
        if not isinstance(raw, dict):
            _fail(path, f"title_patterns.slots.{slot_name} 为对象")
        _warn_unknown_fields(path, f"title_patterns.slots.{slot_name}", set(raw.keys()), _KNOWN_SLOT)
        label = raw.get("label")
        if not isinstance(label, str) or not label:
            _fail(path, f"title_patterns.slots.{slot_name}.label 非空")
        if slot_name == "release":
            subject = _require_nonempty_str_list(
                path,
                f"title_patterns.slots.release.subject_terms",
                raw.get("subject_terms", []),
                allow_empty=True,
            )
            action = _require_nonempty_str_list(
                path,
                f"title_patterns.slots.release.action_terms",
                raw.get("action_terms", []),
                allow_empty=True,
            )
            return TitleSlot(label=label, subject_terms=subject, action_terms=action)
        terms = _require_nonempty_str_list(
            path,
            f"title_patterns.slots.{slot_name}.terms",
            raw.get("terms", []),
            allow_empty=True,
        )
        return TitleSlot(label=label, terms=terms)

    risk = _parse_slot("risk")
    price = _parse_slot("price")
    release = _parse_slot("release")
    workflow = _parse_slot("workflow")

    slot_labels = {risk.label, price.label, release.label, workflow.label}
    expected_keys = slot_labels | set(ENGINE_TITLE_PATTERN_LABELS)
    if set(tp_keys) != expected_keys:
        _fail(
            path,
            "title_patterns.keys 恰好 = 4 槽 label ∪ 4 引擎固定标签",
            f"keys={set(tp_keys)!r} expected={expected_keys!r}",
        )

    title_patterns = TitlePatternsSpec(
        keys=tp_keys,
        risk=risk,
        price=price,
        release=release,
        workflow=workflow,
    )

    description = data.get("description") if isinstance(data.get("description"), str) else ""

    # recommendations：可选字段；缺失 → None；存在则校验结构
    recommendations: RecommendationsSpec | None = None
    if "recommendations" in data:
        rec_raw = data["recommendations"]
        if not isinstance(rec_raw, dict):
            _fail(path, "recommendations 为对象")
        _warn_unknown_fields(path, "recommendations", set(rec_raw.keys()), _KNOWN_RECOMMENDATIONS)
        for req_key in ("topic_ratio", "publish_windows", "headline_rules"):
            if req_key not in rec_raw:
                _fail(path, f"recommendations.{req_key} 齐全")
        tr_raw = rec_raw["topic_ratio"]
        pw_raw = rec_raw["publish_windows"]
        hr_raw = rec_raw["headline_rules"]
        if not isinstance(tr_raw, list):
            _fail(path, "recommendations.topic_ratio 为数组")
        if not isinstance(pw_raw, list):
            _fail(path, "recommendations.publish_windows 为数组")
        if not isinstance(hr_raw, list):
            _fail(path, "recommendations.headline_rules 为数组")
        topic_ratio: list[dict[str, Any]] = []
        for i, item in enumerate(tr_raw):
            if not isinstance(item, dict):
                _fail(path, f"recommendations.topic_ratio[{i}] 为对象")
            _warn_unknown_fields(
                path, f"recommendations.topic_ratio[{i}]", set(item.keys()), _KNOWN_TOPIC_RATIO_ITEM
            )
            label = item.get("label")
            ratio = item.get("ratio")
            role = item.get("role")
            if not isinstance(label, str) or not label:
                _fail(path, f"recommendations.topic_ratio[{i}].label 非空字符串")
            if not isinstance(ratio, (int, float)):
                _fail(path, f"recommendations.topic_ratio[{i}].ratio 为数值")
            if not isinstance(role, str) or not role:
                _fail(path, f"recommendations.topic_ratio[{i}].role 非空字符串")
            topic_ratio.append({"label": label, "ratio": float(ratio), "role": role})
        publish_windows: list[dict[str, Any]] = []
        for i, item in enumerate(pw_raw):
            if not isinstance(item, dict):
                _fail(path, f"recommendations.publish_windows[{i}] 为对象")
            _warn_unknown_fields(
                path,
                f"recommendations.publish_windows[{i}]",
                set(item.keys()),
                _KNOWN_PUBLISH_WINDOW_ITEM,
            )
            window = item.get("window")
            best_for = item.get("best_for")
            if not isinstance(window, str) or not window:
                _fail(path, f"recommendations.publish_windows[{i}].window 非空字符串")
            if not isinstance(best_for, str) or not best_for:
                _fail(path, f"recommendations.publish_windows[{i}].best_for 非空字符串")
            publish_windows.append({"window": window, "best_for": best_for})
        headline_rules: list[str] = []
        for i, item in enumerate(hr_raw):
            if not isinstance(item, str) or not item:
                _fail(path, f"recommendations.headline_rules[{i}] 非空字符串")
            headline_rules.append(item)
        recommendations = RecommendationsSpec(
            topic_ratio=topic_ratio,
            publish_windows=publish_windows,
            headline_rules=headline_rules,
        )

    # scoring：可选字段；内部字段亦全部可选（与 recommendations 子字段必填相反）
    scoring: ScoringSpec | None = None
    if "scoring" in data:
        sc_raw = data["scoring"]
        if not isinstance(sc_raw, dict):
            _fail(path, "scoring 为对象")
        _warn_unknown_fields(path, "scoring", set(sc_raw.keys()), _KNOWN_SCORING)
        if "interaction_thresholds" not in sc_raw:
            scoring = ScoringSpec(interaction_thresholds=None)
        else:
            thr_raw = sc_raw["interaction_thresholds"]
            if not isinstance(thr_raw, dict):
                _fail(path, "scoring.interaction_thresholds 为对象")
            _warn_unknown_fields(
                path,
                "scoring.interaction_thresholds",
                set(thr_raw.keys()),
                INTERACTION_THRESHOLD_FIELDS,
            )
            try:
                validated = validate_threshold_overrides(thr_raw)
            except ValueError as exc:
                _fail(path, f"scoring.interaction_thresholds 合法（{exc}）")
            scoring = ScoringSpec(interaction_thresholds=validated if validated else None)

    return NicheSpec(
        id=niche_id,
        name=name,
        requested_id=requested_id,
        content_types=content_types,
        pain_points=pain_points,
        personas=personas,
        title_patterns=title_patterns,
        description=description or "",
        recommendations=recommendations,
        scoring=scoring,
    )


def _load_path(path: Path, *, requested_id: str, dir_id: str) -> NicheSpec:
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise NicheLoadError(f"赛道包 JSON 解析失败: {path} — {e}") from e
    except OSError as e:
        raise NicheLoadError(f"赛道包读取失败: {path} — {e}") from e
    if not isinstance(data, dict):
        raise NicheLoadError(f"赛道包顶层必须为对象: {path}")
    return _validate_and_build(path, data, requested_id=requested_id, dir_id=dir_id)


def load_niche(niche_id: str) -> NicheSpec:
    """按契约 §2 解析顺序加载赛道包。缺包回落 _generic；坏包硬报错。"""
    if not isinstance(niche_id, str) or not niche_id:
        raise NicheLoadError(f"非法 niche_id: {niche_id!r}")

    path = _resolve_niche_path(niche_id)
    if path is not None:
        return _load_path(path, requested_id=niche_id, dir_id=path.parent.name)

    # 缺包 → 回落 _generic + stderr 警告
    print(f"⚠ 未找到赛道包 {niche_id}，已回落 _generic 通用兜底", file=sys.stderr)
    generic_path = _resolve_niche_path("_generic")
    if generic_path is None:
        # 再试内置硬路径
        generic_path = _PLUGIN_ROOT / "niches" / "_generic" / "niche.json"
    if not generic_path.is_file():
        raise NicheLoadError(
            f"插件安装损坏：内置兜底包 _generic 缺失（{generic_path}）"
        )
    return _load_path(generic_path, requested_id=niche_id, dir_id="_generic")


def set_active(spec: NicheSpec) -> None:
    global _active
    _active = spec


def get_active() -> NicheSpec:
    """未显式 set 时懒加载内置 ai-tools，保证旧调用路径行为不变。"""
    global _active
    if _active is None:
        _active = load_niche("ai-tools")
    return _active


def reset_active() -> None:
    """测试用：清空会话态 active 包。"""
    global _active
    _active = None
