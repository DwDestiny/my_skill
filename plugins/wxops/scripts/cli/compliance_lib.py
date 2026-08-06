#!/usr/bin/env python3
# GEB-L3
# Input: compliance.json 路径/原文 Markdown；三层回落路径由调用方给出
# Output: ComplianceSpec + list[Hit]；schema 非法抛 ComplianceLoadError
# Pos: plugins/wxops/scripts/cli/compliance_lib.py
"""稿件合规闸纯引擎：schema 校验 + terms/regex/cooccur 匹配（每规则每篇最多 1 命中）。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import json

Level = Literal["BLOCK", "WARN"]
MatchType = Literal["terms", "regex", "cooccur"]
LayerLabel = Literal["用户包", "内置包", "通用兜底"]

_VALID_LEVELS = frozenset({"BLOCK", "WARN"})
_VALID_MATCH_TYPES = frozenset({"terms", "regex", "cooccur"})
_SENTENCE_SPLIT_RE = re.compile(r"[。！？；\n]")


class ComplianceLoadError(Exception):
    """规则文件缺失、JSON 坏、schema 不合法。"""


@dataclass
class MatchSpec:
    type: MatchType
    terms: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    compiled: list[re.Pattern[str]] = field(default_factory=list)
    scope: str = "document"
    unless: list[str] = field(default_factory=list)
    exclude_matches: list[str] = field(default_factory=list)
    strip_softeners: bool = False
    left: list[str] = field(default_factory=list)
    right: list[str] = field(default_factory=list)


@dataclass
class Rule:
    id: str
    level: Level
    title: str
    why: str
    fix: str
    match: MatchSpec


@dataclass
class ComplianceSpec:
    id: str
    name: str
    softeners: list[str]
    rules: list[Rule]
    path: Path
    layer: LayerLabel
    niche_shown: str
    basis: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class Hit:
    rule_id: str
    level: Level
    title: str
    line: int
    matched: str
    context: str
    why: str
    fix: str


def resolve_compliance(
    root: Path, niche_id: str, skill_dir: Path
) -> tuple[Path | None, LayerLabel | str, str]:
    """文件级三层回落查找 compliance.json。

    返回 (path | None, layer_label, niche_shown)。
    layer_label: 用户包 / 内置包 / 通用兜底；全无时 layer 为空串。
    """
    niche = (niche_id or "").strip() or "ai-tools"

    user_path = root / "niches" / niche / "compliance.json"
    if user_path.is_file():
        return user_path, "用户包", niche

    builtin_path = skill_dir / "niches" / niche / "compliance.json"
    if builtin_path.is_file():
        return builtin_path, "内置包", niche

    generic_path = skill_dir / "niches" / "_generic" / "compliance.json"
    if generic_path.is_file():
        return generic_path, "通用兜底", "_generic"

    return None, "", niche


def _fail(path: Path, item: str, detail: str = "") -> None:
    msg = f"合规规则校验失败 [{item}]: {path}"
    if detail:
        msg = f"{msg} — {detail}"
    raise ComplianceLoadError(msg)


def _require_str(path: Path, item: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        _fail(path, item, f"得到 {value!r}")
    return value


def _require_str_list(
    path: Path, item: str, value: Any, *, allow_empty: bool = False
) -> list[str]:
    if not isinstance(value, list):
        _fail(path, item, "必须为字符串数组")
    out: list[str] = []
    for i, v in enumerate(value):
        if not isinstance(v, str) or not v:
            _fail(path, item, f"第 {i} 项必须为非空字符串")
        out.append(v)
    if not allow_empty and not out:
        _fail(path, item, "不得为空")
    return out


def _parse_match(path: Path, rule_id: str, raw: Any) -> MatchSpec:
    if not isinstance(raw, dict):
        _fail(path, f"rules[{rule_id}].match", "必须为对象")
    mtype = raw.get("type")
    if not isinstance(mtype, str) or mtype not in _VALID_MATCH_TYPES:
        _fail(
            path,
            f"rules[{rule_id}].match.type",
            f"必须 ∈ {{terms,regex,cooccur}}，得到 {mtype!r}",
        )

    if mtype == "terms":
        terms = _require_str_list(path, f"rules[{rule_id}].match.terms", raw.get("terms"))
        return MatchSpec(type="terms", terms=terms)

    if mtype == "regex":
        patterns = _require_str_list(
            path, f"rules[{rule_id}].match.patterns", raw.get("patterns")
        )
        compiled: list[re.Pattern[str]] = []
        for i, p in enumerate(patterns):
            try:
                compiled.append(re.compile(p))
            except re.error as e:
                _fail(path, f"rules[{rule_id}].match.patterns[{i}]", str(e))
        scope = raw.get("scope", "document")
        if scope not in ("document", "sentence"):
            _fail(path, f"rules[{rule_id}].match.scope", f"得到 {scope!r}")
        unless: list[str] = []
        if "unless" in raw:
            unless = _require_str_list(
                path, f"rules[{rule_id}].match.unless", raw.get("unless"), allow_empty=True
            )
        exclude_matches: list[str] = []
        if "exclude_matches" in raw:
            exclude_matches = _require_str_list(
                path,
                f"rules[{rule_id}].match.exclude_matches",
                raw.get("exclude_matches"),
                allow_empty=True,
            )
        return MatchSpec(
            type="regex",
            patterns=patterns,
            compiled=compiled,
            scope=str(scope),
            unless=unless,
            exclude_matches=exclude_matches,
        )

    # cooccur
    left = _require_str_list(path, f"rules[{rule_id}].match.left", raw.get("left"))
    right = _require_str_list(path, f"rules[{rule_id}].match.right", raw.get("right"))
    scope = raw.get("scope", "sentence")
    if scope not in ("document", "sentence"):
        _fail(path, f"rules[{rule_id}].match.scope", f"得到 {scope!r}")
    strip = raw.get("strip_softeners", False)
    if not isinstance(strip, bool):
        _fail(path, f"rules[{rule_id}].match.strip_softeners", f"得到 {strip!r}")
    return MatchSpec(
        type="cooccur",
        scope=str(scope),
        strip_softeners=strip,
        left=left,
        right=right,
    )


def load_compliance(
    path: Path, *, layer: LayerLabel, niche_shown: str
) -> ComplianceSpec:
    """读并校验 compliance.json → ComplianceSpec。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ComplianceLoadError(f"合规规则 JSON 解析失败: {path} — {e}") from e
    except OSError as e:
        raise ComplianceLoadError(f"合规规则读取失败: {path} — {e}") from e
    if not isinstance(data, dict):
        raise ComplianceLoadError(f"合规规则顶层必须为对象: {path}")

    if data.get("compliance_schema_version") != 1:
        _fail(
            path,
            "compliance_schema_version==1",
            f"得到 {data.get('compliance_schema_version')!r}",
        )

    cid = _require_str(path, "id", data.get("id"))
    name = _require_str(path, "name", data.get("name"))

    if "softeners" not in data:
        _fail(path, "softeners", "字段必须存在（可为空数组）")
    softeners = _require_str_list(path, "softeners", data.get("softeners"), allow_empty=True)

    rules_raw = data.get("rules")
    if not isinstance(rules_raw, list):
        _fail(path, "rules", "必须为数组")

    rules: list[Rule] = []
    seen_ids: set[str] = set()
    for i, raw in enumerate(rules_raw):
        if not isinstance(raw, dict):
            _fail(path, f"rules[{i}]", "必须为对象")
        rid = _require_str(path, f"rules[{i}].id", raw.get("id"))
        if rid in seen_ids:
            _fail(path, f"rules[{i}].id", f"包内重复 id={rid!r}")
        seen_ids.add(rid)
        level = raw.get("level")
        if level not in _VALID_LEVELS:
            _fail(path, f"rules[{i}].level", f"必须 ∈ {{BLOCK,WARN}}，得到 {level!r}")
        title = _require_str(path, f"rules[{i}].title", raw.get("title"))
        why = _require_str(path, f"rules[{i}].why", raw.get("why"))
        fix = _require_str(path, f"rules[{i}].fix", raw.get("fix"))
        if "match" not in raw:
            _fail(path, f"rules[{i}].match", "字段必须存在")
        match = _parse_match(path, rid, raw.get("match"))
        rules.append(
            Rule(id=rid, level=level, title=title, why=why, fix=fix, match=match)  # type: ignore[arg-type]
        )

    basis: list[str] = []
    if "basis" in data and data["basis"] is not None:
        basis = _require_str_list(path, "basis", data.get("basis"), allow_empty=True)
    note = data.get("note") if isinstance(data.get("note"), str) else ""

    return ComplianceSpec(
        id=cid,
        name=name,
        softeners=softeners,
        rules=rules,
        path=path,
        layer=layer,  # type: ignore[arg-type]
        niche_shown=niche_shown,
        basis=basis,
        note=note or "",
    )


