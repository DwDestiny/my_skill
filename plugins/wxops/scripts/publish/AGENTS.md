# scripts/publish — 发布引擎层（L2）

## 模块定位

publish 站的引擎层：Markdown → 公众号 HTML → 网关上传素材 + 建草稿。
多账号编排不在这里——本层不感知账号概念，凭证隔离的责任在调用方 `scripts/cli/publish_cmd.py`。

## 文件清单

| 文件 | 来源 | 职责 |
|---|---|---|
| `wechat_html_renderer_lib.py` | 复制自 hermes（2026-08-01，见文件头注） | Markdown → 内联样式公众号 HTML，纯函数零网络 |
| `wechat_api_prep_lib.py` | 复制自 hermes（同上） | 正文图上传替换微信 URL + 封面 thumb；凭证经 `config_path` 注入 |
| `wechat_gateway_client.py` | 复制自 hermes（同上） | 网关 HTTP client，仅 `upload_material` / `add_draft` 两方法 |
| `draft_builder.py` | wxops 新写（参考 hermes prepare CLI 同名函数） | 图片尺寸读取、2.35:1 / 1:1 裁切框、草稿 article payload 构造 |

## 铁律

- **接口面积红线**：`wechat_gateway_client.py` 永不新增发布（freepublish）/ 群发（mass）类方法——「草稿箱止步」靠这里保证，测试有断言盯着
- **复制件零漂移**：三个复制 lib 只允许头注差异，行为改动必须先在文件头注记录原因与日期，并评估是否需要回馈 hermes 上游（hermes 原文件永远只读）
- **凭证纪律**：AppID/AppSecret/access token/gateway bearer token 一律不打印、不写日志、不进台账、不进 git
- **上游已知状态**（复制时保留，不在本插件修）：client 的 `trust_env=False`（国内固定 IP 网关不走系统代理）、`verify=False`(网关证书过期临时禁用验证，待上游续期)
- **排版主题现状**：renderer 样式为固定暖橙主题（源自麦总玩 AI 号），按账号视觉 tokens 参数化留待后续版本

## 调用编排（生产验证过的顺序，来自 hermes prepare CLI）

```
WechatApiPreparer(config_path=accounts/<slug>/credentials/wechat.json, gateway_base_url, gateway_bearer_token)
  → prepare_html_file(html, cover, output, asset_root)   # 正文图上传 + 封面 thumb
  → 读处理后 HTML 全文作为 content（含 DOCTYPE 的整份文件，微信端接受）
  → build_cover_crop_fields(cover) → pic_crop_235_1 / pic_crop_1_1
  → build_draft_article(...) → gateway_client.add_draft(articles=[...])
  → 响应 media_id → 发布台账
```

## 依赖方向

`cli/publish_cmd.py` → 本层四件；本层内部 `wechat_api_prep_lib` → `wechat_gateway_client`（同目录 sys.path 注入）。
本层不依赖 `cli/`、不读 `~/.wxops` 布局、不解析账号。

## 测试约定

- 一律 `WXOPS_HOME=tmp_path`，绝不碰真实 `~/.wxops`
- 网关一律 mock（monkeypatch `WechatGatewayClient` 方法），CI 零真实网络
- dry-run 用例要装「网络炸弹」：monkeypatch requests 使任何真实调用直接 fail
