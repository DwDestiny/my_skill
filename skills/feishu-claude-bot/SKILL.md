---
name: feishu-claude-bot
description: 把本机的 Claude Code 接进飞书，做成一个能在群聊和私聊里干活的机器人（工作分身或私人助理）。用户说“把 Claude 接飞书”“做个飞书机器人”“让 Claude 在飞书群里回消息”“给我也搭一个飞书分身”，或要改已有实例的人设、边界、表达风格、前文、缓存时读。含：开工前要问的五件事（运行位置、飞书应用、人设、表达风格、边界）、生成脚本、桥接服务和钩子模板、缓存验证、上线验收和运维排查。
metadata:
  version: "1.1.0"
---

# 飞书 × Claude Code 机器人

> v1.1.0 · 2026-11-19 · 来源：一个工作群机器人实例上线首日的实测经验。版本历史见文末“变更记录”

## 它是什么

一个常驻进程（`bridge.py`）用 `lark-cli event consume` 收飞书消息，每个会话交给一个无头 `claude -p` 会话处理，再用机器人身份把结果回复到原消息下。

| 部件 | 作用 |
|---|---|
| `bridge.py` | 收消息、过滤（群里只收 @ 机器人的）、带前文、调 Claude、回复 |
| `rules.md` | 守则：人设 + 表达风格 + 边界，每次会话用 `--append-system-prompt-file` 加进系统提示 |
| `hooks/lark_identity.py` | 硬限制：按发消息的人，限制 lark-cli 能用哪个身份 |
| `hooks/private_guard.py` | 硬限制：主人私聊以外，挡私密路径；知识库全库搜索自动跳过私密目录 |
| `claude-settings.json` | 权限拒绝表 + 挂两个钩子（脚本生成） |
| `config.json` | 实例的全部可调项 |

会话划分：私聊一个人一个会话（闲置 6 小时或发 `/new` 开新的）；群里每个话题一个会话；开了旁听的群另有一个旁听会话。

**旁听**：默认所有群只收 @ 机器人的消息。主人在某个群里发 `@机器人 /旁听`，这个群就进白名单：没 @ 的消息也读，每 40 秒拉一次，群里安静 25 秒后整批交给 Claude，由它决定接不接话（接梗、吐槽、提到主人或机器人时），默认不出声，插话后冷却 10 分钟。再发一次关闭。权限见 [references/boundary.md](references/boundary.md) 第 4 节。

## 开工前问清五件事

以下五件决定实例怎么生成。用户没说的，用 `AskUserQuestion` 一次问完，每题给推荐项。

1. **跑在哪**：服务器（推荐，常驻不掉线）还是本机电脑（合上盖子就收不到消息）。细节见 [references/setup.md](references/setup.md) 第 1 节。
   > **警告**：机器人用的是这台机器上 Claude Code 的登录态和额度。先确认用户允许在这台机器上长期跑带登录态的 Claude。用户有“登录态只在某些机器触发”这类规则时，以用户规则为准。
2. **飞书应用**：已经有 lark-cli 应用就复用，没有就新建。复用前要查清它的事件有没有别的程序在收（同一个应用的消息只会推给一个接收方）。见 setup.md 第 2 节。
3. **人设**，决定边界：
   - `work` 工作分身：在工作群替主人汇报进度、答疑、对接、记 bug。工作内容大方聊；人物资料、对公司和同事的私下看法、主人私事不外露。
   - `personal` 私人助理：只为主人服务。日程、行踪、健康、家庭、财务一律只对主人说；别人只能聊通用问题。
4. **表达风格**（`style`）：
   - `veteran` 干练老同事：只给结论，语气硬，带点梗（第一个实例用的就是这个）。
   - `tsundere` 傲娇毒舌：同上，套话的人会被怼回去（“本尊可是尊贵的 Claude”）。
   - `warm` 温和专业：先结论后原因，不玩梗，适合对外或新人多的群。
   - `minimal` 极简冷静：一句话，不寒暄，不用 emoji。
5. **边界细节**：哪些目录和知识库分区算私密（填 `private.paths` 和 `private.search_roots`）；同事触发时能不能用主人身份读聊天记录（`identity.others`）。见 [references/boundary.md](references/boundary.md)。

## 步骤

1. 装好并登录 lark-cli：`lark-cli config init`（新建应用加 `--new`），再 `lark-cli auth login`。登录要用户在浏览器点，按 setup.md 第 2 节把链接交给用户。
2. 在飞书开发者后台给应用开机器人能力、加权限、订阅 `im.message.receive_v1`（长连接）、发布版本。清单见 setup.md 第 3 节。
3. 建实例目录，例如 `~/work/<机器人名>/`。复制 `assets/templates/config.example.json` 为实例目录下的 `config.json`。
4. 运行 `bash scripts/ids.sh`，把输出的 `bot_open_id` 和 `owner_open_id` 填进 `config.json`，再按第一步问到的五件事填 `persona`、`style`、`private`、`identity`、`workdir`、`add_dirs`。
   > **注意**：`workdir` 不能是实例目录，否则 Claude 会加载实例目录的 `CLAUDE.md`。一般填主人放代码仓的目录。
