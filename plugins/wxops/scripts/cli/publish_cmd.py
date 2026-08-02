#!/usr/bin/env python3
# GEB-L3
# Input: argparse Namespace（--topic/--account/--go/--title/...）+ WXOPS_HOME 工作区
# Output: dry-run 预演或 --go 建草稿（草稿箱止步）；exit 0/1
# Pos: plugins/wxops/scripts/cli/publish_cmd.py
# 参考 hermes prepare_wechat_api_publish.py 编排顺序；引擎层三个 lib 禁改（2026-08-01）
"""publish 主链编排：定稿 → 渲染 HTML →（可选）上传素材 + 建草稿。"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from . import accounts_store
from . import env

# scripts/publish 无 __init__.py → sys.path 注入（与 wechat_api_prep_lib 同模式）
_PUBLISH_DIR = Path(__file__).resolve().parents[1] / "publish"
if str(_PUBLISH_DIR) not in sys.path:
    sys.path.insert(0, str(_PUBLISH_DIR))

from draft_builder import (  # noqa: E402
    build_cover_crop_fields,
    build_draft_article,
    read_image_size,
)
from wechat_html_renderer_lib import render_markdown_file_to_wechat_html  # noqa: E402

_MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_H1_RE = re.compile(r"(?m)^#\s+(.+?)\s*$")


def _root_from_args(args: Any) -> Path:
    """与 main._root_from_args 等价，本文件内联，不改 main helper。"""
    if getattr(args, "workspace", None):
        return Path(args.workspace).expanduser().resolve()
    return env.get_wxops_root()


def _extract_title_from_draft(text: str) -> str:
    m = _H1_RE.search(text)
    if not m:
        return ""
    return m.group(1).strip()


def _normalize_local_image_target(raw: str) -> str | None:
    """返回本地图 basename；远程 / data: 返回 None。"""
    target = unquote(raw.strip().strip("<>").strip())
    if not target:
        return None
    # 去掉 title 部分：url "title"
    if target.startswith('"') or target.startswith("'"):
        return None
    # 简单拆：路径可能带空格+引号标题
    if " " in target and ('"' in target or "'" in target):
        target = target.split(" ", 1)[0]
    target = target.split("#")[0].split("?")[0].strip()
    if not target:
        return None
    lower = target.lower()
    if lower.startswith(("http://", "https://", "data:")):
        return None
    return Path(target).name


def _collect_local_image_refs(draft_text: str) -> list[str]:
    """草稿中本地图片引用的 basename 列表（保序，可重复）。"""
    names: list[str] = []
    for m in _MD_IMAGE_RE.finditer(draft_text):
        name = _normalize_local_image_target(m.group(1))
        if name:
            names.append(name)
    return names


def _load_gateway_config(root: Path) -> tuple[str, str, str | None]:
    """返回 (base_url, bearer_token, source_note)。

    环境变量优先；否则 root/gateway.json。
    source_note 仅用于内部，不打印 token 值。
    """
    env_url = str(os.environ.get("WECHAT_GATEWAY_BASE_URL", "") or "").strip()
    env_token = str(os.environ.get("WECHAT_GATEWAY_BEARER_TOKEN", "") or "").strip()
    if env_url or env_token:
        return env_url, env_token, "env"

    gw_path = root / "gateway.json"
    if gw_path.is_file():
        try:
            data = json.loads(gw_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return "", "", "gateway.json"
        if isinstance(data, dict):
            base = str(data.get("base_url", "") or "").strip()
            token = str(data.get("bearer_token", "") or "").strip()
            return base, token, "gateway.json"
    return "", "", None


def _check_credentials(cred_path: Path) -> tuple[str, bool, str]:
    """返回 (状态, is_hard_fail, 说明)。状态为 ok / warn / fail。

    不回显任何凭证值。
    """
    if not cred_path.is_file():
        return (
            "fail",
            True,
            "凭证缺失：请配置 credentials/wechat.json（含 app_id / app_secret）",
        )
    try:
        data = json.loads(cred_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "fail", True, "凭证不是合法 JSON：credentials/wechat.json"
    if not isinstance(data, dict):
        return "fail", True, "凭证 JSON 必须是对象：credentials/wechat.json"
    app_id = data.get("app_id")
    app_secret = data.get("app_secret")
    if not isinstance(app_id, str) or not app_id.strip():
        return "fail", True, "凭证缺少非空 app_id：credentials/wechat.json"
    if not isinstance(app_secret, str) or not app_secret.strip():
        return "fail", True, "凭证缺少非空 app_secret：credentials/wechat.json"
    try:
        mode = cred_path.stat().st_mode
    except OSError:
        return "fail", True, "无法读取凭证文件权限"
    if mode & 0o077:
        return (
            "fail",
            True,
            f"凭证权限过宽，请执行：chmod 600 {cred_path.resolve()}",
        )
    return "ok", False, "凭证 (credentials/wechat.json)"


def run_publish(args: Any) -> int:
    """发布主链入口。默认 dry-run；--go 才触网建草稿。"""
    root = _root_from_args(args)

    # --- 账号解析（学 kit_cmd.run）---
    slug_raw = (getattr(args, "account", None) or "").strip() or None
    if slug_raw is None:
        current = accounts_store.get_current_slug(root)
        if not current:
            env.print_error(
                "未指定账号，且没有当前账号。"
                "请先 wxops accounts add 或给 --account。"
            )
            return 1
        slug_raw = current

    try:
        slug = accounts_store.validate_slug(slug_raw)
    except ValueError as e:
        env.print_error(str(e))
        return 1

    acct_meta = accounts_store.get_account(root, slug)
    if acct_meta is None:
        env.print_error(f"账号不存在：{slug}")
        slugs = [str(a.get("slug", "")) for a in accounts_store.list_accounts(root)]
        if slugs:
            env.print_info("可用账号：" + "、".join(slugs))
        else:
            env.print_info("当前没有任何账号。")
        return 1

    if str(acct_meta.get("status") or "") == "retired":
        env.print_error(f"账号已退休，不可发布：{slug}")
        return 1

    topic_raw = getattr(args, "topic", None)
    if topic_raw is None or str(topic_raw).strip() == "":
        env.print_error("必须提供 --topic")
        return 1
    try:
        topic = accounts_store.validate_slug(str(topic_raw).strip())
    except ValueError as e:
        env.print_error(str(e))
        return 1

    do_go = bool(getattr(args, "go", False))
    acct = accounts_store.get_account_dir(root, slug)

    draft_md = acct / "drafts" / topic / "draft.md"
    audit_md = acct / "drafts" / topic / "audit.md"
    cover_jpg = acct / "images" / topic / "cover.jpg"
    asset_root = acct / "images" / topic
    output_html = acct / "output" / topic / "draft.html"
    ledger_path = acct / "published" / f"{topic}.json"
    cred_path = acct / "credentials" / "wechat.json"

    # --- 前置检查（收集后统一打表）---
    rows: list[tuple[str, str]] = []  # (mark, text) mark in ok/warn/fail
    hard_fail = False

    draft_text = ""
    if not draft_md.is_file():
        rows.append(("fail", "draft.md 缺失"))
        hard_fail = True
    else:
        try:
            draft_text = draft_md.read_text(encoding="utf-8")
        except OSError:
            rows.append(("fail", "draft.md 无法读取"))
            hard_fail = True
        else:
            if not draft_text.strip():
                rows.append(("fail", "draft.md 为空"))
                hard_fail = True
            else:
                rows.append(("ok", "draft.md 存在且非空"))

    if not audit_md.is_file():
        rows.append(
            (
                "warn",
                "audit.md 缺失：未经审计或未放行，终审责任在主编",
            )
        )
    else:
        try:
            audit_text = audit_md.read_text(encoding="utf-8")
        except OSError:
            rows.append(
                (
                    "warn",
                    "audit.md 无法读取：未经审计或未放行，终审责任在主编",
                )
            )
        else:
            if "放行" in audit_text:
                rows.append(("ok", "audit.md 含「放行」"))
            else:
                rows.append(
                    (
                        "warn",
                        "audit.md 未含「放行」：未经审计或未放行，终审责任在主编",
                    )
                )

    if not cover_jpg.is_file():
        rows.append(("fail", "cover.jpg 缺失"))
        hard_fail = True
    else:
        try:
            cw, ch = read_image_size(cover_jpg)
        except Exception as e:
            rows.append(("fail", f"cover.jpg 无法读取尺寸：{e}"))
            hard_fail = True
        else:
            if (cw, ch) != (900, 383):
                rows.append(
                    (
                        "warn",
                        f"cover.jpg 尺寸为 {cw}×{ch}（建议 900×383）",
                    )
                )
            else:
                rows.append(("ok", "cover.jpg 存在（900×383）"))

    local_imgs = _collect_local_image_refs(draft_text) if draft_text else []
    missing_imgs: list[str] = []
    for name in local_imgs:
        if not (asset_root / name).is_file():
            if name not in missing_imgs:
                missing_imgs.append(name)
    if missing_imgs:
        rows.append(
            (
                "fail",
                "正文本地图缺失：" + "、".join(missing_imgs),
            )
        )
        hard_fail = True
    else:
        rows.append(
            (
                "ok",
                f"正文本地图齐全（{len(local_imgs)} 张引用）",
            )
        )

    cred_status, cred_hard, cred_msg = _check_credentials(cred_path)
    rows.append((cred_status if cred_status != "ok" else "ok", cred_msg))
    if cred_hard:
        hard_fail = True

    gw_base, gw_token, _gw_src = _load_gateway_config(root)
    gw_ok = bool(gw_base and gw_token)
    if gw_ok:
        rows.append(("ok", "网关配置齐全（base_url + bearer_token）"))
    else:
        if do_go:
            rows.append(
                (
                    "fail",
                    "网关配置缺失：请设 WECHAT_GATEWAY_* 或 root/gateway.json",
                )
            )
            hard_fail = True
        else:
            rows.append(
                (
                    "warn",
                    "网关配置缺失（dry-run 可继续；--go 前需配置）",
                )
            )

    title_cli = getattr(args, "title", None)
    title = (str(title_cli).strip() if title_cli is not None else "") or ""
    if not title and draft_text:
        title = _extract_title_from_draft(draft_text)
    if not title:
        rows.append(("fail", "标题不可得：请给 --title 或在 draft.md 写一级标题"))
        hard_fail = True
    else:
        if len(title) > 64:
            rows.append(("warn", f"标题超过 64 字符（当前 {len(title)}）"))
        else:
            rows.append(("ok", f"标题可得：{title}"))

    # 打印检查表
    env.print_header(f"发布预检 · {slug} / {topic}")
    mark_map = {"ok": "✓", "warn": "⚠", "fail": "✗"}
    for mark, text in rows:
        symbol = mark_map.get(mark, "•")
        print(f"{symbol} {text}")

    if hard_fail:
        env.print_error("预检未通过，已中止（未渲染、未触网）")
        return 1

    # --- 渲染（检查全过；dry-run 也渲染）---
    output_html.parent.mkdir(parents=True, exist_ok=True)
    try:
        render_markdown_file_to_wechat_html(
            draft_md,
            output_html_path=output_html,
            title=title,
        )
    except Exception as e:
        env.print_error(f"渲染失败：{e}")
        return 1

    env.print_success(f"已渲染：{output_html.resolve()}")

    author_cli = getattr(args, "author", None)
    if author_cli is not None and str(author_cli).strip() != "":
        author = str(author_cli).strip()
    else:
        author = str(acct_meta.get("name") or "")

    digest_cli = getattr(args, "digest", None)
    digest = str(digest_cli).strip() if digest_cli is not None else ""
    source_url_cli = getattr(args, "source_url", None)
    source_url = str(source_url_cli).strip() if source_url_cli is not None else ""

    n_content_images = len(local_imgs)

    if not do_go:
        env.print_header("动作清单（dry-run，零网络）")
        env.print_step(f"将上传 {n_content_images} 张正文图")
        env.print_step("上传封面 cover.jpg → thumb")
        digest_desc = digest if digest else "微信自动"
        env.print_step(
            "建草稿（草稿箱止步）",
            f"标题={title} · 作者={author or '（空）'} · 摘要={digest_desc}",
        )
        env.print_info(f"渲染产物：{output_html.resolve()}")
        print("\n确认无误后加 --go 执行真实建草稿")
        return 0

    # --- --go：惰性导入 preparer，触网 ---
    try:
        from wechat_api_prep_lib import WechatApiPreparer  # noqa: WPS433
    except Exception as e:
        env.print_error(f"加载发布引擎失败：{e}")
        return 1

    try:
        preparer = WechatApiPreparer(
            config_path=str(cred_path),
            gateway_base_url=gw_base,
            gateway_bearer_token=gw_token,
        )
        result = preparer.prepare_html_file(
            html_path=output_html,
            cover_image_path=cover_jpg,
            output_html_path=output_html,
            asset_root=asset_root,
        )
        content = output_html.read_text(encoding="utf-8")
        pic_crop_235_1, pic_crop_1_1 = build_cover_crop_fields(cover_jpg)
        thumb_media_id = str(result.get("thumb_media_id") or "")
        article = build_draft_article(
            title=title,
            author=author,
            content=content,
            thumb_media_id=thumb_media_id,
            digest=digest,
            content_source_url=source_url,
            need_open_comment=1,
            only_fans_can_comment=0,
            pic_crop_235_1=pic_crop_235_1,
            pic_crop_1_1=pic_crop_1_1,
        )
        resp = preparer.gateway_client.add_draft(
            app_id=preparer.app_id,
            app_secret=preparer.app_secret,
            articles=[article],
        )
    except Exception as e:
        env.print_error(f"建草稿失败：{e}")
        return 1

    if not isinstance(resp, dict):
        env.print_error("建草稿响应异常：非 JSON 对象")
        return 1
    media_id = resp.get("media_id")
    if not media_id:
        snippet = json.dumps(resp, ensure_ascii=False)
        if len(snippet) > 500:
            snippet = snippet[:500]
        env.print_error(f"建草稿响应缺少 media_id：{snippet}")
        return 1

    drafted_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    gateway_host = urlparse(gw_base).hostname or ""
    content_image_count = int(result.get("content_image_count") or n_content_images)

    ledger: dict[str, Any] = {
        "topic_slug": topic,
        "title": title,
        "author": author,
        "digest": digest,
        "draft_media_id": str(media_id),
        "thumb_media_id": thumb_media_id,
        "drafted_at": drafted_at,
        "content_image_count": content_image_count,
        "gateway_host": gateway_host,
    }
    try:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(
            json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as e:
        env.print_error(f"草稿已入箱但台账写入失败：{e}")
        env.print_info(f"media_id={media_id}")
        return 1

    env.print_success(f"草稿已入箱 · media_id={media_id}")
    env.print_info("下一步在公众号后台：预览 → 群发（人操作）")
    env.print_info(f"台账：{ledger_path.resolve()}")
    return 0
