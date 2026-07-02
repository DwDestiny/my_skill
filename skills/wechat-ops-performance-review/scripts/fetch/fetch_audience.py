"""Fetch audience profile (Interface B: /misc/useranalysis).

HTML page with inline <script> data. Parse via regex (tolerant).
Fields may appear as `var xxx = {...};` or `window.xxx = [...]`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page


def _is_nonempty_struct(v: Any) -> bool:
    """Return True only for non-empty list or non-empty dict. Strings/None/other never count as data."""
    return isinstance(v, (list, dict)) and len(v) > 0


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


def _extract_js_var(html: str, var_name: str) -> Any | None:
    """Try multiple common JS literal patterns. Return parsed JSON when possible, else None."""
    if not html or not var_name:
        return None

    # Pattern 1: var/let/const/window.xxx = {..} or [..] ;
    pat1 = rf'(?:var|let|const|window\.)?\s*{re.escape(var_name)}\s*=\s*(\{{[\s\S]*?\}}|\[[\s\S]*?\])\s*;'
    m = re.search(pat1, html, re.IGNORECASE | re.DOTALL)
    if m:
        snippet = m.group(1).strip()
        # sanitize trailing commas (common in JS not JSON)
        snippet = re.sub(r',(\s*[\}\]])', r'\1', snippet)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

    # Pattern 2: inside larger object "key": {..} or key: {..}
    pat2 = rf'["\']?{re.escape(var_name)}["\']?\s*[:=]\s*(\{{[\s\S]*?\}}|\[[\s\S]*?\])'
    m = re.search(pat2, html, re.IGNORECASE | re.DOTALL)
    if m:
        snippet = m.group(1).strip()
        snippet = re.sub(r',(\s*[\}\]])', r'\1', snippet)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

    # Pattern 3: loose until ;
    pat3 = rf'(?:var|let|const|window\.)?\s*{re.escape(var_name)}\s*=\s*([^;]{{0,2000}});'
    m = re.search(pat3, html, re.IGNORECASE | re.DOTALL)
    if m:
        raw = m.group(1).strip()
        raw = re.sub(r',(\s*[\}\]])$', r'\1', raw)
        if raw.startswith(("{", "[")):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None
        # Never leak non-JSON (e.g. JS function code or primitives); only dict/list or None
        return None

    return None


def fetch_audience(page: Page, workspace: Path) -> dict[str, Any]:
    """Goto useranalysis, extract known vars via regex from full HTML, write raw/audience.json with available flag."""
    raw_dir = workspace / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    token = token_from_url(page.url or "")
    if not token:
        page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=30000)
        token = token_from_url(page.url or "")
        if not token:
            raise RuntimeError("login_required: token missing before fetching audience")

    url = f"https://mp.weixin.qq.com/misc/useranalysis?token={token}&lang=zh_CN"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)

    html = page.evaluate("() => document.documentElement.innerHTML") or ""

    data: dict[str, Any] = {
        "cumulate_user": _extract_js_var(html, "cumulate_user"),
        "new_user": _extract_js_var(html, "new_user"),
        "cancel_user": _extract_js_var(html, "cancel_user"),
        "netgain": _extract_js_var(html, "netgain"),
        "city": _extract_js_var(html, "city"),
        "province": _extract_js_var(html, "province"),
        "age": _extract_js_var(html, "age"),
        "user_source": _extract_js_var(html, "user_source"),
    }

    # "almost empty" -> available: false
    # Only non-empty list/dict count as "has data"; garbage strings (e.g. JS code) are ignored.
    core = ["cumulate_user", "new_user", "cancel_user", "netgain"]
    has_core = any(_is_nonempty_struct(data.get(k)) for k in core)
    has_demo = any(_is_nonempty_struct(data.get(k)) for k in ["city", "province", "age", "user_source"])
    data["available"] = bool(has_core or has_demo)

    # ensure all listed fields present even if None (for contract)
    for k in list(data.keys()):
        if data[k] is None and k != "available":
            pass  # already None

    (raw_dir / "audience.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return data