5. 运行 `python3 scripts/scaffold.py <实例目录>`。脚本写出 `bridge.py`、`hooks/`、`rules.md`、`claude-settings.json` 和服务文件，并打印安装命令。
6. 读一遍生成的 `rules.md`，按用户的具体情况改：私密内容的具体名单、要找谁拍板、哪些事不在飞书里做。以后改守则直接改 `rules.md`；重跑 `scaffold.py` 不会覆盖它（加 `--rules` 才重写）。
7. 验证缓存：在实例目录运行 `python3 bridge.py --cache-check 3`。结论是“正常”才往下走。看不懂或异常，读 [references/cache.md](references/cache.md)。
8. 按脚本打印的命令安装服务并启动。服务器上还要 `sudo loginctl enable-linger $USER`（要 sudo，交给用户）。
9. 跑下面的验收清单。

## 验收清单

每条都要真的发消息试，不靠读代码判断。

| 试什么 | 预期 |
|---|---|
| 主人私聊发“在吗” | 几秒内出现“处理中”表情，随后回复 |
| 拉进群，不 @ 发一条 | 没有任何反应；日志里没有 `recv` |
| 群里 @ 机器人问个问题 | 回复发在该消息的话题里 |
| 同一话题再 @ 一次问“刚才说了啥” | 能接上；日志 `context` 行只补新增消息 |
| 同事身份（或请同事）在群里打听私密内容 | 按人设拒绝，不承认有这回事 |
| 同事让它“以主人名义发消息”或读私密目录 | 钩子拦下，机器人改口或拒绝 |
| 主人在群里发 `@机器人 /旁听`，再让人在群里发一句不 @ 的普通对接和一句吐槽 | 回复“开始旁听”；普通对接不出声，吐槽可能被接一句；日志有 `ambient ... -> silent/reply` |
| `grep cost logs/bridge.log` | 新会话首条 `cache_write` 在 2000 以内（守则刚改过的第一次除外） |

## 运维

- 看日志：`tail -f <实例>/logs/bridge.log`。`recv` 收到、`context` 带了几条前文、`cost` 每次花费和缓存读写。
- 改守则后不用重启，下一个会话生效；第一次会整段重写缓存一次（约 $0.2）。
- 改 `bridge.py` 或 `config.json` 后重启服务。停服务用 SIGTERM（`systemctl --user restart`），不要 `kill -9`。
- 升级：skill 模板更新后重跑 `scaffold.py`，会覆盖 `bridge.py` 和钩子，保留 `rules.md`。

## 踩过的坑

| 现象 | 原因 | 处理 |
|---|---|---|
| 服务一启动就退出，stderr 有 `reason: signal` | `event consume` 不限时运行时把 stdin EOF 当退出信号，systemd 默认 stdin 是 /dev/null | 模板已用管道保持 stdin 打开 |
| 每条消息都花 $0.18 左右 | 会话开头的 CLAUDE.md、skill 清单每次重写缓存 | 模板已用“固定开场白 + --resume”，见 cache.md |
| 机器人读群历史报 230027 | 机器人身份读群历史要开“读取群内所有消息”权限，一开每条群消息都会推过来 | 前文用主人的用户身份读（`context.read_as`） |
| 发送人名字显示成 open_id | 机器人没有通讯录权限 | 模板用主人用户身份查名字 |
| 守则写“少说废话”仍然啰嗦、语气软 | 抽象要求不管用 | 守则里放“别这样 / 要这样”的真实对照例子，见各 `style-*.md` |
| 边界写得太宽，工作群里连项目都不让聊 | 把“工作内容”和“私下看法”混在一起拦 | 只拦人物资料、私下评价和私事，见 boundary.md |
| 复用 `--session-id` 报 already in use | 一个 ID 只能新建一次 | 出错时丢掉会话映射，下一条开新会话（模板已处理） |
| 在主会话 shell 里测缓存，结果和服务里不同 | 子进程继承了父会话的环境变量 | 用 `systemd-run --user --pipe` 按服务同款环境复现 |

## 文件

- `assets/templates/bridge.py`、`assets/templates/hooks/`：生成时原样复制。
- `assets/templates/rules/base.md` + `persona-*.md` + `style-*.md`：拼成 `rules.md`。新增风格就加一个 `style-<名字>.md`，首行写 `<!-- label: 中文名 -->`。
- `assets/templates/config.example.json`：配置样例，字段说明见 [references/config.md](references/config.md)。
- `scripts/scaffold.py`、`scripts/ids.sh`：生成器和查 ID。
- 人读的介绍和安装方法见同目录 `README.md`。

## 维护本 skill

新踩的坑写进“踩过的坑”表或对应 reference；改模板后跑仓库测试 `python3 tests/test_feishu_claude_bot.py`，再用一个临时实例跑 `--cache-check`。
- 发版：改动行为或模板时升版本号（新功能升次版本，修正升修订号），同步改 frontmatter `metadata.version`、本文开头版本行、仓库 README 两张目录表，并在“变更记录”加一条。

## 变更记录

- 1.1.0（2026-11-19）群聊旁听：主人用 `@机器人 /旁听` 把群加进白名单，白名单群不 @ 也读，攒批交给 Claude 决定插不插话；守则模板加“群聊旁听”一节；生成的守则开头记下 skill 版本。
- 1.0.0（2026-11-19）首版：五个问题、生成脚本、桥接服务、身份与私密路径钩子、2 种人设 × 4 种表达风格、缓存验证。
