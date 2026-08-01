---
name: topics
description: Use when 选题、定选题、下周写什么、把分析报告变成选题卡、需要赛道热点调研辅助选题, or turning analyze signals and niche intel into topic cards for any managed account.
---

# topics — 选题工位

## 核心原则

选题不是拍脑袋，是**三路信号汇成一张可追溯的选题卡**：

1. **报告信号**（本号历史说话）：analyze 报告的方向卡与爆款基因——这个号什么题材有效、方向引擎推了哪几条路
2. **赛道矩阵**（赛道知识说话）：niche 包的题材桶——本赛道有哪些题材、各题材配什么文体（`niches/<id>/structure.md` 的题材×文体速查）
3. **实时情报**（外部世界说话，可选）：niche-scout 侦察热点/竞品/风向

选题卡是复盘的对账单：每张卡带**依据**（可追溯到具体信号）与**预期指标**（对标本号基线）——发布后 review 站拿真实数据回来对账，选题判断力靠这个闭环长出来。

## 工作流

插件根 = 本 SKILL.md 所在目录的上上级。

1. **读信号**：读该账号最新报告 `~/.wxops/accounts/<slug>/output/report.json` 的 `forward_looking`（方向卡 candidate_paths、内容矩阵 content_matrix）与 `viral_genes`。没有报告或报告过期（> 7 天）→ 先推 `wxops analyze --account <slug>`。报告带 `niche_coverage.alert: true` 时题材类信号已降级，选题依据只用结构信号 + 实时情报，并提醒用户换包/建包。
2. **补情报**（可选）：题材时效性强或用户想追热点 → 派 `niche-scout` agent，任务书里给它 niche 包路径、persona 路径与侦察方向。
3. **共创选题**：给用户 3-5 个候选（每个一句话角度 + 依据来源 + 建议题材桶×文体），**人挑人改人拍板**——不替用户决定写什么。
4. **落选题卡**：拍板后按 `templates/topic-card.template.md` 建卡，落 `~/.wxops/accounts/<slug>/topics/<topic-slug>/card.md`（topic-slug：小写英文/数字/连字符）。占位符全部填实——含 `{{...}}` 的卡过不了 write 站门禁。
5. **建证据清单**：卡上"证据清单"列清写作前要收集什么；证据包 `evidence.md` 可现在建（按 `templates/evidence-pack.template.md`），也可 write 站开工前补齐。

## 选题卡质量线

- **依据可追溯**：引用报告具体字段（哪张方向卡/哪条爆款样本）或调研线索（哪条侦察简报），主编直觉要明写"主编判断"——不许出现"感觉会火"
- **预期贴本号**：预期指标对标 persona.md 数据基线与报告里本号中位数，不抄行业神话
- **一题一卡**：想写的第二个角度是第二张卡

## 红线

- 不替人拍板选题；候选给足依据，决定权在主编
- niche-scout 只读调研，其产出是线索不是事实——时效与传闻标注原样保留到卡上
- 选题卡落盘即入 desk 视野（在途选题），不建"只是想想"的卡——想法记别处，建卡=进流水线
