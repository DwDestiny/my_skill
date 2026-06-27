---
name: wechat-ops-performance-review
description: Use when reviewing WeChat official account performance, refreshing published article metrics, producing an operations diagnosis, or generating a wiki report and local narrative dashboard from公众号后台数据、publish-records JSON、文章台账或运营复盘需求.
---

# WeChat Ops Performance Review

## Core Principle

Turn公众号数据 into a decision report, not a crowded dashboard. 产出必须回答四问:**接下来写什么、数据为何支持、结论有多稳、下一步怎么验证**。

其中"有多稳"是引擎**内部**用来决定展开多少屏、给几个方向的依据,**绝不**在看板上渲染成"置信度 73%"这类数字。置信度内化,只影响呈现,不给用户打分。

## 三步上手(向导式 CLI)

面向使用者的标准路径是可执行入口 `scripts/wxops`:

1. `scripts/wxops init` — 环境自检(Python / Node / playwright 依赖)+ 创建工作区(默认 `~/.wxops`,存放登录态/抓取数据/输出)+ 写配置。
2. `scripts/wxops login` — 引导微信扫码登录公众号后台,登录态持久化到工作区。
3. `scripts/wxops analyze` — 抓取最新数据 → 构建报告 → 启动本地看板。

先看效果、不想登录抓取:`scripts/wxops analyze --demo`,把 skill 内 `fixtures/` 原始输入复制到工作区后跑通全链路(仍需 Node 构建看板,但**无需登录与真实抓取**)。CI / 只读冒烟可加 `--data-only`,只产数据不碰 pnpm。

## 运行契约(代码只读,数据可写)

**skill 目录是只读模板,所有运行态产物落工作区(默认 `~/.wxops`,或 `--workspace <dir>`)。**

- builder 把 wiki JSON、wiki Markdown、看板数据全部写入 `<workspace>/output/`(看板数据为 `<workspace>/output/report.json`),不向 skill 目录写任何东西。
- `analyze` 会把 skill 的 `dashboard/` 模板复制到 `<workspace>/dashboard/`(忽略 node_modules/dist),注入 `output/report.json` 后在工作区副本里跑 `pnpm install/build/dev`,`dist` 落 `<workspace>/dashboard/dist`。
- 因此 skill 可以被放在只读路径(plugin / npx 分发场景)正常运行。

## Standard Workflow(报告生成内部流程)

1. **Refresh data**:取最新 `publish-records-*.json`;若登录态过期,停下要求重新扫码/抓取,绝不拿旧数据硬分析。
2. **Build the contract**:`python3 scripts/build_wechat_ops_report.py --workspace <dir>` —— wiki JSON、wiki Markdown、dashboard 数据全部同源,不各算各的。
3. **Analyze**:用 average、median、P75、max、trimmed mean、sample count 和内化置信度。Never turn one爆款 into a rule。
4. **向前看(forward_looking 方向引擎)**:在诊断之上反推方向——**照镜子**(账号一句话画像 + 六维形状)→ **候选路径**(从历史文章长出的可走方向,每个标信号距离 + 要补什么 + 怎么变现)→ **内容矩阵**(配比 + 四周排期)。样本不足时引擎自锁该屏,不硬凑结论。
5. **爆款基因(viral_genes 四象限)**:高读高享=爆款 / 高读低享=标题党 / 低读高享=深度遗珠 / 双低=待提升。反推"什么题材 + 什么标题型,在本号能爆"。
6. **Generate the experience**:低密度叙事,一屏一结论,证据与动作随行。
7. **Verify**:跑数据测试 + 构建本地站点 + 桌面/移动截图核对。

## Required Output Contract

Read `references/report-contract.md` and `DATA_CONTRACT.md` before changing the schema or report experience.

The JSON must include:

- `account_profile`:analyzed account identity, period, article counts, update time.
- `executive_summary`:first-screen judgment and core metrics.
- `action_plan`:3-5 next actions with why/action/owner/due/validation.
- `analysis_sections`:total-split-total sections, each with conclusion, evidence, action, next test, confidence, and UI slot.
- `viral_genes`:四象限定位 + 反推"题材 × 标题型"爆款组合。
- `forward_looking`:照镜子(mirror)、候选路径(candidate_paths)、内容矩阵(content_matrix)、数据充分度(data_sufficiency)。
- `title_analysis` / `length_analysis`:标题型与正文长度分桶表现。
- `confidence_model`:high/medium/low 规则与完整度说明(**内部用,不渲染数字**)。
- `final_synthesis`:do now、test small、do not decide yet。
- `brand_signature`:small source/author card only;never make it the page hero。

## Analysis Rules

- Only analyze WeChat unless the user explicitly expands scope.
- Separate stable articles from recent 48-hour immature articles.
- Classify every article by content type, pain point, persona, title pattern, and length bucket.
- **爆款标准相对自身**:不是绝对阅读量,是相对本号的倍数(本号均值的 1.5 倍即记爆款)。10 万粉的号和 800 粉的号不用同一把尺子。
- Every section must have a confidence level derived from sample count, distribution skew, and data completeness.
- End with a synthesis board: high-confidence actions, experiments, and hold decisions.

## 置信度内化(红线)

- 引擎**内部**计算 `data_sufficiency` 与各结论置信档,用来决定哪些屏展开、给几个方向、候选数量上限。
- UI **绝不**渲染"置信度 73%"、百分比、进度条或"置信度"字样。样本不足只表现为"该屏暂不展开",而非给用户打分。
- 看板任何位置出现置信度数字 = 违反契约,必须改。

## Experience Rules

- Left top: the analyzed公众号信息, not the Skill author.
- Left bottom: a small source card with author/avatar/Skill/GitHub link.
- Center: scroll narrative screens; one main visual per screen.
- Right: fixed context rail for current evidence, action, and confidence.
- Avoid card walls, crowded first screens, grey-heavy shells, and text-only explanations.

## Validation

最稳的一条(用演示数据跑通全链路):

```bash
scripts/wxops analyze --demo
```

或手动分步(针对真实工作区):

```bash
python3 scripts/build_wechat_ops_report.py --workspace ~/.wxops         # 构建(产物落 ~/.wxops/output/)
python3 scripts/build_wechat_ops_report.py --workspace ~/.wxops --check  # 校验同源
python3 -m pytest tests/ -q                                             # 数据/引擎测试(含只读工作区回归)
scripts/wxops analyze --workspace ~/.wxops --build                     # 看板构建(复制到 ~/.wxops/dashboard 后构建)
```

看板源码会被复制到 `~/.wxops/dashboard/` 后再构建,`dist` 落 `~/.wxops/dashboard/dist`;skill 目录全程只读。

Then open the local dashboard and verify desktop plus mobile: account info is primary, author card is secondary, each screen has a clear visual focus, and no confidence number leaks into the UI.

## Dashboard Preview

See `README.md` for the full visual walkthrough (照镜子 / 找方向 / 规划矩阵 / 爆款基因 / 量化标准 / 数据不足兜底). Screenshots live in `docs/assets/`.
