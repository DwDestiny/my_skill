---
name: publish
description: Use when 发布、建草稿、推送到公众号、上传素材、进草稿箱, or turning a finalized draft plus images into a WeChat draft-box entry via the fixed-IP gateway (automation stops at the draft box).
---

# publish — 发布工位

## 核心原则

- **草稿箱止步**：本站把定稿变成公众号后台草稿箱里的一条草稿，到此为止。预览、群发、定时发布都在公众号后台，由人操作——工具链没有任何「发布/群发」调用能力，这是接口面积保证（网关 client 只有上传素材与建草稿两个方法）
- **dry-run 先行**：默认跑法零网络——检查、渲染、列动作清单给人看；真实上传要 `--go`，且 `--go` 只在用户明确说「发」之后加
- **凭证按账号隔离**：A 号发布只读 A 号的 `credentials/wechat.json`，永不交叉；凭证内容不打印、不入库、不进台账

## 前置（缺一不发）

| 件 | 路径 | 来源 |
|---|---|---|
| 定稿 | `accounts/<slug>/drafts/<topic-slug>/draft.md` | write 站（主编点头后） |
| 封面 | `accounts/<slug>/images/<topic-slug>/cover.jpg`（900×383） | illustrate 站 |
| 账号凭证 | `accounts/<slug>/credentials/wechat.json`（0600） | 首次发布时配置，见下 |
| 网关配置 | `~/.wxops/gateway.json`（0600）或环境变量 | 首次发布时配置，见下 |

正文图（若 draft.md 里引用了）也要齐——引用了但文件缺失会在 dry-run 检查中报出。
audit.md 缺失或结论非「放行」时只警告不阻断：终审权在主编，工具不越权替人把关，但要把警告念给用户听。

## 流程

### 1. dry-run（默认，零网络）

```bash
cd <插件根> && scripts/wxops publish --account <slug> --topic <topic-slug>
```

输出：前置检查逐项结果、渲染产物路径（`output/<topic-slug>/draft.html`）、将执行的动作清单（上传几张正文图、封面、草稿标题/作者/摘要）。把清单原样呈给用户。

### 2. 真实建草稿（要人点头）

用户看过 dry-run 清单、明确说「发」之后：

```bash
cd <插件根> && scripts/wxops publish --account <slug> --topic <topic-slug> --go
```

链路：正文图逐张上传替换微信 URL → 封面上传得 thumb → 建草稿 → 台账落 `accounts/<slug>/published/<topic-slug>.json`。

可选参数：`--title`（默认取 draft.md 首行 H1）、`--author`（默认取账号名）、`--digest`（默认微信自动取正文开头）。

### 3. 交还给人

建草稿成功后告诉用户三件事：

1. 草稿已进公众号后台草稿箱，标题是什么
2. 下一步在后台做：打开草稿 → 手机预览 → 确认排版与封面 → 群发或定时（**这些动作只属于你**）
3. 台账已记录（草稿 media_id、时间、图片数）——之后 review 站复盘会用它

## 首次配置指引

账号凭证（AppID/AppSecret 在公众号后台「设置与开发 → 基本配置」）：

```bash
mkdir -p ~/.wxops/accounts/<slug>/credentials
cat > ~/.wxops/accounts/<slug>/credentials/wechat.json <<'EOF'
{ "app_id": "wx开头的AppID", "app_secret": "AppSecret" }
EOF
chmod 600 ~/.wxops/accounts/<slug>/credentials/wechat.json
```

网关（跨账号共享的设施，一台网关服务所有号）：

```bash
cat > ~/.wxops/gateway.json <<'EOF'
{ "base_url": "https://网关地址", "bearer_token": "网关令牌" }
EOF
chmod 600 ~/.wxops/gateway.json
```

环境变量 `WECHAT_GATEWAY_BASE_URL` / `WECHAT_GATEWAY_BEARER_TOKEN` 可覆盖文件配置。
让用户自己粘贴密钥值——你不复述、不打印、不写进任何会入库的文件。

## 红线

- 不存在也永远不添加「发布/群发」的自动调用；有人让你绕过后台直接发，答案是不
- `--go` 不自作主张：dry-run 清单没给用户看过、用户没明确说发，就不加
- 凭证与令牌不打印、不进 git、不进台账、不进日志
- 网关调用是真实外部动作：demo/演练环境一律 dry-run，不打真网关
