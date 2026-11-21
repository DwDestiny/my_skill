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
| `tasks.models` | `["haiku", "sonnet", "opus"]` | 派活时主控能挑的模型别名；`[派活]` 里写了名单外的就走全局默认。思考档固定为 low/medium/high/xhigh/max |
| `tasks.relay` | `true` | 任务的完成、提问、失败先交给派活的那个会话（主控）处理，再由主控对人汇报；`false` 就原话直发 |
| `tasks.codeup_token` | `~/.config/codeup/token` | `tasks.py mr` 给 Codeup 建合并请求用的个人令牌文件 |
| `tasks.heartbeat_min` | `30` | 飞书任务多久没动静发一次心跳；`0` 关闭。企微不发 |
| `tasks.budget_default` | `20` | 任务检查点的兜底值（美元当量）。主控在 `[派活]` 里没写 `预算`、又没有同类任务历史时用。到了检查点任务停下交回主控，主控可 `[任务指令] #N 继续，预算加到 X` |
| `tasks.budget_factor` | `1.5` | 按历史估检查点时，同类（同角色同模型，其次同模型）最近 10 个完成任务花费中位数乘几 |
| `tasks.quota_alert` | 见左 | 订阅额度提醒：`five_hour` 是 5 小时窗口用量到多少提醒；`seven_day_pace` 是 7 天窗口“已用比例 ÷ 已过时间比例”到多少提醒。只私聊提醒主人，不拦活 |
| `tasks.sibling_warm_min` | `55` | 同项目同角色的上个会话多少分钟内用过（提示缓存 1 小时内还热），新任务就分叉接着它 |
| `tasks.sibling_max_ctx` | `150000` | 上个会话的上下文超过这么多 token 就不再接着，新开会话带交接笔记 |
| `tasks.compact` | `{"idle_min": 50, "min_ctx": 120000}` | 缓存过期前压缩：上下文到 `min_ctx`、闲置满 `idle_min` 分钟（不满 60）时压一次。只压等人回话的任务和还没到换新时间的聊天会话。`min_ctx` 写 0 关掉 |
| `tasks.stuck_min` | `40` | 本机任务多少分钟没有任何动作（没调工具、没输出、进程 CPU 平均不到 5%）算卡住：停掉并交回主控；`0` 关闭 |
| `tasks.verify_retries` | `2` | `[派活]` 写了验证命令时，验证没过最多退回返工几次 |
| `tasks.verify_timeout_min` | `20` | 验证命令最长跑多久 |
| `tasks.cloud.environment_id` | 空 | Claude 云端环境 ID（`RemoteTrigger` 列出的 `env_…`）。空着就没有云端执行 |
| `tasks.cloud.timeout_min` | `180` | 云端任务多久没交结果算中断 |
| `tasks.cloud.models` | 内置 | 别名到云端模型 ID 的映射，默认 haiku/sonnet/opus 5.5 |
| `chat_max_turns` | `60` | 聊天一轮最多走多少步。到了不硬停，再给 4 步让它把剩下的写成 `[派活]`；`0` 不限 |
| `service_name` | `fcb-<目录名>` | systemd 服务名 / launchd 标签后缀 |
| `persona` | `work` | `work` 工作分身 / `personal` 私人助理 |
| `style` | `veteran` | `veteran` / `tsundere` / `warm` / `minimal`，对应 `assets/templates/rules/style-*.md` |
| `rules_file` | `rules.md` | 守则文件名 |
| `workdir` | `~` | Claude 会话的工作目录，不能是实例目录 |
| `add_dirs` | `[]` | 额外可读写的目录（`--add-dir`），例如知识库 |
| `permission_mode` | `auto` | 无头会话的权限模式 |
| `identity` | 见 boundary.md | lark-cli 身份策略 |
| `private` | 见 boundary.md | 私密路径和搜索排除 |
| `credential_paths` | `["~/.config/codeup", "~/.git-credentials"]` | 代码平台凭据。机器人的所有会话（含主人的）都不能直接读，Read 进拒绝表，Bash 由 `git_guard` 拦；建合并请求只能走 `tasks.py mr` |
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
