# plugins/wxops — 公众号多账号编辑部插件（L1 · agent 工作契约）

面向**在这棵子树里干活的 agent**。产品是什么、八个工位分别做什么，看 `README.md`；本文只回答"我该怎么改这里、什么绝对不能碰"。

## 读序

1. 仓库根 `AGENTS.md`
2. 本文（插件级 L1）
3. 目标目录的 `AGENTS.md`（L2）：`scripts/cli/`、`scripts/analyze/`、`scripts/fetch/`、`scripts/publish/`、`dashboard/`、`niches/`、`templates/`、`tests/`
4. 目标文件顶部的 `# GEB-L3` 头——先据此判断要不要读全文

`agents/` 下没有 L2：插件校验器会把该目录所有 `.md` 当 agent 定义扫描，文档只能住 `references/agents-guide.md`。

## 架构不变量（改动不得破坏）

**三层模型是这个插件的宪法**——通用的是动作、赛道的是知识、账号的是身份。落到代码上是三条硬边界：

- **引擎不认赛道**。`scripts/` 里不许出现任何具体赛道的词表、题材名、标题公式。这类知识只能来自 `niches/<id>/niche.json` 与 `structure.md`。P3 已把 ai-tools 从 `constants.py` 里拆出去，别再塞回来。
- **引擎不认账号**。账号身份（persona / 凭证 / 登录态 / 数据）只在 `~/.wxops/accounts/<slug>/` 下，代码里一律按 slug 推导路径，不许硬编码任何账号。
- **agents 提示词零知识**。`agents/*.md` 不带账号也不带赛道，身份与知识运行时喂入。

## 红线（违反即回退，无例外）

- **草稿箱止步**。任何代码路径都不得调用发布 / 群发接口。网关客户端的能力面积被刻意限制为「上传素材 + 建草稿」两个方法，这是结构性保证，不许扩。
- **凭证与登录态永不入库**。`credentials/` 权限 0600；凭证值不打印、不进日志、不进台账、不进报错信息。
- **真实 `~/.wxops` 禁触**。测试、冒烟、调试一律 `WXOPS_HOME` 指向临时目录。
- **触网默认关**。真实网络调用只在显式 `--go` 分支内惰性 import，让"默认跑法零网络"由结构保证而非靠约定。
- **迁移/清理一律 copy-first**：复制到目标 → 校验数量与抽样 → 保留源文件交人处置。不许 `mv`，不许直接删。
- **同账号浏览器 profile 并发互斥**；多账号拉数逐号顺序执行，严禁并行（风控）。
- **看板不渲染置信度数字**（置信度内化契约，见 `DATA_CONTRACT.md`）。
- **不编数**。analyze 拿不到的指标就标「人工核对」，绝不推算填充。

## 分层职责

```
skills/      工位 SKILL.md —— 只写"怎么用"，不写实现
agents/      写作产线四 agents 提示词
scripts/     Python 引擎（唯一实现层）
  cli/       子命令编排：只编排不实现，路径解析一律走 env.py
  fetch/     网络抓取
  analyze/   计算与报告构建
  publish/   渲染与网关（复制自 hermes，带来源注记；三个引擎 lib 禁改）
niches/      赛道数据包（知识层）
templates/   用户侧模板
dashboard/   React 看板模板，构建时复制到账号目录
tests/       引擎测试
fixtures/    只读演示输入（产物落工作区，不回写 fixtures）
```

## 上游来源（已退役）

本插件由 `skills/wechat-ops-performance-review/` 于 2026-08-01 copy-first 迁入。该源已于 2026-08-05 **退役删除**（[#56](https://github.com/DwDestiny/my_skill/issues/56)），公众号工具线只剩本插件一个产物，不再有"新旧两份"。需要考古时从 git 历史取：`git log --all -- skills/wechat-ops-performance-review`。

## 改完必须做

- 测试：插件根 `WXOPS_HOME=/tmp/<临时目录> python3 -m pytest tests/ -q`
- 插件校验：`claude plugin validate ./plugins/wxops --strict`
- 结构变更后按 **L3 → L2 → L1** 顺序回填文档；新增源文件必须带 `# GEB-L3` 头，且 `Input:`/`Output:` 要写具体内容——写成"behavior defined by 它自己"这种占位模板等于没写
- 每期发布前 bump `.claude-plugin/plugin.json` 的 `version`

## 台账

epic #38，分期 #39-#44。问题一律先开 issue 再动手，根因写满三层（现象 / 直接机制 / 系统设计缺口）。
