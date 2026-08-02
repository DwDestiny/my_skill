# dashboard — 叙事看板（L2）

## 模块边界

诊断报告的**阅读端**。只负责把 `report.json` 讲成一条能读下去的叙事线，不做任何计算——所有数字、结论、阈值判定都由 `../scripts/analyze/` 算完写进报告，看板照着渲染。

看板在仓库里是**模板**：`analyze` 跑完会把整个目录复制到账号工作区，再把报告注入副本的 `public/data/`。仓库里这份的 `public/data/` 只放 demo 数据。

## 文件清单

| 文件 | 职责 |
|---|---|
| `src/App.tsx` | 全部组件与数据加载。约 1700 行单文件——是刻意的：一屏一组件、顺序即叙事顺序，拆开反而要跳文件读 |
| `src/styles.css` | 全部样式。CSS 变量定义马卡龙色板与字号阶梯，改配色只动 `:root` |
| `src/main.tsx` | 挂载入口 |
| `public/data/accounts.json` | 账号索引（`analyze` 生成；仓库里这份是 demo 单账号） |
| `public/data/<slug>.json` | 各账号报告 |
| `pnpm-workspace.yaml` | **不是可选的**，见下方构建约束 |

## 数据流

```
public/data/accounts.json ──fetch──> AccountsIndex
        │                              │
        │  current 指向的号             └─> 侧栏账号切换器
        ▼
public/data/<slug>.json ───fetch──> ReportCtx ──> 各屏 useReport()
```

编译期**不许**再 `import report from './data/report.json'`：那样报告会被打进 bundle，一个号一份构建产物，多账号无从谈起。切换账号是运行时 fetch + `Map` 缓存，同一个号第二次切回不再发请求。

`accounts.json` 的字段契约由 `../scripts/cli/analyze_cmd.py` 的 `_inject_accounts_data` 写出，前端 `AccountEntry` 类型必须与之逐字段对齐，改任一侧都要同步另一侧；`tests/test_dashboard_data.py` 守着 Python 那一半。

## 本地规则

- **不渲染置信度数字**。置信度只允许影响措辞强弱（"已经"/"看起来"/"暂时看不出"），不许出现在界面上。契约见 `../DATA_CONTRACT.md`。
- **报告缺字段就不渲染那一块**，不要兜底成 0 或"—"充数；空缺本身是信息。
- 文案一律中文，数字用 `--num` 等宽字族。
- 组件顺序即叙事顺序（体检结论 → 六份证据 → 怎么办），插新屏要想清楚它在这条线上的位置，不能随手追加到末尾。

## 三个会咬人的地方

**① `.main-scroll` 是 scroll-snap 容器**（`scroll-snap-type: y proximity`）。任何插在首屏之前的块——降级警示、迁移提示、数据过期提示——**必须自己声明 `scroll-snap-align: start`**，否则会被吸到下一个吸附点、静默滚出视口，渲染完全正确却没人看得见。P6 的赛道包命中率警示就踩过这个坑。

**② 侧栏 `.sidenav` 的 `z-index: 5` 是承重的**。它在 DOM 里排在 `<main>` 前面，账号切换器弹层要压过主区就必须靠这层；删掉它弹层会被正文盖住。

**③ 窄屏（≤920px）侧栏变顶栏**，弹层的定位基准要从触发器换到 `.sn-author`。触发器在顶栏里只有几十像素宽且位置随内容浮动，以它为基准无论左锚右锚都会擦到屏幕边；`.sn-author` 有 `margin-left: auto`，右沿恒等于顶栏内边距，靠它右对齐在任何视口宽度下都稳定留出同样边距。

## 构建约束

`pnpm-workspace.yaml` 里的 `allowBuilds` / `onlyBuiltDependencies` **必须保留**。vite 依赖 esbuild，esbuild 的安装脚本负责下载对应平台的原生二进制；pnpm 10+ 默认拦截依赖的安装脚本，不显式放行就装不全，`pnpm build` 必失败。两个键并存是为兼容 pnpm 版本差异（11 读前者，10 读后者）。

```bash
pnpm -C plugins/wxops/dashboard install
pnpm -C plugins/wxops/dashboard build   # tsc -b && vite build，必须零类型错误
pnpm -C plugins/wxops/dashboard dev     # 本地预览
```

## 改完怎么验

跑起来看，别只看编译过。用浏览器读 DOM 验证（`preview_inspect` / `preview_eval`）比截图可靠——颜色、间距、层级都要读计算值。

**React 19 不会为程序化 `.click()` 同步刷新状态**：脚本里点完立刻读 `aria-expanded` 拿到的是刷新前的旧值，会把好代码判成坏代码。每次读 DOM 前先 `await` 一个 tick（约 120ms）。
