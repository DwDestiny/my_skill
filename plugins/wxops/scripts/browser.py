#!/usr/bin/env python3
# GEB-L3
# Input: sync_playwright 实例 + profile_dir（读 Last Version）+ 可选 headless/kwargs；扫描 ~/Library/Caches/ms-playwright/chromium-*
# Output: 持久化 BrowserContext；版本不匹配时抛 BrowserVersionMismatch（macOS arm64 严格）
# Pos: plugins/wxops/scripts/browser.py
"""浏览器持久化上下文统一启动入口：按 profile Last Version 自适应选择 Chromium 二进制。

背景（issue #82）：Chromium profile schema 只增不减。低版本二进制读高版本写过的
Local State / Preferences 会 CHECK() 断言失败 → 进程 SIGTRAP，Python 侧无异常。

版本发现途径（实地探查 ~/Library/Caches/ms-playwright/chromium-1234/，2026-08）：
- DEPENDENCIES_VALIDATED / INSTALLATION_COMPLETE 为空标记文件，无版本号
- chrome-mac-arm64/ABOUT 仅为版权说明，无版本号
- 可靠无子进程途径：chrome-mac-arm64/Google Chrome for Testing.app/Contents/Info.plist
  的 CFBundleShortVersionString（如 151.0.7922.34），与 chrome --version 一致
- 仅当目录内无可靠 Info.plist 时，才允许缓存化调用 executable --version
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# 模块级缓存：executable 路径 → 版本串（避免重复起 --version 子进程）
_VERSION_SUBPROCESS_CACHE: dict[str, str | None] = {}

# macOS arm64 下 Playwright 官方 chromium 包布局
_MAC_ARM64_REL_EXECUTABLE = Path(
    "chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
)
_MAC_ARM64_REL_INFO_PLIST = Path(
    "chrome-mac-arm64/Google Chrome for Testing.app/Contents/Info.plist"
)

_VERSION_RE = re.compile(r"(\d+\.\d+\.\d+\.\d+)")


class BrowserVersionMismatch(RuntimeError):
    """profile Last Version 与本机 ms-playwright 已装 Chromium 无法匹配。"""


def _default_ms_playwright_root() -> Path:
    return Path.home() / "Library" / "Caches" / "ms-playwright"


def is_macos_arm64() -> bool:
    """当前进程是否跑在 macOS arm64（本模块严格匹配仅覆盖此平台）。"""
    return sys.platform == "darwin" and platform.machine() == "arm64"


def read_profile_last_version(profile_dir: Path | str) -> str | None:
    """读 profile 的 Last Version 纯文本；不存在或空 → None（全新 profile）。"""
    path = Path(profile_dir) / "Last Version"
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return text or None


def _version_key(version: str) -> tuple[int, ...] | None:
    """将版本串解析为数值元组供分段比较；解析失败返回 None（该候选跳过，不崩）。

    例：'151.0.7922.34' → (151, 0, 7922, 34)
    必须用数值比较，不能用字符串（否则 '151.0.10000.1' < '151.0.7922.34' 会误判）。
    """
    parts = version.strip().split(".")
    if not parts:
        return None
    try:
        key = tuple(int(p) for p in parts)
    except ValueError:
        return None
    return key if key else None


def _parse_version_major(version: str) -> str | None:
    """取 major 段；非法格式返回 None。"""
    key = _version_key(version)
    if key is None:
        return None
    return str(key[0])


def _read_version_from_info_plist(plist_path: Path) -> str | None:
    """从 app bundle Info.plist 读 CFBundleShortVersionString（不起子进程）。"""
    if not plist_path.is_file():
        return None
    try:
        import plistlib

        with plist_path.open("rb") as fh:
            data = plistlib.load(fh)
    except Exception:
        return None
    raw = data.get("CFBundleShortVersionString")
    if not raw:
        return None
    text = str(raw).strip()
    return text or None


def _version_via_subprocess(executable: Path) -> str | None:
    """兜底：跑 executable --version，结果缓存到模块级 dict。"""
    key = str(executable)
    if key in _VERSION_SUBPROCESS_CACHE:
        return _VERSION_SUBPROCESS_CACHE[key]

    version: str | None = None
    try:
        proc = subprocess.run(
            [key, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        blob = (proc.stdout or "") + "\n" + (proc.stderr or "")
        m = _VERSION_RE.search(blob)
        if m:
            version = m.group(1)
    except Exception:
        version = None

    _VERSION_SUBPROCESS_CACHE[key] = version
    return version


def read_chromium_dir_version(chromium_dir: Path) -> str | None:
    """读单个 chromium-* 安装目录的浏览器版本。

    优先 Info.plist（无子进程）；无可靠版本文件时才走缓存化 --version。
    """
    chromium_dir = Path(chromium_dir)
    plist = chromium_dir / _MAC_ARM64_REL_INFO_PLIST
    ver = _read_version_from_info_plist(plist)
    if ver:
        return ver

    exe = chromium_dir / _MAC_ARM64_REL_EXECUTABLE
    if exe.is_file() and os.access(exe, os.X_OK):
        return _version_via_subprocess(exe)
    return None


def executable_path_in_chromium_dir(chromium_dir: Path) -> Path | None:
    """返回 macOS arm64 标准布局下的可执行文件路径；不存在则 None。"""
    exe = Path(chromium_dir) / _MAC_ARM64_REL_EXECUTABLE
    if exe.is_file():
        return exe
    return None


def scan_local_chromiums(
    ms_playwright_root: Path | str | None = None,
) -> list[tuple[str, Path]]:
    """扫描 ms-playwright 下 chromium-*，返回 [(version, executable_path), ...]。

    只收录能解析出版本且存在可执行文件的安装；顺序不保证。
    """
    root = Path(ms_playwright_root) if ms_playwright_root else _default_ms_playwright_root()
    if not root.is_dir():
        return []

    found: list[tuple[str, Path]] = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name)
    except OSError:
        return []

    for entry in entries:
        if not entry.is_dir():
            continue
        if not entry.name.startswith("chromium-"):
            continue
        # 跳过 headless_shell 等（目录名 chromium_headless_shell-* 不以 chromium- 后直接数字？
        # 实际名是 chromium_headless_shell-1234，startswith("chromium-") 为 False，安全跳过。
        # 另防 chromium-foo 杂项：有二进制且有版本即可。
        exe = executable_path_in_chromium_dir(entry)
        if exe is None:
            continue
        ver = read_chromium_dir_version(entry)
        if not ver:
            continue
        found.append((ver, exe))
    return found


def select_executable_for_version(
    profile_version: str | None,
    available: list[tuple[str, Path]],
    *,
    strict: bool,
    profile_dir: Path | str | None = None,
) -> Path | None:
    """纯函数：按 profile 版本从 available 中选 executable_path。

    选择顺序（Chromium profile schema 单调递增，低版本开高版本 profile → SIGTRAP）：
    1) 完整版本串精确匹配 → 直接选用（零风险）
    2) 无精确匹配时：同 major 且 版本 >= profile 的候选中，选最小者
       （同 major 内 migration 幅度最小；绝不自动选用更高 major）
    3) 仍无候选：strict=True 抛 BrowserVersionMismatch；strict=False 返回 None

    - profile_version 为空 → None（调用方走 playwright 默认二进制）
    """
    if not profile_version:
        return None

    wanted = profile_version.strip()
    if not wanted:
        return None

    # 1) 完整串精确匹配
    for ver, exe in available:
        if ver == wanted:
            return exe

    # 2) 同 major 且版本 >= profile：选数值最小者
    wanted_key = _version_key(wanted)
    if wanted_key is not None:
        wanted_major = wanted_key[0]
        eligible: list[tuple[tuple[int, ...], Path]] = []
        for ver, exe in available:
            key = _version_key(ver)
            if key is None:
                continue
            if key[0] != wanted_major:
                continue
            if key >= wanted_key:
                eligible.append((key, exe))
        if eligible:
            eligible.sort(key=lambda item: item[0])
            return eligible[0][1]

    if not strict:
        return None

    avail_list = sorted({v for v, _ in available})
    avail_text = ", ".join(avail_list) if avail_list else "（无）"
    profile_text = str(Path(profile_dir).resolve()) if profile_dir else "（未知）"

    # 同 major 但更低的版本：用户最易困惑的情形，单独点明
    lower_same_major: list[str] = []
    if wanted_key is not None:
        wanted_major = wanted_key[0]
        for ver, _ in available:
            key = _version_key(ver)
            if key is not None and key[0] == wanted_major and key < wanted_key:
                lower_same_major.append(ver)
    lower_note = ""
    if lower_same_major:
        lower_sorted = ", ".join(sorted(set(lower_same_major)))
        lower_note = (
            f"  本机有同系列但更低的版本（{lower_sorted}），用它打开会崩溃，已拒绝。\n"
        )

    raise BrowserVersionMismatch(
        "浏览器 profile 版本与本机 Playwright Chromium 不匹配，拒绝启动以免 SIGTRAP 崩溃。\n"
        f"  profile 路径: {profile_text}\n"
        f"  profile Last Version: {wanted}\n"
        f"  本机 ms-playwright 可用版本: {avail_text}\n"
        f"{lower_note}"
        "修复建议：\n"
        "  1) 安装/补齐匹配或更高小版本：python3 -m playwright install chromium\n"
        "     （须与 profile 同 major，且完整版本 >= profile Last Version；"
        "不要指望更高 major 被自动选用——那会不可逆升级 profile schema）\n"
        "  2) 使用与 profile Last Version 相同、或同 major 且版本不低于 profile 的 Chromium 再打开\n"
        "  3) 不要用低版本 Chromium 打开高版本写过的 profile（schema 只增不减）"
    )


def resolve_executable_for_profile(
    profile_dir: Path | str,
    *,
    ms_playwright_root: Path | str | None = None,
    strict: bool | None = None,
) -> Path | None:
    """组合：读 profile 版本 + 扫描本机二进制 + 选择。

    strict 默认：macOS arm64 为 True，其他平台 False（宽松回落默认二进制）。
    """
    if strict is None:
        strict = is_macos_arm64()

    profile_dir = Path(profile_dir)
    profile_version = read_profile_last_version(profile_dir)
    available = scan_local_chromiums(ms_playwright_root)
    return select_executable_for_version(
        profile_version,
        available,
        strict=strict,
        profile_dir=profile_dir,
    )


def launch_profile_context(
    playwright: Any,
    profile_dir: Path | str,
    headless: bool = True,
    **kwargs: Any,
) -> Any:
    """唯一的持久化上下文启动入口。

    playwright 为调用方已进入的 sync_playwright() 实例。
    版本不匹配时抛 BrowserVersionMismatch，绝不进入 launch 调用。
    """
    profile_dir = Path(profile_dir)
    executable = resolve_executable_for_profile(profile_dir)

    launch_kwargs: dict[str, Any] = {
        "user_data_dir": str(profile_dir),
        "headless": headless,
        **kwargs,
    }
    if executable is not None:
        launch_kwargs["executable_path"] = str(executable)

    return playwright.chromium.launch_persistent_context(**launch_kwargs)
