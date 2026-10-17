# 公开副本说明

本目录由 `make-copy.sh` 从项目内版本生成。不要手改，改源后重跑脚本。

## 与项目内版本的差异

| 项 | 处理 | 原因 |
|---|---|---|
| `evals/` | 排除 | 评测运行目录与记录，含大量截图与内部评审过程 |
| `research/`、`PLAN.md` | 排除 | 内部调研底稿与方案演进记录，公开副本只保留可执行部分 |
| `history/history.json` | 排除 | 运行历史，无复用价值 |
| 超过 300 KB 的图片 | 删除（`examples/finished/*/shots/` 除外） | 控制仓库体积 |
| `agents/openai.yaml` | 新增 | 公开仓入库规则要求 |
| 路径 | `.claude/skills/` 路径改写为 `skills/` | 公开仓目录结构不同 |

保留：`examples/`、`library/`、`stages/`、`references/`、`samples/`、`templates/`、`toolbox/`、`history/README.md`、`SKILL.md`、`README.md`。

## 依赖

- `content-blueprint`：阶段 1 内容蓝图。仓库内已有 `skills/content-blueprint/`。
- `visual-motion-design`：动效引擎与机制示例，阶段 2 到 4 按需引用。仓库内已有 `skills/visual-motion-design/`。
- 没有这两个 skill 时，按 `SKILL.md` 的路由读 `stages/` 与 `references/`，质量下降。

## 示例环境

`references/blender-pipeline.md` 与 `references/craft.md` 中的下列事实来自作者的一台开发机，不是通用前提：

- Blender 4.0.2 与 numpy，只能用 Cycles 小预览，Eevee 因缺 libEGL 崩溃。
- agent-browser 作截图工具，首次 open 需再开一次。
- 2 核 CPU、无 GPU，因此渲染和截图耗时数据偏保守。

读者按自己的环境替换这些值。判断规则（先看环境能力再定实现路线）仍然适用。
