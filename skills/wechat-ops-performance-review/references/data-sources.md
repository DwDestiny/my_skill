# 数据源接口参考(实测探明)

> 本文档记录公众号后台可稳定、安全拿到的数据接口与字段结构,作为抓取层(`scripts/fetch/`)解析实现的依据,以及脱敏 fixtures 的结构蓝本。
> 所有数据通过**用户自己已登录**的浏览器同源 `fetch` 获取;反检测:单轮、接口间随机延迟、失败即停。

## 1. 账号信息 · `/cgi-bin/home?t=home/index&token=<token>`

数据在页面 `window.wx.commonData`(JS 对象,`page.evaluate(() => window.wx?.commonData)` 直接取,比正则 HTML 稳)。

| 字段 | 含义 | 用途 |
|------|------|------|
| `nick_name` | 账号名(实测:麦总玩AI) | 看板账号身份 |
| `head_img` | 头像 URL(wx.qlogo.cn) | 看板头像(**需下载本地化,防盗链**) |
| `user_name` / `fakeid` | 账号标识 | 内部标识 |

## 2. 文章列表 · `/cgi-bin/appmsgpublish?sub=list&begin=&count=10&token=<token>&f=json`

已实现(`export_wechat_publish_records.py`)。分页循环。每篇:阅读/分享/评论/点赞/发布时间/标题。
解析路径:`publish_page`(JSON字符串需二次parse)→ `publish_list[].publish_info.appmsgex[]`。

## 3. 粉丝画像 · `/misc/useranalysis?token=<token>&lang=zh_CN`

HTML 页,数据内联在 `<script>`。字段(实测存在):

| 字段 | 含义 |
|------|------|
| `cumulate_user` | 累计粉丝 |
| `new_user` | 新增粉丝(按日) |
| `cancel_user` | 取消关注(按日) |
| `netgain` | 净增 |
| `city` / `province` | 地域分布 |
| `age` | 年龄分布 |
| `user_source` | 粉丝来源(搜索/分享/扫码…) |

> 解析容错:若结构变动取不到,标记 `audience_available=false`,M4/M5 模块降级为规则推断。

## 4. 内容趋势 · `/misc/appmsganalysis?action=report&token=<token>&lang=zh_CN&f=json`

纯 JSON。顶层结构:`base_resp` / `user_info` / `user_acl` / `read_item` / `share_item` / `like_item` / `zaikan_item` / `comment_item` + 各 `_summary`。

**实测 item 数组结构**(时间序列):

| 数组 | 实测长度 | 字段 |
|------|---------|------|
| `read_item` | 87 | `ref_date`(日期), `attr_type`, `attr_scene`(场景:会话/朋友圈/历史…), `uv`(独立访客), `pv`(浏览量) |
| `share_item` | 23 | 同上 |
| `like_item` / `zaikan_item` / `comment_item` | 本号默认视图为空 | 可能需不同 action,或本号未透出;解析需容错空数组 |

> 含义:`read_item` 按日期×场景给出 uv/pv,可还原"阅读趋势曲线 + 流量来源场景分布"。`attr_scene` 是关键——能看出多少阅读来自朋友圈分享 vs 公众号会话 vs 历史消息,直接服务「内容引擎/涨粉漏斗」分析。

## 5. 菜单/消息(备用,未深挖)

`/misc/menuanalysis`、`/misc/messageanalysis` 接口存在,本期不接入,留占位。

---

## 反检测策略(铁律)

1. 单 context 单轮:一次 analyze 顺序抓完即关,不重试不并发。
2. 接口间随机延迟 3~8s。
3. 复用用户真实登录态(`browser-profile/`),不伪造指纹。
4. 同源 fetch(在 mp.weixin.qq.com 页内),带真实 referer/credentials。
5. 失败即停:`base_resp.ret != 0` 或 token 失效 → 提示重登,绝不用旧数据。
