#!/usr/bin/env python3
# GEB-L3
# Input: wxops root、可选 account slug、draft.md 路径或 --text、--json
# Output: 稿件合规闸终端/JSON 报告；exit 0=无BLOCK，1=有BLOCK，2=用法/缺规则/坏包
# Pos: plugins/wxops/scripts/cli/lint_cmd.py
"""lint 稿件合规闸：按赛道 compliance.json 三层回落扫正文。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from . import accounts_store
from . import compliance_lib
from . import env


def _resolve_account(root: Path, account: str | None) -> tuple[str, dict[str, Any]] | int:
    """成功返回 (slug, acct)；失败打印错误并返回 exit code。"""
    slug_raw = (account or "").strip() or None
    if slug_raw is None:
        current = accounts_store.get_current_slug(root)
        if not current:
            env.print_error(
                "未指定账号，且没有当前账号。"
                "请先 wxops accounts add 或给 --account。"
            )
            return 2
        slug_raw = current
    try:
        slug = accounts_store.validate_slug(slug_raw)
    except ValueError as e:
        env.print_error(str(e))
        return 2
    acct = accounts_store.get_account(root, slug)
    if acct is None:
        env.print_error(f"账号不存在：{slug}")
        slugs = [str(a.get("slug", "")) for a in accounts_store.list_accounts(root)]
        if slugs:
            env.print_info("可用账号：" + "、".join(slugs))
        else:
            env.print_info("当前没有任何账号。")
        return 2
    return slug, acct


def _load_spec_for_account(
    root: Path, niche_id: str
) -> tuple[compliance_lib.ComplianceSpec, None] | tuple[None, int]:
    path, layer, niche_shown = compliance_lib.resolve_compliance(
        root, niche_id, env.get_skill_dir()
    )
    if path is None:
        env.print_error(
            f"未找到合规规则 compliance.json（赛道 {niche_id}）。"
            f"请放到 niches/{niche_id}/compliance.json（用户包）"
            f"或插件 niches/{niche_id}/compliance.json，"
            f"亦可依赖 niches/_generic/compliance.json 通用兜底。"
        )
        return None, 2
    try:
        spec = compliance_lib.load_compliance(
            path, layer=layer, niche_shown=niche_shown  # type: ignore[arg-type]
        )
    except compliance_lib.ComplianceLoadError as e:
        env.print_error(str(e))
        return None, 2
    if layer == "通用兜底":
        env.print_warn(
            f"正在用通用兜底合规规则（_generic），建议为赛道 {niche_id} 建 compliance.json"
        )
    return spec, None


def _print_human(
    *,
    slug: str,
    source_label: str,
    spec: compliance_lib.ComplianceSpec,
    hits: list[compliance_lib.Hit],
) -> None:
    env.print_header(f"稿件合规闸：{slug} / {source_label}")
    print(f"赛道包：{spec.niche_shown}（{spec.layer}）")
    print()
    for h in hits:
        print(
            f"{h.level:<6} {h.title:<20} 第 {h.line} 行  命中「{h.matched}」"
        )
        env.print_info(f"为什么：{h.why}")
        env.print_info(f"怎么改：{h.fix}")
        env.print_info(f"原文：{h.context}")
        print()
    n_block = sum(1 for h in hits if h.level == "BLOCK")
    n_warn = sum(1 for h in hits if h.level == "WARN")
    if not hits:
        print("结论：0 BLOCK / 0 WARN，可发布。")
    elif n_block > 0:
        extra = f"，另有 {n_warn} 处待人工确认" if n_warn else ""
        print(f"结论：{n_block} BLOCK / {n_warn} WARN，不可发布{extra}。")
    else:
        print(f"结论：0 BLOCK / {n_warn} WARN，{n_warn} 处待人工确认。")


def run(
    root: Path,
    account: str | None = None,
    draft: str | None = None,
    text: str | None = None,
    as_json: bool = False,
) -> int:
    """稿件合规闸主入口。"""
    resolved = _resolve_account(root, account)
    if isinstance(resolved, int):
        return resolved
    slug, acct = resolved
    niche_id = str(acct.get("niche") or "ai-tools")

    has_draft = draft is not None and str(draft).strip() != ""
    has_text = text is not None
    if has_draft and has_text:
        env.print_error("请只给草稿文件或 --text 其一，不要同时给。")
        return 2
    if not has_draft and not has_text:
        env.print_error("请提供草稿文件路径，或用 --text 检查一句话。")
        return 2

    if has_text:
        raw = str(text)
        source_label = "（--text）"
    else:
        draft_path = Path(str(draft)).expanduser()
        if not draft_path.is_file():
            env.print_error(f"草稿文件不存在：{draft_path}")
            return 2
        try:
            raw = draft_path.read_text(encoding="utf-8")
        except OSError as e:
            env.print_error(f"无法读取草稿：{e}")
            return 2
        source_label = draft_path.name

    loaded = _load_spec_for_account(root, niche_id)
    if loaded[0] is None:
        return loaded[1]  # type: ignore[return-value]
    spec = loaded[0]

    hits = compliance_lib.scan_text(spec, raw)
    verdict, code = compliance_lib.verdict_and_exit(hits)
    counts = {
        "BLOCK": sum(1 for h in hits if h.level == "BLOCK"),
        "WARN": sum(1 for h in hits if h.level == "WARN"),
    }

    if as_json:
        payload = {
            "account": slug,
            "niche": spec.niche_shown,
            "layer": spec.layer,
            "verdict": verdict,
            "counts": counts,
            "hits": [
                {
                    "rule_id": h.rule_id,
                    "level": h.level,
                    "title": h.title,
                    "line": h.line,
                    "matched": h.matched,
                    "context": h.context,
                    "why": h.why,
                    "fix": h.fix,
                }
                for h in hits
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_human(slug=slug, source_label=source_label, spec=spec, hits=hits)

    return code


def run_from_args(args: Any) -> int:
    if getattr(args, "workspace", None):
        root = Path(args.workspace).expanduser().resolve()
    else:
        root = env.get_wxops_root()
    return run(
        root,
        account=getattr(args, "account", None),
        draft=getattr(args, "draft", None),
        text=getattr(args, "text", None),
        as_json=bool(getattr(args, "json", False)),
    )


if __name__ == "__main__":
    raise SystemExit(run(env.get_wxops_root(), draft=sys.argv[1] if len(sys.argv) > 1 else None))
