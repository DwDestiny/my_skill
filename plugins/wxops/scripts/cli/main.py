#!/usr/bin/env python3
# GEB-L3
# Input: sys.argv → argparse（init/login/analyze/accounts/migrate/desk/kit/publish/review 及 --workspace/--account/--all 等）
# Output: 分发子命令 + 账号/workspace 解析 + login/analyze 持锁与 registry 游标更新；本身不做抓取/分析业务；exit 码透传
# Pos: plugins/wxops/scripts/cli/main.py
"""wxops 可执行入口主分发：init / login / analyze / accounts / migrate / desk / kit / publish / review。"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable

from . import accounts_cmd
from . import accounts_store
from . import analyze_cmd
from . import batch_cmd
from . import desk_cmd
from . import env
from . import health
from . import init_cmd
from . import kit_cmd
from . import lock as lock_mod
from . import login_cmd
from . import migrate_cmd
from . import publish_cmd
from . import review_cmd


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
    p_login.add_argument(
        "--all",
        action="store_true",
        help="批量补登录：先体检后逐号扫码",
    )

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
    p_analyze.add_argument(
        "--all",
        action="store_true",
        help="全部在册账号批量拉数出报告（顺序 + 间隔 + 失败隔离）",
    )

    # accounts（leaf 也挂 common，以便 `accounts list --workspace X` 可用）
    p_accounts = subparsers.add_parser(
        "accounts",
        parents=[common],
        help="多账号管理：add / list / use / remove / check",
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

    p_check = acc_sub.add_parser("check", parents=[common], help="登录态体检")
    p_check.add_argument("slug", nargs="?", default=None, help="可选：只体检指定账号")

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

    # kit（写作三件套门禁；复用 common 的 --account，另加 --topic）
    p_kit = subparsers.add_parser(
        "kit",
        parents=[common],
        help="写作三件套门禁：人设 + 结构契约（+ 选题卡/证据包）",
    )
    p_kit.add_argument(
        "--topic",
        default=None,
        help="选题 slug；给出则做开工体检（四项），否则仅账号级体检（两项）",
    )

    # publish（发布主链；草稿箱止步）
    p_publish = subparsers.add_parser(
        "publish",
        parents=[common],
        help="发布主链：渲染公众号 HTML → 上传素材 → 建草稿（草稿箱止步）",
    )
    p_publish.add_argument("--topic", required=True, help="选题 slug")
    p_publish.add_argument(
        "--go",
        action="store_true",
        help="执行真实建草稿（默认 dry-run 预演）",
    )
    p_publish.add_argument(
        "--title",
        default=None,
        help="标题；默认取 draft.md 首个一级标题",
    )
    p_publish.add_argument(
        "--author",
        default=None,
        help="作者；默认取账号 name",
    )
    p_publish.add_argument(
        "--digest",
        default=None,
        help="摘要；留空则微信自动摘取",
    )
    p_publish.add_argument(
        "--source-url",
        default=None,
        help="原文链接",
    )

    # review（复盘：对照选题卡预期出结论）
    p_review = subparsers.add_parser(
        "review",
        parents=[common],
        help="复盘：对照选题卡预期出结论（先跑 analyze 更新数据）",
    )
    p_review.add_argument("--topic", required=True, help="选题 slug")

    return parser


def _root_from_args(args: argparse.Namespace) -> Path:
    """accounts / migrate / desk / kit 用：--workspace 优先，否则 WXOPS_HOME。"""
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


def _login_all(
    root: Path,
    *,
    checker: Callable[[Path], dict[str, Any]] | None = None,
    sleeper: Callable[[float], None] | None = None,
    login_runner: Callable[[Path], int] | None = None,
) -> int:
    """login --all：先体检，掉线号逐个扫码补登录。"""
    check_fn = checker or health.check_login
    sleep_fn = sleeper or time.sleep
    do_login = login_runner or (
        lambda ws: login_cmd.run(workspace=ws, headless=False)
    )

    accounts = [
        a
        for a in accounts_store.list_accounts(root)
        if a.get("status") == "active"
    ]
    accounts.sort(key=lambda a: str(a.get("slug", "")))
    if not accounts:
        env.print_warn("还没有任何账号。")
        env.print_guide_next('wxops accounts add <slug> --name "<显示名>"')
        return 1

    offline: list[dict[str, Any]] = []
    for i, acct in enumerate(accounts):
        slug = str(acct.get("slug") or "")
        workspace = accounts_store.get_account_dir(root, slug)
        alive = False
        try:
            result = check_fn(workspace)
            alive = bool(result.get("alive"))
            accounts_store.set_login_health(root, slug, alive)
        except lock_mod.ProfileLockError as e:
            env.print_error(str(e))
            alive = False
            # 撞锁记为掉线待处理
            offline.append(acct)
            if i < len(accounts) - 1:
                sleep_fn(random.uniform(1, 3))
            continue

        if not alive:
            offline.append(acct)
        if i < len(accounts) - 1:
            sleep_fn(random.uniform(1, 3))

    n = len(accounts)
    if not offline:
        env.print_success(f"全部 {n} 个账号在线，无需补登录")
        return 0

    ok_count = 0
    still_offline: list[str] = []
    try:
        for acct in offline:
            slug = str(acct.get("slug") or "")
            name = str(acct.get("name") or slug)
            workspace = accounts_store.get_account_dir(root, slug)
            env.print_header(f"即将登录账号：{name}（{slug}）")
            env.print_step("请核对账号", "扫码前确认目标公众号无误，避免扫错号")
            try:
                profile_lock = lock_mod.acquire_profile_lock(workspace)
            except lock_mod.ProfileLockError as e:
                env.print_error(str(e))
                still_offline.append(slug)
                continue
            with profile_lock:
                rc = do_login(workspace)
            if rc == 0:
                accounts_store.touch(root, slug, "last_login_at")
                ok = accounts_store.touch_pipeline(root, slug, "login", ok=True)
                if not ok:
                    env.print_warn("pipeline.json 写入失败（不影响本次登录）")
                accounts_store.set_login_health(root, slug, True)
                ok_count += 1
            else:
                still_offline.append(slug)
    except KeyboardInterrupt:
        env.print_warn("用户中断批量补登录（已完成的保留）")
        return 1

    print()
    print(f"{ok_count} 补登录成功 · {len(still_offline)} 仍掉线")
    if still_offline:
        for s in still_offline:
            env.print_info(f"仍掉线：wxops login --account {s}")
        return 1
    return 0


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
        if sub == "check":
            return accounts_cmd.cmd_check(root, getattr(args, "slug", None))
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

    if args.command == "kit":
        root = _root_from_args(args)
        return kit_cmd.run(
            root,
            account=getattr(args, "account", None),
            topic=getattr(args, "topic", None),
        )

    if args.command == "publish":
        return publish_cmd.run_publish(args)

    if args.command == "review":
        return review_cmd.run_review(args)

    # analyze --all / login --all：必须在 resolve_context 之前（互斥返回 2）
    if args.command == "analyze" and getattr(args, "all", False):
        if (
            getattr(args, "account", None)
            or getattr(args, "workspace", None)
            or getattr(args, "demo", False)
            or getattr(args, "build", False)
        ):
            env.print_error(
                "--all 与 --account / --workspace / --demo / --build 互斥；"
                "批量模式只产数据，看板请对单号跑 analyze --account <slug> --build。"
            )
            return 2
        return batch_cmd.run_all(env.get_wxops_root())

    if args.command == "login" and getattr(args, "all", False):
        if getattr(args, "account", None) or getattr(args, "workspace", None):
            env.print_error(
                "--all 与 --account / --workspace 互斥，请只给 --all。"
            )
            return 2
        return _login_all(env.get_wxops_root())

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
            accounts_store.set_login_health(root, slug, True)
        return rc

    if args.command == "analyze":
        demo = getattr(args, "demo", False)
        do_build_only = getattr(args, "build", False)
        data_only = getattr(args, "data_only", False)
        account_override = getattr(args, "account_name", None)
        # niche：account 模式读 account.json；--workspace 旧模式与 --demo 固定 ai-tools
        niche = "ai-tools"
        # 非 demo 且用户未显式给 --account-name 时，用 account.json 的显示名
        if slug and not demo:
            acct = accounts_store.get_account(root, slug)
            if not account_override and acct and acct.get("name"):
                account_override = str(acct["name"])
            if acct and acct.get("niche"):
                niche = str(acct["niche"])

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
                niche=niche,
                root=root,
                slug=slug,
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
