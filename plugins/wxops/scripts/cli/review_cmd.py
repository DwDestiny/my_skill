#!/usr/bin/env python3
# GEB-L3
# Input: argparse Namespace（--topic/--account/--workspace）+ WXOPS_HOME 工作区
# Output: accounts/<slug>/reports/review-<topic>.md 复盘报告；exit 0/1
# Pos: plugins/wxops/scripts/cli/review_cmd.py
# 只读台账/选题卡/analyze 数据，唯一写动作是落报告；绝不改 persona/niche
"""review 复盘工位：对照选题卡预期与 analyze 实际数据出结论。"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from . import accounts_store
from . import env

# scripts/ 作为包根，供 analyze.io_utils 导入（勿注入 scripts/publish）
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from analyze.io_utils import compact_match_key  # noqa: E402

_RANGE_RE = re.compile(r"(\d+)\s*[-~—]\s*(\d+)")
_THRESHOLD_RE = re.compile(r"[≥>=＞]\s*(\d+)")
_CUSTOM_METRIC_RE = re.compile(
    r"(阅读|在看|点赞|转发|分享)\s*[:：]?\s*(≥|>=|>|≤|<=|<|＞|＜)\s*(\d+)"
)
_METRIC_FIELD = {
    "阅读": "reads",
    "在看": "zaikan",
    "点赞": "likes",
    "转发": "shares",
    "分享": "shares",
}


def _root_from_args(args: Any) -> Path:
    """与 main._root_from_args 等价，本文件内联，不改 main helper。"""
    if getattr(args, "workspace", None):
        return Path(args.workspace).expanduser().resolve()
    return env.get_wxops_root()


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _extract_expected_section(card_text: str) -> str | None:
    """截取「## 预期指标」到下一个同级标题之间的正文；找不到返回 None。"""
    m = re.search(r"(?m)^##\s*预期指标\s*$", card_text)
    if not m:
        return None
    rest = card_text[m.end() :]
    next_h = re.search(r"(?m)^##\s+", rest)
    if next_h:
        rest = rest[: next_h.start()]
    return rest


def _parse_bullet_lines(section: str) -> list[tuple[str, str]]:
    """解析 `- 标签：值` 行，返回 (label, value) 列表。"""
    items: list[tuple[str, str]] = []
    for raw in section.splitlines():
        line = raw.strip()
        if not line.startswith("-"):
            continue
        body = line.lstrip("-").strip()
        if not body or body.startswith(">"):
            continue
        # 去掉可能的 **加粗**
        body = re.sub(r"\*\*(.+?)\*\*", r"\1", body)
        if "：" in body:
            label, value = body.split("：", 1)
        elif ":" in body:
            label, value = body.split(":", 1)
        else:
            continue
        label = label.strip()
        value = value.strip()
        if not label:
            continue
        items.append((label, value))
    return items


def _eval_reads(value: str, reads: int) -> tuple[str, str, bool | None]:
    """返回 (actual_display, verdict, achieved|None)。None=人工。"""
    m = _RANGE_RE.search(value)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        if lo > hi:
            lo, hi = hi, lo
        if lo <= reads <= hi:
            return str(reads), "✅ 达成", True
        if reads > hi:
            return str(reads), "✅ 达成（超预期）", True
        return str(reads), "偏差", False

    m2 = _THRESHOLD_RE.search(value)
    if m2:
        n = int(m2.group(1))
        if reads >= n:
            return str(reads), "✅ 达成", True
        return str(reads), "偏差", False

    return str(reads), "人工核对", None


def _eval_custom(label: str, value: str, article: dict[str, Any]) -> tuple[str, str, bool | None]:
    """自加行：尽力解析比较符；解析不出 → 人工核对。"""
    blob = f"{label}：{value}"
    m = _CUSTOM_METRIC_RE.search(blob) or _CUSTOM_METRIC_RE.search(value)
    if not m:
        return "—", "人工核对", None

    metric_name, op, num_s = m.group(1), m.group(2), m.group(3)
    field = _METRIC_FIELD.get(metric_name)
    if not field:
        return "—", "人工核对", None
    actual = int(article.get(field) or 0)
    n = int(num_s)
    op_n = op.replace("＞", ">").replace("＜", "<")
    if op_n in ("≥", ">="):
        ok = actual >= n
    elif op_n == ">":
        ok = actual > n
    elif op_n in ("≤", "<="):
        ok = actual <= n
    elif op_n == "<":
        ok = actual < n
    else:
        return str(actual), "人工核对", None

    if ok:
        return str(actual), "✅ 达成", True
    return str(actual), "偏差", False


