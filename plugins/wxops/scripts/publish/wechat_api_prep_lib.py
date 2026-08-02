#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# GEB-L3
# Input: config_path（含 app_id/app_secret 的 JSON）+ gateway url/token（参数或环境变量）
# Output: prepare_html_file() → 正文图上传替换微信 URL + 封面 thumb_media_id
# Pos: wxops publish 站引擎层 · 复制自 hermes wechat-publisher
#
# 来源: /Users/dw/Desktop/claude/services/wechat-publisher/scripts/wechat_api_prep_lib.py
# 复制日期: 2026-08-01（wxops P5 · issue #43）；仅加本头注，行为零变更，hermes 原文件未动
# 凭证注入点: WechatApiPreparer(config_path=...) —— wxops 编排层传
#   accounts/<slug>/credentials/wechat.json，即完成按账号凭证隔离；
#   本文件不感知多账号，隔离责任在调用方（publish_cmd）。
# 依赖: 同目录 wechat_gateway_client（sys.path 注入，复制后同目录布局保持有效）
"""独立的公众号 API 预处理能力。"""

from __future__ import annotations

import io
import json
import mimetypes
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote

import requests

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from wechat_gateway_client import WechatGatewayClient


class WechatApiPreparer:
    """公众号 API 预处理器。"""

    def __init__(
        self,
        config_path: str,
        gateway_base_url: str = "",
        gateway_bearer_token: str = "",
    ):
        self.config_path = Path(config_path).expanduser().resolve()
        self.config = self._load_config()
        self.app_id = str(self.config.get("app_id", "")).strip()
        self.app_secret = str(self.config.get("app_secret", "")).strip()

        if not self.app_id or not self.app_secret:
            raise ValueError("公众号配置文件必须包含 app_id 和 app_secret")

        self.gateway_base_url = str(gateway_base_url or os.getenv("WECHAT_GATEWAY_BASE_URL", "")).strip()
        self.gateway_bearer_token = str(
            gateway_bearer_token or os.getenv("WECHAT_GATEWAY_BEARER_TOKEN", "")
        ).strip()
        self.gateway_client = WechatGatewayClient(
            base_url=self.gateway_base_url,
            bearer_token=self.gateway_bearer_token,
        )

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"未找到公众号配置文件: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        if not isinstance(config, dict):
            raise ValueError("公众号配置文件内容必须是 JSON 对象")

        return config

    def _extract_images_from_html(self, html_content: str) -> List[Dict[str, str]]:
        img_tag_pattern = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
        data_src_pattern = re.compile(
            r'\bdata-src\s*=\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s>]+))',
            re.IGNORECASE,
        )
        src_pattern = re.compile(
            r'(?<!data-)src\s*=\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s>]+))',
            re.IGNORECASE,
        )

        images: List[Dict[str, str]] = []
        for match in img_tag_pattern.finditer(html_content):
            full_tag = match.group(0)
            data_src_match = data_src_pattern.search(full_tag)
            src_match = src_pattern.search(full_tag)

            src_value = None
            if data_src_match:
                src_value = next((group for group in data_src_match.groups() if group), None)
            elif src_match:
                src_value = next((group for group in src_match.groups() if group), None)

            if src_value:
                images.append({"src": src_value, "full_tag": full_tag})

        return images

    def _remove_leading_h1(self, html_content: str) -> Tuple[str, bool]:
        body_leading_h1_pattern = re.compile(
            r"(<body[^>]*>\s*)(<h1\b[^>]*>.*?</h1>\s*)",
            re.IGNORECASE | re.DOTALL,
        )
        body_match = body_leading_h1_pattern.search(html_content)
        if body_match:
            updated_html = html_content[:body_match.start(2)] + html_content[body_match.end(2):]
            return updated_html, True

        leading_h1_pattern = re.compile(r"^\s*(<h1\b[^>]*>.*?</h1>\s*)", re.IGNORECASE | re.DOTALL)
        leading_match = leading_h1_pattern.search(html_content)
        if leading_match:
            updated_html = html_content[:leading_match.start(1)] + html_content[leading_match.end(1):]
            return updated_html, True

        return html_content, False

    def _resolve_image_path(self, src_value: str, asset_root: Path) -> Optional[Path]:
        normalized_src = unquote(src_value.strip()).split("#")[0].split("?")[0].strip()
        if not normalized_src:
            return None
        if normalized_src.startswith(("http://", "https://", "//")):
            return None

        clean_src = normalized_src.lstrip("./").lstrip("/")
        candidate_paths = [
            asset_root / clean_src,
            asset_root / Path(clean_src).name,
            asset_root / "images" / Path(clean_src).name,
            asset_root / "image" / Path(clean_src).name,
        ]

        if clean_src.startswith("images/"):
            candidate_paths.append(asset_root / clean_src.replace("images/", "", 1))
        if clean_src.startswith("image/"):
            candidate_paths.append(asset_root / clean_src.replace("image/", "", 1))

        for candidate_path in candidate_paths:
            resolved_candidate = candidate_path.resolve()
            if resolved_candidate.exists() and resolved_candidate.is_file():
                return resolved_candidate

        return None

    def _prepare_content_image_for_upload(
        self,
        image_path: Path,
    ) -> Tuple[Optional[Path], Optional[str], Optional[Path]]:
        suffix = image_path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            return image_path, "image/jpeg", None
        if suffix == ".png":
            return image_path, "image/png", None
        if suffix == ".gif":
            return image_path, "image/gif", None

        try:
            from PIL import Image

            with Image.open(image_path) as image_obj:
                image_format = (image_obj.format or "").upper()
                if image_format == "JPEG":
                    return image_path, "image/jpeg", None
                if image_format == "PNG":
                    return image_path, "image/png", None
                if image_format == "GIF":
                    return image_path, "image/gif", None

                converted_path = image_path.parent / f"{image_path.stem}_wechat_upload.jpg"
                converted_image = image_obj.convert("RGB")
                converted_image.save(converted_path, format="JPEG", quality=92, optimize=True)
                return converted_path, "image/jpeg", converted_path
        except ImportError:
            guessed_mime_type, _encoding = mimetypes.guess_type(str(image_path))
            if guessed_mime_type in {"image/jpeg", "image/png", "image/gif"}:
                return image_path, guessed_mime_type, None
        except Exception:
            return None, None, None

        return None, None, None

    def _upload_content_image(self, image_path: Path) -> str:
        upload_path, _mime_type, temp_path = self._prepare_content_image_for_upload(image_path)
        if not upload_path:
            raise RuntimeError(f"正文图片格式不支持或无法读取: {image_path.name}")

        try:
            upload_result = self.gateway_client.upload_material(
                app_id=self.app_id,
                app_secret=self.app_secret,
                upload_kind="content_image",
                file_path=upload_path,
            )
            return str(upload_result["url"])
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def _upload_thumb(self, image_path: Path) -> str:
        upload_result = self.gateway_client.upload_material(
            app_id=self.app_id,
            app_secret=self.app_secret,
            upload_kind="thumb",
            file_path=image_path,
        )
        return str(upload_result["media_id"])

    def _upload_permanent_image(self, image_path: Path) -> str:
        """上传图片消息所需的永久图片素材。"""
        upload_result = self.gateway_client.upload_material(
            app_id=self.app_id,
            app_secret=self.app_secret,
            upload_kind="thumb",
            file_path=image_path,
        )
        return str(upload_result["media_id"])

    def prepare_newspic_images(self, image_paths: List[Path]) -> List[str]:
        """上传图片消息图片，并返回微信永久素材 media_id 列表。"""
        if not image_paths:
            raise ValueError("图片消息至少需要 1 张图片")
        if len(image_paths) > 20:
            raise ValueError("图片消息最多支持 20 张图片")

        media_ids: List[str] = []
        for image_path in image_paths:
            resolved_image_path = Path(image_path).expanduser().resolve()
            if not resolved_image_path.exists():
                raise FileNotFoundError(f"未找到图片消息图片: {resolved_image_path}")
            media_ids.append(self._upload_permanent_image(resolved_image_path))
        return media_ids

    def _replace_content_images_with_wechat_urls(
        self,
        html_content: str,
        images: List[Dict[str, str]],
        asset_root: Path,
    ) -> Tuple[str, int, int]:
        updated_html = html_content
        success_count = 0
        failed_count = 0

        for image_info in images:
            src_value = image_info["src"]
            full_tag = image_info["full_tag"]

            if "mmbiz.qpic.cn" in src_value or "weixin.qq.com" in src_value:
                continue

            local_image_path = self._resolve_image_path(src_value, asset_root)
            if local_image_path is None:
                raise RuntimeError(f"未找到正文图片: {src_value}")

            try:
                wechat_url = self._upload_content_image(local_image_path)
            except Exception as error:
                raise RuntimeError(f"正文图片上传失败: {local_image_path.name}: {error}") from error

            updated_html = updated_html.replace(full_tag, full_tag.replace(src_value, wechat_url))
            success_count += 1

        return updated_html, success_count, failed_count

    def _save_processed_html(self, html_path: Path, html_content: str) -> None:
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_content, encoding="utf-8")

    def prepare_html_file(
        self,
        html_path: Path,
        cover_image_path: Path,
        output_html_path: Optional[Path] = None,
        asset_root: Optional[Path] = None,
    ) -> Dict[str, Any]:
        resolved_html_path = Path(html_path).expanduser().resolve()
        resolved_cover_image_path = Path(cover_image_path).expanduser().resolve()
        final_output_html_path = (
            Path(output_html_path).expanduser().resolve()
            if output_html_path is not None
            else resolved_html_path
        )
        final_asset_root = (
            Path(asset_root).expanduser().resolve()
            if asset_root is not None
            else resolved_html_path.parent
        )

        if not resolved_html_path.exists():
            raise FileNotFoundError(f"未找到 HTML 文件: {resolved_html_path}")
        if not resolved_cover_image_path.exists():
            raise FileNotFoundError(f"未找到封面图: {resolved_cover_image_path}")
        if not final_asset_root.exists():
            raise FileNotFoundError(f"未找到正文图片资源目录: {final_asset_root}")

        html_content = resolved_html_path.read_text(encoding="utf-8")
        html_content, leading_h1_removed = self._remove_leading_h1(html_content)
        images = self._extract_images_from_html(html_content)
        html_content, success_count, failed_count = self._replace_content_images_with_wechat_urls(
            html_content=html_content,
            images=images,
            asset_root=final_asset_root,
        )

        thumb_media_id = self._upload_thumb(resolved_cover_image_path)
        self._save_processed_html(final_output_html_path, html_content)

        return {
            "html_path": str(final_output_html_path),
            "source_html_path": str(resolved_html_path),
            "asset_root": str(final_asset_root),
            "thumb_media_id": thumb_media_id,
            "cover_image_path": str(resolved_cover_image_path),
            "content_image_count": len(images),
            "content_image_success_count": success_count,
            "content_image_failed_count": failed_count,
            "leading_h1_removed": leading_h1_removed,
        }
