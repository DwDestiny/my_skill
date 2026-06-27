#!/usr/bin/env python3
"""wxops login：使用 persistent context 打开 mp.weixin.qq.com，引导用户扫码登录，确认后验证 token 并持久化。"""

from __future__ import annotations

import sys
from pathlib import Path

from . import env


def _ensure_in_path(skill_dir: Path) -> None:
    s = str(skill_dir)
    if s not in sys.path:
        sys.path.insert(0, s)


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

    profile_dir = env.get_browser_profile_dir(workspace)
    profile_dir.mkdir(parents=True, exist_ok=True)

    print_step("启动持久化浏览器上下文", f"用户数据目录: {profile_dir}")
    print_info("即将打开 https://mp.weixin.qq.com/ （headless=" + str(headless) + "）")

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            if "mp.weixin.qq.com" not in (page.url or ""):
                page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=30000)

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

            # 读取当前页 URL，检测 token
            current_url = page.url or ""
            from scripts.export_wechat_publish_records import token_from_url  # 复用

            token = token_from_url(current_url)
            if token:
                print_success("登录成功，登录态已保存")
                print_info("（persistent context 会自动把 cookies 等保存到 browser-profile/）")
                print_guide_next("wxops analyze   （抓取最新数据并生成看板）")
                return 0
            else:
                print_warn("未检测到登录态（URL 中没有 token）。")
                print_info("可能原因：未完成扫码、页面还在登录中、或使用了个人订阅号而非服务号/公众号后台。")
                print_info("请重新运行 wxops login 再试。")
                return 1
        finally:
            context.close()
