# 发布为 Artifact 时的平台契约（可切换附录）

只在产物要通过 Artifact 工具发布时读本文。本地 HTML 交付不受这些限制，Artifact 外链须符合下表的允许域名与固定版本规则。发布前先用 Skill 工具加载 `artifact-design`，以它的最新文本为准。本文是摘要。

| 项 | 本地 HTML | Artifact |
|---|---|---|
| 骨架 | 自己写 doctype/html/head/body | 不写；只放 `<title>` 与 `<style>` 在文件顶部 |
| `<title>` | 自由 | 2 到 4 个词的名字，不是摘要；解释写进发布参数 `description` |
| 图标 | 无 | 首次发布传 `icon`，一个通用词 |
| 外部脚本 | 建议内联 | 只允许 cdnjs.cloudflare.com、cdn.jsdelivr.net/npm/、unpkg.com、cdn.tailwindcss.com、code.jquery.com；版本精确且发布满两周 |
| 外部样式与字体 | 建议本地 | 只允许 fonts.googleapis.com 与 fonts.gstatic.com |
| 图片、媒体、fetch | 自由 | 全部拦截；须内联或 `data:` URI |
| 体积 | 无硬限 | ≤16MB（含 `data:` URI） |
| 主题 | 建议双主题 | 三态令牌结构强制；`body` 用令牌设显式背景 |
| 侧边距 | 16px 起 | `padding-left: max(16px, env(safe-area-inset-left, 0px))`，右侧同理 |
| 打印按钮、下载链接、alert | 可用 | 不可用 |
| mailto / tel | 可用 | 不可靠，地址作为可选中文本展示 |
| localStorage | 可用 | 可用，须 try/catch，只存便利状态 |
| Mermaid | 自己加载库 | 原生渲染，不加载库 |

> **警告**：发布让内容可被分享。发布前确认页面不含联系方式、未脱敏数据与凭据。发布动作本身需要用户同意。
