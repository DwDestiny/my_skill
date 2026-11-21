# config.json 字段

| 字段 | 默认 | 说明 |
|---|---|---|
| `name` | 必填 | 机器人在守则里的名字，建议和飞书应用名一致 |
| `owner_name` | 必填 | 主人的名字 |
| `owner_open_id` | 启用飞书时必填 | 主人的飞书 open_id。`scripts/ids.sh` 查 |
| `bot_open_id` | 启用飞书时必填 | 群里判断是不是 @ 了机器人。`scripts/ids.sh` 查 |
| `channels.feishu.enabled` | `true` | 收飞书消息 |
| `channels.wecom.enabled` | `false` | 收企业微信消息，见 [wecom.md](wecom.md) |
| `channels.wecom.owner_userid` | 启用企微时必填 | 主人的企微 userid，从日志 `recv` 行看 |
| `channels.wecom.credentials` | `wecom-cli` | 机器人凭证来源：`wecom-cli`（读 `wecom-cli auth init` 存的）或 JSON 文件路径 |
| `cross_im_read` | `false` | 两个渠道都启用时：会话能不能读另一个 IM 的聊天记录。打开要主人确认，见 boundary.md |
| `tasks.enabled` | `true` | 长任务开关，见 tasks.md |
| `tasks.root` | `~/work/.bot-tasks` | 任务工作树放哪（按服务名分子目录）。不能在实例目录里 |
| `tasks.max_running` | `2` | 同时跑几个后台任务（与聊天并发 `max_parallel` 分开） |
| `tasks.approval_hours` | `24` | 同事派的活多久没人批就作废 |
| `tasks.heartbeat_min` | `30` | 飞书任务多久没动静发一次心跳；`0` 关闭。企微不发 |
| `service_name` | `fcb-<目录名>` | systemd 服务名 / launchd 标签后缀 |
| `persona` | `work` | `work` 工作分身 / `personal` 私人助理 |
| `style` | `veteran` | `veteran` / `tsundere` / `warm` / `minimal`，对应 `assets/templates/rules/style-*.md` |
| `rules_file` | `rules.md` | 守则文件名 |
| `workdir` | `~` | Claude 会话的工作目录，不能是实例目录 |
| `add_dirs` | `[]` | 额外可读写的目录（`--add-dir`），例如知识库 |
| `permission_mode` | `auto` | 无头会话的权限模式 |
| `identity` | 见 boundary.md | lark-cli 身份策略 |
| `private` | 见 boundary.md | 私密路径和搜索排除 |
| `deny_extra` | `[]` | 额外的权限拒绝规则，格式同 Claude Code settings |
| `context.enabled` | `true` | 是否带前文 |
| `context.max` / `topic_max` | 20 / 50 | 群聊或私聊最多几条；话题里最多几条 |
| `context.group_window_h` / `p2p_window_h` | 2 / 24 | 只取这段时间内的消息 |
| `context.max_chars` | 400 | 单条前文截断长度 |
| `context.read_as` | `user` | 读前文用的身份。`bot` 读不了群历史 |
| `ambient.enabled` | `true` | 允许旁听。开了也只对主人用命令加进白名单的群生效，默认没有群 |
| `ambient.command` | `/旁听` | 主人在群里 @ 机器人发这个命令开关；加“ 状态”查看，加“ 关”关闭 |
| `ambient.poll_seconds` | 40 | 多久拉一次白名单群的新消息 |
| `ambient.quiet_seconds` / `max_wait_seconds` | 25 / 180 | 群里安静多久后整批处理；最多攒多久 |
| `ambient.max_batch` | 30 | 一批最多几条 |
| `ambient.cooldown_min` | 10 | 插话后多久内不再主动插话 |
| `ambient.rotate_turns` | 40 | 旁听会话处理多少批后换新会话 |
| `prime` | `true` | 固定开场白，见 cache.md |
| `disable_mcp` | `true` | 不加载 MCP，见 cache.md |
| `p2p_idle_hours` | 6 | 私聊闲置多久开新会话 |
| `group_idle_hours` | 2 | 群里（不在话题中）闲置多久开新会话 |
| `max_parallel` | 3 | 同时跑几个 Claude 会话 |
| `claude_timeout_min` | 40 | 单条消息最长处理时间 |
| `processing_emoji` | `OnIt` | 处理中表情 |
| `new_session_commands` | `/new` 等 | 私聊里发这些词开新会话 |
