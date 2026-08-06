# GEB-L3
# Input: raw_records（原始导出 records 列表）+ 可选 derived 探测器结果 dict
# Output: 全维度 metric_availability 申报（status/coverage/all_zero/detail）
# Pos: plugins/wxops/scripts/analyze/metric_registry.py
"""指标维度注册表与可得性探测（issue #61）。

单一真源：新增指标只加 METRIC_DIMENSIONS 条目。
可得性看「源字段是否出现」，不看值是否为 0；值为 0 且字段存在 = 真零。
"""
from __future__ import annotations

from typing import Any, Literal

MetricProbe = Literal["raw_field", "derived"]

METRIC_DIMENSIONS: list[dict[str, Any]] = [
    {
        "key": "reads",
        "label": "阅读数",
        "probe": "raw_field",
        "source_fields": ("read_num",),
        "core": True,
    },
    {
        "key": "shares",
        "label": "分享数",
        "probe": "raw_field",
        "source_fields": ("share_num",),
        "core": True,
    },
    {
        "key": "comments",
        "label": "评论数",
        "probe": "raw_field",
        "source_fields": ("comment_num",),
        "core": True,
    },
    {
        "key": "likes",
        "label": "点赞数",
        "probe": "raw_field",
        "source_fields": ("like_num",),
        "core": True,
    },
    {
        "key": "old_likes",
        "label": "旧版点赞",
        "probe": "raw_field",
        "source_fields": ("old_like_num",),
        "core": False,
    },
    {
        "key": "moment_likes",
        "label": "朋友圈点赞",
        "probe": "raw_field",
        "source_fields": ("moment_like_num",),
        "core": False,
    },
    {
        "key": "reprints",
        "label": "转载数",
        "probe": "raw_field",
        "source_fields": ("reprint_num",),
        "core": False,
    },
    {
        "key": "zaikan",
        "label": "在看数",
        "probe": "raw_field",
        "source_fields": ("wow_num", "looking_num", "zaikan_num"),
        "core": False,
    },
    {
        "key": "article_length_chars",
        "label": "正文字数",
        "probe": "derived",
        "core": False,
    },
    {
        "key": "fans_portrait",
        "label": "粉丝画像",
        "probe": "derived",
        "core": False,
    },
]

_VALID_STATUSES = frozenset(
    {"available", "platform_not_provided", "fetch_missing", "not_applicable"}
)


def core_pending_count(availability: dict[str, dict[str, Any]]) -> int:
    """核心指标缺口数：core=True 且 status != available。"""
    n = 0
    for dim in METRIC_DIMENSIONS:
        if not dim.get("core"):
            continue
        entry = availability.get(dim["key"]) or {}
        if entry.get("status") != "available":
            n += 1
    return n


def _probe_raw_field(
    raw_records: list[dict[str, Any]],
    *,
    label: str,
    source_fields: tuple[str, ...],
) -> dict[str, Any]:
    total = len(raw_records)
    if total == 0:
        fields_txt = " / ".join(source_fields)
        return {
            "label": label,
            "status": "fetch_missing",
            "coverage": 0.0,
            "all_zero": None,
            "detail": f"无原始记录，无法探测 {fields_txt}",
        }

    # 一条记录只要出现任一 source_field 即计为覆盖
    present_flags: list[bool] = []
    values_when_present: list[Any] = []
    for rec in raw_records:
        if not isinstance(rec, dict):
            present_flags.append(False)
            continue
        hit = False
        for field in source_fields:
            if field in rec:
                hit = True
                values_when_present.append(rec.get(field))
                break
        present_flags.append(hit)

    present_count = sum(1 for f in present_flags if f)
    coverage = round(present_count / total, 4)
    fields_txt = " / ".join(source_fields)

    if present_count == 0:
        return {
            "label": label,
            "status": "platform_not_provided",
            "coverage": 0.0,
            "all_zero": None,
            "detail": f"原始记录 {total} 条中未出现 {fields_txt}",
        }

    # 可得：值为 0 就是真零；all_zero 仅作观察
    all_zero: bool | None = None
    if values_when_present:
        def _is_zero(v: Any) -> bool:
            if v is None:
                return True
            if isinstance(v, (int, float)):
                return float(v) == 0.0
            text = str(v).replace(",", "").strip()
            if not text:
                return True
            try:
                return float(text) == 0.0
            except ValueError:
                return False

        all_zero = all(_is_zero(v) for v in values_when_present)

    detail = f"原始记录 {present_count}/{total} 条出现 {fields_txt}"
    if present_count < total:
        detail += f"（覆盖率 {coverage}）"
    if all_zero:
        detail += "；出现处值全为 0"

    return {
        "label": label,
        "status": "available",
        "coverage": coverage,
        "all_zero": all_zero,
        "detail": detail,
    }


