# footer.design：页脚案例库

核实：2026-10-15 读首页与 `/styles/large-type`。未看截图。许可与价格：未写。无源码。构建者 NOOON。

## 1. 结构与网址

| 项 | 内容 |
|---|---|
| 风格页 | `/styles/typographic`、`small-type`、`illustrative`、`grid`、`flat`、`animated`、`cards`、`bright`、`dark`、`large-type`、`bold`（均在 `/styles/` 下） |
| 全部 | `/browse`（约 65 页） |
| 条目页 | `/sites/<名称>` |
| 其他 | `/submit` 投稿，`/info` 介绍。部分条目带"编辑精选"标。有赞助条目，会跳到外站 |
| 条目信息 | 列表只有名称、缩略图、站点链接。无文字描述 |

`/styles/large-type` 第 1 页有 12 条：Trove、Aperios Design、Nothin'、Decimals、Playfolly、The Design Society、Reality Is__、Cronicle、Heron AI、Outway、Flexion、++hellohello。共 27 页。

## 2. 怎么用

1. 先问页脚要完成什么任务。讲解页的页脚有三个任务：收尾、放来源与术语入口、回到页首。
2. 按任务选风格页。收尾感强：大字（`large-type`）、字体型（`typographic`）。信息多：网格（`grid`）、小字（`small-type`）。
3. 每个风格页最多看 10 条。只看版式骨架：几列、层级、最大的元素是什么。
4. 页脚是舞台区（`gears.md` 第 5 节）。`clear` 档不加页脚动效。`mixed`、`show` 档可有一个收尾动作。
5. 写吸收记录。

## 3. 示例：来源登记页脚

| 项 | 内容 |
|---|---|
| 任务 | 页脚放：一句收尾结论、"来源登记""最不可靠信息""术语表"三个入口、回到页首 |
| 查询路径 | `/styles/small-type` 看信息密集型。`/styles/large-type` 看收尾型 |
| 取 | 一个大元素加三个小入口的层级。入口之间的间距 |
| 舍 | 动画、插画、品牌色块 |
| 约束 | 全部是真文本。入口 ≥24px。页脚不压住可信度标记 |
| 记录示例 | `footer.design / large-type 第 1 页 / 取：单个大句收尾 / 舍：全部外观 / 理由：Defaults 禁令禁装饰编号和等宽小标签` |

## 4. 不适用

1. 带品牌插画、吉祥物的页脚：讲解页没有品牌插画预算。
2. 订阅表单、社交图标行：本项目不收集联系方式。
