# tests — 测试层(L2)

## 模块边界
对 `../scripts/` 全链路的 pytest 测试。fixtures 一律用仓库内样本或构造数据,**绝不提交真实发布记录**(涉及账号隐私)。

## 文件清单
| 文件 | 覆盖对象 |
|---|---|
| `conftest.py` | 公共 fixtures 与 sys.path 配置(fixtures 路径已改为对 cwd 不敏感) |
| `test_wechat_ops_report.py` | build 报告主链路 |
| `test_modules.py` | m1-m7 各分析模块 |
| `test_viral_genes.py` | m2 四象限判定 |
| `test_account_type.py` | m9 账号类型路由 |
| `test_forward.py` | m8 向前看引擎 |
| `test_semantics.py` | 语义与文案输出 |
| `test_readonly_workspace.py` | 只读 workspace 防护 |
| `test_accounts.py` | 多账号底座:store / resolve_context / migrate / lock / desk / pipeline e2e / legacy 不变性 |
| `test_health_batch.py` | 登录态体检 check_login/cmd_check + analyze --all 批量编排 + main 互斥 + desk login_alive |
| `test_niche_loader.py` | 赛道包加载:解析序/用户覆盖/坏包硬报错/懒加载/未知字段警告 |
| `test_niche_coverage.py` | C4 覆盖率闸门:非 AI fixture 触闸(G2)、_generic 恒触闸、total=0 不告警、m8/m9 降级、MD 警示块、内置 ai-tools 字面量钉死 |

## 本地规则
- 运行方式:skill 根目录下 `python3 -m pytest tests -q`(当前基线含多账号新增用例)。
- 新增分析模块必须配对新增测试;修 bug 先补能复现的失败用例再修(issue #24 的 m4 修复即此流程)。
- 畸形数据测试是一等公民:每个 m 模块至少一条"字段缺失/类型错误仍能降级"的用例。
- 多账号测试必须 `monkeypatch.setenv("WXOPS_HOME", ...)` 隔离,绝不碰真实 `~/.wxops`。
