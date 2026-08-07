#!/usr/bin/env python3
# GEB-L3
# Input: workspace 路径 + headless 标志；读写 browser-profile 持久化目录
# Output: 打开 mp.weixin.qq.com 引导扫码；按回车后经 _confirm_token（快路径读 URL + 最多 3 轮主动 goto 探 token）确认登录态：有 token 则 exit 0，否则 exit 1 并提示用 accounts check 复核
# Pos: plugins/wxops/scripts/cli/login_cmd.py
"""wxops login：使用 persistent context 打开 mp.weixin.qq.com，引导用户扫码登录，确认后验证 token 并持久化。"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

from . import env
from . import lock as lock_mod

# 登录态确认：快路径无 token 时的主动 goto 重探参数（与 health._probe 同原理，就地复用当前 page）
_TOKEN_RETRY_ROUNDS = 3
_TOKEN_RETRY_INTERVAL_S = 1.5
_TOKEN_PROBE_TIMEOUT_MS = 8000
_MP_HOME_URL = "https://mp.weixin.qq.com/"


def _ensure_in_path(skill_dir: Path) -> None:
    s = str(skill_dir)
    if s not in sys.path:
        sys.path.insert(0, s)


def _confirm_token(page: Any) -> str | None:
    """在已打开的 page 上确认登录 token（模块级，供测试 monkeypatch）。

    1. 快路径：当前 URL 已有 token 则直接返回（不 goto）。
    2. 兜底：最多 _TOKEN_RETRY_ROUNDS 轮主动 goto 后台首页再读 URL；
       goto 异常当作本轮无 token，不向上抛。
    """
    _ensure_in_path(env.get_skill_dir())
    from scripts.export_wechat_publish_records import token_from_url  # 复用

    token = token_from_url(page.url or "")
    if token:
        return token

    for i in range(_TOKEN_RETRY_ROUNDS):
        try:
            page.goto(
                _MP_HOME_URL,
                wait_until="domcontentloaded",
                timeout=_TOKEN_PROBE_TIMEOUT_MS,
            )
        except Exception:
            # 超时/网络等：本轮视为无 token，继续后续轮次
            pass
        token = token_from_url(page.url or "")
        if token:
            return token
        if i < _TOKEN_RETRY_ROUNDS - 1:
            time.sleep(_TOKEN_RETRY_INTERVAL_S)
    return None


def run(workspace: Path, headless: bool = False) -> int:
    print_header = env.print_header
    print_step = env.print_step
    print_success = env.print_success
    print_warn = env.print_warn
    print_error = env.print_error
    print_info = env.print_info
    print_guide_next = env.print_guide_next

    print_header("登录公众号后台（持久化登录态）")

    # 懒导入 playwright（未装时给出提示）
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print_error("playwright 未安装。请先运行: wxops init")
        return 1

    _ensure_in_path(env.get_skill_dir())
    from scripts.browser import launch_profile_context  # 统一入口（版本自适应）

    profile_dir = env.get_browser_profile_dir(workspace)
    profile_dir.mkdir(parents=True, exist_ok=True)

    print_step("启动持久化浏览器上下文", f"用户数据目录: {profile_dir}")
    print_info("即将打开 https://mp.weixin.qq.com/ （headless=" + str(headless) + "）")

    # 与 health/batch 一致：持锁期间独占 browser-profile（login 与拉数互斥）
    try:
        with lock_mod.profile_lock(workspace):
            with sync_playwright() as playwright:
                context = launch_profile_context(
                    playwright, profile_dir, headless=headless
                )
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                    if "mp.weixin.qq.com" not in (page.url or ""):
                        page.goto(
                            "https://mp.weixin.qq.com/",
                            wait_until="domcontentloaded",
                            timeout=30000,
                        )

                    print("\n" + "=" * 50)
                    print("浏览器已打开公众号登录页")
                    print("① 浏览器已打开 →")
                    print("② 请用公众号管理员微信扫码登录")
                    print("③ 登录成功后回到终端按回车确认")
                    print("=" * 50 + "\n")

                    try:
                        input("登录完成后请按回车继续...")
                    except (EOFError, KeyboardInterrupt):
                        print_warn("用户中断")
                        return 1

                    # 就地确认 token（快路径 + 主动 goto 重探）；禁止调用
                    # health.check_login（其内部会再抢 profile 锁，同进程二次 flock 失败）
                    token = _confirm_token(page)
                    if token:
                        print_success("登录成功，登录态已保存")
                        print_info(
                            "（persistent context 会自动把 cookies 等保存到 browser-profile/）"
                        )
                        print_guide_next("wxops analyze   （抓取最新数据并生成看板）")
                        return 0
                    else:
                        print_warn("未能在页面 URL 中确认到登录 token。")
                        print_info(
                            "若你确认已扫码成功，可运行 `wxops accounts check` 复核真实登录态；"
                            "本次未能在页面 URL 捕获到 token，登录态可能已保存但未被确认。"
                        )
                        print_info(
                            "可能原因：未完成扫码、页面还在登录中、网络延迟，"
                            "或使用了个人订阅号而非服务号/公众号后台。"
                        )
                        print_info(
                            "请重新运行 wxops login 再试，或先用 accounts check 确认状态。"
                        )
                        return 1
                finally:
                    context.close()
    except lock_mod.ProfileLockError as e:
        print_error(str(e))
        return 1
