---
name: analyze
description: Use when 拉取公众号后台数据、运营复盘、生成诊断报告与本地叙事看板、分析某个账号的文章表现/爆款基因/下一步方向, or refreshing WeChat article metrics for any managed account.
---

# analyze — 数据分析工位

## 核心原则

把公众号数据变成**决策报告**，不是堆满卡片的仪表盘。产出必须回答四问：**接下来写什么、数据为何支持、结论有多稳、下一步怎么验证**。

"有多稳"是引擎内部用来决定展开多少屏、给几个方向的依据，**绝不**在看板上渲染成"置信度 73%"这类数字。置信度内化，只影响呈现，不给用户打分。

> **使用边界**：仅抓取使用者**本人拥有管理权限**的公众号后台数据；遵守微信公众平台服务协议，主动限频，不伪造指纹、不绕平台机制、不碰无授权的第三方账号。

## 引擎入口

插件根 = 本 SKILL.md 所在目录的上上级。

```bash
<插件根>/scripts/wxops analyze --account <slug>          # 抓数据 → 建报告 → 起看板
<插件根>/scripts/wxops analyze --account <slug> --build  # 只构建看板不起 dev 服务器
<插件根>/scripts/wxops analyze --all                     # 全部在册账号批量拉数出报告（见下）
<插件根>/scripts/wxops analyze --demo --data-only        # 演示数据只产报告，零登录零 Node 依赖
```

- 不给 `--account` 用当前账号；`--workspace <dir>` 为旧模式直通（与 `--account` 互斥）。
- 首次真实分析前该账号需已 `login`（登录态过期会明确报错，**绝不拿旧数据硬分析**）。
- 看板构建需要 Node ≥ 18 + pnpm；只要数据用 `--data-only`。

## 批量模式（analyze --all）

「严禁并行抓取」这条铁律的官方实现——多号复盘不要手写循环，用 `--all`：

1. **顺序执行**：按 slug 排序逐号跑，永不并行
2. **前置体检**：每号先探测登录态，掉线号直接跳过（不硬拉、不烧重试），给出补登录命令
3. **防风控间隔**：相邻两次真实拉数之间随机等 30-90 秒，等待在日志明确可见
4. **失败隔离**：单号失败记录原因后继续下一号，绝不中断批次
5. **批次报告**：汇总落 `~/.wxops/runs/analyze-all-<时间戳>.json`，终端同步输出汇总表

```
=== 批次汇总 ===
✓ maizong   报告已更新    accounts/maizong/output/report.json
○ backup    已跳过        登录态掉线 → wxops login --account backup
✗ oldnum    拉取失败      token 失效（其余账号未受影响）

1 成功 · 1 失败 · 1 跳过 · 批次报告：runs/analyze-all-20260801-153000.json
```

批量模式只产数据不起看板（要看某号看板：`analyze --account <slug> --build`）。`--all` 与 `--account` / `--workspace` / `--demo` / `--build` 互斥。retired 账号不进批次。

## 运行契约（代码只读，数据可写）

插件目录是只读模板。所有运行态落该账号的办公室 `~/.wxops/accounts/<slug>/`：

- 原始抓取落 `raw/` 与 `reports/wechat/`，报告落 `output/`（看板数据 `output/report.json`）
- 看板模板从插件复制到 `<账号目录>/dashboard/` 后再 pnpm 构建，`dist` 落账号目录
- 跑完自动更新 `account.json` 的 `last_fetch_at` 与 `pipeline.json` 游标（desk 总控台靠它）

## 分析链路（引擎自动跑，无需手工干预）

1. 量化诊断：均值 / 中位数 / P75 / 截尾均值 + 样本量，**绝不把一篇爆款当规律**
2. 账号类型路由：自动识别六类账号并切换诊断口径，信号不足回退通用链路
3. 爆款基因四象限：高读高享=爆款 / 高读低享=标题党 / 低读高享=深度遗珠 / 双低=待提升
4. 向前看方向引擎：照镜子 → 候选路径 → 内容矩阵；样本不足自锁该屏，不硬凑结论
5. 爆款标准相对自身：本号均值 1.5 倍即记爆款，10 万粉和 800 粉不用同一把尺子

改 schema 或报告体验前，必读插件内 `DATA_CONTRACT.md` 与 `references/report-contract.md`、`references/account-type-playbooks.md`。

## 红线

- UI 任何位置出现"置信度"数字/百分比/进度条 = 违反契约，必须改
- 登录态过期就停下要求重新扫码，不静默降级
- 多账号批量拉数逐号顺序执行，账号之间留间隔，**严禁并行抓取**

## 验证

```bash
<插件根>/scripts/wxops analyze --demo          # 演示数据全链路
python3 -m pytest tests/ -q                    # 在插件根执行：数据/引擎测试
```
