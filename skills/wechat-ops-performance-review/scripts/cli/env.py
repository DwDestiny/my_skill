#!/usr/bin/env python3
"""环境与配置工具：SKILL_DIR 自定位、workspace 解析、config 读写、依赖探测、友好打印。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# cli/ 在 scripts/ 下，scripts 在 skill 根下
SKILL_DIR = Path(__file__).resolve().parents[2]

DEFAULT_WORKSPACE = Path.home() / ".wxops"


def get_skill_dir() -> Path:
    return SKILL_DIR


def get_default_workspace() -> Path:
    return DEFAULT_WORKSPACE


def resolve_workspace(override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_WORKSPACE.resolve()


def get_config_path(workspace: Path) -> Path:
    return workspace / "config.json"


def load_config(workspace: Path) -> dict[str, Any]:
    cfg_path = get_config_path(workspace)
    if cfg_path.exists():
        try:
            import json

            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_config(workspace: Path, config: dict[str, Any]) -> None:
    cfg_path = get_config_path(workspace)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    import json

    cfg_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_workspace_dirs(workspace: Path) -> None:
    (workspace / "reports" / "wechat").mkdir(parents=True, exist_ok=True)
    (workspace / "data" / "social_ops" / "indexes").mkdir(parents=True, exist_ok=True)
    (workspace / "output").mkdir(parents=True, exist_ok=True)
    (workspace / "browser-profile").mkdir(parents=True, exist_ok=True)


def get_browser_profile_dir(workspace: Path) -> Path:
    return workspace / "browser-profile"


def get_fixtures_dir() -> Path:
    return SKILL_DIR / "fixtures"


def get_skill_dashboard_dir() -> Path:
    """只读 dashboard 模板（位于 skill 目录，不可写）。"""
    return SKILL_DIR / "dashboard"


def get_workspace_dashboard_dir(workspace: Path) -> Path:
    """工作区内的 dashboard 运行态副本（可写：node_modules / dist / 注入数据）。"""
    return workspace / "dashboard"


def get_workspace_output_dir(workspace: Path) -> Path:
    return workspace / "output"


# 依赖探测（不强制崩溃，只返回状态）

def check_python_version() -> tuple[bool, str]:
    """检查 Python ≥ 3.10（脚本使用 X | Y 联合类型和 zoneinfo）。"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro}（需 ≥ 3.10）"


def check_playwright_available() -> tuple[bool, str]:
    """尝试 import playwright（懒探测）。"""
    try:
        import playwright  # type: ignore  # noqa: F401

        return True, "playwright 已安装"
    except ImportError:
        return False, "playwright 未安装"


def check_node_available() -> tuple[bool, str]:
    node = shutil.which("node")
    if node:
        try:
            out = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=5)
            ver = out.stdout.strip() or out.stderr.strip()
            return True, f"node {ver}"
        except Exception:
            return True, "node 可用"
    return False, "node 未找到"


def check_pnpm_available() -> tuple[bool, str]:
    pnpm = shutil.which("pnpm")
    if pnpm:
        try:
            out = subprocess.run([pnpm, "--version"], capture_output=True, text=True, timeout=5)
            ver = out.stdout.strip()
            return True, f"pnpm {ver}"
        except Exception:
            return True, "pnpm 可用"
    return False, "pnpm 未找到"


def run_command_stream(cmd: list[str], desc: str) -> tuple[int, str]:
    """实时透传子进程 stdout/stderr，返回 (returncode, last_output)。"""
    print(f"→ 正在执行: {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        output_lines: list[str] = []
        if proc.stdout:
            for line in proc.stdout:
                print(line, end="")
                output_lines.append(line)
        proc.wait()
        return proc.returncode, "".join(output_lines[-20:])
    except Exception as e:
        print(f"命令执行异常: {e}")
        return 1, str(e)


# 友好中文打印

def print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def print_step(step: str, detail: str = "") -> None:
    if detail:
        print(f"• {step}")
        print(f"  {detail}")
    else:
        print(f"• {step}")


def print_success(msg: str) -> None:
    print(f"✓ {msg}")


def print_warn(msg: str) -> None:
    print(f"⚠ {msg}")


def print_error(msg: str) -> None:
    print(f"✗ {msg}")


def print_info(msg: str) -> None:
    print(f"  {msg}")


def print_guide_next(cmd: str) -> None:
    print(f"\n下一步：{cmd}\n")
