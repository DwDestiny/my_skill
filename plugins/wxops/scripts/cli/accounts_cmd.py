#!/usr/bin/env python3
# GEB-L3
# Input: wxops root + add/list/use/remove/check 参数（slug/name/niche）；可选 health checker/sleeper
# Output: 中文向导式终端表与下一步提示；经 store 建号/切换/退休/写 login_alive；exit 0/1
# Pos: plugins/wxops/scripts/cli/accounts_cmd.py
"""accounts 子命令：add / list / use / remove / check 的中文向导式输出。"""

from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Any, Callable

from . import accounts_store
from . import env
from . import health
from . import lock as lock_mod


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


def cmd_check(
    root: Path,
    slug: str | None = None,
    *,
    checker: Callable[[Path], dict[str, Any]] | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> int:
    """登录态体检：逐号 headless 探测，写回 login_alive / last_check_at。"""
    check_fn = checker or health.check_login
    sleep_fn = sleeper or time.sleep

    targets: list[dict[str, Any]] = []
    if slug is not None:
        try:
            slug = accounts_store.validate_slug(slug)
        except ValueError as e:
            env.print_error(str(e))
            return 1
        account = accounts_store.get_account(root, slug)
        if account is None:
            env.print_error(f"账号不存在：{slug}")
            _list_available_slugs(root)
            return 1
        targets = [account]
    else:
        targets = [
            a
            for a in accounts_store.list_accounts(root)
            if a.get("status") == "active"
        ]
        targets.sort(key=lambda a: str(a.get("slug", "")))
        if not targets:
            env.print_warn("还没有任何账号。")
            env.print_guide_next('wxops accounts add <slug> --name "<显示名>"')
            return 1

    env.print_header("登录态体检")
    headers = ["账号", "名称", "登录态", "最近登录", "耗时"]
    rows: list[list[str]] = []
    offline_slugs: list[str] = []
    probed = 0

    for i, acct in enumerate(targets):
        s = str(acct.get("slug") or "")
        name = str(acct.get("name") or s)
        workspace = accounts_store.get_account_dir(root, s)
        login_col = "○ 掉线"
        duration_col = "—"
        try:
            result = check_fn(workspace)
            alive = bool(result.get("alive"))
            duration_s = float(result.get("duration_s") or 0.0)
            accounts_store.set_login_health(root, s, alive)
            login_col = "● 在线" if alive else "○ 掉线"
            duration_col = f"{duration_s:.1f}s"
            probed += 1
            if not alive:
                offline_slugs.append(s)
        except lock_mod.ProfileLockError as e:
            login_col = "⚠ 占用"
            env.print_error(str(e))

        rows.append(
            [
                s,
                name,
                login_col,
                accounts_store.humanize_ts(acct.get("last_login_at")),
                duration_col,
            ]
        )

        # 号间间隔；最后一号后不 sleep
        if i < len(targets) - 1:
            sleep_fn(random.uniform(1, 3))

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

    if offline_slugs:
        # 掉线号补登录提示（撞锁账号不算掉线，不进此提示）
        first = offline_slugs[0]
        tip = f"掉线号补登录：wxops login --account {first}"
        if len(offline_slugs) > 1:
            tip += "   （一次补齐：wxops login --all）"
        print()
        print(tip)

    return 0 if probed > 0 else 1
