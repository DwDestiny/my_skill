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
| `test_login_cmd.py` | login `_confirm_token`：快路径零 goto / 延迟跳转首轮得 token / 真未登录三轮 goto / goto 异常不崩溃（issue #53） |
| `test_browser.py` | issue #82：`launch_profile_context` 版本选择——精确匹配优先、同 major 且版本不低者取最小、同 major 更低与跨 major 一律 fail-fast、全新 profile 不传 executable；禁真浏览器禁子进程 |
| `test_fetch_account.py` | issue #83：`fetch_account` 嵌套取值/回退/fail-fast 不写盘/空白串/旧顶层路径拒收；orchestrator 结构性校验（`available=false` 合法、非 dict 失败）；duck-typed 假 page，禁真浏览器禁子进程 |
| `test_niche_loader.py` | 赛道包加载:解析序/用户覆盖/坏包硬报错/懒加载/未知字段警告 |
| `test_niche_coverage.py` | C4 覆盖率闸门:非 AI fixture 触闸(G2)、_generic 恒触闸、total=0 不告警、m8/m9 降级、MD 警示块、内置 ai-tools 字面量钉死 |
| `test_kit.py` | kit 写作三件套门禁:空壳三态/结构三层回落/账号级与开工级/未知账号 + desk 在途列与建议 |
| `test_lint.py` | 稿件合规闸:三种 match / exclude_matches / unless / softeners / 句级 scope / 每规则一次 / frontmatter 行号 / 退出码 / 三层回落 / schema |
| `test_dedup.py` | 选题去重闸:sim BLOCK/WARN/PASS / object 180 天窗口 / summary 排除 / 只读 stable / CLI JSON |
| `test_quality_portrait_disclosure.py` | issue #54：数据质量章双覆盖维度（文章指标 + 粉丝画像）文案分支、长度契约、markdown 数据口径披露 |
| `test_rates.py` | issue #59：`aggregate_rate` ratio-of-means / 多字段分子 / 分母 0 / 空列表；`median_rate` min_reads 过滤与样本不足回落 |
| `test_topic_roles.py` | issue #60：题材角色 maizong/health 锚点、零样本守卫、content-engine 角色叙事、无 AI 字样、recommendations 可选与 ai-tools 等值 |
| `test_metric_availability.py` | issue #61：指标可得性四态 / 真零 / 部分覆盖 / core pending / m1 权重重分配 / m7 阈值短路 / 防回归闸门 |
| `test_niche_scoring_override.py` | issue #74 PR B：赛道包 interaction_thresholds 二阶覆写、load 期校验、scoring_source 留痕、零覆写等价 |

## 本地规则
- 运行方式:skill 根目录下 `python3 -m pytest tests -q`(当前基线含多账号新增用例)。
- 新增分析模块必须配对新增测试;修 bug 先补能复现的失败用例再修(issue #24 的 m4 修复即此流程)。
- 畸形数据测试是一等公民:每个 m 模块至少一条"字段缺失/类型错误仍能降级"的用例。
- 多账号测试必须 `monkeypatch.setenv("WXOPS_HOME", ...)` 隔离,绝不碰真实 `~/.wxops`。
