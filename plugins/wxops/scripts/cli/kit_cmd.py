#!/usr/bin/env python3
# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by scripts/cli/kit_cmd.py
# Pos: plugins/wxops/scripts/cli/kit_cmd.py
"""kit 写作三件套门禁：只读体检 persona + 结构契约（+ 选题卡/证据包）。"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from . import accounts_store
from . import env

ShellReason = Literal["缺失", "为空", "含未填占位符"]


def _check_shell(path: Path) -> tuple[bool, ShellReason | None]:
    """三条空壳判定：存在、strip 非空、不含 `{{`。

    返回 (ok, reason)；ok 时 reason 为 None。
    """
    if not path.is_file():
        return False, "缺失"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False, "缺失"
    if not text.strip():
        return False, "为空"
    if "{{" in text:
        return False, "含未填占位符"
    return True, None


def _reason_display(reason: ShellReason) -> str:
    if reason == "含未填占位符":
        return "存在但含未填占位符 {{...}}"
    if reason == "为空":
        return "存在但为空"
    return "缺失"


def _guide_for(
    reason: ShellReason,
    *,
    template: str,
    rel_path: str,
) -> str:
    if reason == "缺失":
        return f"→ 按 {template} 建 {rel_path}"
    if reason == "为空":
        return f"→ 按 {template} 填写 {rel_path}"
    return f"→ 填完 {rel_path} 的全部 {{{{...}}}} 占位符"


def _resolve_structure(
    root: Path, niche_id: str
) -> tuple[Path | None, str, str]:
    """文件级三层回落查找 structure.md。

    返回 (path | None, layer_label, niche_shown)。
    layer_label: 用户包 / 内置包 / 通用兜底；全无时 layer 为空串。
    """
    niche = (niche_id or "").strip() or "ai-tools"

    user_path = root / "niches" / niche / "structure.md"
    if user_path.is_file():
        return user_path, "用户包", niche

    skill_dir = env.get_skill_dir()
    builtin_path = skill_dir / "niches" / niche / "structure.md"
    if builtin_path.is_file():
        return builtin_path, "内置包", niche

    generic_path = skill_dir / "niches" / "_generic" / "structure.md"
    if generic_path.is_file():
        return generic_path, "通用兜底", "_generic"

    return None, "", niche


def run(
    root: Path,
    account: str | None = None,
    topic: str | None = None,
) -> int:
    """写作三件套只读门禁。不创建、不修改任何文件。"""
    # --- 解析账号 ---
    slug_raw = (account or "").strip() or None
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

    acct = accounts_store.get_account(root, slug)
    if acct is None:
        env.print_error(f"账号不存在：{slug}")
        slugs = [str(a.get("slug", "")) for a in accounts_store.list_accounts(root)]
        if slugs:
            env.print_info("可用账号：" + "、".join(slugs))
        else:
            env.print_info("当前没有任何账号。")
        return 1

    # --- 解析 topic（可选）---
    topic_slug: str | None = None
    if topic is not None and str(topic).strip() != "":
        try:
            topic_slug = accounts_store.validate_slug(str(topic).strip())
        except ValueError as e:
            env.print_error(f"topic 不合法：{e}")
            return 1

    acct_dir = accounts_store.get_account_dir(root, slug)
    niche_id = str(acct.get("niche") or "ai-tools")

    if topic_slug:
        env.print_header(f"开工体检：{slug} / {topic_slug}")
    else:
        env.print_header(f"账号体检：{slug}")

    fail_count = 0

    # 1) persona
    persona_path = acct_dir / "persona.md"
    persona_rel = f"accounts/{slug}/persona.md"
    ok, reason = _check_shell(persona_path)
    if ok:
        env.print_success(f"人设 persona.md        {persona_rel}")
    else:
        assert reason is not None
        fail_count += 1
        env.print_error(
            f"人设 persona.md        {_reason_display(reason)}"
        )
        env.print_info(
            _guide_for(
                reason,
                template="templates/persona.template.md",
                rel_path=persona_rel,
            )
        )

    # 2) structure（文件级三层回落；存在即可，不做空壳判定）
    struct_path, layer, niche_shown = _resolve_structure(root, niche_id)
    if struct_path is None:
        fail_count += 1
        env.print_error("结构契约 structure.md   缺失（三层均未找到）")
        env.print_info(
            f"→ 在 niches/{niche_id}/structure.md（用户包）"
            f"或插件 niches/{niche_id}/structure.md 放置结构契约"
        )
    else:
        env.print_success(
            f"结构契约 structure.md   {layer} {niche_shown}"
        )
        if layer == "通用兜底":
            env.print_warn(
                "正在用通用兜底结构契约，建议为你的赛道建 structure.md"
            )

    # 3)(4) 选题卡 + 证据包（仅开工体检）
    if topic_slug:
        topic_dir = acct_dir / "topics" / topic_slug
        card_path = topic_dir / "card.md"
        card_rel = f"accounts/{slug}/topics/{topic_slug}/card.md"
        ok, reason = _check_shell(card_path)
        if ok:
            env.print_success(f"选题卡 card.md         {card_rel}")
        else:
            assert reason is not None
            fail_count += 1
            env.print_error(
                f"选题卡 card.md         {_reason_display(reason)}"
            )
            env.print_info(
                _guide_for(
                    reason,
                    template="templates/topic-card.template.md",
                    rel_path=card_rel,
                )
            )

        evid_path = topic_dir / "evidence.md"
        evid_rel = f"accounts/{slug}/topics/{topic_slug}/evidence.md"
        ok, reason = _check_shell(evid_path)
        if ok:
            env.print_success(f"证据包 evidence.md      {evid_rel}")
        else:
            assert reason is not None
            fail_count += 1
            env.print_error(
                f"证据包 evidence.md      {_reason_display(reason)}"
            )
            env.print_info(
                _guide_for(
                    reason,
                    template="templates/evidence-pack.template.md",
                    rel_path=evid_rel,
                )
            )

    print()
    if fail_count == 0:
        if topic_slug:
            print("结论：三件套齐备，可开工。")
        else:
            print("结论：人设与结构契约就位。")
        return 0

    print(f"结论：缺 {fail_count} 件，不可开工。")
    return 1
