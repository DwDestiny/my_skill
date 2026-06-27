#!/usr/bin/env python3
"""wxops analyze：抓取（或 demo）→ build 报告 → dashboard 预览/构建。

运行契约（issue #16）：skill 目录只读模板，全部运行态产物落工作区
（默认 ~/.wxops）。dashboard 被复制到 <workspace>/dashboard 后再注入数据、
跑 pnpm，dist 落 <workspace>/dashboard/dist。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from . import env

# 复制 skill dashboard 模板到工作区时忽略的运行态/构建产物
_DASHBOARD_IGNORE = shutil.ignore_patterns(
    "node_modules",
    "dist",
    "*.tsbuildinfo",
    "qa-screenshots",
    ".vite",
)

# 复制 fixtures 原始输入到工作区时忽略的产物子目录（fixtures/output 是产物，不是输入）
_FIXTURES_IGNORE = shutil.ignore_patterns("output")


def _ensure_in_path(skill_dir: Path) -> None:
    s = str(skill_dir)
    if s not in sys.path:
        sys.path.insert(0, s)


def _sync_dashboard_to_workspace(workspace: Path) -> Path:
    """把 skill 只读 dashboard 模板同步到 <workspace>/dashboard（可写副本）。

    忽略 node_modules / dist / *.tsbuildinfo / qa-screenshots，只同步源码
    （src/、public/、index.html、package.json、pnpm-lock.yaml、vite.config.ts、
    tsconfig*.json 等）。返回工作区 dashboard 目录。
    """
    src = env.get_skill_dashboard_dir()
    dst = env.get_workspace_dashboard_dir(workspace)
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=_DASHBOARD_IGNORE)
    return dst


def _inject_report_data(workspace: Path, dashboard_dir: Path) -> bool:
    """把 builder 产出的 <workspace>/output/report.json 注入 dashboard 副本。

    App.tsx 用编译期静态 import "./data/report.json"，故数据必须落到
    <workspace>/dashboard/src/data/report.json。
    """
    out_report = env.get_workspace_output_dir(workspace) / "report.json"
    if not out_report.exists():
        return False
    target = dashboard_dir / "src" / "data" / "report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out_report, target)
    return True


def _seed_demo_workspace(workspace: Path) -> None:
    """把 skill fixtures 里的原始输入数据 copy 到工作区（排除 fixtures/output 产物）。

    fixtures = 只读输入，产物落工作区。复制 raw/、reports/、data/、content/ 等
    输入目录，builder 即可从工作区正常读到 raw 数据并把产物写回工作区。
    """
    src = env.get_fixtures_dir()
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, workspace, dirs_exist_ok=True, ignore=_FIXTURES_IGNORE)


def _run_build(workspace: Path, account_name: str) -> int:
    """调用 build_wechat_ops_report.py（子进程）。产物落工作区，skill 只读。"""
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
                env.print_success(f"Dashboard 构建完成 → {dashboard_dir / 'dist'}")
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


def _build_dashboard(workspace: Path, build_only: bool) -> None:
    """同步 dashboard 副本 → 注入数据 → install → build/dev。全部在工作区内进行。"""
    dashboard_dir = _sync_dashboard_to_workspace(workspace)
    if not _inject_report_data(workspace, dashboard_dir):
        env.print_warn(
            f"未找到 {env.get_workspace_output_dir(workspace) / 'report.json'}，看板将使用上次注入的数据"
        )
    if not _ensure_dashboard_deps(dashboard_dir):
        env.print_warn(
            f"dashboard 依赖安装可能未完成，请手动 cd {dashboard_dir} && pnpm install"
        )
    _start_dashboard(dashboard_dir, build_only)


def run(
    workspace: Path,
    demo: bool = False,
    build_only: bool = False,
    account_name_override: str | None = None,
    data_only: bool = False,
) -> int:
    print_header = env.print_header
    print_step = env.print_step
    print_success = env.print_success
    print_warn = env.print_warn
    print_error = env.print_error
    print_info = env.print_info

    print_header("分析并生成叙事看板 (wxops analyze)")

    skill_dir = env.get_skill_dir()
    _ensure_in_path(skill_dir)

    if demo:
        print_step("DEMO 模式", "跳过抓取，把 fixtures 原始输入复制到工作区后正常构建")
        account_name = "样例运营号"
        print_info(f"工作区: {workspace}")
        print_info(f"公众号: {account_name}")
        # fixtures = 只读输入；产物落工作区
        _seed_demo_workspace(workspace)

        rc = _run_build(workspace, account_name)
        if rc != 0:
            print_error("build 失败")
            return rc
        print_success(f"报告构建完成（demo 数据）→ {workspace / 'output' / 'report.json'}")

        if data_only:
            print_success("已跳过 dashboard 构建（--data-only）。")
            return 0
        _build_dashboard(workspace, build_only)
        return 0

    # === 正常模式：需要 playwright + 已登录态 ===
    print_step("正常模式", "将使用持久化浏览器上下文复用登录态抓取最新数据")

    config = env.load_config(workspace)
    account_name = account_name_override or config.get("account_name") or "我的公众号"
    profile_dir = env.get_browser_profile_dir(workspace)

    # 懒导入 orchestrator（此时才 import，会带入 playwright）
    try:
        from scripts.fetch.orchestrator import run as fetch_run  # type: ignore
    except ImportError as e:
        print_error(f"无法导入抓取模块: {e}")
        print_info("请确认已运行 wxops init 安装 playwright，或手动 python3 -m pip install playwright")
        return 1

    print_step("多接口抓取（文章列表 + 账号 + 粉丝画像 + 内容趋势）", f"profile={profile_dir}")
    result = fetch_run(workspace, profile_dir, headless=True)
    if result.get("status") != "ok":
        err = result.get("error", "抓取失败")
        hint = result.get("hint", "")
        print_error(str(err))
        if hint:
            print_info(str(hint))
        return 1
    print_success(f"抓取完成: publish={result.get('publish_export')}, raw={result.get('raw_dir')}")

    # 构建
    rc = _run_build(workspace, account_name)
    if rc != 0:
        print_error("报告构建失败")
        return rc
    print_success(f"报告构建完成 → {workspace / 'output' / 'report.json'}")

    if data_only:
        print_success("已跳过 dashboard 构建（--data-only）。")
        print_info(f"报告与看板数据已写入 {workspace / 'output' / 'report.json'}（skill 目录只读）")
        return 0

    # dashboard（工作区副本）
    _build_dashboard(workspace, build_only)

    # 额外提示
    print_success("分析流程结束。")
    print_info(f"报告与看板数据已写入 {workspace / 'output' / 'report.json'}（skill 目录只读）")
    print_info(f"看板运行态副本：{env.get_workspace_dashboard_dir(workspace)}")
    return 0
