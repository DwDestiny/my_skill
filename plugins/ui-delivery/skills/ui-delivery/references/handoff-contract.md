# UI 交付交接契约（v1 / v2）

## 版本选择与兼容

`delivery.py init` 新建 schema **v2**。v2 把用户旅程、页面/状态/必需元素、视觉基线、组件、实现文件清单与运行验收证据关联起来。`schema_version: 1` 仍可按下方保留的 v1 规则做 legacy 结构校验；CLI 必须将成功结果标成 legacy，不能把它描述为通过 v2 保真门。除非明确核验的是旧交付，否则新交付不要手工降为 v1。

本文件先完整保留 v1 说明，再追加 v2 增量规则与填表示例。v2 继续遵循 v1 的阶段目录、stage 状态、审查、快照、路径和 ID 约束，增量规则优先。

## 使用方式与边界（v1 保留说明）

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

## v2 新增门槛

以下规则在 v1 目录、ID、状态、审查和快照规则之上生效。新交付必须使用 `schema_version: 2`。

### 1. 旅程、页面和必需元素

- `delivery.json.journeys[]` 登记每条有序用户旅程：`id`、`steps[]`。每步包含 `page_id`、`screen_id`、`state_id`、`action`；三种 ID 必须指向注册表中的同一页面与 screen 状态。每个已登记 page 至少被一条旅程覆盖，旅程步骤定义本次设计范围。
- `02-ux-architecture/state-matrix.json` 中每个适用组合都列 `required_elements[]`，每项包含稳定的 `id` 和 `role`；角色只允许 `navigation`、`control`、`content`、`decoration`，这是元素类别，不是 ARIA role。CTA、按钮和输入控件归 `control`，标题/文案归 `content`，装饰图形归 `decoration`。`navigation` 和 `control` 必须带 `component_id`；其它角色可选。每个适用的 default state 至少列一个关键元素。
- 必需元素由规划和 UX 人工识别；校验器不能从截图或页面自动发现漏掉的按钮、文本或业务内容。所有范围内页面、各 screen/state、必要元素都要持续追溯，不能把 Hero 或代表页当成完整范围。

### 2. 视觉方向与设计系统

- `03-visual-direction/style-decision.json` 延续 v1 的 `options`、`selected_id` 和选择依据。`source_kind=concept` 的生图文件必须是签名与扩展名一致的 PNG/JPEG/WebP；`provided_reference` 可使用现有可查看格式。
- `04-design-system/tokens.json` 的 `colors`、`typography`、`spacing`、`layout` 都必须非空，并有 `style_sha256` 指向被选视觉基线文件的 SHA-256。
- `component-inventory.json.components[]` 每项包含唯一 `id`、`revision`、阶段目录内的 `master_path`、非空且有效的 `used_by` screen ID，以及 `render_mode`：`code`、`figma`、`structured` 或 `raster`。被必需导航或控件引用的组件不能使用 `raster`。

### 3. 逐屏高保真规格

- `05-high-fidelity/screen-specs.json.specs[]` 必须与所有适用的 screen × state × viewport 组合完全一致。每条规格都精确列出对应的 `element_ids`、组件版本 `component_refs[{id,revision}]` 和人工检查记录 `review:{by,note}`。
- 每个适用的 default screen × viewport 必须使用 `visual_mode=full`，提供阶段目录内真实可查看的 raster `asset_path`，`asset_kind` 为 `design` 或 `render`，并含至少一项由审查人选定的关键尺寸/间距测量。每项 `measurements[]` 包含 `id`、`element_id`、`property`、数值 `expected`、`unit` 和非负数值 `tolerance`。校验器会检查字段、元素关联和数字容差，不会判断这个测量是否真能代表关键尺寸；由审查人确认。
- 其它适用状态可以使用 `visual_mode=delta`，写明该 screen 的 default `base_state_id` 和非空 `state_delta`，不再伪装成完整图片。delta 的测量继承 default 测量，并可按 ID 覆盖或增加；QA 仍须逐项核对继承后的完整测量集合。
- `prototypes[]` 可选，独立列明 `journey_id` 和阶段目录内的 HTML `path`。静态视觉规格不等于原型，原型也不等于最终运行验收。

