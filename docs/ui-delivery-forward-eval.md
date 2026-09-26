# UI Delivery Skill 前向行为评估

评估日期：2026-09-26（Asia/Taipei；读取与记录约 21:02–21:10）
范围：仅按当前 UI Delivery 与相关阶段 Skill 的说明处理 A–C 三个文本请求，以及 D 一个指定的合成需求。没有读取测试、Issue 或预期答案；没有访问被测产品仓库或运行应用，也未修改 Skill/代码。本报告记录的是受限行为评估，不是产品实机验收。

## 读取材料与执行边界

本次读取了以下 Skill 与阶段工作流：

- `skills/ui-delivery/AGENTS.md`、`skills/ui-delivery/SKILL.md`
- `skills/ui-delivery/references/AGENTS.md`、`skills/ui-delivery/references/handoff-contract.md`
- `skills/ui-ux-architecture/AGENTS.md`、`SKILL.md` 与 `references/workflow.md`
- `skills/ui-frontend-implementation/AGENTS.md`、`SKILL.md` 与 `references/workflow.md`
- `skills/ui-visual-direction/AGENTS.md`、`SKILL.md` 与 `references/workflow.md`
- `skills/ui-visual-qa/AGENTS.md`、`SKILL.md` 与 `references/workflow.md`
- `skills/ui-product-planning/AGENTS.md`、`SKILL.md`
- `skills/ui-delivery/scripts/AGENTS.md`；执行了 `skills/ui-delivery/scripts/delivery.py`

阶段文件均相对于仓库根目录 `/Users/dw/Desktop/my_skill/`。其中：

`docs/` 下没有模块级 `AGENTS.md`；UX、前端实现、视觉方向、视觉验收阶段目录下也没有 `references/AGENTS.md`。产品规划的 `references/workflow.md` 在 D1 评估时仍处于编辑中、暂缺于工作区：其 AGENTS 与 SKILL 已引用该文件，但当时目录清单和读取均未找到。该工作流目前已存在，并已在 D2 复核中读取。本轮不调用图像生成或浏览器工具，也不使用真实项目、运行地址或客户数据。A–C 不创建阶段文件或快照；D 按父任务要求在隔离的 `/tmp` 工作区执行。

## A. 只补客户列表请求失败反馈与重试

**用户输入**
“已有设计系统和客户列表实现，只补客户列表请求失败时的反馈与重试，不重做整体风格。”

**采用阶段**
局部 UX/信息架构阶段，用来定义失败态、重试路径和低保真位置；前端实现阶段因缺少目标仓库、项目规则、现存页面和可运行环境而阻塞。以用户描述为范围输入，不把“已有实现和设计系统”写成已检查事实。

**可交付的交互契约（本轮实际产出）**

| 场景 | 状态与行为 |
|---|---|
| 打开客户列表并发出请求 | 保持现有页面及其设计系统；沿用已有加载表现（本轮未能检查其样式）。 |
| 请求失败 | 在客户列表内容区域呈现局部错误反馈及“重试”入口；不要把失败误呈现为空列表，也不要替换整页或重新设计视觉风格。 |
| 点击重试 | 对相同列表请求再次发起请求；展示加载中反馈并防止重复触发。查询参数、筛选、排序、分页及当前页面上下文应保留；这些是待对照现有实现验证的行为假设。 |
| 重试成功 | 清除失败反馈并呈现响应结果。 |
| 重试再次失败 | 保持错误反馈和再次重试入口；不得声称已经恢复。 |

对应结构骨架：`customer-list` 页面中的列表内容区在 `error` 状态显示一条错误说明和重试按钮，用户操作后进入 `loading`，请求成功进入 `success`，失败则留在 `error`。错误文案可采用“客户列表暂时加载失败，请重试”，避免向用户暴露底层异常文本。屏幕布局、组件、色值与既有令牌需以实际设计系统为准。

**对用户的实际回应**
“我会把范围限定在客户列表的请求失败反馈和重试，不改整体视觉。可确定的行为是：失败时在列表区域显示错误提示和重试入口；重试时显示加载反馈；成功后恢复列表，继续失败则保留提示并允许再次重试。筛选、排序、分页等上下文是否保留，需要对照现有页面和请求实现核实。本次只收到文字描述，没有项目文件或运行页面，所以我能交付这份局部交互契约，不能声称已修改代码、接通真实请求或验证视觉效果。实现阶段目前阻塞在缺少可检查的项目与运行环境。”

