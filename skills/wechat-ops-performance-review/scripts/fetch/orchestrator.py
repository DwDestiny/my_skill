"""Orchestrator: coordinates the 4 interfaces with anti-detection sleeps.

Flow:
  1. launch_persistent_context
  2. open_logged_in_page -> (page, token)
  3. scrape_publish_records + write_export
  4. sleep(3~8)
  5. fetch_account
  6. sleep
  7. fetch_audience
  8. sleep
  9. fetch_content_trend
  Any failure (login or base_resp.ret !=0 ) -> immediate {"status":"failed", ...} no retry/continue.
"""
from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


def _ensure_scripts_on_path() -> None:
    here = Path(__file__).resolve().parent
    scripts_dir = here.parent
    skill_root = scripts_dir.parent
    for p in (str(scripts_dir), str(skill_root)):
        if p not in sys.path:
            sys.path.insert(0, p)


_ensure_scripts_on_path()


def run(workspace: Path | str, profile_dir: Path | str, headless: bool = True) -> dict[str, Any]:
    """Main entry for multi-fetch. Mirrors export_via_persistent style but adds 3 more interfaces."""
    workspace = Path(workspace).resolve()
    profile_dir = Path(profile_dir).resolve()
    raw_dir = workspace / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    captured_at = datetime.now(timezone.utc).isoformat()

    # Robust import for different sys.path setups used by this project:
    # - CLI: inserts skill_root → "scripts.fetch.xxx" / "scripts.export_..."
    # - tests/acceptance: inserts "scripts" → "fetch.xxx" / bare "export_..."
    def _import_session():
        try:
            from fetch.session import open_logged_in_page  # type: ignore
            return open_logged_in_page
        except ImportError:
            pass
        try:
            from scripts.fetch.session import open_logged_in_page  # type: ignore
            return open_logged_in_page
        except ImportError:
            pass
        from session import open_logged_in_page  # type: ignore
        return open_logged_in_page

    def _import_publish_funcs():
        # 复用底层 _fetch/_process 以保留 totals/groups 元数据(供 build 的 data_quality)
        try:
            from export_wechat_publish_records import _fetch_publish_payload, _process_publish_payload, write_export  # type: ignore
            return _fetch_publish_payload, _process_publish_payload, write_export
        except ImportError:
            pass
        from scripts.export_wechat_publish_records import _fetch_publish_payload, _process_publish_payload, write_export  # type: ignore
        return _fetch_publish_payload, _process_publish_payload, write_export

    def _import_fetchers():
        for mod_path in (
            ("fetch.fetch_account", "fetch.fetch_audience", "fetch.fetch_content_trend"),
            ("scripts.fetch.fetch_account", "scripts.fetch.fetch_audience", "scripts.fetch.fetch_content_trend"),
        ):
            try:
                fa = __import__(mod_path[0], fromlist=["fetch_account"]).fetch_account
                fau = __import__(mod_path[1], fromlist=["fetch_audience"]).fetch_audience
                fc = __import__(mod_path[2], fromlist=["fetch_content_trend"]).fetch_content_trend
                return fa, fau, fc
            except Exception:
                continue
        # last resort bare (unlikely)
        from fetch_account import fetch_account  # type: ignore
        from fetch_audience import fetch_audience  # type: ignore
        from fetch_content_trend import fetch_content_trend  # type: ignore
        return fetch_account, fetch_audience, fetch_content_trend

    open_logged_in_page = _import_session()
    _fetch_publish_payload, _process_publish_payload, write_export = _import_publish_funcs()
    fetch_account, fetch_audience, fetch_content_trend = _import_fetchers()

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
        )
        try:
            page, token = open_logged_in_page(context)

            # 1. 文章列表 (reuse existing,保留 totals/groups 元数据)
            payload = _fetch_publish_payload(page, token)
            groups, records, totals = _process_publish_payload(payload)
            publish_export = write_export(
                workspace,
                records,
                totals=totals,
                groups=groups,
                captured_at=captured_at,
                source="mp.weixin.qq.com multi-fetch orchestrator (publish + account + audience + trend)",
            )

            # Anti-detect sleeps between interfaces
            time.sleep(random.uniform(3, 8))

            # 2. 账号信息
            fetch_account(page, workspace)
            time.sleep(random.uniform(3, 8))

            # 3. 粉丝画像
            fetch_audience(page, workspace)
            time.sleep(random.uniform(3, 8))

            # 4. 内容趋势
            fetch_content_trend(page, workspace)

            return {
                "status": "ok",
                "raw_dir": str(raw_dir),
                "publish_export": str(publish_export),
                "captured_at": captured_at,
            }
        except Exception as exc:
            msg = str(exc)
            # login or ret!=0 cases -> failed with hint
            if "login_required" in msg or "token_or_cookie_invalid" in msg or "login" in msg.lower() or "token" in msg.lower():
                return {
                    "status": "failed",
                    "error": msg,
                    "hint": "运行 wxops login 重新登录",
                }
            # base_resp ret errors etc.
            return {
                "status": "failed",
                "error": msg,
                "hint": "运行 wxops login 重新登录",
            }
        finally:
            context.close()
