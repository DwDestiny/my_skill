#!/usr/bin/env python3
# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by scripts/cli/main.py
# Pos: plugins/wxops/scripts/cli/main.py
"""wxops 可执行入口主分发：init / login / analyze / accounts / migrate / desk。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import accounts_cmd
from . import accounts_store
from . import analyze_cmd
from . import desk_cmd
from . import env
from . import init_cmd
from . import lock as lock_mod
from . import login_cmd
from . import migrate_cmd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wxops",
        description="公众号运营分析向导式 CLI：三步上手（环境自检 → 登录 → 分析看板）。",
    )

    # 顶层也声明（帮助可见），并用 parent 确保子命令后带 flag 也生效
    parser.add_argument(
        "--workspace",
        default=None,
        help="工作区目录（默认 ~/.wxops 或 WXOPS_HOME，存放登录态、抓取数据、输出）。",
    )
    parser.add_argument(
        "--account",
        default=None,
        help="账号 slug（工作区 = <root>/accounts/<slug>；与 --workspace 互斥）。",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--workspace",
        default=None,
        help="工作区目录（默认 ~/.wxops 或 WXOPS_HOME，存放登录态、抓取数据、输出）。",
    )
    common.add_argument(
        "--account",
        default=None,
        help="账号 slug（工作区 = <root>/accounts/<slug>；与 --workspace 互斥）。",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", parents=[common], help="环境自检 + 创建 workspace + 写入配置")
    p_init.add_argument("--account-name", default=None, help="公众号名称（不传则交互输入）")

    # login
    p_login = subparsers.add_parser("login", parents=[common], help="引导使用微信扫码登录公众号后台，持久化登录态")
    p_login.add_argument("--headless", action="store_true", help="无头模式（默认交互需可视化扫码）")

    # analyze
    p_analyze = subparsers.add_parser("analyze", parents=[common], help="抓取/使用数据 → 构建报告 → 启动看板")
    p_analyze.add_argument("--demo", action="store_true", help="使用 skill 内 fixtures 演示数据（无需登录/抓取）")
    p_analyze.add_argument("--build", action="store_true", help="仅构建 dashboard（pnpm build），不启动 dev 服务器")
    p_analyze.add_argument(
        "--data-only",
        action="store_true",
        help="只产出数据（report.json/MD），不复制 dashboard、不跑 pnpm（CI / 只读冒烟用）",
    )
    p_analyze.add_argument("--account-name", default=None, help="覆盖配置中的公众号名称")

    # accounts（leaf 也挂 common，以便 `accounts list --workspace X` 可用）
    p_accounts = subparsers.add_parser(
        "accounts",
        parents=[common],
        help="多账号管理：add / list / use / remove",
    )
    acc_sub = p_accounts.add_subparsers(dest="accounts_command", required=True)

    p_add = acc_sub.add_parser("add", parents=[common], help="创建账号办公室")
    p_add.add_argument("slug", help="账号 slug（小写字母/数字/连字符）")
    p_add.add_argument("--name", default=None, help="显示名")
    p_add.add_argument("--niche", default="ai-tools", help="赛道（默认 ai-tools）")

    acc_sub.add_parser("list", parents=[common], help="列出全部账号")

    p_use = acc_sub.add_parser("use", parents=[common], help="切换当前账号")
    p_use.add_argument("slug", help="账号 slug")

    p_remove = acc_sub.add_parser("remove", parents=[common], help="退休账号（不删数据）")
    p_remove.add_argument("slug", help="账号 slug")

    # migrate
    p_migrate = subparsers.add_parser(
        "migrate",
        parents=[common],
        help="旧单账号工作区 → accounts/<slug>/（copy-first）",
    )
    p_migrate.add_argument("--slug", default="default", help="目标账号 slug（默认 default）")
    p_migrate.add_argument("--name", default=None, help="显示名（默认读 config.json 的 account_name）")

    # desk
    subparsers.add_parser(
        "desk",
        parents=[common],
        help="编辑部总控台：各账号流水线状态与下一步建议",
    )

    return parser


def _root_from_args(args: argparse.Namespace) -> Path:
    """accounts / migrate / desk 用：--workspace 优先，否则 WXOPS_HOME。"""
    if getattr(args, "workspace", None):
        return Path(args.workspace).expanduser().resolve()
    return env.get_wxops_root()


def resolve_context(args: argparse.Namespace) -> tuple[Path, str | None]:
    """返回 (workspace, slug)。slug=None 表示 legacy 单租户模式。

    优先级（accounts/SKILL.md）：
      1. --workspace  → legacy 直通，slug=None（与 --account 互斥）
      2. --account    → root/accounts/<slug>
      3. registry.current → root/accounts/<current>
      4. 都没有       → legacy 回落 root 本身，slug=None
    """
    workspace_override = getattr(args, "workspace", None)
    account = getattr(args, "account", None)
    # accounts 子命令相关参数不走这里；root 固定取 WXOPS_HOME
    root = env.get_wxops_root()

    if workspace_override and account:
        env.print_error("--workspace 与 --account 互斥，请只给其一。")
        raise SystemExit(2)

    if workspace_override:
        return Path(workspace_override).expanduser().resolve(), None

    if account:
        try:
            slug = accounts_store.validate_slug(account)
        except ValueError as e:
            env.print_error(str(e))
            raise SystemExit(1) from e
        acct = accounts_store.get_account(root, slug)
        if acct is None:
            env.print_error(f"账号不存在：{slug}")
            slugs = [str(a.get("slug", "")) for a in accounts_store.list_accounts(root)]
            if slugs:
                env.print_info("可用账号：" + "、".join(slugs))
            else:
                env.print_info("当前没有任何账号。")
            raise SystemExit(1)
        return accounts_store.get_account_dir(root, slug), slug

    current = accounts_store.get_current_slug(root)
    if current:
        acct = accounts_store.get_account(root, current)
        if acct is not None:
            return accounts_store.get_account_dir(root, current), current
        env.print_warn(
            f"注册表当前账号指向了不存在的账号：{current}，回退到旧版单账号工作区。"
        )

    # legacy 回落
    if accounts_store.has_legacy_layout(root):
        env.print_info(
            "提示：检测到旧版单账号数据，可运行 wxops migrate 升级为多账号结构。"
        )
    return root, None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # accounts / migrate / desk：直接操作 root，不走 resolve_context
    if args.command == "accounts":
        root = _root_from_args(args)
        sub = getattr(args, "accounts_command", None)
        if sub == "add":
            return accounts_cmd.cmd_add(
                root,
                slug=args.slug,
                name=getattr(args, "name", None),
                niche=getattr(args, "niche", "ai-tools") or "ai-tools",
            )
        if sub == "list":
            return accounts_cmd.cmd_list(root)
        if sub == "use":
            return accounts_cmd.cmd_use(root, slug=args.slug)
        if sub == "remove":
            return accounts_cmd.cmd_remove(root, slug=args.slug)
        env.print_error("未知 accounts 子命令")
        return 1

    if args.command == "migrate":
        root = _root_from_args(args)
        return migrate_cmd.run(
            root,
            slug=getattr(args, "slug", "default") or "default",
            name=getattr(args, "name", None),
        )

    if args.command == "desk":
        root = _root_from_args(args)
        return desk_cmd.run(root)

    # init / login / analyze
    try:
        workspace, slug = resolve_context(args)
    except SystemExit as e:
        code = e.code
        if code is None:
            return 1
        if isinstance(code, int):
            return code
        return 1

    root = env.get_wxops_root()
    if slug:
        env.ensure_account_dirs(workspace)
    else:
        env.ensure_workspace_dirs(workspace)

    if args.command == "init":
        return init_cmd.run(
            workspace=workspace,
            account_name_override=getattr(args, "account_name", None),
        )

    if args.command == "login":
        headless = getattr(args, "headless", False)
        if slug:
            acct = accounts_store.get_account(root, slug)
            name = (acct or {}).get("name") or slug
            env.print_header(f"即将登录账号：{name}（{slug}）")
            env.print_step("请核对账号", "扫码前确认目标公众号无误，避免扫错号")
        try:
            profile_lock = lock_mod.acquire_profile_lock(workspace)
        except lock_mod.ProfileLockError as e:
            env.print_error(str(e))
            return 1
        with profile_lock:
            rc = login_cmd.run(workspace=workspace, headless=headless)
        if rc == 0 and slug:
            accounts_store.touch(root, slug, "last_login_at")
            ok = accounts_store.touch_pipeline(root, slug, "login", ok=True)
            if not ok:
                env.print_warn("pipeline.json 写入失败（不影响本次登录）")
        return rc

    if args.command == "analyze":
        demo = getattr(args, "demo", False)
        do_build_only = getattr(args, "build", False)
        data_only = getattr(args, "data_only", False)
        account_override = getattr(args, "account_name", None)
        # 非 demo 且用户未显式给 --account-name 时，用 account.json 的显示名
        if slug and not demo and not account_override:
            acct = accounts_store.get_account(root, slug)
            if acct and acct.get("name"):
                account_override = str(acct["name"])

        profile_lock = None
        if not demo:
            try:
                profile_lock = lock_mod.acquire_profile_lock(workspace)
            except lock_mod.ProfileLockError as e:
                env.print_error(str(e))
                return 1
        try:
            rc = analyze_cmd.run(
                workspace=workspace,
                demo=demo,
                build_only=do_build_only,
                account_name_override=account_override,
                data_only=data_only,
            )
        finally:
            if profile_lock is not None:
                profile_lock.release()

        if rc == 0 and slug:
            if not demo:
                accounts_store.touch(root, slug, "last_fetch_at")
                ok_fetch = accounts_store.touch_pipeline(root, slug, "fetch", ok=True)
                if not ok_fetch:
                    env.print_warn("pipeline.json fetch 游标写入失败（不影响本次分析）")
            accounts_store.touch(root, slug, "last_analyze_at")
            report_path = str(workspace / "output" / "report.json")
            ok_an = accounts_store.touch_pipeline(
                root, slug, "analyze", ok=True, report=report_path
            )
            if not ok_an:
                env.print_warn("pipeline.json analyze 游标写入失败（不影响本次分析）")
        return rc

    print("未知命令")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
