# create-wechat-ops-skill

一键安装「**公众号运营复盘**」Claude Code 技能：扫码登录公众号后台、抓取发布数据，自动生成运营复盘报告与交互式数据看板。

一条命令把技能投放到 `~/.claude/skills`，Claude Code 即可自动发现并使用。

## 快速开始

```bash
npx create-wechat-ops-skill
```

默认安装到 `~/.claude/skills/wechat-ops-performance-review/`。

## 用法

```bash
npx create-wechat-ops-skill [目标目录] [选项]
```

### 选项

| 选项 | 说明 |
| --- | --- |
| `[目标目录]` | 技能安装位置（可选）。默认 `~/.claude/skills/wechat-ops-performance-review` |
| `--dir <path>` | 指定安装目录（等价于位置参数；同时给出时以 `--dir` 为准） |
| `--ref <ref>` | 拉取的 Git 分支 / 标签 / commit（默认 `main`） |
| `--force` | 目标目录已存在时覆盖（先清空再写入） |
| `-h`, `--help` | 显示帮助 |

### 示例

```bash
# 装到默认位置
npx create-wechat-ops-skill

# 装到指定目录并覆盖
npx create-wechat-ops-skill ./my-skill --force

# 指定目录 + 分支
npx create-wechat-ops-skill --dir ~/skills/wxops --ref main
```

## 安装后下一步

技能目录为**只读模板**；所有运行态数据写入工作区 `~/.wxops`，不会污染技能目录。

```bash
# ① 安装 Python 依赖（playwright + 浏览器内核）
cd ~/.claude/skills/wechat-ops-performance-review
pip install -r requirements.txt
playwright install chromium

# ② 跑通 demo（内置脱敏样本，无需登录，验证全链路）
python3 scripts/wxops analyze --demo

# ③ 正式使用（抓取真实公众号数据）
wxops init      # 初始化工作区 ~/.wxops
wxops login     # 扫码登录公众号后台
wxops analyze   # 抓取 → 生成报告 → 渲染看板
```

`wxops` 即技能内的 `scripts/wxops`，可加入 PATH 或用绝对路径调用。

## 本技能与 wxops 插件的关系

本包安装的是**单账号复盘技能**。它的后续演进已经转移到 **wxops 插件**——同一个仓库里的多账号编辑部，除复盘外还包含选题、写作、配图、发布（草稿箱止步）与复盘闭环。

注意别混：marketplace 里的 `wechat-ops-performance-review` 条目和本 npx 包投放的是同一份技能，两条通道等价。`wxops` 是另一个插件，不是本包的新版本：

| | 本包（老技能） | wxops 插件 |
| --- | --- | --- |
| 账号模型 | 单账号，`~/.wxops/` 直接放数据 | 多账号，`~/.wxops/accounts/<slug>/` |
| 能力 | 登录 → 拉数 → 复盘报告 → 看板 | 上述全部 + 选题 / 写作 / 配图 / 发布 / 复盘闭环 |
| 赛道知识 | 硬编码（AI 工具赛道） | 可替换的赛道数据包 |
| 演进 | **冻结**，只修阻断性问题 | 活跃开发 |

**本技能不会被停掉，现有工作流一行都不用改。** 只做数据复盘、只有一个号，留在原地完全够用。

要升级或想了解怎么把已有 `~/.wxops` 数据搬过去，见 [MIGRATION.md](./MIGRATION.md)。迁移是 copy-first 的，源文件一个字节不动。

## 私有仓库

仓库为私有时，需先设置环境变量再运行：

```bash
GIGET_AUTH=<GitHub token> npx create-wechat-ops-skill
```

## 环境要求

- Node.js >= 18
- Python 3.9+（技能运行时依赖，详见技能内 `requirements.txt`）

## License

MIT © [麦总玩AI](https://github.com/DwDestiny)
