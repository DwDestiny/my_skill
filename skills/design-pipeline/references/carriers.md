# 载体对照表（9 载体）

> 何时读：阶段 1 定载体时读"读法"与对应载体的"HTML 平替"；阶段 4 抄载体数值时。

调研日期 2026-10-16。数据底稿：`research/R1-carriers.md`（已归档，不在本仓库）。机器可读档案：`library/carriers.json`。

## 读法

1. 阶段 1 定载体时，`node toolbox/lib.mjs carriers <id>` 取对应载体的对象。再读本文件的"HTML 平替"一节。
2. 值带 `src`。`unverified` 是记忆值，`inferred` 是推断值，`not_found` 是空缺。三者落地前必须核对，不要当事实用。
3. 没有设备外框。原型按载体视口直接出页面，视口之外不画任何图形。

## 关键差异

| 载体 | 视口 (px) | 正文 / 最小字号 | 最小命中区 | hover | 主导航 | Reduce Motion 开关 |
|---|---|---|---|---|---|---|
| wechat-mini | 375 或 390 宽 | 17 / 12 pt | 40x40 pt | 无 | Tab 栏 2 到 5 个 | 无统一开关 |
| alipay-mini | 375 宽 (待核) | 未找到来源 | 未找到来源 | 无 | TabBar (antd-mini) | 未找到来源 |
| ios | 393x852 (未核) | 17 / 11 pt | 28x28 pt (默认 44) | 无 (iPad 指针除外) | 底部 Tab 栏 | 设置 > 辅助功能 > 动态效果 |
| android | 412x915 (未核) | 16 sp (未核) | 48 dp (未核) | 无 | 底栏 / 导轨 / 抽屉 | 设置 > 辅助功能 > 移除动画 |
| harmony | 360x780 (未核) | 未找到来源 | 未找到来源 | 无 | 底部 Tab / 侧栏 (未核) | 未找到来源 |
| mobile-web | 390x844 主 (推断) | 16 px / 12 px (推断) | 24 px 底线，建议 44 | 不可依赖 | 自己做底部 Tab | CSS prefers-reduced-motion |
| desktop-web | 1440x900 主 | 14-16 px / 12 px (推断) | 24 px | 有，作增强 | 顶栏或左侧栏 | CSS prefers-reduced-motion |
| macos | 约 1200x760 (未核) | 13 / 10 pt | 20x20 pt (默认 28) | 有 | 侧栏 + 菜单栏 + 工具栏 | 系统设置 > 辅助功能 > 动态效果 > 减弱动态效果 |
| windows | 约 1280x800 (未核) | 14 px / 12 px | 40x40 px (触控) | 有 | NavigationView | 设置 > 辅助功能 > 视觉效果 > 动画效果 |

## HTML 平替

规则：

1. 在设计计划里写：载体、视口、字体栈、最小字号、最小命中区。
2. 触屏载体不写 hover，用 `:active`。桌面载体写全四态：hover、focus、pressed、disabled。
3. 手势全部提供按钮替代。
4. 玻璃和 blur 只放在浮层。给 `prefers-reduced-transparency` 提供实色回退。
5. 截图用载体视口，不用浏览器默认窗口。

按载体：

- wechat-mini：390x844。顶部 44 高导航条加右上胶囊预留 87x32 (87x32 为 [记])。组件用 WeUI (MIT)，绿色主色。顶栏纯色，不做渐变或视频。
- alipay-mini：同微信的视口与顶栏。组件外观参考 antd-mini，主色用 Ant 蓝预留，页面标"待核"。不复用 WeUI 绿色。
- ios：393x852。状态栏加 44 高导航条，底部 Tab 栏 49 加手势条留白。字体栈 `-apple-system, "SF Pro Text", "PingFang SC", sans-serif`。玻璃用 `backdrop-filter: blur() saturate()` 加半透明底，只放悬浮底栏和顶栏。组件用 Framework7 或 Konsta UI 的 iOS 主题。
- android：412x915。字体栈 `Roboto, "Noto Sans SC", sans-serif`。弹簧用 CSS `linear()` 近似或 Motion / GSAP，参数见 `library/carriers.json` 的 `motion_norm.springs`。组件用 Konsta UI 或 Framework7 的 Material 主题。
- harmony：360x780。字体栈 `"HarmonyOS Sans SC", "PingFang SC", "Noto Sans SC", sans-serif`。无现成库，用 Konsta UI 或自写令牌。页面标"鸿蒙参数待核"。
- mobile-web：不需要壳。agent-browser 设视口 390 844。meta 写 `viewport-fit=cover`，高度用 `dvh`，底部栏加 `env(safe-area-inset-bottom)`。组件自写令牌，Ionic 可选。
- desktop-web：主截图 1440x900，另测 1280 和 1920。内容宽度封顶 1200-1440 并居中。焦点环可见。
- macos：窗口内容约 1200x760。顶部 24 高菜单栏预留，下接 52 高工具栏区。正文 13 px。侧栏 220-260 px，半透明加 `backdrop-filter`。无成熟组件库，自写令牌。
- windows：窗口内容 1280x800，标题栏 32 高。字体栈 `"Segoe UI Variable", "Segoe UI", "Microsoft YaHei UI", sans-serif`。Mica 用纯色加轻微着色，不用大面积 blur。Acrylic 只放弹出菜单。组件库许可与版本未核。

