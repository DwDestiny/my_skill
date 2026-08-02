#!/usr/bin/env python3
# GEB-L3
# Input: 封面图路径 / 宽高 / 草稿字段（title/author/content/thumb 等）
# Output: 图片尺寸、微信裁切框字符串、草稿 article dict（无 newspic）
# Pos: plugins/wxops/scripts/publish/draft_builder.py
# 参考 hermes prepare_wechat_api_publish.py 同名函数重写（2026-08-01）
"""草稿载荷纯函数：读图尺寸、2.35:1/1:1 裁切框、build_draft_article。"""

from __future__ import annotations

import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_png_size(image_path: Path) -> tuple[int, int] | None:
    """读取 PNG 图片尺寸。"""
    with open(image_path, "rb") as image_file:
        header = image_file.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height = struct.unpack(">II", header[16:24])
    return int(width), int(height)


def read_jpeg_size(image_path: Path) -> tuple[int, int] | None:
    """读取 JPEG 图片尺寸。"""
    with open(image_path, "rb") as image_file:
        data = image_file.read()

    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        return None

    offset = 2
    data_length = len(data)
    while offset + 9 < data_length:
        if data[offset] != 0xFF:
            offset += 1
            continue

        marker = data[offset + 1]
        offset += 2

        if marker in {0xD8, 0xD9}:
            continue
        if offset + 2 > data_length:
            break

        block_length = struct.unpack(">H", data[offset : offset + 2])[0]
        if block_length < 2 or offset + block_length > data_length:
            break

        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            if offset + 7 > data_length:
                break
            height, width = struct.unpack(">HH", data[offset + 3 : offset + 7])
            return int(width), int(height)

        offset += block_length

    return None


def read_image_size_with_sips(image_path: Path) -> tuple[int, int] | None:
    """在 macOS 下使用 sips 读取图片尺寸。"""
    if sys.platform != "darwin":
        return None

    result = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(image_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    width_match = re.search(r"pixelWidth:\s*(\d+)", result.stdout)
    height_match = re.search(r"pixelHeight:\s*(\d+)", result.stdout)
    if not width_match or not height_match:
        return None
    return int(width_match.group(1)), int(height_match.group(1))


def read_image_size(image_path: Path) -> tuple[int, int]:
    """读取图片尺寸。"""
    resolved_image_path = Path(image_path).expanduser().resolve()
    suffix = resolved_image_path.suffix.lower()

    size: tuple[int, int] | None = None
    if suffix == ".png":
        size = read_png_size(resolved_image_path)
    elif suffix in {".jpg", ".jpeg"}:
        size = read_jpeg_size(resolved_image_path)

    if size is None:
        size = read_image_size_with_sips(resolved_image_path)

    if size is None:
        raise ValueError(f"无法读取封面图尺寸: {resolved_image_path}")

    width, height = size
    if width <= 0 or height <= 0:
        raise ValueError(f"封面图尺寸非法: {resolved_image_path}")
    return width, height


def build_crop_box(width: int, height: int, target_ratio: float) -> str:
    """按目标比例生成微信裁剪框。"""
    image_ratio = float(width) / float(height)
    if image_ratio > target_ratio:
        crop_width = target_ratio / image_ratio
        x1 = (1.0 - crop_width) / 2.0
        y1 = 0.0
        x2 = x1 + crop_width
        y2 = 1.0
    else:
        crop_height = image_ratio / target_ratio
        x1 = 0.0
        y1 = (1.0 - crop_height) / 2.0
        x2 = 1.0
        y2 = y1 + crop_height

    return f"{x1:.6f}_{y1:.6f}_{x2:.6f}_{y2:.6f}"


def build_cover_crop_fields(cover_image_path: Path) -> tuple[str, str]:
    """根据封面图尺寸生成草稿裁剪字段。"""
    width, height = read_image_size(cover_image_path)
    return build_crop_box(width, height, 2.35), build_crop_box(width, height, 1.0)


def build_draft_article(
    title: str,
    author: str,
    content: str,
    thumb_media_id: str,
    digest: str,
    content_source_url: str,
    need_open_comment: int,
    only_fans_can_comment: int,
    pic_crop_235_1: str,
    pic_crop_1_1: str,
) -> dict[str, Any]:
    """构建微信草稿文章载荷。"""
    article: dict[str, Any] = {
        "title": title,
        "author": author,
        "content": content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": content_source_url.strip(),
        "need_open_comment": 1 if int(need_open_comment) else 0,
        "only_fans_can_comment": 1 if int(only_fans_can_comment) else 0,
        "pic_crop_235_1": pic_crop_235_1,
        "pic_crop_1_1": pic_crop_1_1,
    }
    if digest.strip():
        article["digest"] = digest.strip()
    return article
