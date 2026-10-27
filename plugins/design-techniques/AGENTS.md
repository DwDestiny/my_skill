# plugins/design-techniques

本目录是设计手法库插件的完整源码。插件只收在真实项目里做出好效果的视觉手法。

- `.claude-plugin/plugin.json` 是唯一清单。改插件内容时升 `version`，与 `README.md` 顶部版本行保持一致。
- `skills/catalog/` 是入口索引。它的手法表、`README.md` 的手法节、仓库根 `README.md` 的 Skill 目录三处列出同一组手法；加、删手法时三处同改。
- `skills/<手法 id>/` 一个手法一个目录，自成一体：`SKILL.md`、`CARD.md`、`agents/openai.yaml`、`references/`、`templates/starter/`、`showcase/`，可选 `scripts/`。手法之间不互相引用文件。
- 每个手法 `SKILL.md` 写成通品：原理、方法（含多题材推演）、验收标准、按原理归类的踩坑；一次实例的参数只作起点。不写成某一次作品的复刻说明。
- `CANDIDATES.md` 记未收录的候选、外部 skill 和试过没达标的方向。它不是 skill，不在 `skills/` 下。
- `evals/` 是 `claude plugin eval` 用例。加手法时加一条该手法的触发用例。
- 素材都放在插件目录内。单个文件 ≤300 KB，一个手法目录合计 ≤2 MB。
- 本仓公开。提交前对改动目录跑脱敏检查：不写公司名、人名、业务方法论原文和本机路径。
- 收录标准与步骤见 `skills/catalog/SKILL.md` 第 4 节。