def mask_frontmatter(text: str) -> str:
    """YAML frontmatter 行替换为空内容（保留换行），使行号与原文对齐。"""
    if not text.startswith("---"):
        return text
    # 首行必须是单独的 ---
    lines = text.splitlines(keepends=True)
    if not lines:
        return text
    if lines[0].strip() != "---":
        return text
    end_idx: int | None = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return text
    out: list[str] = []
    for i, line in enumerate(lines):
        if i <= end_idx:
            if line.endswith("\r\n"):
                out.append("\r\n")
            elif line.endswith("\n"):
                out.append("\n")
            else:
                out.append("")
        else:
            out.append(line)
    return "".join(out)


def line_of(text: str, offset: int) -> int:
    """1-based 行号。"""
    if offset < 0:
        offset = 0
    if offset > len(text):
        offset = len(text)
    return text.count("\n", 0, offset) + 1


def split_scope_units(text: str, scope: str) -> list[tuple[str, int]]:
    """返回 [(unit_text, start_offset), ...]。scope=document 时整篇一条。"""
    if scope != "sentence":
        return [(text, 0)]
    units: list[tuple[str, int]] = []
    start = 0
    for m in _SENTENCE_SPLIT_RE.finditer(text):
        content = text[start : m.start()]
        if content:
            units.append((content, start))
        start = m.end()
    if start < len(text):
        content = text[start:]
        if content:
            units.append((content, start))
    return units


