# 扩展资源：推文之外的灵感库与组件库

核实：2026-10-15。本页只收录读到了首页文字的资源。被拦截、重定向或只取到标题的站点已删除，要用时重新核实再加。都没有看图。

## 1. 登记表

| 站点 | 内容 | 许可与价格 | 状态 |
|---|---|---|---|
| component.gallery | 组件参考：60 种组件，95 个设计系统，2671 个例子。对比不同设计系统如何做同一个组件（如 Tabs、Accordion、Pagination、Popover） | 未写。不提供组件代码，部分设计系统带代码示例的标记 | 已读 |
| awwwards.com/websites/scrolling | 滚动类获奖网站合集。可按类别（27 类）和技术（GSAP、WebGL、Three.js 等）筛选 | 未写 | 已读 |
| pudding.cool | 数据驱动的视觉故事。例：#204 生日效应、#217 小说里的 20 万个比喻、#216 互动旅程、#220 浏览 5000 份餐厅菜单 | 未写 | 已读 |
| explorabl.es | "可探索的解释"合集，站点代码开源（GitHub），许可需查仓库 | 未写 | 已读 |
| easings.net | 30 个缓动函数名（Sine、Quad、Cubic、Quart、Quint、Expo、Circ、Back、Elastic、Bounce，各含 In、Out、InOut）。站点开源，许可需查仓库 | 未写 | 已读 |
| reactbits.dev | React 动画组件：文字动画、动画、组件、背景、微交互。复制源码或用 CLI 安装 | 未写 | 已读 |
| designeer.xyz | 索引站（2026 年上线，免费）：把 Awwwards、Dribbble、Mobbin、Land-book、navbar.design、footer.design、Saaspo、Supahero、Sombra、Cosmos、shadcn/ui、Radix、React Bits、OKLCH、Three.js 等收在 Inspiration、Components、Build、Visuals、Utilities 五栏，另有 Designers 栏。它自己不出作品，只能当"找一手站点的地图"。用户 2026-10-17 提议 | 免费 | 未读：VPS 访问被 Cloudflare 人机验证拦下，信息来自 Product Hunt 页面与搜索摘要（2026-10-17）。按 design-pipeline 案例库规则，入库仍要打开它指向的原站 |

## 2. 各站怎么用

### component.gallery

1. 用于：本 skill `components.md` 的任何组件，查"别人怎么拆它"。
2. 查法：按组件名进入，比较 5 个设计系统的变体、命名、状态。
3. 示例：设计折叠区（Accordion）。比较各系统的头部写法、展开图标位置、是否允许同时多个展开。取：命名和状态清单。舍：外观。落地：本 skill 规则"最多两层，折叠头写清内容"。
4. 价值：它给出"成熟设计系统的共识"，适合解决"这个组件该叫什么、该有几个状态"。

### awwwards 滚动合集

1. 用于：预设 `show`的舞台区构图参考。
2. 查法：筛选技术 GSAP，类别选 Institutions 或 Magazine/Newspaper/Blog，因为接近讲解类内容。
3. 示例：只看 5 条的章节开场构图和滚动节奏。获奖站倾向炫技，需要对照 `gears.md` 的预算后再取。
4. 注意：获奖站常违反"原生滚动""可读性"底线。不抄。

### pudding.cool

1. 用于：讲解页的叙事方法。一个问题一个故事，数据先行，互动服务问题。
2. 示例：#217 的做法是把 20 万个例子汇成一个分析问题。借鉴到本页：每一章以一个可检验的问题开场（本项目已用结论句标题）。
3. 注意：站点首页没有说明技术与代码是否开源。不假设。

### explorabl.es

1. 用于：想让读者"动手调一个参数看结果"时。本页可用在 s5 的成熟度图（切换阶段看证据强弱）。
2. 站点代码开源，许可看其 GitHub 仓库。使用前先读许可。

### easings.net

1. 用于：给 `motion.md` 的时长表补缓动词汇。结构类用 Out 系，不回弹（不用 Back、Elastic、Bounce）。
2. 页面没有给 cubic-bezier 数值，数值须自查，不编造。

### reactbits.dev

1. 用于：想法层的词汇："文字动画""背景""微交互"。
2. 本 skill 输出单文件 HTML。不引入 React。只看效果名，用 GSAP 引擎自写。

## 3. 优先级建议

| 优先级 | 资源 | 原因 |
|---|---|---|
| 高 | component.gallery、navbar.gallery、60fps.design | 与讲解页的组件和动效直接相关，已核实 |
| 中 | pudding.cool、explorabl.es、easings.net | 叙事与交互方法，已核实 |
| 低 | footer.design、404s.design、cta.gallery | 营销导向多，取少量做法 |
| 仅预设 show | awwwards 滚动合集、reactbits.dev | 炫技方向 |
| 索引 | designeer.xyz | 找一手站点用。Supahero（hero）、Saaspo（page、pricing、testimonial、form）、Sombra（深色氛围）是它指向的、本表还没登记的三个入口 |
