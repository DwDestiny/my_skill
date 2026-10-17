# history

此目录存放发牌使用史。`history.json` 不入 Git，由 `.gitignore` 排除。

## 文件

| 文件 | 内容 |
|---|---|
| `history.json` | `toolbox/deal.mjs --commit` 追加的记录，`--set-components` 补写组件案例 |
| `.gitkeep` | 让空目录保留在 Git 中 |

## history.json 字段

文件是一个对象，键 `entries` 是数组。每条记录如下。

| 字段 | 类型 | 含义 |
|---|---|---|
| `date` | 字符串 | 日期，格式 YYYY-MM-DD |
| `project` | 字符串 | 项目名 |
| `carrier` | 字符串 | 载体，如 `web-desktop` |
| `gear` | 字符串或 null | 旧字段，2026-10-17 起不再要求。保留以兼容旧记录 |
| `topic` | 字符串或 null | 题材 |
| `direction` | 字符串 | 方向卡 id |
| `palette` | 字符串或 null | 配色类 id |
| `form` | 字符串数组 | 表现形式 id |
| `outcome` | 字符串或 null | 用户评价：`好` `一般` `差` |
| `note` | 字符串 | 一句话说明 |
| `components` | 对象数组，可空 | 阶段 3 选中的案例：`[{slot, id}]`。阶段 3 结束时 `--set-components --project <名> --components slot:id,slot:id` 补写 |

## 规则

1. 不要把 `history.json` 提交到 Git。
2. 发牌脚本排除最近 5 条记录里的方向 id。`--slot` 发组件手法卡时排除最近 5 条里同槽的卡 id。
3. 同一方向用得越多，权重越低。权重是 1 除以（1 加使用次数）。
4. 评价为 `差` 的方向，在同载体同题材下权重再减半。
5. 不要手工改旧记录。需要更正时追加新记录。
