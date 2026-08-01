#!/usr/bin/env python3
# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by scripts/cli/accounts_cmd.py
# Pos: plugins/wxops/scripts/cli/accounts_cmd.py
"""accounts 子命令：add / list / use / remove 的中文向导式输出。"""

from __future__ import annotations

from pathlib import Path

from . import accounts_store
from . import env


def cmd_add(root: Path, slug: str, name: str | None, niche: str = "ai-tools") -> int:
    display_name = (name or "").strip() or slug
    niche = niche or "ai-tools"
    try:
        before_current = accounts_store.get_current_slug(root)
        account = accounts_store.create_account(root, slug, display_name, niche=niche)
    except (ValueError, FileExistsError) as e:
        env.print_error(str(e))
        return 1

    acct_dir = accounts_store.get_account_dir(root, slug)
    env.print_success(f"账号已创建：{account.get('name', display_name)}（{slug}）")
    env.print_info(f"办公室目录：{acct_dir.resolve()}")
    env.print_info(f"  credentials/  browser-profile/  raw/  reports/  output/")
    env.print_info(f"  topics/  drafts/  images/  published/")

    after_current = accounts_store.get_current_slug(root)
    if before_current is None and after_current == slug:
        env.print_success("已设为当前账号")

    env.print_guide_next(f"wxops login --account {slug}   （扫码登录该账号后台）")
    return 0


def cmd_list(root: Path) -> int:
    accounts = accounts_store.list_accounts(root)
    if not accounts:
        env.print_warn("还没有任何账号。")
        env.print_guide_next('wxops accounts add <slug> --name "<显示名>"')
        if accounts_store.has_legacy_layout(root):
            env.print_info("检测到旧版单账号数据，可运行：wxops migrate")
        return 0

    current = accounts_store.get_current_slug(root)
    headers = ["", "账号", "名称", "赛道", "最近登录", "最近拉数", "状态"]
    rows: list[list[str]] = []
    for acct in accounts:
        slug = str(acct.get("slug", ""))
        mark = "●" if slug == current else "○"
        rows.append(
            [
                mark,
                slug,
                str(acct.get("name") or ""),
                str(acct.get("niche") or ""),
                accounts_store.humanize_ts(acct.get("last_login_at")),
                accounts_store.humanize_ts(acct.get("last_fetch_at")),
                str(acct.get("status") or ""),
            ]
        )

    widths = [accounts_store.display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], accounts_store.display_width(cell))

    def fmt_row(cols: list[str]) -> str:
        parts = [accounts_store.pad_display(c, widths[i]) for i, c in enumerate(cols)]
        return "  ".join(parts)

    print(fmt_row(headers))
    for row in rows:
        print(fmt_row(row))
    print("(● = 当前账号)")
    return 0


def _list_available_slugs(root: Path) -> None:
    slugs = [str(a.get("slug", "")) for a in accounts_store.list_accounts(root)]
    if slugs:
        env.print_info("可用账号：" + "、".join(slugs))
    else:
        env.print_info("当前没有任何账号。")


def cmd_use(root: Path, slug: str) -> int:
    account = accounts_store.get_account(root, slug)
    if account is None:
        env.print_error(f"账号不存在：{slug}")
        _list_available_slugs(root)
        return 1
    try:
        accounts_store.set_current(root, slug)
    except ValueError as e:
        env.print_error(str(e))
        return 1
    name = account.get("name") or slug
    env.print_success(f"当前账号已切换为：{name}（{slug}）")
    env.print_guide_next("wxops desk   （看看现在该干嘛）")
    return 0


def cmd_remove(root: Path, slug: str) -> int:
    account = accounts_store.get_account(root, slug)
    if account is None:
        env.print_error(f"账号不存在：{slug}")
        _list_available_slugs(root)
        return 1

    was_current = accounts_store.get_current_slug(root) == slug
    try:
        updated = accounts_store.retire_account(root, slug)
    except ValueError as e:
        env.print_error(str(e))
        return 1

    name = updated.get("name") or slug
    acct_dir = accounts_store.get_account_dir(root, slug)
    env.print_success(f"账号已退休：{name}（{slug}）")
    env.print_info("数据一个字节都没有删除，全部保留在：")
    env.print_info(str(acct_dir.resolve()))
    env.print_info("如需彻底删除，请自行确认后手动删除该目录。")
    if was_current:
        env.print_warn("该账号原为当前账号，当前账号已置空。")
        env.print_guide_next("wxops accounts use <slug>   （切换到其他账号）")
    return 0