**可观察结果及限制**
形成了具体的错误态与重试行为，不引入新的品牌/视觉方向；未产出或检查真实页面文件、设计令牌、API 行为和运行截图。客户列表路由、权限规则、既有加载态、请求参数保留机制均未知。故 UX 输出是基于需求的局部契约，不是完整页面信息架构；前端实现没有完成。

## B. 社区借书页面的三种视觉风格图片方案

**用户输入**
“为社区借书页面做三种不同视觉风格的图片方案，让我选；内容、结构相同。”

**采用阶段与状态**
`ui-visual-direction`；状态为 **blocked**。本次环境约束禁止调用图像生成和浏览器工具，因此不能产出并查看图片。虽然用户已明确要求三种风格并指定内容、结构保持一致，但没有具体页面内容/结构资产可供逐图核对。

**对用户的实际回应**
“目前无法在这个环境里生成并查看三张可供比较的页面方案，因此视觉方向阶段标记为 blocked；现在没有图片方案可供你选择。我会保留‘三种风格、相同内容与结构’这两项约束，不用文字描述冒充图片，也不代替你选定方向。解除阻塞后需要实际生成并检查三张图片，再交给你比较。”

**可观察结果及限制**
没有方向图片、可查看候选或用户选择记录；没有伪造 `direction-options.md` 中的图片候选，也没有将文字方向描述冒充可交付方案。阶段未通过，用户尚无内容可选。

## C. Build 成功、只有 mock 高保真图、没有运行地址时请求整体放行

**用户输入**
“前端build成功，只有一张标注mock的高保真图、没有可运行地址，现在能把整个UI交付标通过吗？”

**采用阶段与判断**
采用 `ui-visual-qa` 的证据规则，并按交接契约判断整体交付门禁。**不能标整体通过。** QA 当前状态是 **blocked / 无法验证**：缺少运行地址或启动方式，因此无法检查目标版本的实际路由、状态和视口。build 成功只说明 build 门禁通过；标注为 `mock` 的图片属于设计对照材料，不是运行截图。

**对用户的实际回应**
“现在不能把整个 UI 交付标为通过。Build 成功只证明构建门禁通过；这张标注为 mock 的图不能证明真实页面可运行或交互正常。视觉验收目前应标为 blocked／无法验证，而不是 pass。下一步请提供目标版本的可运行地址或启动方式及 revision；随后需要按页面、关键状态和视口检查真实运行界面并留存可复核证据，再由独立审查人给出整体 verdict。”

**可观察结果及限制**
没有尝试访问不存在的运行地址，没有把 mock 纳入 `runtime_capture`，也没有伪造 QA 截图、矩阵或 revision。整体交付保持未通过放行；需要可达的运行应用、明确 revision 和真实页面/状态/视口证据后才能继续 QA。

## D. 仅做社区图书馆公开借阅入口的产品页面规划

**用户输入**
“给社区图书馆做公开借阅入口：读者查询可借书并提交预约；馆员审核属于现有后台；本轮只做读者公开页 /borrow。预约确认回执代表提交成功，库存/登录由现有系统提供；禁止杜撰借阅量；PC1440/mobile375。先只交产品页面规划。”

**采用阶段与输入性质**
只采用 `ui-product-planning`，没有进入任何下游阶段。父任务明确指定本例全部需求材料为合成案例，因此规划产物和 revision 均有标记，不指向真实机构或系统。

**实际产物路径**
隔离工作区为 `/tmp/ui-delivery-forward-D.6IPrFgFS/workspace/`。阶段文件：

- `01-product-planning/product-brief.md`：目标、读者任务、成功信号、范围/非目标、系统依赖、假设和未决项。
- `01-product-planning/page-inventory.json`：页面 `/borrow`、唯一页面 ID `borrow`、屏 `borrow-entry`、入口说明、任务和状态注册表。
- `delivery.json`：项目/revision 合成标识；`desktop=1440 px`、`mobile=375 px`。脚手架默认高度 `900/844 px` 保留并明确标注为未由需求给定的占位值。
- `01-product-planning/stage.json` 与 `01-product-planning/snapshot.json`：产品规划阶段状态和快照。

