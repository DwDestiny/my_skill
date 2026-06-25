#!/usr/bin/env python3
"""Export WeChat official account publish records from the logged-in backend.

This script connects to the long-running Laoliang browser over CDP, reads the
current mp.weixin.qq.com backend token from the active logged-in page, and
fetches the same-origin publish detail JSON. It never writes cookies or the
backend token to disk.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path("/Users/dw/Desktop/claude")
CDP_URL = os.environ.get("LAOLIANG_CDP_URL", "http://127.0.0.1:9333")


def safe_int(value: Any) -> int:
    try:
        return int(str(value).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0


def iso_from_send_time(value: Any) -> str | None:
    timestamp = safe_int(value)
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def find_wechat_page(pages: list[Page]) -> Page | None:
    for page in pages:
        if "mp.weixin.qq.com" in page.url:
            return page
    return None


def token_from_url(url: str) -> str | None:
    match = re.search(r"[?&]token=(\d+)", url)
    return match.group(1) if match else None


def decode_publish_group(group: dict[str, Any]) -> dict[str, Any]:
    if isinstance(group.get("info"), dict):
        return {
            "publish_type": group.get("publish_type"),
            "info": group.get("info") or {},
        }
    publish_info = group.get("publish_info") or {}
    if isinstance(publish_info, str):
        try:
            publish_info = json.loads(publish_info)
        except json.JSONDecodeError:
            publish_info = {}
    return {
        "publish_type": group.get("publish_type"),
        "info": publish_info if isinstance(publish_info, dict) else {},
    }


def normalize_records(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for group_index, raw_group in enumerate(groups):
        group = decode_publish_group(raw_group)
        info = group.get("info") or {}
        publish_type = group.get("publish_type")
        group_msgid = info.get("msgid")
        appmsg_info = info.get("appmsg_info") or []
        for article in appmsg_info:
            line_info = article.get("line_info") or {}
            send_time = line_info.get("send_time") or info.get("send_time")
            records.append(
                {
                    "group_index": group_index,
                    "publish_type": publish_type,
                    "msgid": group_msgid,
                    "type": info.get("type"),
                    "new_publish": info.get("new_publish"),
                    "appmsgid": article.get("appmsgid") or group_msgid,
                    "itemidx": article.get("itemidx"),
                    "title": article.get("title") or "",
                    "digest": article.get("digest") or "",
                    "content_url": article.get("content_url") or "",
                    "cover": article.get("cover") or "",
                    "pic_cdn_url_235_1": article.get("pic_cdn_url_235_1") or "",
                    "pic_cdn_url_1_1": article.get("pic_cdn_url_1_1") or "",
                    "read_num": safe_int(article.get("read_num")),
                    "like_num": safe_int(article.get("like_num")),
                    "old_like_num": safe_int(article.get("old_like_num")),
                    "moment_like_num": safe_int(article.get("moment_like_num")),
                    "comment_num": safe_int(article.get("comment_num")),
                    "total_comment_count_contains_reply": safe_int(
                        article.get("total_comment_count_contains_reply")
                    ),
                    "share_num": safe_int(article.get("share_num")),
                    "reprint_num": safe_int(article.get("reprint_num")),
                    "reward_money": str(article.get("reward_money") or "0.00"),
                    "is_deleted": bool(article.get("is_deleted")),
                    "is_comment_enable": bool(article.get("is_comment_enable")),
                    "can_modify": article.get("can_modify_status") or article.get("can_modify"),
                    "modify_wording": article.get("modify_wording") or "",
                    "copyright_status": article.get("copyright_status"),
                    "copyright_type": article.get("copyright_type"),
                    "item_show_type": article.get("item_show_type"),
                    "send_time": send_time,
                    "published_at": iso_from_send_time(send_time),
                    "raw_article": article,
                }
            )
    return records


def export_records(root: Path, cdp_url: str) -> Path:
    captured_at = datetime.now(timezone.utc).isoformat()
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(cdp_url)
        if not browser.contexts:
            raise RuntimeError("login_required: no browser context found on CDP endpoint")
        context = browser.contexts[0]
        page = find_wechat_page(context.pages) or context.new_page()
        if "mp.weixin.qq.com" not in page.url:
            page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=15000)
        token = token_from_url(page.url)
        if not token:
            raise RuntimeError("login_required: open the logged-in mp.weixin.qq.com backend page first")
        payload = page.evaluate(
            """async (token) => {
                const count = 10;
                const groups = [];
                let totals = {};
                let lastBaseResp = { ret: 0, err_msg: "ok" };
                for (let begin = 0; begin < 1000; begin += count) {
                    const url = `/cgi-bin/appmsgpublish?sub=list&begin=${begin}&count=${count}&token=${token}&lang=zh_CN&f=json&ajax=1`;
                    const response = await fetch(url, { credentials: "include" });
                    const data = await response.json();
                    lastBaseResp = data.base_resp || lastBaseResp;
                    if (String(lastBaseResp.ret ?? 0) !== "0") {
                        return data;
                    }
                    const publishPage = JSON.parse(data.publish_page || "{}");
                    totals = {
                        total_count: publishPage.total_count,
                        publish_count: publishPage.publish_count,
                        masssend_count: publishPage.masssend_count,
                    };
                    groups.push(...(publishPage.publish_list || []));
                    if (groups.length >= Number(publishPage.total_count || 0)) {
                        break;
                    }
                }
                return {
                    base_resp: lastBaseResp,
                    publish_page: JSON.stringify({ ...totals, publish_list: groups }),
                };
            }""",
            token,
        )
        browser.close()

    base_resp = payload.get("base_resp") or {}
    if str(base_resp.get("ret", 0)) != "0":
        raise RuntimeError(f"token_or_cookie_invalid: {base_resp}")
    publish_page = json.loads(payload.get("publish_page") or "{}")
    raw_groups = publish_page.get("publish_list") or []
    groups = [decode_publish_group(group) for group in raw_groups]
    records = normalize_records(groups)
    if not records:
        raise RuntimeError("data_empty: backend returned zero publish records")

    out_dir = root / "reports" / "wechat"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"publish-records-{stamp}.json"
    export = {
        "url": "https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&begin=0&count=10&token=<redacted>&lang=zh_CN",
        "captured_at": captured_at,
        "source": "mp.weixin.qq.com appmsgpublish list via logged-in browser",
        "totals": {
            "total_count": publish_page.get("total_count"),
            "publish_count": publish_page.get("publish_count"),
            "masssend_count": publish_page.get("masssend_count"),
        },
        "groups": groups,
        "record_count": len(records),
        "records": records,
    }
    out_path.write_text(json.dumps(export, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_path = out_path.with_suffix(".summary.json")
    summary_path.write_text(
        json.dumps(
            {
                "captured_at": captured_at,
                "record_count": len(records),
                "totals": export["totals"],
                "data_export": out_path.as_posix(),
                "quality_status": "ok",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--cdp-url", default=CDP_URL)
    args = parser.parse_args()
    try:
        out_path = export_records(Path(args.root).resolve(), args.cdp_url)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "ok", "data_export": out_path.as_posix()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
