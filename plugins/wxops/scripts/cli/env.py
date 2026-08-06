#!/usr/bin/env python3
# GEB-L3
# Input: WXOPS_HOME/workspace 覆盖路径；workspace/config.json；PATH 上的 node/pnpm/playwright
# Output: 路径解析、config 读写、目录创建、运行清单唯一命名、依赖探测 (ok,msg)、print_* 中文终端样式
# Pos: plugins/wxops/scripts/cli/env.py
"""环境与配置工具：SKILL_DIR 自定位、workspace 解析、config 读写、依赖探测、友好打印。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# cli/ 在 scripts/ 下，scripts 在 skill 根下
SKILL_DIR = Path(__file__).resolve().parents[2]

# 保留模块级名字以兼容残留引用；运行时路径请走 get_wxops_root()
DEFAULT_WORKSPACE = Path.home() / ".wxops"


def get_skill_dir() -> Path:
    return SKILL_DIR


def get_wxops_root() -> Path:
    """wxops 数据根。环境变量 WXOPS_HOME 优先，默认 ~/.wxops。"""
    raw = os.environ.get("WXOPS_HOME")
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / ".wxops").resolve()


def get_default_workspace() -> Path:
    return get_wxops_root()


def resolve_workspace(override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return get_wxops_root()


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


def ensure_account_dirs(workspace: Path) -> None:
    """账号办公室完整目录树：旧四目录 + credentials(0700) + 内容工位目录。"""
    ensure_workspace_dirs(workspace)
    cred = workspace / "credentials"
    cred.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(cred, 0o700)
    except OSError:
        pass
    for name in ("topics", "drafts", "images", "published", "raw"):
        (workspace / name).mkdir(parents=True, exist_ok=True)


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


def new_run_manifest_path(root: Path, prefix: str) -> Path:
    """runs/<prefix>-<毫秒时间戳>.json，撞名让路，绝不覆盖已有凭证。

    运行清单是审计凭证：用户被告知「源文件原位保留，确认无误后可自行归档」，
    归档前核对的就是它。秒级时间戳在同秒二次运行时会撞名并被静默覆盖（#72），
    故精度提到毫秒，并在极端情况（时钟回拨、同毫秒并发）追加 -2 / -3 序号让路。

    让路检查是尽力而为的单进程保证，不做跨进程锁——wxops 是单机 CLI，
    为跨进程竞态加锁的复杂度换不来实际安全收益。

    目录不存在时一并创建。
    """
    runs_dir = root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f")[:-3]
    candidate = runs_dir / f"{prefix}-{stamp}.json"
    if not candidate.exists():
        return candidate
    for n in range(2, 1001):
        candidate = runs_dir / f"{prefix}-{stamp}-{n}.json"
        if not candidate.exists():
            return candidate
    raise RuntimeError(
        f"无法为运行清单分配唯一路径：{runs_dir / f'{prefix}-{stamp}'}-*.json "
        f"（序号已用尽至 1000）"
    )


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
