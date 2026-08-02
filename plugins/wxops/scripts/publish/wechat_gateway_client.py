#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# GEB-L3
# Input: gateway base_url + bearer token（构造）；app_id/app_secret 按调用传参
# Output: upload_material() 上传素材 / add_draft() 建草稿（网关 JSON 响应）
# Pos: wxops publish 站引擎层 · 复制自 hermes wechat-publisher
#
# 来源: /Users/dw/Desktop/claude/services/wechat-publisher/scripts/wechat_gateway_client.py
# 复制日期: 2026-08-01（wxops P5 · issue #43）；仅加本头注，行为零变更，hermes 原文件未动
# 上游已知状态保留: trust_env=False（固定 IP 网关在国内，不走系统代理）；
#   verify=False（网关证书过期临时禁用验证，待上游续期，非本插件可修）
# 红线注记: 本 client 仅有 upload_material / add_draft 两个方法，无任何
#   发布（freepublish）/ 群发（mass）接口——「草稿箱止步」的接口面积保证，
#   不得在本文件新增发布类方法。
"""微信公众号固定 IP 网关客户端。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import requests


class WechatGatewayClient:
    """调用固定 IP 微信 API 网关。"""

    def __init__(self, base_url: str, bearer_token: str):
        self.base_url = str(base_url).rstrip("/")
        self.bearer_token = str(bearer_token).strip()
        if not self.base_url:
            raise ValueError("gateway_base_url 不能为空")
        if not self.bearer_token:
            raise ValueError("gateway_bearer_token 不能为空")
        self.session = requests.Session()
        # 公众号固定 IP 网关在国内，不能继承 Hermes/Grok 的系统代理。
        self.session.trust_env = False
        # 网关证书已过期，临时禁用验证，等待证书续期
        self.session.verify = False

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.bearer_token}"}

    def _raise_for_gateway_error(self, response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            response_text = response.text.strip()
            if len(response_text) > 500:
                response_text = f"{response_text[:500]}..."
            raise requests.HTTPError(
                f"{error}; response_body={response_text}",
                response=response,
            ) from error

    def upload_material(
        self,
        app_id: str,
        app_secret: str,
        upload_kind: str,
        file_path: Path,
    ) -> Dict[str, Any]:
        resolved_file_path = Path(file_path).expanduser().resolve()
        if not resolved_file_path.exists():
            raise FileNotFoundError(f"未找到待上传文件: {resolved_file_path}")

        with open(resolved_file_path, "rb") as upload_file:
            response = self.session.post(
                f"{self.base_url}/v1/wechat/material/upload",
                headers=self._headers(),
                data={
                    "app_id": app_id,
                    "app_secret": app_secret,
                    "upload_kind": upload_kind,
                },
                files={"file": (resolved_file_path.name, upload_file)},
                timeout=120,
            )
        self._raise_for_gateway_error(response)
        return response.json()

    def add_draft(
        self,
        app_id: str,
        app_secret: str,
        articles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/v1/wechat/draft/add",
            headers={**self._headers(), "Content-Type": "application/json"},
            json={
                "app_id": app_id,
                "app_secret": app_secret,
                "articles": articles,
            },
            timeout=120,
        )
        self._raise_for_gateway_error(response)
        return response.json()