def _context_snippet(text: str, start: int, end: int, matched: str, limit: int = 60) -> str:
    """截取命中附近原文，命中词用「」标出，总长约 limit。"""
    # 以命中为中心向两侧扩展
    pad = max(0, (limit - len(matched)) // 2)
    left = max(0, start - pad)
    right = min(len(text), end + pad)
    chunk = text[left:right]
    # 在 chunk 内高亮第一次出现的 matched
    idx = chunk.find(matched)
    if idx >= 0:
        chunk = chunk[:idx] + f"「{matched}」" + chunk[idx + len(matched) :]
    chunk = chunk.replace("\n", " ").strip()
    if left > 0:
        chunk = "…" + chunk
    if right < len(text):
        chunk = chunk + "…"
    if len(chunk) > limit + 10:
        chunk = chunk[: limit + 10] + "…"
    return chunk


def _match_terms(rule: Rule, text: str) -> Hit | None:
    for term in rule.match.terms:
        pos = text.find(term)
        if pos < 0:
            continue
        return Hit(
            rule_id=rule.id,
            level=rule.level,
            title=rule.title,
            line=line_of(text, pos),
            matched=term,
            context=_context_snippet(text, pos, pos + len(term), term),
            why=rule.why,
            fix=rule.fix,
        )
    return None


def _match_regex(rule: Rule, text: str) -> Hit | None:
    units = split_scope_units(text, rule.match.scope)
    exclude = set(rule.match.exclude_matches)
    unless = rule.match.unless
    for unit, unit_off in units:
        for cre in rule.match.compiled:
            for mo in cre.finditer(unit):
                hit_text = mo.group(0)
                if hit_text in exclude:
                    continue
                if unless and any(u in unit for u in unless):
                    continue
                abs_start = unit_off + mo.start()
                abs_end = unit_off + mo.end()
                return Hit(
                    rule_id=rule.id,
                    level=rule.level,
                    title=rule.title,
                    line=line_of(text, abs_start),
                    matched=hit_text,
                    context=_context_snippet(text, abs_start, abs_end, hit_text),
                    why=rule.why,
                    fix=rule.fix,
                )
    return None


def _match_cooccur(rule: Rule, text: str, softeners: list[str]) -> Hit | None:
    # cooccur 按句切分（默认 sentence）
    scope = rule.match.scope if rule.match.scope else "sentence"
    units = split_scope_units(text, scope)
    for unit, unit_off in units:
        probe = unit
        if rule.match.strip_softeners:
            for s in softeners:
                if s:
                    probe = probe.replace(s, "")
        left_hit: str | None = None
        right_hit: str | None = None
        for L in rule.match.left:
            if L in probe:
                left_hit = L
                break
        if left_hit is None:
            continue
        for R in rule.match.right:
            if R in probe:
                right_hit = R
                break
        if right_hit is None:
            continue
        # 行号：取 left 在原 unit 中的位置（软化词可能已删，优先原 unit）
        pos_in_unit = unit.find(left_hit)
        if pos_in_unit < 0:
            pos_in_unit = probe.find(left_hit)
            if pos_in_unit < 0:
                pos_in_unit = 0
        abs_start = unit_off + max(0, pos_in_unit)
        matched = f"{left_hit}×{right_hit}"
        return Hit(
            rule_id=rule.id,
            level=rule.level,
            title=rule.title,
            line=line_of(text, abs_start),
            matched=matched,
            context=_context_snippet(
                text, abs_start, abs_start + len(left_hit), left_hit
            ),
            why=rule.why,
            fix=rule.fix,
        )
    return None


def scan_text(spec: ComplianceSpec, raw_text: str) -> list[Hit]:
    """对原文跑全部规则；frontmatter 跳过；每规则最多 1 命中。"""
    text = mask_frontmatter(raw_text)
    hits: list[Hit] = []
    for rule in spec.rules:
        hit: Hit | None = None
        if rule.match.type == "terms":
            hit = _match_terms(rule, text)
        elif rule.match.type == "regex":
            hit = _match_regex(rule, text)
        elif rule.match.type == "cooccur":
            hit = _match_cooccur(rule, text, spec.softeners)
        if hit is not None:
            hits.append(hit)
    # 排序：BLOCK 先，组内行号升序
    level_rank = {"BLOCK": 0, "WARN": 1}
    hits.sort(key=lambda h: (level_rank.get(h.level, 9), h.line, h.rule_id))
    return hits


def verdict_and_exit(hits: list[Hit]) -> tuple[str, int]:
    """返回 (verdict, exit_code)。verdict ∈ {PASS,WARN,BLOCK}。"""
    n_block = sum(1 for h in hits if h.level == "BLOCK")
    n_warn = sum(1 for h in hits if h.level == "WARN")
    if n_block > 0:
        return "BLOCK", 1
    if n_warn > 0:
        return "WARN", 0
    return "PASS", 0
