# 视觉走查 · 检查清单与探针

四大主诉维度（容器边界 / hover 交互 / 文本密度 / 视觉引导）+ 骨架与技术卫生。

## A. 容器边界

- [ ] 可比较、可操作、可跳转的实体（案例、应用、团队、保障项）是否有承载容器（卡/panel），还是只有 hairline 裸排
- [ ] 容器语义一致性：同页/全站「卡片 / 分隔线列表 / panel」三种承载方式是否有可说明的规则——同一张页面内一半有底板一半没有即不一致
- [ ] 卡套卡层级是否过度（证据块 vs 外层卡语义混淆）
- [ ] 统计带/说明带是否有承载，数字与标签是否成组

实测：取元素 computed style 四要素。

```js
const c = document.querySelector('目标选择器');
const cs = getComputedStyle(c);
({border: cs.border, background: cs.backgroundColor, radius: cs.borderRadius, shadow: cs.boxShadow});
// 全空 = 无容器，无论视觉上多像卡片
```

## B. hover / 交互动效

- [ ] 每个可点元素（卡、行、tab、chip、按钮、链接）hover 是否有可见反馈（位移/边框/背景/阴影/箭头位移）
- [ ] **覆盖层检测**：有没有整组禁用规则把某区域的 hover 置 none（典型：`.<page> .card:hover { transform:none }`）——存在 hover 规则但全被禁用 = 交互死区
- [ ] 同站交互一致性：A 区有 hover、B 区同性质元素没有 → 记 issue
- [ ] 令牌/规则双轨冲突：同一选择器在两个样式源里定义不同值

```js
// 枚举所有非框架库的 :hover 规则（框架前缀按项目调，如 .semi- .ant- .el-）
const out=[]; const walk=(rs)=>{for(const r of rs){const t=r.cssText||'';
  if(r.cssRules?.length) walk(r.cssRules);
  else if(t.includes(':hover')&&!t.includes('.semi-')) out.push(t.slice(0,140));}};
for(const ss of document.styleSheets){try{walk(ss.cssRules)}catch(e){}};
out; // 逐条看：哪些是启用效果，哪些是显式禁用
```

```js
// 真实 hover（playwright MCP）：dispatchEvent 不触发 :hover，必须 browser_hover
// hover 中截图与静止态截图对比 = 零反馈实证的取证方式
```

## C. 文本密度与可读性

- [ ] 字号分布：<12px 算硬伤区，12–13px 记密度；统计全页文本节点量化
- [ ] 截断：chip 状态字、步骤条标题、卡标题（横向 ellipsis + 纵向裁切都要看）
- [ ] 单卡信息预算：标签/指标/简介/痛点/引用/代表作/流程/CTA 全堆一卡 = 过载
- [ ] 死占位文本（"即将上线"类）与真实按钮混排 → 误导点击预期
- [ ] 移动端首屏被长段简介占满、CTA 挤出首屏

```js
// 全页字号分布 + <13px 采样
const counts={}, small=[];
document.querySelectorAll('p,span,div,li,a,button,td,th').forEach(e=>{
  const t=e.textContent.trim(); if(!t||t.length>60||e.children.length>2) return;
  const fs=parseFloat(getComputedStyle(e).fontSize); counts[fs]=(counts[fs]||0)+1;
  if(fs<13&&t.length>4) small.push(t.slice(0,24)+' @'+fs+'px');});
({counts, smallSample: small.slice(0,15)});
```

```js
// 截断检测：横向 ellipsis / 纵向裁切
[...document.querySelectorAll('目标选择器')].map(e=>({
  text: e.textContent.trim().slice(0,20),
  clippedX: e.scrollWidth > e.clientWidth,
  clippedY: e.scrollHeight > e.clientHeight + 2}));
```

## D. 视觉引导

- [ ] 首屏 CTA 是否首屏可达（移动端重点）
- [ ] 空态/少内容区是否有引导（"没有什么可去 X"）而不是大片空白
- [ ] 可横滑容器（锚点条/标签行/表格）有无渐变 mask/箭头/滚动条提示——**桌面端溢出同样算缺陷**
- [ ] 孤标签/孤儿元素：游离在角落、与内容无归属关系的 tag/badge

## E. 骨架一致性

- [ ] 页脚/导航在详情页是否存在（查路由白名单代码，如 `FOOTER_ROUTES`）
- [ ] 页面无页脚时是否在推荐区之后戛然结束、无回流入口

## F. 技术卫生

- [ ] 每页 console error 收集（非法嵌套、hydration、资源 404）
- [ ] 文档声称的路由/入口实测存在性（README 与路由表不符 = issue）
- [ ] reveal/懒加载机制对非滚动场景（打印、整页截图、无 IO）的影响
- [ ] 中英混排一致性（标题体系内混入英文缩写）

## 分级口径

| 级 | 定义 | 例 |
|---|---|---|
| P0 | 明确缺陷：截断/裁切/报错/缺失/死链 | chip 文字「交…」、标题被裁、`<p>` 嵌 `<div>` 报错 |
| P1 | 体验硬伤：无容器、无 hover、超小字、密度过载、CTA 出首屏 | 案例区裸排、hover 死区、10.5px 标签 |
| P2 | 建议项：架构单薄、占位文案、文档不一致、伪影风险 | 详情页无页脚、"/join" 文档残留 |
