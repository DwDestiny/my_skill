#!/usr/bin/env python3
"""wxops analyze：抓取（或 demo）→ build 报告 → dashboard 预览/构建。"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from . import env


def _ensure_in_path(skill_dir: Path) -> None:
    s = str(skill_dir)
    if s not in sys.path:
        sys.path.insert(0, s)


def _run_build(workspace: Path, account_name: str) -> int:
    """调用 build_wechat_ops_report.py（子进程）。"""
    cmd = [
        sys.executable,
        str(env.get_skill_dir() / "scripts" / "build_wechat_ops_report.py"),
        "--workspace",
        str(workspace),
        "--account-name",
        account_name,
    ]
    print(f"→ 正在构建报告: {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=False)
    return proc.returncode


def _ensure_dashboard_deps(dashboard_dir: Path) -> bool:
    node_modules = dashboard_dir / "node_modules"
    if node_modules.exists():
        return True
    print("→ dashboard/node_modules 不存在，正在执行 pnpm install ...")
    try:
        proc = subprocess.run(
            ["pnpm", "install"],
            cwd=str(dashboard_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(proc.stdout or "")
        return proc.returncode == 0
    except Exception as e:
        print(f"pnpm install 失败: {e}")
        return False


def _start_dashboard(dashboard_dir: Path, build_only: bool) -> None:
    if build_only:
        print("→ 执行 pnpm build ...")
        try:
            proc = subprocess.run(
                ["pnpm", "build"],
                cwd=str(dashboard_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            print(proc.stdout or "")
            if proc.returncode == 0:
                env.print_success("Dashboard 构建完成 → dashboard/dist/")
            else:
                env.print_error("pnpm build 失败")
        except Exception as e:
            env.print_error(f"构建失败: {e}")
        return

    # dev 模式
    print("→ 正在启动本地预览服务器 (pnpm dev) ...")
    print("  看板地址通常为: http://127.0.0.1:5173")
    env.print_info("（Vite 默认端口，首次可能稍慢）")

    # 尝试自动打开浏览器（macOS）
    url = "http://127.0.0.1:5173"
    try:
        subprocess.Popen(["open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        env.print_success(f"已尝试自动打开浏览器: {url}")
    except Exception:
        env.print_info(f"请手动打开: {url}")

    try:
        # 前台启动，让用户看到日志；Ctrl-C 退出
        proc = subprocess.Popen(
            ["pnpm", "dev"],
            cwd=str(dashboard_dir),
        )
        proc.wait()
    except KeyboardInterrupt:
        print("\n已收到中断，停止 dev 服务器。")
    except Exception as e:
        env.print_error(f"启动 dev 失败: {e}")


def run(
    workspace: Path,
    demo: bool = False,
    build_only: bool = False,
    account_name_override: str | None = None,
) -> int:
    print_header = env.print_header
    print_step = env.print_step
    print_success = env.print_success
    print_warn = env.print_warn
    print_error = env.print_error
    print_info = env.print_info
    print_guide_next = env.print_guide_next

    print_header("分析并生成叙事看板 (wxops analyze)")

    skill_dir = env.get_skill_dir()
    _ensure_in_path(skill_dir)
    dashboard_dir = skill_dir / "dashboard"

    if demo:
        print_step("DEMO 模式", "跳过抓取，使用 fixtures 演示数据")
        ws_for_build = env.get_fixtures_dir()
        account_name = "样例运营号"
        print_info(f"数据源: {ws_for_build}")
        print_info(f"公众号: {account_name}")

        # 直接 build（不触发 playwright）
        rc = _run_build(ws_for_build, account_name)
        if rc != 0:
            print_error("build 失败")
            return rc
        print_success("报告构建完成（使用 fixtures）")

        # dashboard 部分
        if not _ensure_dashboard_deps(dashboard_dir):
            print_warn("dashboard 依赖安装可能未完成，请手动 cd dashboard && pnpm install")
        _start_dashboard(dashboard_dir, build_only)
        return 0

    # === 正常模式：需要 playwright + 已登录态 ===
    print_step("正常模式", "将使用持久化浏览器上下文复用登录态抓取最新数据")

    # 懒导入 export（此时才 import，会带入 playwright）
    try:
        from scripts.export_wechat_publish_records import export_via_persistent  # type: ignore
    except ImportError as e:
        print_error(f"无法导入抓取模块: {e}")
        print_info("请确认已运行 wxops init 安装 playwright，或手动 python3 -m pip install playwright")
        return 1

    config = env.load_config(workspace)
    account_name = account_name_override or config.get("account_name") or "我的公众号"
    profile_dir = env.get_browser_profile_dir(workspace)

    print_step("复用登录态抓取 publish records", f"profile={profile_dir}")
    try:
        out_path = export_via_persistent(workspace, profile_dir, headless=True)
        print_success(f"抓取完成: {out_path}")
    except Exception as exc:
        msg = str(exc)
        if "login_required" in msg or "token_or_cookie_invalid" in msg:
            print_error("登录态无效或已过期。")
            print_info("请运行: wxops login  重新扫码登录")
            print_warn("不会使用旧数据继续分析。")
            return 1
        print_error(f"抓取失败: {msg}")
        return 1

    # 构建
    rc = _run_build(workspace, account_name)
    if rc != 0:
        print_error("报告构建失败")
        return rc
    print_success("报告构建完成")

    # dashboard
    if not _ensure_dashboard_deps(dashboard_dir):
        print_warn("dashboard 依赖安装可能未完成，请手动 cd dashboard && pnpm install")
    _start_dashboard(dashboard_dir, build_only)

    # 额外提示
    print_success("分析流程结束。")
    print_info("报告与看板数据已写入 dashboard/src/data/report.json")
    print_info(f"也可查看 workspace/output/ 下的 JSON/MD：{workspace / 'output'}")

    return 0