### 4. 实现映射与运行包清单

- `07-frontend-implementation/implementation-map.json` 保留 v1 的 `revision` 和完整路由映射，新增 `implemented_by`、`runtime_manifest_path`、`runtime_fingerprint`、`elements[]` 和 `components[]`。
- `runtime_manifest_path` 指向阶段目录内 JSON；其中 `files` 是“相对文件路径 → SHA-256”的非空映射。每个路径都必须是阶段目录内存在的文件，内容哈希必须匹配；`runtime_fingerprint` 等于该 manifest 文件本身的 SHA-256。
- `elements[]` 将每个适用的必需元素映射为 `{screen_id,element_id,code_path}`；`code_path` 必须出现在 manifest 的 `files` 中。`components[]` 将实际实现使用的组件映射到精确 `{id,revision}`。不能只登记首页或一个代表组件。
- 该指纹只绑定提交在第 07 阶段的已列文件，不会验证阶段外未登记源码，也不能证明用户浏览器正在运行同一进程。运行验收仍要核对进程工作目录、URL、构建身份和目标 revision。

### 5. 运行态 QA、旅程点击与独立结论

- `08-visual-qa/evidence.json.items[]` 延续 v1 的证据字段。`kind=runtime_capture` 时还要有真实页面 `source_url`、`runtime_fingerprint` 和 `captured_at`；route、state、viewport、revision、URL 路径与图像签名必须相符。`concept` 和 `mock` 不能充当运行截图。
- `qa-matrix.json.rows[]` 对每个适用的 screen × state × viewport 都要通过。每行包含 `baseline_sha256`（delta 指向对应 viewport 的 default 完整图片哈希）、阶段内 `comparison_path`（MD/HTML/raster）、覆盖所有必需元素且全部通过的 `element_checks[]`，以及覆盖完整测量集合的 `measurements[]`。每项检查都引用与该 screen/state/viewport 匹配的运行证据；实际测量值须在 expected ± tolerance 内。
- `journey_results[]` 必须逐条覆盖每个旅程 × `delivery.json` 中声明的**全部视口**；注册表至少包含 desktop 和 mobile，若再登记 tablet 等视口，也必须走查。每条结果含 `journey_id`、`viewport_id`、`result=pass` 和按注册顺序排列的 `steps[]`。每步含与计划一致的 `action`、真实观察到的 `observed_result`、阶段内的 `interaction_path` 操作记录和匹配的运行 `evidence_id`。
- `verdict.json` 新增 `reviewed_by` 和 `open_blockers`；独立审查者不得与 `implementation-map.json.implemented_by` 相同，放行必须是空阻塞清单。
- 校验器只验证记录形状、引用、文件、签名和数字关系。浏览器是否真点击、截图是否来自目标页面、比较结论是否可信、记录人是否真实执行，仍需人工或主控独立审查。HTTP 200、打开 tab、结构校验通过或实现者自述都不能替代页面级证据。

### v2 新增字段填表示例（合成内容）

以下展示每种新增字段的完整对象形状，路径相对于各阶段目录。尖括号内的 SHA-256 和图片名是待替换占位值，示例文件未提供，不可直接报告为通过。实际交付必须按注册表展开所有适用组合，而不是只保留下面的代表行。

`delivery.json` 的 v2 增量：

