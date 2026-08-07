# GEB-L3
# Input: 已登录 Page + workspace；从 URL 取 token，goto /cgi-bin/home，读 window.wx.commonData
# Output: 写 raw/account.json（nick_name/head_img/user_name/avatar_local）；关键字段缺失即抛错、不写盘；头像 best-effort 经 page.request.get 落 raw/avatar.<ext>（按 content-type：jpeg→.jpg / png→.png / gif→.gif / webp→.webp，其它回落 .jpg）
# Pos: plugins/wxops/scripts/fetch/fetch_account.py
"""Fetch account profile (Interface A: /cgi-bin/home).

Extracts nick_name / user_name / head_img from window.wx.commonData nested paths
(data / user_info), fail-fast on missing critical fields, downloads avatar best-effort.
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


_TOP_KEYS_LIMIT = 30

# content-type（分号前主类型，小写）→ 落盘扩展名；未知/缺失回落 .jpg
_CONTENT_TYPE_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _nonempty_str(value: Any) -> str | None:
    """None / 非字符串 / strip 后空串 → 取不到。"""
    if not isinstance(value, str):
        return None
    s = value.strip()
    return s if s else None


def _ext_from_content_type(content_type: str | None) -> str:
    """按 content-type 定扩展名；带参数时取分号前；未知/缺失 → .jpg。"""
    if not content_type:
        return ".jpg"
    base = content_type.split(";", 1)[0].strip().lower()
    return _CONTENT_TYPE_EXT.get(base, ".jpg")


def _top_keys_preview(common_data: dict[str, Any], limit: int = _TOP_KEYS_LIMIT) -> list[Any]:
    keys = list(common_data.keys())
    if len(keys) <= limit:
        return keys
    return keys[:limit] + [f"...(+{len(keys) - limit} more)"]


def _fail_missing_field(field: str, common_data: dict[str, Any], detail: str) -> None:
    keys = _top_keys_preview(common_data)
    raise RuntimeError(
        f"account_fetch_failed: commonData 里取不到 {field}（{detail}）。\n"
        f"  commonData 顶层键: {keys}\n"
        "  这通常意味着微信后台前端结构已变更，需要重新探查取值路径。"
    )


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

    common_data = page.evaluate("() => window.wx && window.wx.commonData")
    if not isinstance(common_data, dict):
        raise RuntimeError(
            "account_fetch_failed: 页面上取不到 window.wx.commonData"
            f"（实际拿到 {type(common_data).__name__}）。"
            "常见原因：登录态失效、未成功导航到 /cgi-bin/home、或后台前端结构调整。"
        )

    data = _as_dict(common_data.get("data"))
    user_info = _as_dict(common_data.get("user_info"))

    nick_name = _nonempty_str(data.get("nick_name")) or _nonempty_str(
        user_info.get("nick_name")
    )
    if not nick_name:
        _fail_missing_field("nick_name", common_data, "data / user_info 均无")

    user_name = _nonempty_str(data.get("user_name")) or _nonempty_str(data.get("alias"))
    if not user_name:
        _fail_missing_field("user_name", common_data, "data.user_name / data.alias 均无")

    head_img = _nonempty_str(data.get("head_img")) or _nonempty_str(
        user_info.get("head_img")
    )
    if not head_img:
        print(
            "警告: commonData 中取不到 head_img（data / user_info 均无），"
            "将继续写盘但 head_img 与 avatar_local 为 null。",
            file=sys.stderr,
        )
        head_img = None

    # 头像 best-effort：走 Playwright APIRequestContext（page.request），不受页面 CORS 约束。
    # 页面内 fetch 会被 wx.qlogo.cn 的同源策略挡死（无 Access-Control-Allow-Origin），
    # 历史上整条下载路径从未成功过，且失败被双重 catch 静默吞掉。
    avatar_local: str | None = None
    if head_img:
        request_ctx = getattr(page, "request", None)
        if request_ctx is None:
            print(
                "警告: page 无 request 属性，无法下载头像，"
                "将继续写盘但 avatar_local 为 null。",
                file=sys.stderr,
            )
        else:
            try:
                resp = request_ctx.get(head_img)
                status = getattr(resp, "status", None)
                if status != 200:
                    print(
                        f"警告: 头像下载失败：HTTP status={status}（非 200），"
                        "将继续写盘但 avatar_local 为 null。",
                        file=sys.stderr,
                    )
                else:
                    body = resp.body()
                    if not body or len(body) == 0:
                        print(
                            "警告: 头像下载失败：响应 body 为空，"
                            "将继续写盘但 avatar_local 为 null。",
                            file=sys.stderr,
                        )
                    else:
                        headers = getattr(resp, "headers", None) or {}
                        ct = None
                        if isinstance(headers, dict):
                            ct = headers.get("content-type") or headers.get("Content-Type")
                        ext = _ext_from_content_type(ct if isinstance(ct, str) else None)
                        avatar_path = raw_dir / f"avatar{ext}"
                        avatar_path.write_bytes(body)
                        avatar_local = f"raw/avatar{ext}"
            except Exception as exc:
                # best-effort：任何异常都不得中断采集
                print(
                    f"警告: 头像下载失败：{type(exc).__name__}: {exc}，"
                    "将继续写盘但 avatar_local 为 null。",
                    file=sys.stderr,
                )
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
