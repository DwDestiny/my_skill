# UI 交付交接契约（v1）

## 使用方式与边界

总调度先执行 `python3 skills/ui-delivery/scripts/delivery.py init <交付目录>`。该命令仅生成可填写的 `delivery.json`、八个阶段目录和字段骨架，所有阶段均为 `draft`，不生成完成证据；目标已存在时拒绝覆盖。每阶段完成实物、审查后，将对应 `stage.json.status` 改为 `ready`，填入 `review`，再执行 `snapshot <交付目录> --stage <slug>`。`snapshot` 冻结本阶段目录内全部本地交付文件（包括原型所带 CSS/JS/图片）、`stage.json` 及上游快照的 SHA256，不改变 `status`、`review` 或 `verdict`。生成的 `snapshot.json`、`.DS_Store`、`.pyc`、`__pycache__`、`.pytest_cache`、`.mypy_cache` 和 `.ruff_cache` 缓存不计入；阶段目录内的软链会被拒绝。外部网络资源、阶段目录外的本地引用不在哈希保护内，使用它们时须由人工固定版本并核对。`validate <交付目录> [--through <slug>]` 验证全链或某个前缀，失败返回非零码。

阶段 Skill 可以单独用于局部工作，直接交付它自己的文档和设计产物；只有宣称完整端到端交付时，才要求全链 `validate`。`--through` 是从第 1 阶段到所选阶段的前缀门禁，不是跳过上游的捷径。结构与哈希校验通过只表示契约自洽。视觉、交互、产品是否过关，由独立的人或主控审查；实测来源仍须人工核对。

## 目录和必填文件

| 阶段 slug | 目录 | 必填文件 | 下游主要读取 |
|---|---|---|---|
| `product-planning` | `01-product-planning/` | `product-brief.md`, `page-inventory.json` | 页面目标、page/screen 注册表 |
| `ux-architecture` | `02-ux-architecture/` | `ux-map.md`, `state-matrix.json`, `wireframes.md` | 用户路径、状态和两档视口骨架 |
| `visual-direction` | `03-visual-direction/` | `direction-options.md`, `style-decision.json`，以及其引用的概念图 | 备选视觉与明确选择 |
| `design-system` | `04-design-system/` | `design-system.md`, `tokens.json`, `component-inventory.json` | 可复用视觉规则与组件 |
| `high-fidelity` | `05-high-fidelity/` | `high-fidelity.md`, `screen-specs.json`，以及其引用的可查看设计图或原型 | 逐屏逐状态设计 |
| `motion-design` | `06-motion-design/` | `motion-spec.md`, `motion-map.json` | 动作及 reduced motion 替代 |
| `frontend-implementation` | `07-frontend-implementation/` | `implementation-report.md`, `implementation-map.json` | 实现路由、版本与屏对应 |
| `visual-qa` | `08-visual-qa/` | `qa-report.md`, `qa-matrix.json`, `evidence.json`, `verdict.json`，以及引用的截图 | 运行态实测、问题、独立最终判断 |

每个目录另有 `stage.json`；`snapshot.json` 由工具生成。`stage.json` 的 `stage` 与目录 slug 一致，`artifacts` 精确列出表内必填文件，`status` 只能是 `draft`、`ready`、`blocked`、`skipped`。`draft`、`blocked` 不通过。`skipped` 仅允许 `motion-design`，必须写 `reason` 并有独立审查记录；`motion-spec.md` 须写明无需额外动效的依据，`motion-map.json` 须为 `{"motions":[]}`，两份文件仍纳入快照，修改后旧快照失效。其余阶段不能以跳过绕过关键依赖。每个通过的阶段都须有 `review: {"verdict":"approved","by":"...","note":"..."}`，由主控或人工真实填写。工具只检查记录存在，不验证记录人身份或判断本身。

## 统一 ID 与状态覆盖

`delivery.json` 是项目、页面、屏、状态、视口 ID 的唯一注册表。所有 ID 使用小写字母开头、后续仅小写字母/数字/短横线；同类 ID 不重复，`screen.id` 和 `state.id` 在项目内全局唯一。`project.revision` 是本次实现及验收共同指向的版本。页面路由是以 `/` 开头的应用内路径。必须有 `desktop`（宽 ≥800）和 `mobile`（宽 ≤480）两个视口，也可加其它视口。