**产物复核与命令结果**
复核了输入事实是否进入页面目标与任务、公共页和馆员后台的边界、确认回执语义、两个宽度注册，以及借阅量等未给数据是否保持未定义。复核通过后，将规划阶段记为 `ready`，review note 标明这是受 root 委托的规划产物复核，不是产品验收。

| 命令 | 结果 |
|---|---|
| `mktemp -d /tmp/ui-delivery-forward-D.XXXXXXXX` | 退出码 `0`；目录 `/tmp/ui-delivery-forward-D.6IPrFgFS` |
| `python3 skills/ui-delivery/scripts/delivery.py init /tmp/ui-delivery-forward-D.6IPrFgFS/workspace` | 退出码 `0`；建立 draft 套件工作区 |
| `python3 skills/ui-delivery/scripts/delivery.py snapshot /tmp/ui-delivery-forward-D.6IPrFgFS/workspace --stage product-planning` | 退出码 `0`；输出 `Snapshotted product-planning; status remains ready.` |
| `python3 skills/ui-delivery/scripts/delivery.py validate /tmp/ui-delivery-forward-D.6IPrFgFS/workspace --through product-planning` | 退出码 `0`；输出 `Contract valid through product-planning; human visual judgment is separate.` |

**关键边界与观察**
规划明确不做馆员后台、不重造库存和登录、不写借阅量或预约量，也没有把“预约提交成功”扩张成“馆员审核通过”或“借阅完成”。权限拒绝、查询/预约失败等状态登记了来源依赖和待确认点，没有为它们虚构具体处理政策。脚手架与注册表校验通过只说明规划阶段契约有效。

未做 UX 架构、视觉方向、设计系统、高保真、动效、前端实现或视觉 QA；没有接触真实图书目录、库存、登录系统、预约服务或运行环境。D 是合成需求上的规划产物测试，不是现实产品交付或实机验收。

## 评估结论

A–C 分别产生了局部交互契约、视觉方向阻塞回应、以及拒绝以 build/mock 冒充整体通过的 QA 判断；D 实际产出了合成需求下的产品规划文件，并通过产品规划阶段快照与前缀契约校验。Skill 边界阻止了无项目输入时声称已实现、以及没有运行证据时声称已验收。A 的筛选/分页保留等内容仍是明确假设；B 没有可查看图片就没有可选交付；C 的状态是无法验证而不是已知运行缺陷；D 的 CLI 通过只证明规划产物与套件契约自洽。

本文件只记录技能行为。A–C 不代表客户列表的真实实现、社区借书页面设计或产品实机验收；D 是合成需求规划，不代表真实机构产品交付。

## D2. 补齐产品规划工作流要求并检查样例

D1 的 `delivery.py snapshot` 与 `validate --through product-planning` 均通过，证明当时的阶段文件结构、状态和哈希链符合契约；这不代表规划内容已完整满足产品规划工作流。D1 的 `product-brief.md` 缺少两项明确内容：模块到用户任务映射，以及 CTA 优先级矩阵。

D2 将原合成案例复制到 [`docs/examples/ui-delivery-product-planning/`](examples/ui-delivery-product-planning/)，只保留根 `delivery.json` 和 `01-product-planning/` 下的四个阶段文件。产品简报现在列明查询模块服务于“找可借书”、查询为主；结果/选择模块服务于选书并提交预约，预约为主且受现有资格与登录规则约束；提交回执模块只说明提交成功，返回查询为次，馆员审核不在本轮范围。矩阵标注为规划建议，不声称系统已有特定字段或政策，并明确预约回执不表示审核通过。

复核时重做了阶段快照，并运行 `python3 skills/ui-delivery/scripts/delivery.py validate docs/examples/ui-delivery-product-planning --through product-planning`；两条命令均通过。`stage.json` 的 review note 已更新为 D2 内容复核说明。校验只证明本样例的产品规划阶段文件与契约一致，不是研究、真实业务或实机验收。示例目录的使用说明见 [`README.md`](examples/ui-delivery-product-planning/README.md)。
