# 来源、吸收与舍弃

## 1. 吸收表

| 来源 | 许可 | 吸收了什么 | 舍弃了什么 | 原因 |
|---|---|---|---|---|
| Leonxlnx/taste-skill（design-taste-frontend，已安装） | 见其 README | 论点表先于设计；点子来自主体与竞品测试；14 遍看图法与 ROUND 格式；修复顺序；3 轮上限；文本左边线 2 到 3 条；相邻节版式不同；强调色 <5%；正文满墨色；动效时长表；`html.js` 门控与 2.5 秒保险；lint / inspect 的门禁思路 | 至少 4 张真图与自动取图；两行 32 字符英文标题预算；创意分权重用于 clear 档；允许编造演示内容；默认 8 个动元素的硬门槛 | 讲解页以图表与表格为主；取图需授权；中文标题按字数算；内容必须来自证据 |
| juliobsz/skills awwwards | MIT | 流程门禁（简报→概念卡→艺术指导→构建→QA→盲评）；genericness test；按角色命名的 4 到 6 色；动效动词；一个签名时刻；一个时钟；驱动模块；sticky 舞台；加载器真实进度 1.1 到 2.6 秒；减少动效门控；数据属性 API；hover 在 `@media (hover: hover)` 且 focus-visible 同步；评分表（show 档）；"remove one accessory"；真实内容规则 | 把 GSAP 文件放进本 skill（只从 CDN 加载）；Next.js / Astro 适配；英文显示字行高 0.85 与负字距；无破折号与句首大写的英文文案规则；Unsplash 取图脚本；部署与 OG | 离线可开与不装包；中文排版不同；取图需授权 |
| Caho1/open-claude-ui | MIT（内容来自对第三方产品的拆解） | 令牌三层结构；表面明度阶梯与低透明度边框；单闭合边框原则；角色绑定字号；5 档时长成倍增长；grid 0fr→1fr 折叠；渐进披露的折叠头部写清内容；`tabular-nums`；`text-wrap: balance/pretty`；同心圆角；焦点环多层；"视觉廉价感来自硬边框与死黑阴影"的判断 | 全部色值、字体名、图标、logo、暖米底与陶土强调的外观、衬线问候语、聊天与桌面专用组件、Framer Motion 弹簧参数（自相矛盾） | 版权与商标；数值不可靠；只取方法 |
| cathrynlavery/diagram-design（已安装） | MIT | 45 类图的选型与预算；4px 网格；节点 ≤9；正交连线；形状承载类型；中文 12px 下限与宽度估算；离线 `self_check.py --offline` | 默认皮肤（米白、衬线、橙色、eyebrow）；Google Fonts 默认链接；7 到 9px 小字 | 踩中 Defaults 禁令；中文不可读 |
| wheresryan22/anatomy（已安装） | MIT | "物体即解释"；Figure 档预算；四调阴影与一个 `lit`；读数真实单位；空闲 1.4 秒自动演示与交互暂停；键盘与 `aria-valuetext`；reduced-motion 跳到目标；"能删掉而解释仍成立就删" | `publish.mjs`（公开发布）；Hero / Epic 档默认 | 不发布到公开库；成本 |
| frontend-design（官方插件） | 见其 LICENSE | 设计计划两遍法（计划→对照简报改默认）；五类 AI 默认外观；"一处大胆"；文案规则 | 无 | |
| artifact-design（内置） | 内置 | 平台契约；三态主题结构；静止即完整；安全区侧边距 | "最多看一次渲染图"（用户规则要求修到过） | 用户规则优先 |
| dataviz（内置） | 内置 | 选形式→分配颜色→校验器→标记→悬停→无障碍；强调法；表格孪生；状态色固定 | 无 | |
| artifact-diagramming（内置） | 内置 | 画机制不画名称；每条箭头有标签；`currentColor`；figure/figcaption/role=img | 无 | |
| 灵感库（navbar.gallery、footer.design、cta.gallery、404s.design、60fps.design，加扩展 6 站；见 `inspiration-library.md` 与 `inspiration/`） | 多数未写许可 | 入口、分类方式、与本 skill 组件的对应关系 | 图片、提示词、代码、外观 | 许可不明。只作灵感索引，实际吸收时再逐条登记 |
| 用户全局设计规则 | 用户 | 5 步流程；10 项检查表；"门禁不证明设计好" | 无；冲突项按 `gears.md` 第 3 节解释 | |

## 2. 取更严值的记录

| 项 | A 路 | B 路 | 取值 |
|---|---|---|---|
| 同屏字号 | taste ≤5 | 用户 ≤4 | 4 |
| 触控命中区 | juliobsz ≥24px | taste ≥44px | 普通 ≥24px，主操作 ≥44px |
| 图内最小字 | diagram-design 7 到 9px（拉丁） | diagram-design 中文 12px | 12px |
| 正文对比 | 各方 4.5:1 | 一致 | 4.5:1，深浅各算 |
| 加载器 | taste 无 | juliobsz 1.1 到 2.6 秒 | 按预算预设：clear 无；mixed ≤1.2；show 1.1 到 2.6 |
| 弹簧参数 | open-claude-ui 两处矛盾 | 无 | 不抄数值，只取"结构类不回弹、反馈类可回弹" |

## 3. 运行时依赖（从 CDN 加载，不分发）

| 库 | 版本 | 许可 | 说明 |
|---|---|---|---|
| GSAP 与 ScrollTrigger | 3.15.0 | GSAP 标准免费许可（standard no-charge license），见 https://gsap.com/standard-license | 从 CDN 加载，未再分发。使用条件以该链接为准 |
| Lenis | 1.3.26 | MIT | 从 CDN 加载，未再分发 |

零依赖引擎 `motion-engine.js` 是 预设 `clear`的引擎，也是 CDN 失败时的回退。

## 4. 版权规则

1. 不使用任何 Anthropic / Claude 品牌色、字体名、图标、logo，也不仿制。
2. 引擎保留 juliobsz 的 MIT 声明。GSAP 文件不放进本 skill。
3. 本 skill 自写的文字与代码以 MIT 发布。