def _has_unfilled_placeholder(value: str) -> bool:
    """value 中出现连续两个左花括号即判定选题卡占位符未填（与 kit 空壳口径一致）。"""
    return "{{" in value


def _all_rows_unfilled_placeholder(rows: list[dict[str, Any]]) -> bool:
    """预期对照行非空且全部为占位符未填。空列表不算。"""
    if not rows:
        return False
    return all(
        r.get("verdict") == "选题卡未填写（占位符未替换）" for r in rows
    )


def _build_expected_rows(
    items: list[tuple[str, str]],
    article: dict[str, Any],
) -> list[dict[str, Any]]:
    """构建预期对照行。"""
    rows: list[dict[str, Any]] = []
    reads = int(article.get("reads") or 0)
    for label, value in items:
        expected_cell = f"{label}：{value}" if value else label
        # 占位符未填优先：不参与任何机器判定（逐行，非整卡）
        if _has_unfilled_placeholder(value):
            rows.append(
                {
                    "expected": expected_cell,
                    "actual": "—",
                    "verdict": "选题卡未填写（占位符未替换）",
                    "achieved": None,
                }
            )
            continue
        label_n = label.replace(" ", "")
        if "预计阅读" in label_n or label_n in ("阅读", "预计阅读量"):
            actual, verdict, achieved = _eval_reads(value, reads)
            rows.append(
                {
                    "expected": expected_cell,
                    "actual": actual,
                    "verdict": verdict,
                    "achieved": achieved,
                }
            )
            continue
        if "预计完读" in label_n or "完读" in label_n:
            rows.append(
                {
                    "expected": expected_cell,
                    "actual": "—",
                    "verdict": "人工核对（后台单篇完读数据未采集，请人工在公众号后台核对）",
                    "achieved": None,
                }
            )
            continue
        if "核心验证点" in label_n or "验证点" in label_n:
            rows.append(
                {
                    "expected": expected_cell,
                    "actual": "—",
                    "verdict": "人工判断",
                    "achieved": None,
                }
            )
            continue
        # 其他自加行
        actual, verdict, achieved = _eval_custom(label, value, article)
        rows.append(
            {
                "expected": expected_cell,
                "actual": actual,
                "verdict": verdict,
                "achieved": achieved,
            }
        )
    return rows


def _summary_line(rows: list[dict[str, Any]] | None) -> str:
    """机器可判定汇总结论。"""
    if not rows:
        return "待人工判断（机器可判定 0 项中 0 项达成；另有人工核对项 0 项）"

    machine = [r for r in rows if r.get("achieved") is not None]
    human = [r for r in rows if r.get("achieved") is None]
    x = len(machine)
    y = sum(1 for r in machine if r.get("achieved") is True)
    z = len(human)

    if x == 0:
        head = "待人工判断"
    elif y == x:
        head = "达成"
    elif y == 0:
        head = "偏差"
    else:
        head = "部分达成"
    return f"{head}（机器可判定 {x} 项中 {y} 项达成；另有人工核对项 {z} 项）"