```json
{
  "schema_version": 2,
  "project": {"id": "sample", "name": "Synthetic sample", "revision": "r2"},
  "viewports": [
    {"id": "desktop", "width": 1440, "height": 900},
    {"id": "mobile", "width": 390, "height": 844}
  ],
  "pages": [{
    "id": "catalog",
    "route": "/catalog",
    "screens": [{
      "id": "catalog-main",
      "states": [
        {"id": "catalog-default", "kind": "default"},
        {"id": "catalog-loading", "kind": "loading"},
        {"id": "catalog-empty", "kind": "empty"},
        {"id": "catalog-error", "kind": "error"},
        {"id": "catalog-denied", "kind": "permission_denied"},
        {"id": "catalog-success", "kind": "success"}
      ]
    }]
  }],
  "journeys": [{
    "id": "find-item",
    "steps": [{
      "page_id": "catalog",
      "screen_id": "catalog-main",
      "state_id": "catalog-default",
      "action": "输入关键词并提交搜索"
    }]
  }]
}
```

`02-ux-architecture/state-matrix.json` 的 v2 适用状态行：

```json
{
  "rows": [{
    "page_id": "catalog",
    "screen_id": "catalog-main",
    "state_id": "catalog-default",
    "viewport_id": "desktop",
    "applicability": "applicable",
    "behavior": "显示目录与搜索结果入口",
    "required_elements": [
      {"id": "primary-navigation", "role": "navigation", "component_id": "main-nav"},
      {"id": "search-submit", "role": "control", "component_id": "search-control"},
      {"id": "catalog-heading", "role": "content"}
    ]
  }]
}
```

对其余五种 state 和每个 viewport 重复登记适用性；不适用组合仍按 v1 行规则列出 `reason`。每个适用状态的元素 ID 在该组合内唯一。角色限 `navigation`、`control`、`content`、`decoration`；导航/控件必须有设计组件引用。

`03-visual-direction/style-decision.json` 保留 v1 字段，例如 `source_kind=concept`、`concept_path`、`selected_id` 和选择记录；`04-design-system` 的增量示例：

`tokens.json`：

```json
{
  "colors": {"surface": "#ffffff"},
  "typography": {"body": "16px/24px"},
  "spacing": {"page-gutter": "24px"},
  "layout": {"content-max": "1200px"},
  "style_sha256": "<64 位小写 SHA-256：所选基线文件>"
}
```

`component-inventory.json`：

```json
{
  "components": [
    {"id": "main-nav", "revision": "1", "master_path": "masters/main-nav.html", "render_mode": "structured", "used_by": ["catalog-main"]},
    {"id": "search-control", "revision": "1", "master_path": "masters/search.html", "render_mode": "code", "used_by": ["catalog-main"]}
  ]
}
```

`05-high-fidelity/screen-specs.json` 中每个 default × viewport 使用 `full`；其它状态可使用 `delta`：

```json
{
  "specs": [
    {
      "screen_id": "catalog-main", "state_id": "catalog-default", "viewport_id": "desktop",
      "visual_mode": "full", "asset_path": "screens/catalog-default-desktop.webp", "asset_kind": "design",
      "element_ids": ["primary-navigation", "search-submit", "catalog-heading"],
      "component_refs": [{"id": "main-nav", "revision": "1"}, {"id": "search-control", "revision": "1"}],
      "measurements": [{"id": "page-gutter", "element_id": "catalog-heading", "property": "outer page gutter", "expected": 24, "unit": "px", "tolerance": 2}],
      "review": {"by": "reviewer", "note": "已打开图片并核对页面范围和必需元素"}
    },
    {
      "screen_id": "catalog-main", "state_id": "catalog-loading", "viewport_id": "desktop",
      "visual_mode": "delta", "base_state_id": "catalog-default", "state_delta": "结果区域显示加载占位，导航与搜索位置不变",
      "element_ids": ["primary-navigation", "search-submit", "catalog-heading"],
      "component_refs": [{"id": "main-nav", "revision": "1"}, {"id": "search-control", "revision": "1"}],
      "measurements": [],
      "review": {"by": "reviewer", "note": "已对照默认图确认状态差异"}
    }
  ],
  "prototypes": [{"journey_id": "find-item", "path": "prototype/index.html"}]
}
```

实际 `specs` 必须精确覆盖 state-matrix 的所有适用组合；这段只示范字段。default 必须有完整 raster 图片及至少一个审查人选定的关键尺寸/间距测量。测量属性含义由人审，不靠校验器从图像推断。

