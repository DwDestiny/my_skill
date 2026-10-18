# navbar.gallery：导航栏案例库

核实：2026-10-15 读首页、`/type/side-bar`、`/blog/sidebar-navigation`、`/navbar/cloudflare` 的文字。未看截图。

## 1. 它是什么

真实网站的导航栏案例库。作者 Christina Liubynska，Mobbin 赞助，可投稿。许可与价格：站点未写。无源码。

## 2. 结构与网址

| 项 | 内容 |
|---|---|
| 类型页 | `/type/static`、`/type/dropdowns`、`/type/mega-menu`、`/type/side-bar`、`/type/search-bar`、`/type/announcement`、`/type/full-screen`、`/type/breadcrumbs` |
| 全部 | `/browse`（约 38 页） |
| 条目页 | `/navbar/<名称>`，例如 `/navbar/cloudflare` |
| 条目页字段 | 标题、一句话简介、设计者、投稿者、导航类型、网站类型（如 SaaS）、桌面截图、手机截图、访问链接 |
| 文章 | `/blog/sidebar-navigation`、`/blog/what-is-a-mega-menu` |

条目页没有导航栏的文字分析。结构要自己看截图或打开原网站。

## 3. 文章里的可用规则（转述）

侧栏导航（`/blog/sidebar-navigation`）：

1. 条目多、彼此无明确分类但都要快速到达时，用侧栏。
2. 顶栏会拥挤时，用侧栏。
3. 侧栏用竖排，链接旁加图标。
4. 预留增长：用手风琴展开。
5. 侧栏可兼做功能：主题切换、滚动进度（文章举例：一个作品集放了主题开关，一个站点的侧栏动画跟随滚动进度）。
6. 文章没有给数字规则，也没有讲手机端。手机端要自己设计。

## 4. 怎么用

1. 在设计计划写下导航任务，例如"12 个目录项，桌面用侧栏，手机用抽屉"。
2. 打开对应类型页。侧栏页共 4 页，列表第 1 页有 13 条，包括 Aveon、Big Dirty Agency、Bud、Ayush Wanjari、Coterie、E Dey Happen、Brethen Design Co.、Mugen Studio、Zoox、Escape Cafe、Hims、Significa、Three Circles。
3. 每个条目只看三件事：当前位置怎么提示、收起后剩什么、手机视图怎么处理。
4. 写吸收记录，格式见 `../inspiration-library.md` 第 4 节。

## 5. 示例：工程设计院讲解页的目录

| 项 | 内容 |
|---|---|
| 任务 | 12 个目录项。桌面常驻。手机收为抽屉（本 skill `components.md` 第 2 节） |
| 查询路径 | `/type/side-bar` 看桌面。条目页看手机截图 |
| 候选 | 上面第 2 步的 13 条。需要用户同意后才可保存截图 |
| 取 | 当前章节的提示方式。滚动进度的表达。收起态保留的信息量 |
| 舍 | 外观：图标风格、配色、字体、品牌图形 |
| 落地 | 用本页令牌重画。当前项用下划线加面板底，不只靠颜色。命中区 ≥24px |
| 记录示例 | `navbar.gallery / 侧栏 / 取：滚动进度跟随目录 / 舍：动画样式 / 理由：mixed 档阅读区动效 ≤2` |

## 6. 不适用

1. 巨型菜单（Mega Menu）、搜索栏、公告条：讲解页单页，用不到。
2. 条目多为营销站，转化导向。只取结构，不取"引导点击"的做法。
