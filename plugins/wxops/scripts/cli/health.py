#!/usr/bin/env python3
# GEB-L3
# Input: workspace 账号办公室路径、可选探测超时；browser-profile 登录态
# Output: check_login 返回 {alive, error, duration_s}；_probe 返回 token 或 None
# Pos: plugins/wxops/scripts/cli/health.py
"""登录态健康探测：headless 打开 browser-profile，看 mp.weixin.qq.com URL 是否含 token。"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

from . import env
from . import lock as lock_mod


def _ensure_in_path(skill_dir: Path) -> None:
    s = str(skill_dir)
    if s not in sys.path:
        sys.path.insert(0, s)


def _probe(profile_dir: Path, timeout_ms: int) -> str | None:
    """打开 persistent context，探测 mp 后台 URL 中的 token。

    模块级函数，供测试 monkeypatch；check_login 必须以 _probe(...) 形式调用。
    """
    from playwright.sync_api import sync_playwright

    _ensure_in_path(env.get_skill_dir())
    from scripts.export_wechat_publish_records import token_from_url  # 复用

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=True,
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(
                "https://mp.weixin.qq.com/",
                wait_until="domcontentloaded",
                timeout=timeout_ms,
            )
            return token_from_url(page.url or "")
        finally:
            context.close()


def _profile_is_empty(profile_dir: Path) -> bool:
    if not profile_dir.exists() or not profile_dir.is_dir():
        return True
    try:
        return not any(profile_dir.iterdir())
    except OSError:
        return True


def check_login(workspace: Path, timeout_ms: int = 15000) -> dict[str, Any]:
    """探测账号办公室登录态是否存活。

    返回 {"alive": bool, "error": str | None, "duration_s": float}。
    ProfileLockError 不捕获，由调用方展示。
    """
    profile_dir = workspace / "browser-profile"
    if _profile_is_empty(profile_dir):
        return {
            "alive": False,
            "error": "从未登录（无登录态档案）",
            "duration_s": 0.0,
        }

    started = time.monotonic()
    try:
        with lock_mod.profile_lock(workspace):
            token = _probe(profile_dir, timeout_ms)
    except lock_mod.ProfileLockError:
        raise
    except ImportError:
        duration = time.monotonic() - started
        return {
            "alive": False,
            "error": "playwright 未安装，请先运行 wxops init",
            "duration_s": round(duration, 3),
        }
    except Exception as e:
        duration = time.monotonic() - started
        msg = str(e).strip() or e.__class__.__name__
        # 超时类异常给中文描述
        lower = msg.lower()
        if "timeout" in lower or "超时" in msg:
            err = f"探测超时：{msg}"
        else:
            err = f"探测失败：{msg}"
        return {
            "alive": False,
            "error": err,
            "duration_s": round(duration, 3),
        }

    duration = time.monotonic() - started
    if token:
        return {"alive": True, "error": None, "duration_s": round(duration, 3)}
    return {
        "alive": False,
        "error": "登录态已失效（未检测到 token）",
        "duration_s": round(duration, 3),
    }