`07-frontend-implementation/implementation-map.json` 与其 manifest：

`runtime-manifest.json`（哈希值替换为对应文件真实 SHA-256）：

```json
{"files": {"src/catalog-page.tsx": "<64 位小写 SHA-256>"}}
```

`implementation-map.json`：

```json
{
  "revision": "r2",
  "routes": [{"page_id": "catalog", "route": "/catalog", "screen_ids": ["catalog-main"]}],
  "implemented_by": "implementer",
  "runtime_manifest_path": "runtime-manifest.json",
  "runtime_fingerprint": "<runtime-manifest.json 文件的 SHA-256>",
  "elements": [
    {"screen_id": "catalog-main", "element_id": "primary-navigation", "code_path": "src/catalog-page.tsx"},
    {"screen_id": "catalog-main", "element_id": "search-submit", "code_path": "src/catalog-page.tsx"},
    {"screen_id": "catalog-main", "element_id": "catalog-heading", "code_path": "src/catalog-page.tsx"}
  ],
  "components": [{"id": "main-nav", "revision": "1"}, {"id": "search-control", "revision": "1"}]
}
```

真实的 `runtime-manifest.json` 必须列出每个被映射文件，且文件存在、哈希匹配；`code_path` 必须是该清单中的路径。示例中的同一文件可映射多个元素，但不能因此省略元素映射。

`08-visual-qa` 每条运行证据、页面比较、元素检查、测量和旅程结果都必须能互相引用：

`evidence.json`：

```json
{
  "items": [{
    "id": "catalog-default-desktop", "kind": "runtime_capture", "path": "captures/catalog-default-desktop.png",
    "route": "/catalog", "viewport_id": "desktop", "state_id": "catalog-default", "revision": "r2",
    "captured_at": "2026-09-27T10:00:00Z", "source_url": "https://app.example.test/catalog",
    "runtime_fingerprint": "<implementation-map 中的指纹>"
  }]
}
```

`qa-matrix.json`（每个适用组合一行；`journey_results` 覆盖所有声明视口）：

```json
{
  "rows": [{
    "screen_id": "catalog-main", "state_id": "catalog-default", "viewport_id": "desktop",
    "result": "pass", "evidence_ids": ["catalog-default-desktop"],
    "baseline_sha256": "<stage-05 对应完整图的 SHA-256>", "comparison_path": "comparisons/catalog-default-desktop.md",
    "element_checks": [
      {"element_id": "primary-navigation", "result": "pass", "evidence_id": "catalog-default-desktop"},
      {"element_id": "search-submit", "result": "pass", "evidence_id": "catalog-default-desktop"},
      {"element_id": "catalog-heading", "result": "pass", "evidence_id": "catalog-default-desktop"}
    ],
    "measurements": [{"id": "page-gutter", "actual": 24, "evidence_id": "catalog-default-desktop"}]
  }],
  "journey_results": [{
    "journey_id": "find-item", "viewport_id": "desktop", "result": "pass",
    "steps": [{
      "action": "输入关键词并提交搜索", "observed_result": "结果区域展示匹配条目",
      "interaction_path": "interactions/find-item-desktop.md", "evidence_id": "catalog-default-desktop"
    }]
  }]
}
```

此示例只列一个 desktop 行。实际矩阵要覆盖每个适用组合；每条旅程都要在 `delivery.json` 声明的所有 viewport（至少 desktop 和 mobile）逐步真实操作并附证据。实施者之外的独立审查结论形状：

```json
{"verdict": "pass", "by": "reviewer", "basis": "所有声明页面、状态、视口与旅程均完成核对", "reviewed_by": "reviewer", "open_blockers": []}
```

完成报告时要保留证据等级：图片签名、哈希和校验器通过只证明文件和记录之间的机械关系；浏览器操作、运行服务归属、页面视觉和用户签收需有独立实际证据。
