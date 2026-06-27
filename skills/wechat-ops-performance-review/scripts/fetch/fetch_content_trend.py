"""Fetch content trend stats (Interface C: /misc/appmsganalysis?action=report&f=json).

Pure JSON response. Validates base_resp.ret == 0, keeps item arrays + counts.
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


def fetch_content_trend(page: Page, workspace: Path) -> dict[str, Any]:
    """Fetch JSON trend data, validate ret, write raw/content-trend.json, return dict with arrays + lengths."""
    raw_dir = workspace / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    token = token_from_url(page.url or "")
    if not token:
        page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=30000)
        token = token_from_url(page.url or "")
        if not token:
            raise RuntimeError("login_required: token missing before fetching content trend")

    url = (
        f"https://mp.weixin.qq.com/misc/appmsganalysis"
        f"?action=report&token={token}&lang=zh_CN&f=json"
    )

    payload = page.evaluate(
        """async (u) => {
            const r = await fetch(u, { credentials: 'include' });
            return await r.json();
        }""",
        url,
    )

    if not isinstance(payload, dict):
        payload = {}

    base_resp = payload.get("base_resp") or {}
    if str(base_resp.get("ret", -1)) != "0":
        raise RuntimeError(f"base_resp ret != 0: {base_resp}")

    read_item = payload.get("read_item") or []
    share_item = payload.get("share_item") or []
    like_item = payload.get("like_item") or []
    zaikan_item = payload.get("zaikan_item") or []
    comment_item = payload.get("comment_item") or []

    result: dict[str, Any] = {
        "base_resp": base_resp,
        "read_item": read_item,
        "share_item": share_item,
        "like_item": like_item,
        "zaikan_item": zaikan_item,
        "comment_item": comment_item,
        "counts": {
            "read_item": len(read_item),
            "share_item": len(share_item),
            "like_item": len(like_item),
            "zaikan_item": len(zaikan_item),
            "comment_item": len(comment_item),
        },
    }

    (raw_dir / "content-trend.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result
