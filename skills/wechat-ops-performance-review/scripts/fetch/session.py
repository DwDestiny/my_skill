"""Session helpers for logged-in MP backend pages.

Reuses token_from_url from export_wechat_publish_records.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

from playwright.sync_api import BrowserContext, Page


def _ensure_scripts_on_path() -> None:
    """Ensure 'scripts' dir or skill root is importable for sibling imports."""
    here = Path(__file__).resolve().parent  # scripts/fetch
    scripts_dir = here.parent  # scripts/
    skill_root = scripts_dir.parent
    for p in (str(scripts_dir), str(skill_root)):
        if p not in sys.path:
            sys.path.insert(0, p)


_ensure_scripts_on_path()

try:
    from export_wechat_publish_records import token_from_url  # type: ignore
except ImportError:
    from scripts.export_wechat_publish_records import token_from_url  # type: ignore


def open_logged_in_page(context: BrowserContext) -> Tuple[Page, str]:
    """Ensure we have a page on mp.weixin.qq.com with token in URL. Return (page, token)."""
    page = context.pages[0] if context.pages else context.new_page()
    if "mp.weixin.qq.com" not in (page.url or ""):
        page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=30000)
    token = token_from_url(page.url or "")
    if not token:
        raise RuntimeError("login_required: open the logged-in mp.weixin.qq.com backend page first")
    return page, token
