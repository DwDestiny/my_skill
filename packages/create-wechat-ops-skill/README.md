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

## 与 plugin marketplace 通道的关系

本 npx 包与 Claude Code 的 **plugin marketplace** 是两条**等价**的安装路径，最终都把技能落到 `~/.claude/skills`：

- **npx 通道**（本包）：`npx create-wechat-ops-skill`，适合命令行一键安装、脚本化部署。
- **plugin marketplace 通道**：在 Claude Code 内通过插件市场安装，适合图形化、托管式更新。

两者投放的是同一份只读模板，安装后使用方式完全一致，按习惯任选其一即可。

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
