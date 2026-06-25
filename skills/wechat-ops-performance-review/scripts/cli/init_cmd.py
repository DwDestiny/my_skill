#!/usr/bin/env python3
"""wxops init：环境自检 + 依赖自动装 + workspace 初始化 + 配置写入。"""

from __future__ import annotations

import sys
from pathlib import Path

from . import env


def run(workspace: Path, account_name_override: str | None = None) -> int:
    print_header = env.print_header
    print_step = env.print_step
    print_success = env.print_success
    print_warn = env.print_warn
    print_error = env.print_error
    print_info = env.print_info
    print_guide_next = env.print_guide_next

    print_header("公众号运营分析环境自检 (wxops init)")

    # 1. Python 版本
    ok_py, py_info = env.check_python_version()
    if not ok_py:
        print_error(f"Python 版本不足: {py_info}")
        print_info("请升级到 Python 3.10+ 后再试（推荐使用 pyenv 或系统包管理器）。")
        print_info("macOS 示例: brew install python@3.11 && python3.11 -m pip install --upgrade pip")
        return 1
    print_success(f"Python 版本: {py_info}")

    # 2. playwright 检查 + 自动安装
    has_pw, pw_info = env.check_playwright_available()
    if not has_pw:
        print_warn("playwright 未安装。")
        print_info("将安装 playwright 及 Chromium 浏览器（约 150MB+），用于登录你的公众号后台读取数据。")
        # 自动安装
        code1, _ = env.run_command_stream(
            [sys.executable, "-m", "pip", "install", "playwright"],
            "安装 playwright",
        )
        if code1 != 0:
            print_error("pip install playwright 失败。")
            print_info("请手动执行: python3 -m pip install playwright")
            print_info("然后: python3 -m playwright install chromium")
            return 1
        code2, _ = env.run_command_stream(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            "安装 Chromium 浏览器",
        )
        if code2 != 0:
            print_error("playwright install chromium 失败。")
            print_info("请手动执行: python3 -m playwright install chromium")
            return 1
        print_success("playwright + Chromium 安装完成")
    else:
        print_success(f"playwright: {pw_info}")

    # 3. node / pnpm（仅提示，不强装）
    has_node, node_info = env.check_node_available()
    if has_node:
        print_success(f"node: {node_info}")
    else:
        print_warn(f"node: {node_info}")
        print_info("Dashboard 需要 Node.js。安装后请运行: npm i -g pnpm")

    has_pnpm, pnpm_info = env.check_pnpm_available()
    if has_pnpm:
        print_success(f"pnpm: {pnpm_info}")
    else:
        print_warn(f"pnpm: {pnpm_info}")
        print_info("推荐全局安装 pnpm: npm i -g pnpm （或 corepack enable && corepack prepare pnpm@latest --activate）")

    # 4. 创建目录 + config
    env.ensure_workspace_dirs(workspace)

    # 确定 account_name
    account_name = account_name_override
    if not account_name:
        try:
            account_name = input("请输入你的公众号名称（例如：麦总玩 AI）：").strip()
        except (EOFError, KeyboardInterrupt):
            print_error("未输入公众号名称，初始化中止。")
            return 1
    if not account_name:
        account_name = "我的公众号"

    # 写 config.json（created_at 用 datetime.now().isoformat()）
    from datetime import datetime

    config = {
        "account_name": account_name,
        "workspace": str(workspace),
        "created_at": datetime.now().isoformat(),
    }
    env.save_config(workspace, config)

    print_success(f"工作区已就绪: {workspace}")
    print_info(f"  - 登录态目录: {workspace / 'browser-profile'}")
    print_info(f"  - 抓取数据:   {workspace / 'reports' / 'wechat'}")
    print_info(f"  - 分析产物:   {workspace / 'output'}")
    print_success(f"公众号名称已保存: {account_name}")

    # 5. 结尾引导
    print_success("环境就绪 ✓")
    print_guide_next("wxops login   （扫码登录公众号后台，保存登录态）")

    return 0