每个 screen 声明六种基线 `kind`：`default`、`loading`、`empty`、`error`、`permission_denied`、`success`。业务可以有多个同 kind 状态，例如 Planning、Executing、Streaming 都属于 loading，但各有独立 `state.id`。`02/state-matrix.json` 对每个 screen × state × viewport 填一行：适用时 `applicability=applicable` 并写 `behavior`；确实不适用时 `not_applicable` 并写具体 `reason`。每个 screen 在每个视口至少有一个适用的 default 状态。此规则保证窄屏、错误及权限失败态不会因漏列而消失；不适用的判断仍需主控审查。

最小注册表示意（**合成 shape 示例，不是真实项目证据**）：

```json
{
  "schema_version": 1,
  "project": {"id": "sample", "name": "Synthetic sample", "revision": "sample-r1"},
  "viewports": [{"id": "desktop", "width": 1440, "height": 900}, {"id": "mobile", "width": 390, "height": 844}],
  "pages": [{"id": "home", "route": "/", "screens": [{"id": "home-hero", "states": [
    {"id": "hero-default", "kind": "default"},
    {"id": "hero-loading", "kind": "loading"},
    {"id": "hero-empty", "kind": "empty"},
    {"id": "hero-error", "kind": "error"},
    {"id": "hero-denied", "kind": "permission_denied"},
    {"id": "hero-success", "kind": "success"}
  ]}]}]
}
```

对应 `page-inventory.json` 是 `{"pages":[{"id":"home","screen_ids":["home-hero"]}]}`。`state-matrix.json` 的每个组合形如 `{"page_id":"home","screen_id":"home-hero","state_id":"hero-error","viewport_id":"mobile","applicability":"applicable","behavior":"展示错误说明及重试入口"}`。因此该示例需要六种状态 × 两档视口共 12 行；不适用的行仍必须列出并给理由。

## 阶段结构字段

- `style-decision.json`：`options` 至少一项可查看的视觉方案，每项 `id`、本阶段内 `concept_path`、`source_kind=concept` 或 `provided_reference`。通常探索 2–3 个方向；用户明确只要一个方向或已有参考图时可以只有一项。机械门只校验至少一项，用户要求的候选数量是否满足由本阶段人工审查。`selected_id` 必须指向存在的方案。`selection.by` 为 `user` 或 `authorized_agent`，`selection.evidence` 记录实际选择依据；代理代选时另填 `selection.authorization`，须是用户明确授权的记录，不能把等待超时写成授权。
- `tokens.json`：`colors` 至少有一个真实色彩 token。`component-inventory.json.components[]` 含 `id` 和 `used_by` screen ID。
- `screen-specs.json.specs[]`：逐项覆盖 `state-matrix` 中所有适用的 screen × state × viewport，字段为 `screen_id`、`state_id`、`viewport_id`、本地 `asset_path`、`asset_kind`（`mock`、`design`、`render` 或 `prototype`）。`asset_path` 应指向可查看的 PNG/JPEG/WebP/SVG/PDF/HTML 文件；静态图不能证明交互，`high-fidelity.md` 需说明状态切换、跳转和原型操作，审查人须实际查看。缺设计工具时保持 `blocked`，不能用文字冒充高保真。
- `motion-map.json.motions[]`：每项 `id`、`screen_id`、`state_id`、`reduced_motion`。无动效可依跳过协议记录；基础交互状态仍在 UX 阶段定义。
- `implementation-map.json`：`revision` 必须等于 `project.revision`，`routes[]` 的 `page_id`、`route`、`screen_ids` 精确覆盖注册表。
- `qa-matrix.json.rows[]`：逐项覆盖所有适用的 screen × state × viewport；全链通过时每行 `result=pass` 且 `evidence_ids` 至少引用一条匹配的真实运行截图。`evidence.json.items[]` 记录 `id`、`kind`、本地 `path`、`route`、`viewport_id`、`state_id`、`revision`；`runtime_capture` 另填 `captured_at`。`kind=concept/mock` 可保留作设计对照，但不能抵运行验收。运行截图只接受 PNG/JPEG/WebP 且检查文件签名，签名只排除明显伪文件，仍不能证明截图确实来自运行产品。`verdict.json` 另有 `verdict`、`by`、`basis`；通过须由主控或人工独立写 `pass` 和依据。

所有 JSON 契约中引用的资产必须使用相对本阶段目录的路径。绝对路径、`..` 上级穿越、软链以及空文件均拒绝。阶段目录内的全部本地交付文件一并进入阶段快照，包括未直接列在 JSON 中的嵌套原型依赖；任何本地交付文件、上游文件、项目 revision 或审查记录改变后，旧快照失效，须重新审查并逐阶段快照。外部网络或阶段目录外的依赖不在此保证中，应人工固定版本与来源。工具绝不从图片的存在推断实测通过，也不负责部署、账号权限或运行态写入。
