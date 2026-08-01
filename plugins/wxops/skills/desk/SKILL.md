---
name: desk
description: Use when 开工先看全局、查看所有公众号账号的流水线状态、"我现在该干嘛"、哪个号该登录/该拉数据/有在途草稿, or getting a cross-account editorial desk overview and next-step suggestions.
---

# desk — 编辑部总控台

## 这是什么

编辑部的晨会白板。一眼看清每个账号在流水线上的位置：登录态还活着吗、数据新不新鲜、最近一次报告是什么时候、下一步该干嘛。**开工先跑 desk，再决定去哪个工位。**

## 用法

插件根 = 本 SKILL.md 所在目录的上上级。

```bash
<插件根>/scripts/wxops desk
```

输出形如：

```
=== wxops 编辑部总控台 ===
账号          登录          数据          报告          下一步
● maizong     3 天前        2 天前        2 天前        数据尚新，可直接复盘
○ foodie      从未登录      —             —             wxops login --account foodie
(● = 当前账号)
```

## 怎么读、怎么答

用户问"我现在该干嘛"时：跑 desk，按「下一步」列给出具体命令，**一次只推一步**，别把全流程倒给用户。建议规则：

- 体检结果掉线（`login_alive: false`）/ 从未登录 → 先 `wxops login --account <slug>`
- 在线、无数据或数据 > 7 天 → `wxops analyze --account <slug>`
- 多个号同时要拉数 → 推一条 `wxops analyze --all`（顺序 + 间隔 + 失败隔离，别逐号手跑）
- 数据较新 → 可直接看报告 / 看板，或进入内容工位

登录列优先引用 `accounts check` 的真探测结果（`● 在线` / `○ 掉线`）；没体检过的号回落到按最近登录时间推断。状态存疑先推一次 `wxops accounts check`。

## 数据来源

每个账号目录下的 `pipeline.json`（各工位命令跑完自动写入游标）+ `account.json` 时间戳。desk 只读不写，随时可跑，零风险。

## 工位地图

编辑部共八个工位。当前版本已入驻：**accounts**（账号）、**analyze**（数据分析）、**desk**（总控台）。选题 topics、写作 write、配图 illustrate、发布 publish（草稿箱止步）、复盘 review 将按版本陆续入驻——desk 的「下一步」建议会随工位开放自动变聪明。

产品铁律：自动化推进到"最后负责时刻"为止——草稿入箱人点发布，人设改动人来确认。desk 永远只**建议**下一步，不代替人拍板。
