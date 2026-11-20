# 企业微信渠道

> 2026-11-20 在一台 Linux 服务器上实测：wecom-cli 1.3.4、@wecom/aibot-node-sdk 1.0.7。

## 1. 为什么要一个网关子进程

- `wecom-cli` 只能查和发，没有事件订阅命令，收不了消息。
- 收消息用企微智能机器人的**长连接**：`wss://openws.work.weixin.qq.com`，用 Bot ID 和 Secret 认证，不需要公网回调地址。官方 SDK 是 Node 的 `@wecom/aibot-node-sdk`。
- 回复要用收到消息时的 `req_id`，走同一条连接，所以收和回都放在 `wecom_gateway.mjs` 里。`bridge.py` 用它的 stdin 发指令、读它的 stdout 收事件，跟 `lark-cli event consume` 的用法一样。

```
企微 ──长连接── wecom_gateway.mjs ──NDJSON──┐
飞书 ──lark-cli event consume ──NDJSON──────┤
                                            ▼
                                  bridge.py（统一事件 → 会话排队 → claude -p）
                                            │
              回复按 ev["channel"] 走原渠道 ◄┘
```

## 2. 开通

1. 装 CLI 并扫码授权：`npm i -g @wecom/cli`，再 `wecom-cli auth init`。服务器上没有浏览器时加 `--noninteractive --no-browser --output-qrcode <png 路径>`，把打印出的链接交给主人用企业微信打开扫码。二维码 5 分钟过期（`QrTimeout`），过期重新运行；`--output-qrcode` 的文件已存在会报错，先删旧文件。
2. 扫码会建好一个智能机器人，Bot ID 和 Secret 加密存在 `~/.config/wecom/`。网关默认直接读这里（`channels.wecom.credentials = "wecom-cli"`）。
   - 这是 wecom-cli 的内部格式，升级后可能变。读失败时网关会报错退出，改用 JSON 凭证文件：`{"bot_id": "...", "secret": "..."}`，权限 0600，路径填进 `credentials`。
   - 密钥只存在系统 keyring（不在 `.encryption_key` 文件里）时也读不到，同样改用 JSON 文件。
3. 在 `config.json` 里打开 `channels.wecom.enabled`，先把 `owner_userid` 随便填一个占位值，运行 `scaffold.py`（会装好 SDK），启动服务。
4. 主人在企微里私聊机器人一句，日志 `recv` 行里的发送人就是主人的 userid。填进 `owner_userid`，重启服务。
   > **注意**：`wecom-cli identity whoami` 显示的 ID 是加密过的，跟长连接消息里的 userid 不是一个值，不能拿来填。

## 3. 平台限制（影响设计）

| 限制 | 影响 |
|---|---|
| 一个机器人同时只能有一条长连接，新连接会把旧的挤掉（服务端先推 `disconnected_event`） | 测试前先停服务；网关被挤掉后退出码 3，bridge 等 5 分钟再重连，避免两边互相挤 |
| 群里只推 @ 机器人的消息 | 企微没有旁听；群里也没有前文，引用的消息随消息带来 |
| 流式回复超过 6 分钟没更新就过期（errcode 846608） | 网关先回“思考中”，结束时更新成结果；过期就改为主动推送到原会话（官方 OpenClaw 插件同样处理） |
| Markdown 最长 20480 字节（UTF-8） | bridge 按字节截断 |
| 图片、文件的下载地址 5 分钟内有效，内容 AES 加密 | 网关收到就下载解密，存到实例的 `inbox/`，3 天后删；主人私聊收到的放 `inbox/private/`，别的会话读不了 |
| 机器人主动发消息只能发给最近有过往来的会话 | 守则写明；要私聊主人时先 `wecom-cli message aibot sessions list` |
| SDK 默认重连 10 次就放弃 | 网关设为无限重连 |

## 4. wecom-cli 的权限

wecom-cli 用“机器人代主人”的授权调接口，能读主人的邮件、文档、日程、微盘。只要本机装了它，**飞书渠道的会话也能调用**，所以 `hooks/wecom_guard.py` 不论是否启用企微都挂上：

- 所有人：不能动授权（`auth`），不能以主人名义发企微消息（`message send`），不能发、回、转邮件，不能读 `~/.config/wecom`。
- 主人本人发的：其余命令可用。
- 其他人发的：只能用 `wecom-cli message aibot`（机器人发消息）和 `wecom-cli contact`；`identity.others` 为 `bot_read_im` 时还能读企微聊天记录（`wecom-cli chat`）。
- 跨 IM 读取关闭时，飞书来的会话不能用 `wecom-cli chat`，见 boundary.md。命令里出现别的 wecom 调用写法（`$(which wecom-cli)`、二进制全路径）一律拦。

## 5. 缓存

企微会话和飞书会话用同一套 `claude` 参数、同一份守则、同一句开场白，缓存前缀共享。渠道差异只在每条消息开头的消息头（`[企微消息]`），在缓存前缀之后。不要为企微另写一份守则：守则不同，两个渠道就各写一份缓存。
