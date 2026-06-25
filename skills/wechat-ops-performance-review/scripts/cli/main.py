#!/usr/bin/env python3
"""wxops 可执行入口主分发：init / login / analyze 子命令。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import analyze_cmd
from . import env
from . import init_cmd
from . import login_cmd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wxops",
        description="公众号运营分析向导式 CLI：三步上手（环境自检 → 登录 → 分析看板）。",
    )

    # 顶层也声明（帮助可见），并用 parent 确保子命令后带 flag 也生效
    parser.add_argument(
        "--workspace",
        default=None,
        help="工作区目录（默认 ~/.wxops，存放登录态、抓取数据、输出）。",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--workspace",
        default=None,
        help="工作区目录（默认 ~/.wxops，存放登录态、抓取数据、输出）。",
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
    p_analyze.add_argument("--account-name", default=None, help="覆盖配置中的公众号名称")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    workspace = env.resolve_workspace(args.workspace)
    env.ensure_workspace_dirs(workspace)

    if args.command == "init":
        return init_cmd.run(workspace=workspace, account_name_override=getattr(args, "account_name", None))

    if args.command == "login":
        headless = getattr(args, "headless", False)
        return login_cmd.run(workspace=workspace, headless=headless)

    if args.command == "analyze":
        demo = getattr(args, "demo", False)
        do_build_only = getattr(args, "build", False)
        account_override = getattr(args, "account_name", None)
        return analyze_cmd.run(
            workspace=workspace,
            demo=demo,
            build_only=do_build_only,
            account_name_override=account_override,
        )

    print("未知命令")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
