# scripts/fetch — 后台抓取层(L2)

## 模块边界
对 mp.weixin.qq.com 已登录后台的四接口抓取。输入为 Playwright 持久化 context(登录态在 `~/.wxops/browser-profile`),输出统一写 `<workspace>/raw/*.json`。只抓用户自己有管理权的账号;登录失败即抛 `login_required`,不重试不绕过。

## 文件清单
| 文件 | 职责 |
|---|---|
| `orchestrator.py` | 四接口总编排:发布记录 → 账号 → 画像 → 内容趋势,接口间 3-8s 随机 sleep,任一失败立即返回 failed |
| `session.py` | 登录态判定与页面获取(`open_logged_in_page` → page + token) |
| `fetch_account.py` | 接口 A `/cgi-bin/home`,取 `window.wx.commonData`(已知缺口:取值路径错层——昵称/头像/user_name 在 `commonData.data` 子对象内而非顶层,叠加 `or {}` 静默兜底致四字段恒 null 却报成功,见 #83;原「domcontentloaded 时机竞态」诊断已实测证伪,commonData 22ms 即就绪) |
| `fetch_audience.py` | 接口 B `/misc/useranalysis`,正则解析内联 JS 变量,非空 list/dict 才算有数据,垃圾输入降级为 None |
| `fetch_content_trend.py` | 接口 C `/misc/appmsganalysis?action=report&f=json` |

## 本地规则
- 反检测 sleep 不得删除或缩短;新增接口沿用「单接口单文件 + orchestrator 注册」结构。
- 原始响应只落 `raw/`,不做业务加工;加工在 `../analyze/`。
- token 属敏感信息:不落日志、不进报告,导出物里的 URL 必须先脱敏。
- 页面结构解析必须容错:后台改版时降级返回 `available: false`,不允许抛未分类异常。