def _format_share_rate(article: dict[str, Any]) -> str:
    """share_rate 为小数比例（如 0.0238 = 2.38%），展示时乘 100。"""
    sr = article.get("share_rate")
    if sr is None:
        return "—"
    try:
        return f"{float(sr) * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def _write_report(
    path: Path,
    *,
    title: str,
    slug: str,
    account_name: str,
    drafted_at: str,
    content_image_count: Any,
    generated_at: str,
    article: dict[str, Any] | None,
    data_not_ready_reason: str | None,
    expected_rows: list[dict[str, Any]] | None,
    expected_note: str | None,
    skip_expected_table: bool,
    zaikan_status: str | None = None,
) -> None:
    lines: list[str] = []
    lines.append(f"# 复盘 · {title}")
    lines.append("")
    lines.append(f"- 账号：{slug}（{account_name}）")
    lines.append(f"- 草稿创建：{drafted_at}（实际群发时间以后台为准）")
    lines.append(f"- 图片数：{content_image_count}")
    lines.append(f"- 复盘生成：{generated_at}")
    lines.append("")

    if data_not_ready_reason:
        lines.append("## 结论")
        lines.append("")
        lines.append(data_not_ready_reason)
        lines.append("")
        lines.append("## 修订建议（待主编确认）")
        lines.append("")
        lines.append(
            "（复盘建议由主编结合归因讨论提出；本工具不自动生成 persona/niche 修订）"
        )
        lines.append("")
    else:
        assert article is not None
        lines.append("## 实际数据")
        lines.append("")
        lines.append("| 指标 | 值 |")
        lines.append("|---|---|")
        lines.append(f"| 阅读 | {int(article.get('reads') or 0)} |")
        lines.append(f"| 点赞 | {int(article.get('likes') or 0)} |")
        # issue #61：仅改显示层；阈值判定逻辑不动
        if zaikan_status and zaikan_status != "available":
            lines.append("| 在看 | 不可得（平台未提供） |")
        else:
            lines.append(f"| 在看 | {int(article.get('zaikan') or 0)} |")
        lines.append(f"| 转发 | {int(article.get('shares') or 0)} |")
        lines.append(f"| 转发率 | {_format_share_rate(article)} |")
        lines.append("")

        if not skip_expected_table and expected_rows is not None:
            lines.append("## 预期对照")
            lines.append("")
            if expected_note:
                lines.append(expected_note)
                lines.append("")
            lines.append("| 预期 | 实际 | 结论 |")
            lines.append("|---|---|---|")
            for r in expected_rows:
                lines.append(
                    f"| {r['expected']} | {r['actual']} | {r['verdict']} |"
                )
            lines.append("")
        elif expected_note:
            lines.append("## 预期对照")
            lines.append("")
            lines.append(expected_note)
            lines.append("")

        lines.append("## 结论")
        lines.append("")
        if skip_expected_table or expected_rows is None:
            # 无预期可对：仅实际数据，结论偏人工
            lines.append(
                "待人工判断（机器可判定 0 项中 0 项达成；另有人工核对项 0 项）"
            )
        else:
            lines.append(_summary_line(expected_rows))
            if _all_rows_unfilled_placeholder(expected_rows):
                lines.append(
                    "选题卡预期指标尚未填写（全部为占位符），本次无机器可判定项。"
                )
        lines.append("")
        lines.append("## 修订建议（待主编确认）")
        lines.append("")
        lines.append(
            "（复盘建议由主编结合归因讨论提出；本工具不自动生成 persona/niche 修订）"
        )
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_review(args: Any) -> int:
    """复盘入口：只读台账/选题卡/report，落 reports/review-<topic>.md。"""
    root = _root_from_args(args)

    # --- 账号解析（照 publish_cmd）---
    slug_raw = (getattr(args, "account", None) or "").strip() or None
    if slug_raw is None:
        current = accounts_store.get_current_slug(root)
        if not current:
            env.print_error(
                "未指定账号，且没有当前账号。"
                "请先 wxops accounts add 或给 --account。"
            )
            return 1
        slug_raw = current

    try:
        slug = accounts_store.validate_slug(slug_raw)
    except ValueError as e:
        env.print_error(str(e))
        return 1

    acct_meta = accounts_store.get_account(root, slug)
    if acct_meta is None:
        env.print_error(f"账号不存在：{slug}")
        slugs = [str(a.get("slug", "")) for a in accounts_store.list_accounts(root)]
        if slugs:
            env.print_info("可用账号：" + "、".join(slugs))
        else:
            env.print_info("当前没有任何账号。")
        return 1

    if str(acct_meta.get("status") or "") == "retired":
        env.print_error(f"账号已退休，不可复盘：{slug}")
        return 1

    topic_raw = getattr(args, "topic", None)
    if topic_raw is None or str(topic_raw).strip() == "":
        env.print_error("必须提供 --topic")
        return 1
    try:
        topic = accounts_store.validate_slug(str(topic_raw).strip())
    except ValueError as e:
        env.print_error(str(e))
        return 1

    account_name = str(acct_meta.get("name") or slug)
    acct = accounts_store.get_account_dir(root, slug)
    ledger_path = acct / "published" / f"{topic}.json"
    card_path = acct / "topics" / topic / "card.md"
    report_json = acct / "output" / "report.json"
    out_path = acct / "reports" / f"review-{topic}.md"

    env.print_header(f"复盘 · {slug} / {topic}")

    # --- 1. 台账 ---
    if not ledger_path.is_file():
        env.print_error("该选题未发布过（无台账），先跑 wxops publish")
        return 1

    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        env.print_error(f"台账无法解析：{ledger_path}")
        return 1
    if not isinstance(ledger, dict):
        env.print_error(f"台账格式错误（非对象）：{ledger_path}")
        return 1

    title = str(ledger.get("title") or topic)
    drafted_at = str(ledger.get("drafted_at") or "—")
    content_image_count = ledger.get("content_image_count", "—")
    generated_at = _now_iso()

    # --- 2. 选题卡 ---
    card_text: str | None = None
    expected_items: list[tuple[str, str]] | None = None
    skip_expected_table = False
    expected_note: str | None = None

    if not card_path.is_file():
        env.print_warn("无选题卡，跳过预期对照")
        skip_expected_table = True
        expected_note = None
    else:
        try:
            card_text = card_path.read_text(encoding="utf-8")
        except OSError:
            env.print_warn("选题卡无法读取，跳过预期对照")
            skip_expected_table = True
            card_text = None
        if card_text is not None:
            section = _extract_expected_section(card_text)
            if section is None:
                env.print_warn("选题卡无预期指标段，仅出实际数据")
                skip_expected_table = True
                expected_note = "选题卡无预期指标段，仅出实际数据"
            else:
                expected_items = _parse_bullet_lines(section)

    # --- 3. report.json ---
    data_not_ready_reason: str | None = None
    article: dict[str, Any] | None = None
    zaikan_status: str | None = None

    if not report_json.is_file():
        data_not_ready_reason = (
            f"数据未就绪：先跑 wxops analyze --account {slug}"
        )
    else:
        try:
            data = json.loads(report_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data_not_ready_reason = (
                f"数据未就绪：report.json 无法解析，请重跑 "
                f"wxops analyze --account {slug}"
            )
            data = None
        if data is not None:
            # issue #61：显示层读 metric_availability.zaikan
            _z = ((data.get("metric_availability") or {}).get("zaikan") or {}).get(
                "status"
            )
            if isinstance(_z, str):
                zaikan_status = _z
            articles_obj = data.get("articles") if isinstance(data, dict) else None
            all_period: list[Any] = []
            if isinstance(articles_obj, dict):
                raw_list = articles_obj.get("all_period")
                if isinstance(raw_list, list):
                    all_period = raw_list

            title_key = compact_match_key(title)
            matched: dict[str, Any] | None = None
            for item in all_period:
                if not isinstance(item, dict):
                    continue
                if compact_match_key(str(item.get("title") or "")) == title_key:
                    matched = item
                    break

            if matched is None:
                data_not_ready_reason = (
                    "数据未就绪（analyze 数据未覆盖本文，建议明日重跑 analyze 后再试）"
                )
            elif matched.get("is_immature") is True:
                data_not_ready_reason = (
                    "数据未就绪（发布未满 48h，建议 T+3 后复盘）"
                )
            else:
                article = matched

    expected_rows: list[dict[str, Any]] | None = None
    if data_not_ready_reason is None and article is not None:
        if not skip_expected_table and expected_items is not None:
            expected_rows = _build_expected_rows(expected_items, article)

    if expected_rows is not None and _all_rows_unfilled_placeholder(expected_rows):
        env.print_warn(
            "选题卡预期指标尚未填写（全部为占位符），本次无机器可判定项。"
        )

    _write_report(
        out_path,
        title=title,
        slug=slug,
        account_name=account_name,
        drafted_at=drafted_at,
        content_image_count=content_image_count,
        generated_at=generated_at,
        article=article,
        data_not_ready_reason=data_not_ready_reason,
        expected_rows=expected_rows,
        expected_note=expected_note,
        skip_expected_table=skip_expected_table,
        zaikan_status=zaikan_status,
    )

    if data_not_ready_reason:
        conclusion = data_not_ready_reason
    elif expected_rows is not None:
        conclusion = _summary_line(expected_rows)
    else:
        conclusion = (
            "待人工判断（机器可判定 0 项中 0 项达成；另有人工核对项 0 项）"
        )
    env.print_info(conclusion)
    env.print_success(str(out_path))
    return 0
