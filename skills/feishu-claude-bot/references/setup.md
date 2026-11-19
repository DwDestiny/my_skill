# 安装：运行位置、飞书应用、后台配置

## 1. 跑在服务器还是本机

| | 服务器（Linux VPS） | 本机（Mac 笔记本） |
|---|---|---|
| 在线 | 常驻。用 systemd 用户服务，加 `loginctl enable-linger` 后不登录也跑 | 合盖或睡眠就收不到消息；醒来后 10 分钟以前的消息直接跳过 |
| 能读什么 | 服务器上的代码仓和知识库 | 本机全部文件，私密面更大，`private.paths` 要填得更全 |
| 服务 | scaffold 生成 `fcb-<目录名>.service` | scaffold 生成 launchd `com.fcb-<目录名>.plist` |
| 登录态 | 服务器上的 Claude Code 登录态 | 本机的 Claude Code 登录态 |

推荐服务器。本机适合先试一试。

> **警告**：两种都会长期使用这台机器的 Claude 登录态和额度。用户有“登录态只能在哪些机器上用”的规则时，先对照规则，不符合就停下。

本机注意：
- 要让 Mac 不睡：`系统设置 → 电池 → 选项` 里关自动睡眠，或用 `caffeinate -s`。
- launchd 的 PATH 很短，scaffold 已把 `lark-cli` 和 `claude` 所在目录写进 plist。换了安装位置就重跑 scaffold。

## 2. 飞书应用：复用还是新建

先运行 `lark-cli config show` 和 `lark-cli auth status` 看有没有现成配置。

**复用现有应用**，满足以下全部条件才行：
1. 应用是“企业自建应用”，能开机器人能力。
2. 没有别的程序在用这个应用收 `im.message.receive_v1`（OpenClaw、Hermes、另一个机器人服务）。同一应用的事件只推给一个接收方，抢到的一方收，另一方静悄悄丢消息。
3. 用户接受机器人的名字和头像就是这个应用的名字和头像。改名在后台“应用信息”里改，改完要发布版本。

**新建**：`lark-cli config init --new`。命令会一直等到用户在浏览器里完成设置，所以放后台跑，从输出里取验证链接交给用户。在 OpenClaw、Hermes 这类智能体工作区里，`config init` 默认拒绝新建，要绑定现有应用用 `config bind`。

**用户身份登录**：`lark-cli auth login --no-wait --json` 拿到验证链接，交给用户点，用户确认后再用 `--device-code` 完成。前文、查名字、日历文档这些都靠用户身份。

## 3. 开发者后台清单

在 `https://open.feishu.cn/app` 里打开应用，逐项做：

1. **添加应用能力 → 机器人**：打开。
2. **权限管理**，至少开：
   - `im:message.p2p_msg:readonly`：收私聊。
   - `im:message.group_at_msg:readonly`：只收群里 @ 机器人的消息。
   - `im:message:send_as_bot`：机器人发消息。
   - 表情回复权限（处理中的表情；缺了只是没有表情，不影响回复）。
   > **注意**：不要开 `im:message.group_msg`（读取群内所有消息）。开了以后每条群消息都推给机器人，“不 @ 不触发”只能靠代码过滤，白白多收消息。
3. **事件与回调 → 事件配置**：订阅方式选“长连接”，添加事件 `im.message.receive_v1`。
4. **版本管理与发布**：创建版本并发布。权限、事件、名字的每次改动都要重新发布才生效。
5. 用户身份需要的权限（日历、文档、读聊天记录、通讯录）在 `auth login` 时按提示授权；少了哪个，lark-cli 报错会写出缺的 scope，按报错补。

## 4. 验证收得到消息

在不起服务的情况下单独试：

```bash
lark-cli event consume im.message.receive_v1 --as bot --max-events 1 --timeout 60s
```

然后在飞书私聊机器人发一句话。预期：命令输出一行 JSON 后退出。收不到时依次查：事件是否订阅并发布、是否有别的进程在收（`ps aux | grep "event consume"`）、机器人是否在可用范围内。