## 跨载体底线

| 项 | 底线 | 来源 |
|---|---|---|
| 命中区 | 触控默认 44 pt (iOS)。Android 48 dp [记]。Windows 触控 40 px。网页硬底线 24 CSS px | S6b, S16, S18w |
| 命中区 (小元素) | 微信长辈模式热区不小于 40x40 pt，控件间留间距 | S5b |
| 对比度 | 正文 4.5:1。大字或粗体 3:1。深浅两套都要过 | S6b, S11, S5b |
| 字号 | iOS 正文 17 pt，最小 11。macOS 13 pt，最小 10。Windows 最小 12 px 常规或 14 px 半粗。网页正文 16 px [推] | S5, S15 |
| Reduce Motion | 所有载体要有回退。动效不是唯一的信息通道。不让人等动画结束 | S7b, S19b |
| 透明度 | 玻璃类效果要有"降低透明度"和"增强对比度"的实色回退 | S11, S7 |
| 颜色 | 不只用颜色传达信息，配形状或文字 | S6b |
| 系统缩放 | 版式要承受字体放大。微信长辈模式 x1.4 | S5b, S5 |
| 键盘 | 桌面端全部功能可仅用键盘到达 | S9, S18 |

## 来源编号与 URL

访问日期 2026-10-16。读取方式与要点见归档内 `research/R1-carriers.md` 第 5 节。

| 编号 | URL |
|---|---|
| S1 | https://developers.weixin.qq.com/miniprogram/design/ |
| S2 | https://developers.weixin.qq.com/miniprogram/dev/api/ui/menu/wx.getMenuButtonBoundingClientRect.html 。社区：https://cloud.tencent.com/developer/article/1900462 |
| S3 | https://developers.weixin.qq.com/miniprogram/dev/framework/view/wxss.html |
| S3b | https://developers.weixin.qq.com/miniprogram/dev/framework/ability/darkmode.html |
| S3c | https://developers.weixin.qq.com/miniprogram/dev/reference/configuration/app.html |
| S4 | 同 S1 |
| S5 | https://developer.apple.com/design/human-interface-guidelines/typography （读取 JSON：https://developer.apple.com/tutorials/data/design/human-interface-guidelines/typography.json ） |
| S5b | https://developers.weixin.qq.com/miniprogram/en/design/elderly.html |
| S6 | https://developer.apple.com/design/human-interface-guidelines/layout |
| S6b | https://developer.apple.com/design/human-interface-guidelines/accessibility |
| S7 | https://developer.apple.com/design/human-interface-guidelines/materials |
| S7b | https://developer.apple.com/design/human-interface-guidelines/motion |
| S8 | https://developer.apple.com/design/human-interface-guidelines/tab-bars |
| S9 | https://developer.apple.com/design/human-interface-guidelines/designing-for-macos |
| S10 | https://developer.apple.com/design/human-interface-guidelines/sidebars |
| S10b | https://developer.apple.com/design/human-interface-guidelines/pointing-devices |
| S10c | https://developer.apple.com/design/human-interface-guidelines/toolbars |
| S11 | https://developer.apple.com/design/human-interface-guidelines/dark-mode |
| S12 | https://developer.android.com/develop/ui/compose/layouts/adaptive/support-different-screen-sizes 。搜索摘要：https://dev.to/marlonlom/material-3-adaptive-implementing-window-size-classes-in-kotlin-compose-40po |
| S12b | https://android-developers.googleblog.com/2025/05/the-android-show-io-edition.html |
| S13 | https://developer.android.com/design/ui/mobile/guides/layout-and-content/layout-basics |
| S14 | https://github.com/material-components/material-components-android/blob/master/docs/theming/Motion.md |
| S14b | https://github.com/material-components/material-components-android/blob/master/docs/components/BottomNavigation.md |
| S15 | https://learn.microsoft.com/en-us/windows/apps/design/style/typography 。Fluent 2：https://fluent2.microsoft.design/typography |
| S15b | https://learn.microsoft.com/en-us/windows/apps/design/motion/timing-and-easing |
| S16 | https://learn.microsoft.com/en-us/windows/apps/design/input/guidelines-for-targeting |
| S16b | https://fluent2.microsoft.design/ |
| S16c | https://learn.microsoft.com/en-us/windows/apps/design/basics/content-basics |
| S17 | https://learn.microsoft.com/en-us/windows/apps/design/controls/navigationview |
| S17b | https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/materials |
| S18 | https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-overview |
| S18w | https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html |
| S19 | https://developer.mozilla.org/en-US/docs/Web/CSS/env |
| S19b | https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion |
| S20 | https://dev.to/xhunmon/multi-device-adaptation-and-responsive-design-best-practices-39bd 。https://www.cnblogs.com/xpzll/p/19109607 |
| S21 | https://ant-design-mini.antgroup.com/ 。https://miniprogram.alipay.com/docs/miniprogram/mpdev/extended_component_antd_mini_tabbar |
| S22 | https://github.com/Tencent/weui |
| S23 | https://github.com/framework7io/framework7 |
| S24 | https://github.com/konstaui/konsta |
| S25 | https://github.com/picturepan2/devices.css |
| S26 | https://github.com/ionic-team/ionic-framework |
| S27 | https://github.com/microsoft/fluentui-system-icons |