def probe_availability(
    raw_records: list[dict[str, Any]],
    *,
    derived: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """遍历 METRIC_DIMENSIONS，逐维度申报可得性。

    raw_records: 原始导出的 records 列表（不是 enrich 后的 article）
    derived: {"article_length_chars": {"status": ..., "coverage": ..., "detail": ...}, ...}
             probe == "derived" 的维度由调用方传入；未传入 → not_applicable
    """
    derived = derived or {}
    out: dict[str, dict[str, Any]] = {}

    for dim in METRIC_DIMENSIONS:
        key = dim["key"]
        label = dim["label"]
        probe = dim["probe"]

        if probe == "raw_field":
            source_fields = tuple(dim.get("source_fields") or ())
            out[key] = _probe_raw_field(
                raw_records, label=label, source_fields=source_fields
            )
            continue

        # derived
        payload = derived.get(key)
        if not payload:
            out[key] = {
                "label": label,
                "status": "not_applicable",
                "coverage": 0.0,
                "all_zero": None,
                "detail": f"{label}：调用方未传入 derived 探测器，标记为不适用",
            }
            continue

        status = str(payload.get("status") or "not_applicable")
        if status not in _VALID_STATUSES:
            status = "not_applicable"
        coverage = payload.get("coverage", 0.0)
        try:
            coverage_f = float(coverage)
        except (TypeError, ValueError):
            coverage_f = 0.0
        all_zero = payload.get("all_zero", None)
        detail = str(payload.get("detail") or f"{label}：{status}")
        out[key] = {
            "label": label,
            "status": status,
            "coverage": coverage_f,
            "all_zero": all_zero,
            "detail": detail,
        }

    return out


def derived_article_length(stable: list[dict[str, Any]]) -> dict[str, Any]:
    """正文字数 derived 探测器：matched_local_article 比例。"""
    total = len(stable)
    if total == 0:
        return {
            "status": "fetch_missing",
            "coverage": 0.0,
            "all_zero": None,
            "detail": "稳定样本 0 篇，正文字数无法匹配",
        }
    matched = sum(
        1 for a in stable if a.get("length_status") == "matched_local_article"
    )
    coverage = round(matched / total, 4)
    detail = f"正文本地匹配 {matched}/{total}"
    if matched == total:
        return {
            "status": "available",
            "coverage": coverage,
            "all_zero": None,
            "detail": detail,
        }
    return {
        "status": "fetch_missing",
        "coverage": coverage,
        "all_zero": None,
        "detail": detail,
    }


def derived_fans_portrait(fans_portrait_available: bool) -> dict[str, Any]:
    """粉丝画像 derived 探测器：后台画像需登录补抓。"""
    if fans_portrait_available:
        return {
            "status": "available",
            "coverage": 1.0,
            "all_zero": None,
            "detail": "后台粉丝画像可得",
        }
    return {
        "status": "fetch_missing",
        "coverage": 0.0,
        "all_zero": None,
        "detail": "后台粉丝画像不可得，需登录补抓",
    }
