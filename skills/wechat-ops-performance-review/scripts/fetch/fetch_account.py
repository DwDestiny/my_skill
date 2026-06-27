"""Fetch account profile (Interface A: /cgi-bin/home).

Extracts from window.wx.commonData and downloads avatar using page fetch context.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page


def _ensure_scripts_on_path() -> None:
    here = Path(__file__).resolve().parent
    scripts_dir = here.parent
    skill_root = scripts_dir.parent
    for p in (str(scripts_dir), str(skill_root)):
        if p not in sys.path:
            sys.path.insert(0, p)


_ensure_scripts_on_path()

try:
    from export_wechat_publish_records import token_from_url  # type: ignore
except ImportError:
    from scripts.export_wechat_publish_records import token_from_url  # type: ignore


def fetch_account(page: Page, workspace: Path) -> dict[str, Any]:
    """Navigate to home, read commonData, download avatar (best effort), write raw/account.json, return dict."""
    raw_dir = workspace / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    token = token_from_url(page.url or "")
    if not token:
        # try ensure
        page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=30000)
        token = token_from_url(page.url or "")
        if not token:
            raise RuntimeError("login_required: token missing before fetching account")

    home_url = f"https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token={token}&lang=zh_CN"
    page.goto(home_url, wait_until="domcontentloaded", timeout=30000)

    common_data = page.evaluate("() => window.wx && window.wx.commonData") or {}
    if not isinstance(common_data, dict):
        common_data = {}

    nick_name = common_data.get("nick_name")
    head_img = common_data.get("head_img")
    user_name = common_data.get("user_name")

    avatar_local: str | None = None
    if head_img:
        try:
            # Use page context fetch to bypass hotlink protection
            buf_list = page.evaluate(
                """async (url) => {
                    if (!url) return null;
                    try {
                        const resp = await fetch(url, { credentials: 'include', mode: 'cors' });
                        if (!resp.ok) return null;
                        const ab = await resp.arrayBuffer();
                        return Array.from(new Uint8Array(ab));
                    } catch (e) {
                        return null;
                    }
                }""",
                head_img,
            )
            if buf_list:
                avatar_path = raw_dir / "avatar.png"
                avatar_path.write_bytes(bytes(buf_list))
                avatar_local = "raw/avatar.png"
        except Exception:
            # swallow, do not fail whole capture
            avatar_local = None

    result: dict[str, Any] = {
        "nick_name": nick_name,
        "head_img": head_img,
        "user_name": user_name,
        "avatar_local": avatar_local,
    }

    (raw_dir / "account.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result
