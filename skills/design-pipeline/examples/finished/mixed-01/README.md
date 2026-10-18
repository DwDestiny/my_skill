# 成品范例 mixed-01 · 相机加图纸的讲解页

来源：E1 样例（设计院行业 AI 讲解页），2026-10-16，S6 修改轮后的页面。运行记录在 `evals/E1/runs/20261016/`。

| 项 | 值 |
|---|---|
| 动效气质 | 见 design.md 第 1 节（图像与材质加少量舞台） |
| 页面形态 | 一张 A0 图纸上的相机。12 章 = 12 个图幅，两张图纸，P11 翻页 |
| 舞台停靠点 | 首屏（渗印章）、s2（五步到 WebGL 体块）、s5（成熟度格）、s8（章特写渗印） |
| 盲评 | 修改前 2 分，修改后 4 分（`mixed` 门槛 3） |
| Fable | S3 改后过门，S3.5 改后过门，S6 第 1 轮 2 分未过门，修改后按停止条件收口 |
| 依赖 | GSAP 3.13.0（5 s 未到则零依赖退路并热换）、three 0.186.0（只在 s2 第 5 步加载）、Google Fonts |
| 本机未验 | 真实 GPU 帧率、Safari、Firefox、768 到 1279 宽 |
| 截图 | `shots/`：`1440-hero.jpg`、`1280-s3.jpg`、`1440-s11.jpg`、`390-hero.jpg`。S6 盲评与可区分性并排用 |

## 打开

在本目录起服务：`python3 -m http.server 8100 --bind 127.0.0.1`，打开 `http://127.0.0.1:8100/page/index.html`。资产在 `assets/generated/`，页面用 `../assets/generated/` 引用。

## 不可照抄的部分

见 `page/index.html` 文件头。要点：形态、配色与图纸语言、签名时刻"章落定并渗印"、全部文案与断言编号都是 E1 的决定。下一个项目先过 S3，命中同一形态或同一签名时刻就换。

## 可借的部分

| 文件 | 可借 |
|---|---|
| `page/src/camera.js` | 相机插值（缩放对数、平移按 1/s 加权、换排中途拉远）、停靠表、总览反向缩放、舞台按距离挂载与销毁、已读记录 |
| `page/src/ink.js` | 渗印着色器（原生 WebGL1，一个全屏三角带，结束后转静态图释放上下文） |
| `page/src/stage-*.js` | 舞台模块契约 `mount(host, opts) -> { set(t), play(), destroy() }`，Reduce Motion 分支 |
| `page/src/engine/` | 引擎门控与 GSAP 热换（派生自 MIT 代码，许可见 `LICENSE-MIT.txt`） |
| `page/src/page.css` | 令牌结构、深色"拷贝台"方案、总览 `is-far` 规则、`scroll-margin-top` 处理 sticky 导航 |

## 已知残余问题

s6、s7、s10 没有主图形。s9 停靠首屏只露出详图圈上半。s1 折线第三点的连接待核。见 `evals/E1/runs/20261016/05-评审/ROUND-3.md` 第 5 节。
