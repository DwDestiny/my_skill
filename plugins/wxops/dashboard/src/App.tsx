// GEB-L3
// Input: caller, project conventions, and local dependencies
// Output: behavior defined by dashboard/src/App.tsx
// Pos: dashboard/src/App.tsx
import * as React from "react";
import {
  Activity,
  Aperture,
  Signpost,
  LayoutGrid,
  Gauge,
  Dna,
  Layers3,
  Users,
  TrendingUp,
  ListChecks,
  Target,
  Github,
  Star,
  Check,
  ChevronsUpDown,
  AlertTriangle,
} from "lucide-react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  AreaChart,
  Area,
  Cell,
} from "recharts";

/* ===================== 数据层(运行时加载,多账号) =====================
   原先是编译期 `import report from "./data/report.json"` + 模块级 const data。
   改为 fetch `data/accounts.json` 拿账号索引,再按账号取报告,经 Context 下发。
   各屏组件仍以 `const data = useReport()` 取到同名局部变量,内部读法不变。 */
type AccountEntry = {
  slug: string;
  name: string;
  has_report: boolean;
  /** 相对路径(不带前导斜杠),未分析的账号为 null */
  report_url: string | null;
  generated_at: string | null;
  article_count: number | null;
};
type AccountsIndex = {
  generated_at: string;
  current: string;
  accounts: AccountEntry[];
};

const ReportCtx = React.createContext<any>(null);
function useReport(): any {
  return React.useContext(ReportCtx);
}

/* ===================== Tokens(马卡龙) ===================== */
const MACARON = {
  mint: "#5FC9A3",
  peach: "#FF9E7A",
  butter: "#FFC95C",
  blush: "#FF93A8",
  lavender: "#A99CE8",
  sky: "#76C5E8",
};
const SERIES = [
  MACARON.mint,
  MACARON.peach,
  MACARON.butter,
  MACARON.blush,
  MACARON.lavender,
  MACARON.sky,
];
const QUADRANT_COLOR: Record<string, string> = {
  爆款: MACARON.mint,
  标题党: MACARON.peach,
  深度遗珠: MACARON.lavender,
  平稳: MACARON.sky,
};

/* ===================== 工具 ===================== */
function fmtNum(value: number | undefined, digits = 0) {
  return (value ?? 0).toLocaleString("zh-CN", { maximumFractionDigits: digits });
}
function pct(value: number | undefined, digits = 0) {
  return `${((value ?? 0) * 100).toFixed(digits)}%`;
}

const prefersReducedMotion =
  typeof window !== "undefined" &&
  window.matchMedia &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** rAF 数字滚动 */
function useCountUp(target: number, duration = 700) {
  const [val, setVal] = React.useState(prefersReducedMotion ? target : 0);
  React.useEffect(() => {
    if (prefersReducedMotion) {
      setVal(target);
      return;
    }
    let raf = 0;
    let start = 0;
    const step = (ts: number) => {
      if (!start) start = ts;
      const p = Math.min(1, (ts - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(target * eased);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return val;
}

/** 进入视口揭示 */
function useInView<T extends HTMLElement>() {
  const ref = React.useRef<T | null>(null);
  const [seen, setSeen] = React.useState(false);
  React.useEffect(() => {
    if (prefersReducedMotion) {
      setSeen(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setSeen(true);
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.18 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return { ref, seen };
}

/* ===================== 导航(叙事三段:结论 / 为什么 / 怎么办) ===================== */
type NavItem = { id: string; no?: string; label: string; icon: any; star?: boolean };
type NavGroup = { group: string; items: NavItem[] };

const OVERVIEW_ITEM: NavItem = { id: "overview", label: "体检结论", icon: Gauge };

// 为什么:六份证据,编号 01-06 编码诊断逻辑顺序
const EVIDENCE_ITEMS: NavItem[] = [
  { id: "checkup", no: "01", label: "账号体检", icon: Activity },
  { id: "viral", no: "02", label: "爆款基因", icon: Dna },
  { id: "content", no: "03", label: "内容引擎", icon: Layers3 },
  { id: "audience", no: "04", label: "读者画像", icon: Users },
  { id: "growth", no: "05", label: "涨粉漏斗", icon: TrendingUp },
  { id: "standards", no: "06", label: "量化标准", icon: Target },
];

// 怎么办:向前看三屏 + 本周行动;闸门未过时向前看塌缩为单入口
const FORWARD_ITEMS: NavItem[] = [
  { id: "mirror", label: "照镜子", icon: Aperture },
  { id: "paths", label: "找方向", icon: Signpost, star: true },
  { id: "matrix", label: "规划矩阵", icon: LayoutGrid },
];
const FORWARD_BLOCKED_ITEMS: NavItem[] = [{ id: "mirror", label: "向前看", icon: Aperture }];
const WEEKLY_ITEM: NavItem = { id: "action", label: "本周行动", icon: ListChecks };

function buildNavGroups(passed: boolean): NavGroup[] {
  return [
    { group: "", items: [OVERVIEW_ITEM] },
    { group: "为什么", items: EVIDENCE_ITEMS },
    {
      group: "怎么办",
      items: [...(passed ? FORWARD_ITEMS : FORWARD_BLOCKED_ITEMS), WEEKLY_ITEM],
    },
  ];
}

function useActiveSection(ids: string[]) {
  const [active, setActive] = React.useState(ids[0] ?? "overview");
  React.useEffect(() => {
    const scroller = document.querySelector(".main-scroll");
    const els = ids
      .map((id) => document.getElementById(id))
      .filter((e): e is HTMLElement => Boolean(e));
    if (!els.length) return;
    const io = new IntersectionObserver(
      (entries) => {
        const vis = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (vis?.target.id) setActive(vis.target.id);
      },
      { root: scroller, rootMargin: "-30% 0px -55% 0px", threshold: [0.2, 0.5] },
    );
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, [ids]);
  return active;
}

/* ===================== 账号切换器 =====================
   位置在侧栏底部账号区 —— 那里本来就写着「当前是谁」，切换能力长在原地。
   单账号时退化为纯展示：没有 chevron、没有 hover、不可点。
   能力从数据里长出来，而不是常驻一个提示你「只有一个号」的控件。 */

/** slug 稳定哈希取色 + 名字首字，免去头像文件同步 */
function AcctAvatar({ name, slug, size = 22 }: { name: string; slug: string; size?: number }) {
  const ch = ((name || slug || "?").trim()[0] || "?").toUpperCase();
  let h = 0;
  for (let i = 0; i < slug.length; i += 1) h = (h * 31 + slug.charCodeAt(i)) >>> 0;
  return (
    <span
      className="acct-av"
      style={{
        width: size,
        height: size,
        background: SERIES[h % SERIES.length],
        fontSize: Math.round(size * 0.46),
      }}
      aria-hidden
    >
      {ch}
    </span>
  );
}

/** 「3 天前分析」；超 7 天视为陈旧，用于提示该重跑 analyze 了 */
function relAnalyzed(iso: string | null): { text: string; stale: boolean } {
  if (!iso) return { text: "未分析", stale: true };
  const t = new Date(iso).getTime();
  if (!Number.isFinite(t)) return { text: "未分析", stale: true };
  const days = Math.floor((Date.now() - t) / 86400000);
  if (days <= 0) return { text: "今天分析", stale: false };
  if (days === 1) return { text: "昨天分析", stale: false };
  if (days < 30) return { text: `${days} 天前分析`, stale: days > 7 };
  return { text: `${Math.floor(days / 30)} 个月前分析`, stale: true };
}

function AccountSwitcher({
  index,
  current,
  fallbackName,
  switching,
  onSwitch,
}: {
  index: AccountsIndex | null;
  current: string;
  fallbackName: string;
  switching: boolean;
  onSwitch: (slug: string) => void;
}) {
  const [open, setOpen] = React.useState(false);
  const boxRef = React.useRef<HTMLDivElement>(null);
  const list = index?.accounts ?? [];
  const me = list.find((a) => a.slug === current);
  const name = me?.name ?? fallbackName;

  React.useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!boxRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  // 单账号：与改造前同一副样子，不留任何切换痕迹
  if (list.length <= 1) {
    return (
      <div className="sn-author-name">
        <AcctAvatar name={name} slug={current || "_"} />
        {name}
      </div>
    );
  }

  return (
    <div className="acct-switch" ref={boxRef}>
      {open ? (
        <div className="acct-pop" role="listbox" aria-label="切换账号">
          {list.map((a) => {
            const rel = relAnalyzed(a.generated_at);
            const isMe = a.slug === current;
            return (
              <button
                key={a.slug}
                type="button"
                role="option"
                aria-selected={isMe}
                disabled={!a.has_report}
                className={`acct-opt${isMe ? " me" : ""}${a.has_report ? "" : " void"}`}
                title={
                  a.has_report
                    ? undefined
                    : `该账号还没有分析数据：先跑 wxops analyze --account ${a.slug}`
                }
                onClick={() => {
                  if (a.has_report && !isMe) onSwitch(a.slug);
                  setOpen(false);
                }}
              >
                <AcctAvatar name={a.name} slug={a.slug} size={26} />
                <span className="acct-opt-text">
                  <span className="acct-opt-name">{a.name}</span>
                  <span className={`acct-opt-sub${rel.stale ? " stale" : ""}`}>
                    {a.has_report
                      ? `${a.article_count ?? "—"} 篇 · ${rel.text}`
                      : "未分析"}
                  </span>
                </span>
                {isMe ? <Check className="acct-opt-tick" size={14} /> : null}
              </button>
            );
          })}
        </div>
      ) : null}
      <button
        type="button"
        className={`acct-trigger${open ? " open" : ""}`}
        aria-haspopup="listbox"
        aria-expanded={open}
        /* 窄屏只剩头像和 chevron，可见文字不足以说明这是切换器，名字挂在这里 */
        aria-label={`当前账号：${name}，点击切换`}
        title={name}
        onClick={() => setOpen((v) => !v)}
      >
        <AcctAvatar name={name} slug={current || "_"} />
        <span className="acct-trigger-name">{name}</span>
        {switching ? (
          <span className="acct-spin" aria-label="加载中" />
        ) : (
          <ChevronsUpDown className="acct-chev" size={13} />
        )}
      </button>
    </div>
  );
}

/* ===================== 左栏 ===================== */
function SideNav({
  groups,
  active,
  index,
  current,
  switching,
  onSwitch,
}: {
  groups: NavGroup[];
  active: string;
  index: AccountsIndex | null;
  current: string;
  switching: boolean;
  onSwitch: (slug: string) => void;
}) {
  const data = useReport();
  const sig = data.brand_signature ?? {};
  const repo = sig.skill_repo || sig.star_url || "https://github.com";
  return (
    <aside className="sidenav">
      <div className="sn-brand">
        <svg className="sn-logo" width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden>
          <rect width="24" height="24" rx="7.5" fill="url(#lg)" />
          <path
            d="M5 13.2 H8.2 L10 7.5 L12.3 16.5 L14 11.6 H19"
            stroke="#fff"
            strokeWidth="1.7"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <defs>
            <linearGradient id="lg" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
              <stop stopColor="#5FC9A3" />
              <stop offset="1" stopColor="#76C5E8" />
            </linearGradient>
          </defs>
        </svg>
        运营诊断
      </div>

      <nav className="sn-nav" aria-label="诊断叙事导航">
        {groups.map((g) => (
          <div key={g.group || "_top"} className="sn-group">
            {g.group ? <p className="sn-group-label">{g.group}</p> : null}
            {g.items.map((m) => (
              <a
                key={m.id}
                href={`#${m.id}`}
                className={`sn-item${active === m.id ? " active" : ""}${m.star ? " star" : ""}`}
              >
                <span className="sn-no">{m.no || <m.icon size={15} />}</span>
                <span className="sn-label">{m.label}</span>
                {m.star ? <Signpost className="sn-star" size={13} /> : null}
              </a>
            ))}
          </div>
        ))}
      </nav>

      <div className="sn-author">
        <AccountSwitcher
          index={index}
          current={current}
          fallbackName={sig.author_name ?? "本账号"}
          switching={switching}
          onSwitch={onSwitch}
        />
        <a className="sn-star-btn" href={repo} target="_blank" rel="noreferrer">
          <Github size={14} />
          <span>Star on GitHub</span>
          <Star className="star" size={13} />
        </a>
      </div>
    </aside>
  );
}

/* ===================== 幕间屏(默会转场:一句提问 + 留白) ===================== */
function ActDivider({ eyebrow, line, sub }: { eyebrow: string; line: string; sub?: string }) {
  const { ref, seen } = useInView<HTMLElement>();
  return (
    <section className={`act-divider${seen ? " in" : ""}`} ref={ref as any}>
      <p className="ad-eyebrow">{eyebrow}</p>
      <h2 className="ad-line">{line}</h2>
      {sub ? <p className="ad-sub">{sub}</p> : null}
    </section>
  );
}

/* ===================== 爆款基因卡(signature) ===================== */
function ViralGeneCard() {
  const data = useReport();
  const f = data.viral_genes?.viral_formula ?? {};
  const counts = data.viral_genes?.quadrant_counts ?? {};
  const factors = [
    f.topic,
    f.title_pattern,
    f.timing_weekday ? `${f.timing_weekday}${f.timing_hour ?? ""}点` : null,
  ].filter(Boolean);
  const reliable = f.reliable;
  return (
    <div className={`gene-card${reliable ? "" : " tentative"}`}>
      <div className="gene-top">
        <Dna size={16} />
        <span>{reliable ? "你的爆款密码" : "爆款线索（样本待积累）"}</span>
      </div>
      <div className="gene-formula">
        {factors.length ? (
          factors.map((fac: string, i: number) => (
            <React.Fragment key={i}>
              <span className="gene-factor" style={{ animationDelay: `${i * 140}ms` }}>
                {fac}
              </span>
              {i < factors.length - 1 ? <span className="gene-x">╳</span> : null}
            </React.Fragment>
          ))
        ) : (
          <span className="gene-empty">暂无足够爆款样本，先积累更多文章</span>
        )}
      </div>
      <div className="gene-meta">
        {reliable
          ? `${f.sample_count} 篇验证 · 占四象限爆款区 ${counts["爆款"] ?? 0} 篇`
          : "初步迹象，继续观察同类题材表现"}
      </div>
    </div>
  );
}

/* ===================== 概览首屏(F1 判断 → F2 数字带 → F3 基因卡) ===================== */
function Overview() {
  const data = useReport();
  const acc = data.account ?? {};
  const bm = data.benchmark ?? {};
  const checkup = data.modules?.checkup ?? {};
  const growth = data.modules?.growth_funnel ?? {};
  const top = data.top_conclusion ?? {};
  const meta = data.meta ?? {};
  const recentNet = (growth?.netgain_trend ?? [])
    .slice(-7)
    .reduce((s: number, r: any) => s + (r.netgain ?? 0), 0);
  const score = useCountUp(checkup.health_score ?? 0);
  const fans = useCountUp(acc.cumulate_user ?? 0);
  const median = useCountUp(bm.read_median ?? 0);

  const digits: { label: string; hint: string; value?: string; node?: React.ReactNode }[] = [
    {
      label: "健康分",
      node: (
        <div
          className="ovd-ring"
          style={{
            background: `conic-gradient(${MACARON.mint} ${Math.min(100, checkup.health_score ?? 0)}%, #ECE7DF 0)`,
          }}
        >
          <b>{Math.round(score)}</b>
        </div>
      ),
      hint: "0-100 综合体检",
    },
    { label: "累计粉丝", value: fmtNum(Math.round(fans)), hint: "公众号后台口径" },
    { label: "中位阅读", value: fmtNum(Math.round(median)), hint: "稳定样本中位数" },
    {
      label: "近 7 天净增",
      value: `${recentNet >= 0 ? "+" : ""}${fmtNum(recentNet)}`,
      hint: "关注减取关",
    },
  ];

  return (
    <section id="overview" className="screen overview">
      {/* 账号身份行(安静) */}
      <header className="ov-id">
        <div className="ov-avatar">
          {acc.avatar_local ? (
            <img src={acc.avatar_local} alt="" />
          ) : (
            <span>{(acc.name ?? "公").slice(0, 1)}</span>
          )}
        </div>
        <div>
          <h1>{acc.name ?? "公众号"}</h1>
          <p>
            微信公众号 · {String(meta.period_start ?? "").slice(0, 10)} 起 · 稳定样本{" "}
            {fmtNum(data.data_quality?.stable_article_count)} 篇
          </p>
        </div>
      </header>

      {/* F1:总判断(全站唯一 hero 级衬线大字) */}
      <div className="ov-verdict">
        <p className="ovv-eyebrow">体检结论</p>
        <h2 className="ovv-line">{top.verdict ?? checkup.verdict ?? "数据分析中"}</h2>
        {top.next_action ? (
          <p className="ovv-next">{String(top.next_action).replace(/^→\s*/, "→ ")}</p>
        ) : null}
      </div>

      {/* F2:关键数字带(判断的第一层依据) */}
      <div className="ov-digits">
        {digits.map((d) => (
          <div key={d.label} className="ovd">
            {d.node ?? <b className="ovd-val">{d.value}</b>}
            <span className="ovd-label">{d.label}</span>
            <small className="ovd-hint">{d.hint}</small>
          </div>
        ))}
      </div>

      {/* F3:爆款密码(signature,钩住继续下滑) */}
      <ViralGeneCard />
    </section>
  );
}

/* ===================== 模块屏壳:垂直流 =====================
   kicker(编号·模块名·本屏问题) → deck(结论,衬线) → evidence(数据依据一行)
   → stage(单一主视觉) → note(下一步,屏底单行) */
function FlowScreen({
  id,
  no,
  title,
  question,
  conclusion,
  evidence,
  action,
  children,
}: {
  id: string;
  no?: string;
  title: string;
  question?: string;
  conclusion?: string;
  evidence?: string;
  action?: string;
  children: React.ReactNode;
}) {
  const { ref, seen } = useInView<HTMLDivElement>();
  return (
    <section id={id} className="screen flow">
      <header className="flow-head">
        <p className="flow-kicker">
          <span className="fk-id">{no ? `${no} · ${title}` : title}</span>
          {question ? <span className="fk-q">{question}</span> : null}
        </p>
        <h2 className="flow-deck">{conclusion || title}</h2>
        {evidence ? <p className="flow-evidence">{evidence}</p> : null}
      </header>
      <div className={`flow-stage${seen ? " in" : ""}`} ref={ref as any}>
        {children}
      </div>
      {action ? (
        <p className="flow-note">
          <span className="fn-arrow">→</span>
          <span>{action}</span>
        </p>
      ) : null}
    </section>
  );
}

/* ===================== 01 账号体检 ===================== */
function CheckupScreen() {
  const data = useReport();
  const c = data.modules?.checkup ?? {};
  const bm = data.benchmark ?? {};
  const inter = c.interaction ?? {};
  const score = useCountUp(c.health_score ?? 0);
  const rows = [
    { label: "中位阅读", value: fmtNum(bm.read_median), color: MACARON.mint },
    { label: "P75 阅读", value: fmtNum(bm.read_p75), color: MACARON.sky },
    { label: "去极值均值", value: fmtNum(bm.read_trimmed_mean), color: MACARON.lavender },
    { label: "最高阅读", value: fmtNum(bm.read_max), color: MACARON.peach },
  ];
  // issue #61：指标不可得时显示「不可得」，不把 null 当 0%
  const zaikanUnavailable =
    inter.zaikan_rate == null ||
    inter.zaikan_status === "platform_not_provided" ||
    inter.zaikan_status === "fetch_missing" ||
    inter.zaikan_status === "not_applicable";
  const inters = [
    {
      label: "在看率",
      value: zaikanUnavailable ? "不可得" : pct(inter.zaikan_rate, 1),
      color: MACARON.mint,
      hint: zaikanUnavailable
        ? inter.zaikan_status === "platform_not_provided"
          ? "平台未提供该字段"
          : inter.zaikan_status === "fetch_missing"
            ? "本次采集缺失"
            : "该维度不可得"
        : undefined,
    },
    { label: "分享率", value: pct(inter.share_rate, 1), color: MACARON.blush },
    { label: "评论率", value: pct(inter.comment_rate, 1), color: MACARON.butter },
  ];
  return (
    <FlowScreen
      id="checkup"
      no="01"
      title="账号体检"
      question="账号现在什么状态？"
      conclusion={c.verdict}
      evidence={c.analysis}
      action={c.action}
    >
      <div className="checkup-grid">
        <div
          className="health-ring big"
          style={{ background: `conic-gradient(${MACARON.mint} ${Math.min(100, c.health_score ?? 0)}%, #EFEAE1 0)` }}
        >
          <div className="health-core">
            <strong>{Math.round(score)}</strong>
            <span>健康分</span>
          </div>
        </div>
        <div className="checkup-stats">
          {rows.map((r) => (
            <div key={r.label} className="cstat">
              <i style={{ background: r.color }} />
              <span>{r.label}</span>
              <b>{r.value}</b>
            </div>
          ))}
        </div>
        <div className="checkup-micro">
          {inters.map((r) => (
            <span key={r.label} className="cmicro" title={(r as any).hint || undefined}>
              <i style={{ background: r.color }} />
              <span className="cm-label">{r.label}</span>
              <b>{r.value}</b>
            </span>
          ))}
        </div>
      </div>
    </FlowScreen>
  );
}

/* ===================== 02 爆款基因(四象限,可下钻) ===================== */
const QUADRANT_DESC: Record<string, string> = {
  爆款: "高读高享 · 复制这个配方",
  标题党: "高读低享 · 标题骗到点击但内容没留住",
  深度遗珠: "低读高享 · 内容好但标题/时段没拉到量",
  平稳: "低读低享 · 常规盘",
};

function ViralScreen() {
  const data = useReport();
  const vg = data.viral_genes ?? {};
  const bm = data.benchmark ?? {};
  const all = vg.quadrant ?? [];
  const counts = vg.quadrant_counts ?? {};
  const order = ["爆款", "标题党", "深度遗珠", "平稳"];
  const [active, setActive] = React.useState<string | null>(null);

  const points = all.map((a: any) => ({
    x: a.reads,
    y: (a.share_rate ?? 0) * 100,
    q: a.quadrant,
    title: a.title,
    dim: active ? a.quadrant !== active : false,
  }));
  const drillList = active
    ? all
        .filter((a: any) => a.quadrant === active)
        .sort((a: any, b: any) => (b.reads ?? 0) - (a.reads ?? 0))
    : [];

  return (
    <FlowScreen
      id="viral"
      no="02"
      title="爆款基因"
      question="什么样的内容在你号上能爆？"
      conclusion={
        vg.viral_formula?.reliable
          ? `爆款集中在「${vg.viral_formula.topic}」题材 +「${vg.viral_formula.title_pattern}」标题`
          : "爆款样本还不够，规律待验证"
      }
      action="下一批按爆款密码排选题，标题先写损失/收益"
    >
      <div className="viral-wrap">
        <div className="quadrant-chart">
          <ResponsiveContainer width="100%" height={380}>
            <ScatterChart margin={{ top: 16, right: 24, bottom: 28, left: 8 }}>
              <CartesianGrid stroke="#EEE9E0" />
              <XAxis
                type="number"
                dataKey="x"
                scale="log"
                domain={["auto", "auto"]}
                name="阅读"
                tickFormatter={(v) => fmtNum(v)}
                fontSize={11}
                stroke="#A8A4AE"
                label={{ value: "阅读量(对数)", position: "insideBottom", offset: -14, fontSize: 11, fill: "#76727E" }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="分享率"
                unit="%"
                fontSize={11}
                stroke="#A8A4AE"
                label={{ value: "分享率", angle: -90, position: "insideLeft", fontSize: 11, fill: "#76727E" }}
              />
              <ZAxis range={[90, 90]} />
              <ReferenceLine x={bm.read_median} stroke="#C9C2D6" strokeDasharray="4 4" />
              <ReferenceLine y={(bm.share_rate_median ?? 0) * 100} stroke="#C9C2D6" strokeDasharray="4 4" />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                content={({ active: act, payload }: any) => {
                  if (!act || !payload?.length) return null;
                  const d = payload[0].payload;
                  return (
                    <div className="chart-tip">
                      <b style={{ color: QUADRANT_COLOR[d.q] }}>{d.q}</b>
                      <span>{d.title}</span>
                      <small>
                        阅读 {fmtNum(d.x)} · 分享率 {d.y.toFixed(1)}%
                      </small>
                    </div>
                  );
                }}
              />
              <Scatter data={points} isAnimationActive={!prefersReducedMotion}>
                {points.map((p: any, i: number) => (
                  <Cell
                    key={i}
                    fill={QUADRANT_COLOR[p.q] ?? MACARON.sky}
                    fillOpacity={p.dim ? 0.16 : 1}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div className="quadrant-legend">
          {order.map((q) => (
            <button
              key={q}
              type="button"
              className={`qleg${active === q ? " on" : ""}`}
              onClick={() => setActive(active === q ? null : q)}
            >
              <i style={{ background: QUADRANT_COLOR[q] }} />
              <span>{q}</span>
              <b>{counts[q] ?? 0}</b>
            </button>
          ))}
          <p className="qhint">点击查看该象限具体文章。高读高享=爆款，高读低享=标题党，低读高享=深度遗珠。</p>
        </div>
      </div>

      {active ? (
        <div className="drill">
          <div className="drill-head">
            <span className="drill-dot" style={{ background: QUADRANT_COLOR[active] }} />
            <strong>{active}</strong>
            <span className="drill-desc">{QUADRANT_DESC[active]}</span>
            <span className="drill-count">{drillList.length} 篇</span>
          </div>
          <ol className="drill-list">
            {drillList.map((a: any, i: number) => (
              <li key={i}>
                <span className="dl-rank">{i + 1}</span>
                <span className="dl-title">{a.title}</span>
                <span className="dl-type">{a.content_type}</span>
                <span className="dl-reads">{fmtNum(a.reads)}</span>
                <span className="dl-share">{(a.share_rate * 100).toFixed(1)}%</span>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
    </FlowScreen>
  );
}

/* ===================== 排行条 ===================== */
function RankBars({ rows, max, unit }: { rows: { label: string; value: number }[]; max: number; unit?: string }) {
  return (
    <div className="rank-bars">
      {rows.map((r, i) => (
        <div key={r.label} className="rank-row">
          <span className="rank-label">{r.label}</span>
          <div className="rank-track">
            <div
              className="rank-fill"
              style={{ width: `${max ? Math.max(4, (r.value / max) * 100) : 0}%`, background: SERIES[i % SERIES.length] }}
            />
          </div>
          <b className="rank-val">
            {fmtNum(r.value)}
            {unit}
          </b>
        </div>
      ))}
    </div>
  );
}

/* ===================== 03 内容引擎 ===================== */
function ContentScreen() {
  const data = useReport();
  const ce = data.modules?.content_engine ?? {};
  const topics = (ce.by_topic ?? [])
    .filter((t: any) => (t.count ?? 0) > 0)
    .sort((a: any, b: any) => (b.median ?? 0) - (a.median ?? 0));
  const max = Math.max(...topics.map((t: any) => t.median ?? 0), 1);
  const rows = topics.map((t: any) => ({ label: t.key, value: t.median ?? 0 }));
  const ratio = ce.recommended_ratio ?? [];
  return (
    <FlowScreen
      id="content"
      no="03"
      title="内容引擎"
      question="哪些题材拉新，哪些建心智？"
      conclusion={ce.conclusion}
      evidence={ce.analysis}
      action={ce.action}
    >
      <div className="content-wrap">
        <p className="stage-cap">题材战力 · 按中位阅读排序</p>
        <RankBars rows={rows} max={max} unit="" />
        <div className="ratio-stack-wrap">
          <h4 className="ratio-stack-head">推荐发文配比</h4>
          <div className="ratio-stack">
            {ratio.slice(0, 6).map((r: any, i: number) => (
              <span
                key={r.topic}
                className="ratio-seg"
                style={{ width: `${(r.ratio ?? 0) * 100}%`, background: SERIES[i % SERIES.length] }}
                title={`${r.topic} ${pct(r.ratio)}`}
              />
            ))}
          </div>
          <div className="ratio-legend">
            {ratio.slice(0, 6).map((r: any, i: number) => (
              <span key={r.topic} className="rl-item">
                <i style={{ background: SERIES[i % SERIES.length] }} />
                <span className="rl-topic">{r.topic}</span>
                <b>{pct(r.ratio)}</b>
              </span>
            ))}
          </div>
        </div>
      </div>
    </FlowScreen>
  );
}

/* ===================== 04 读者画像 ===================== */
function AudienceScreen() {
  const data = useReport();
  const au = data.modules?.audience ?? {};
  const available = au.fans_portrait_available;
  const city = (au.city ?? []).slice(0, 8);
  const maxCity = Math.max(...city.map((c: any) => c.value ?? 0), 1);
  const age = au.age ?? [];
  const src = au.user_source ?? [];
  return (
    <FlowScreen
      id="audience"
      no="04"
      title="读者画像"
      question="你的读者到底是谁？"
      conclusion={au.conclusion}
      evidence={au.analysis}
      action={au.action}
    >
      {available ? (
        <div className="audience-wrap">
          <div className="aud-city">
            <h4>粉丝地域 TOP</h4>
            <RankBars rows={city.map((c: any) => ({ label: c.name, value: c.value }))} max={maxCity} unit=" 人" />
          </div>
          <div className="aud-side">
            <div className="aud-block">
              <h4>年龄</h4>
              <div className="seg-bars">
                {age.map((a: any, i: number) => (
                  <div key={a.range} className="seg">
                    <div className="seg-bar" style={{ height: `${(a.value ?? 0) * 160}px`, background: SERIES[i % SERIES.length] }} />
                    <b>{pct(a.value)}</b>
                    <span>{a.range}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="aud-block">
              <h4>粉丝来源</h4>
              <ul className="src-list">
                {src.map((s: any, i: number) => (
                  <li key={s.source}>
                    <i style={{ background: SERIES[i % SERIES.length] }} />
                    <span>{s.source}</span>
                    <b>{pct(s.value)}</b>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ) : (
        <div className="degrade-note">未抓到粉丝画像数据，当前基于文章人群规则推断。运行 wxops login 后可解锁真实地域/年龄/来源。</div>
      )}
    </FlowScreen>
  );
}

/* ===================== 05 涨粉漏斗 ===================== */
function GrowthScreen() {
  const data = useReport();
  const g = data.modules?.growth_funnel ?? {};
  const trend = (g.netgain_trend ?? []).map((r: any) => ({
    date: String(r.date ?? "").slice(5),
    netgain: r.netgain ?? 0,
  }));
  const plan = g.startup_plan ?? [];
  return (
    <FlowScreen
      id="growth"
      no="05"
      title="涨粉漏斗"
      question="怎么涨粉、怎么起号？"
      conclusion={g.conclusion}
      action={g.action}
    >
      <div className="growth-wrap">
        <div className="growth-chart">
          <h4>粉丝净增趋势</h4>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trend} margin={{ top: 8, right: 16, bottom: 4, left: -10 }}>
              <defs>
                <linearGradient id="netg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={MACARON.mint} stopOpacity={0.5} />
                  <stop offset="100%" stopColor={MACARON.mint} stopOpacity={0.03} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#EEE9E0" vertical={false} />
              <XAxis dataKey="date" fontSize={10} stroke="#A8A4AE" interval={5} />
              <YAxis fontSize={10} stroke="#A8A4AE" width={34} />
              <Tooltip
                content={({ active, payload, label }: any) => {
                  if (!active || !payload?.length) return null;
                  return (
                    <div className="chart-tip">
                      <b>{label}</b>
                      <small>净增 {payload[0].value}</small>
                    </div>
                  );
                }}
              />
              <Area type="monotone" dataKey="netgain" stroke={MACARON.mint} strokeWidth={2.5} fill="url(#netg)" isAnimationActive={!prefersReducedMotion} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        {plan.length ? (
          <div className="startup-plan">
            <h4>起号计划表 · {plan.length} 周</h4>
            <ol className="timeline">
              {plan.map((w: any, i: number) => (
                <li key={i} style={{ ["--c" as any]: SERIES[i % SERIES.length] }}>
                  <span className="tl-node" />
                  <span className="tl-wk">W{w.week ?? i + 1}</span>
                  <strong className="tl-focus">{w.focus}</strong>
                  <small className="tl-topics">{Array.isArray(w.topics) ? w.topics.join("、") : w.topics}</small>
                </li>
              ))}
            </ol>
          </div>
        ) : null}
      </div>
    </FlowScreen>
  );
}

/* ===================== 06 量化标准(巨数 + 三小注 定义表) ===================== */
function StandardsScreen() {
  const data = useReport();
  const bm = data.benchmark ?? {};
  const hero = {
    label: "爆款阅读门槛",
    value: fmtNum(bm.viral_read_threshold),
    hint: "≥ 本号均值 1.5 倍，达到即记爆款",
  };
  // issue #61：zaikan 不可得时 viral_zaikan_threshold 为 null，不显示 5%
  const zaikanThrMissing =
    bm.viral_zaikan_threshold == null || bm.viral_zaikan_threshold === undefined;
  const notes = [
    { label: "爆款分享率门槛", value: pct(bm.viral_share_threshold, 1), hint: "≥ 中位 2 倍" },
    {
      label: "在看率门槛",
      value: zaikanThrMissing ? "不可得" : pct(bm.viral_zaikan_threshold, 0),
      hint: zaikanThrMissing ? "平台未提供该字段" : "优质传播线",
    },
    { label: "选题有效率", value: pct(bm.topic_select_rate, 0), hint: "超本号均值文章占比" },
  ];
  return (
    <FlowScreen
      id="standards"
      no="06"
      title="量化标准"
      question="怎么算爆款？"
      conclusion="爆款不是绝对阅读量，是相对你自己的倍数"
      action="每月追踪选题有效率是否上行，反映选题能力进步。"
    >
      <div className="standards-def">
        <div className="sd-hero">
          <b className="sd-hero-val">{hero.value}</b>
          <div className="sd-hero-cap">
            <strong>{hero.label}</strong>
            <small>{hero.hint}</small>
          </div>
        </div>
        <dl className="sd-notes">
          {notes.map((n) => (
            <div key={n.label} className="sd-note">
              <dt>
                <strong>{n.label}</strong>
                <small>{n.hint}</small>
              </dt>
              <dd>{n.value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </FlowScreen>
  );
}

/* ===================== 向前看:色映射 ===================== */
// 六维谱配色(逐轴循环)
const AXIS_COLOR = [MACARON.mint, MACARON.peach, MACARON.butter, MACARON.blush, MACARON.lavender, MACARON.sky];
// 信号强度档 → 强度条宽度(表达"信号有多明确",非位置、非置信度)
const LEVEL_W: Record<string, number> = { 强: 84, 中: 56, 弱: 30 };
// feasibility(信号距离/改造成本)→ 色,不带价值判断
const FEAS_COLOR: Record<string, string> = {
  顺手: MACARON.mint,
  够得着: MACARON.sky,
  要改造: MACARON.butter,
  阻力大: MACARON.lavender,
};
// 五角色固定色
const ROLE_COLOR: Record<string, string> = {
  拉新: MACARON.mint,
  养信任: MACARON.blush,
  建专业: MACARON.lavender,
  转化: MACARON.peach,
  留存: MACARON.sky,
};

/* ===================== 怎么办 · 照镜子 ===================== */
function MirrorScreen() {
  const data = useReport();
  const fl = data.forward_looking ?? {};
  const mirror = fl.mirror ?? {};
  const axes = mirror.axes ?? [];
  return (
    <FlowScreen
      id="mirror"
      no="怎么办"
      title="照镜子"
      question="先看清你现在是一个什么样的号"
      conclusion={mirror.statement}
      action="这些特征决定了你接下来能往哪走 —— 见「找方向」"
    >
      <div className="mirror-axes">
        {axes.map((ax: any, i: number) => {
          const weak = ax.level === "弱";
          const c = AXIS_COLOR[i % AXIS_COLOR.length];
          return (
            <div key={ax.key} className={`mx-row${weak ? " weak" : ""}`}>
              <span className="mx-label">{ax.label}</span>
              <span className="mx-level" style={{ color: c }}>
                {ax.level}
              </span>
              <div className="mx-track">
                <div className="mx-fill" style={{ width: `${LEVEL_W[ax.level] ?? 40}%`, background: c }} />
              </div>
              <span className="mx-poles">
                {ax.low} <em>↔</em> {ax.high}
              </span>
              {ax.note ? <span className="mx-note">{ax.note}</span> : null}
            </div>
          );
        })}
      </div>
      {mirror.uncertainty_note ? <p className="mirror-uncertainty">{mirror.uncertainty_note}</p> : null}
    </FlowScreen>
  );
}

/* ===================== 怎么办 · 找方向(选方向) ===================== */
function PathScreen({
  selectedPathId,
  onSelect,
}: {
  selectedPathId: string | null;
  onSelect: (id: string) => void;
}) {
  const data = useReport();
  const fl = data.forward_looking ?? {};
  const paths = fl.candidate_paths ?? [];
  const n = fl.data_sufficiency?.article_count;
  return (
    <FlowScreen
      id="paths"
      no="怎么办"
      title="找方向"
      question="这些方向不是通用模板，是从你的文章里长出来的"
      conclusion={`从你${n ? ` ${n} ` : ""}篇文章里，长出了 ${paths.length} 个可走的方向`}
      action="选一个方向 → 它的内容规划矩阵会在下一屏展开"
    >
      <div className="path-list">
        {paths.map((p: any) => {
          const on = p.id === selectedPathId;
          const c = FEAS_COLOR[p.feasibility] ?? MACARON.sky;
          return (
            <button
              key={p.id}
              type="button"
              className={`path-card${on ? " on" : ""}`}
              style={{ ["--pc" as any]: c }}
              onClick={() => onSelect(p.id)}
            >
              <div className="pc-head">
                <h3 className="pc-name">{p.path_name}</h3>
                <span className="pc-feas" style={{ color: c }}>
                  <i style={{ background: c }} />
                  信号距离 · {p.feasibility}
                </span>
                {on ? (
                  <span className="pc-check" style={{ background: c }}>
                    <Check size={12} strokeWidth={3} />
                  </span>
                ) : null}
              </div>
              <p className="pc-why">{p.rationale_from_status}</p>
              {p.feasibility_note ? <p className="pc-feasnote">{p.feasibility_note}</p> : null}
              <div className="pc-cols">
                <div className="pc-col">
                  <h4>要补上</h4>
                  <ul>
                    {(p.gap ?? []).map((g: string, i: number) => (
                      <li key={i}>{g}</li>
                    ))}
                  </ul>
                </div>
                <div className="pc-col">
                  <h4>怎么变现</h4>
                  <p>{p.monetization}</p>
                </div>
              </div>
              <p className="pc-hint">{p.matrix_hint}</p>
            </button>
          );
        })}
      </div>
    </FlowScreen>
  );
}

/* ===================== 怎么办 · 规划矩阵(读 selectedPathId) ===================== */
function MatrixScreen({
  selectedPathId,
  onSelect,
}: {
  selectedPathId: string | null;
  onSelect: (id: string) => void;
}) {
  const data = useReport();
  const fl = data.forward_looking ?? {};
  const paths = fl.candidate_paths ?? [];
  const byDir = fl.content_matrix?.by_direction ?? {};
  const sel = selectedPathId && byDir[selectedPathId] ? selectedPathId : paths[0]?.id;
  const plan = byDir[sel] ?? {};
  const buckets = (plan.buckets ?? []).slice(0, 6);
  const schedule = plan.schedule ?? [];
  const selName = paths.find((p: any) => p.id === sel)?.path_name ?? "";
  const maxW = Math.max(...buckets.map((b: any) => b.weight ?? 0), 0.01);
  return (
    <FlowScreen
      id="matrix"
      no="怎么办"
      title="规划矩阵"
      question="选定方向后，内容按 5 个角色分桶配比"
      conclusion={selName ? `「${selName}」的内容配比与排期` : "选一个方向，看它的内容配比"}
      action="想换方向？点上方任一方向，配比与排期会实时重排"
    >
      <div className="matrix-switch">
        {paths.map((p: any) => (
          <button
            key={p.id}
            type="button"
            className={`ms-chip${p.id === sel ? " on" : ""}`}
            onClick={() => onSelect(p.id)}
          >
            {p.path_name}
          </button>
        ))}
      </div>

      <div className="matrix-buckets">
        {buckets.map((b: any, i: number) => {
          const c = ROLE_COLOR[b.role] ?? MACARON.sky;
          return (
            <div key={i} className="mb-row" style={{ ["--rc" as any]: c }}>
              <span className="mb-role">{b.role}</span>
              <div className="mb-bar-wrap">
                <div className="mb-bar" style={{ width: `${(b.weight / maxW) * 100}%` }} />
                <b className="mb-pct">{pct(b.weight)}</b>
              </div>
              <div className="mb-topics">
                {(b.topics ?? []).map((t: string, j: number) => (
                  <span key={j} className="mb-tag">
                    {t}
                  </span>
                ))}
              </div>
              <span className="mb-meta">
                {b.horizon} · {b.rhythm}
              </span>
            </div>
          );
        })}
      </div>

      {schedule.length ? (
        <div className="matrix-schedule">
          <h4 className="ms-head">排期</h4>
          <ol className="ms-timeline">
            {schedule.map((s: any, i: number) => (
              <li key={i} style={{ ["--c" as any]: SERIES[i % SERIES.length] }}>
                <span className="mst-node" />
                <span className="mst-phase">{s.phase}</span>
                <strong className="mst-focus">{s.focus}</strong>
                <span className="mst-cadence">{s.cadence}</span>
                <small className="mst-topics">{(s.topics ?? []).join("、")}</small>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
    </FlowScreen>
  );
}

/* ===================== 怎么办 · 数据不足屏(闸门未过) ===================== */
function InsufficientScreen() {
  const data = useReport();
  const fl = data.forward_looking ?? {};
  const ds = fl.data_sufficiency ?? {};
  const reasons = ds.reasons ?? [];
  return (
    <FlowScreen
      id="mirror"
      no="怎么办"
      title="向前看"
      question="方向推导需要足够的样本厚度"
      conclusion={ds.statement || "样本还不够，方向推导暂未解锁"}
      action="继续积累文章，达到样本门槛后这里会自动展开照镜子 / 找方向 / 规划矩阵"
    >
      <div className="insufficient">
        {reasons.length ? (
          <ul className="ins-reasons">
            {reasons.map((r: string, i: number) => (
              <li key={i}>
                <span className="ins-dot" />
                {r}
              </li>
            ))}
          </ul>
        ) : (
          <p className="ins-empty">达到样本门槛后，方向引擎会基于你的真实文章构成，推导出专属于你的方向。</p>
        )}
      </div>
    </FlowScreen>
  );
}

/* ===================== 怎么办 · 本周行动(三篮子,置信内化为版面重量) ===================== */
function ActionScreen() {
  const data = useReport();
  const a = data.modules?.action_plan ?? {};
  const asText = (it: any) => (typeof it === "string" ? it : it.title ?? it.text ?? "");
  const now: any[] = a.now ?? [];
  const experiment: any[] = a.experiment ?? [];
  const hold: any[] = a.hold ?? [];
  const nextTopics = Array.isArray(a.next_topics) ? a.next_topics : [];
  return (
    <FlowScreen
      id="action"
      no="怎么办"
      title="本周行动"
      question="落到下周，具体做什么？"
      conclusion={a.analysis}
      action={nextTopics.length ? `下周选题：${nextTopics.slice(0, 2).join("；")}` : undefined}
    >
      <div className="weekly">
        <div className="wk-now">
          <p className="wk-cap" style={{ ["--c" as any]: MACARON.mint }}>
            现在就做
          </p>
          <ul className="wk-now-list">
            {now.length ? (
              now.map((it, i) => <li key={i}>{asText(it)}</li>)
            ) : (
              <li className="empty">暂无</li>
            )}
          </ul>
        </div>
        <div className="wk-rest">
          <div className="wk-col">
            <p className="wk-cap" style={{ ["--c" as any]: MACARON.butter }}>
              小步验证
            </p>
            <ul className="wk-list">
              {experiment.length ? (
                experiment.map((it, i) => <li key={i}>{asText(it)}</li>)
              ) : (
                <li className="empty">暂无</li>
              )}
            </ul>
          </div>
          <div className="wk-col hold">
            <p className="wk-cap" style={{ ["--c" as any]: MACARON.lavender }}>
              暂不拍板
            </p>
            <ul className="wk-list">
              {hold.length ? (
                hold.map((it, i) => <li key={i}>{asText(it)}</li>)
              ) : (
                <li className="empty">暂无</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </FlowScreen>
  );
}

/* ===================== 覆盖率警示(C4 闸门在看板的落点) =====================
   与 Markdown 报告同口径：题材/痛点/人群三组分布不可作决策依据，
   方向引擎与账号类型路由已降级为通用链路。
   不用刺目红色 —— 这是「结论要打折看」，不是「系统坏了」。 */
function CoverageAlert() {
  const data = useReport();
  const cov = data.niche_coverage ?? {};
  if (cov.alert !== true) return null;
  const name = cov.niche_name || cov.niche_id || "当前赛道包";
  const hit = pct(cov.hit_rate, 1);
  const thr = pct(cov.threshold, 0);
  const req = cov.requested_id;
  const fellBack = req && cov.niche_id && req !== cov.niche_id;
  return (
    <div className="cov-wrap">
      <div className="cov-alert" role="status">
        <AlertTriangle className="cov-ico" size={16} aria-hidden />
        <div className="cov-body">
          <p className="cov-head">
            赛道包「{name}」与本号内容匹配度过低 —— 题材词表命中率 {hit}，低于阈值 {thr}
          </p>
          <p className="cov-sub">
            {fellBack ? `你指定的赛道包 ${req} 未找到，已回落通用兜底包。` : ""}
            下文【题材 / 痛点 / 人群】三组分布不可作为决策依据，方向引擎与账号类型路由都已降级为通用链路。
            出路有两条：换用更贴合的赛道包，或给现有包补词表，然后重跑 analyze。
          </p>
        </div>
      </div>
    </div>
  );
}

/* ===================== 加载 / 失败屏 ===================== */
function BootScreen() {
  // 延迟 200ms 才淡入：本地 fetch 通常更快，避免加载态一闪而过
  return (
    <div className="boot">
      <span className="boot-dot" aria-hidden />
      <p className="boot-line">正在加载账号数据…</p>
    </div>
  );
}

function LoadError({ message }: { message: string }) {
  return (
    <div className="boot boot-err">
      <AlertTriangle className="boot-err-ico" size={22} aria-hidden />
      <p className="boot-line">看板数据没能加载</p>
      <p className="boot-hint">{message}</p>
      <p className="boot-hint dim">
        先确认这个账号跑过 <code>wxops analyze</code>；如果刚跑完，刷新页面重试。
      </p>
    </div>
  );
}

/* ===================== 数据编排 =====================
   先取 data/accounts.json 账号索引，再按当前账号取报告。
   换号命中缓存则零延迟切换；未命中才 fetch，期间保留当前内容不白屏。 */
function useDashboardData() {
  const [index, setIndex] = React.useState<AccountsIndex | null>(null);
  const [slug, setSlug] = React.useState("");
  const [report, setReport] = React.useState<any>(null);
  const [error, setError] = React.useState("");
  const [switching, setSwitching] = React.useState(false);
  const cache = React.useRef(new Map<string, any>());

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await fetch("data/accounts.json", { cache: "no-store" });
        if (!r.ok) throw new Error(`读取账号索引失败（HTTP ${r.status}）`);
        const idx: AccountsIndex = await r.json();
        if (!alive) return;
        setIndex(idx);
        const list = idx.accounts ?? [];
        const pick =
          list.find((a) => a.slug === idx.current && a.has_report) ??
          list.find((a) => a.has_report);
        if (!pick?.report_url) {
          setError("还没有任何账号的分析数据。先跑一次 wxops analyze 生成报告。");
          return;
        }
        const rr = await fetch(pick.report_url, { cache: "no-store" });
        if (!rr.ok) throw new Error(`读取报告失败（HTTP ${rr.status}）`);
        const rep = await rr.json();
        if (!alive) return;
        cache.current.set(pick.slug, rep);
        setSlug(pick.slug);
        setReport(rep);
      } catch (e: any) {
        if (alive) setError(String(e?.message ?? e));
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const switchTo = React.useCallback(
    async (next: string) => {
      if (!next || next === slug) return;
      const hit = cache.current.get(next);
      if (hit) {
        setSlug(next);
        setReport(hit);
        return;
      }
      const entry = (index?.accounts ?? []).find((a) => a.slug === next);
      if (!entry?.report_url) return;
      setSwitching(true);
      try {
        const r = await fetch(entry.report_url, { cache: "no-store" });
        if (!r.ok) throw new Error(`读取报告失败（HTTP ${r.status}）`);
        const rep = await r.json();
        cache.current.set(next, rep);
        setSlug(next);
        setReport(rep);
      } catch (e: any) {
        setError(String(e?.message ?? e));
      } finally {
        setSwitching(false);
      }
    },
    [slug, index],
  );

  return { index, slug, report, error, switching, switchTo };
}

/* ===================== App ===================== */
export default function App() {
  const { index, slug, report, error, switching, switchTo } = useDashboardData();
  if (error) return <LoadError message={error} />;
  if (!report) return <BootScreen />;
  return (
    <ReportCtx.Provider value={report}>
      <Dashboard
        index={index}
        slug={slug}
        switching={switching}
        onSwitch={switchTo}
      />
    </ReportCtx.Provider>
  );
}

function Dashboard({
  index,
  slug,
  switching,
  onSwitch,
}: {
  index: AccountsIndex | null;
  slug: string;
  switching: boolean;
  onSwitch: (slug: string) => void;
}) {
  const data = useReport();
  const fl = data.forward_looking ?? {};
  const passed = Boolean(fl.data_sufficiency?.passed);
  const paths: any[] = fl.candidate_paths ?? [];
  const groups = buildNavGroups(passed);
  const ids = groups.flatMap((g) => g.items.map((m) => m.id));
  const active = useActiveSection(ids);
  const [selectedPathId, setSelectedPathId] = React.useState<string | null>(paths[0]?.id ?? null);

  // 换号 = 换了一份报告：重置路径选择并回到开头，让叙事重新讲一遍
  const first = React.useRef(true);
  React.useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    setSelectedPathId(paths[0]?.id ?? null);
    document.querySelector(".main-scroll")?.scrollTo({
      top: 0,
      behavior: prefersReducedMotion ? "auto" : "smooth",
    });
    // paths 随 data 一同更新，此处只由 slug 驱动
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  return (
    <div className="page">
      <SideNav
        groups={groups}
        active={active}
        index={index}
        current={slug}
        switching={switching}
        onSwitch={onSwitch}
      />
      <main className="main-scroll" aria-label="公众号运营诊断">
        {/* 赛道包命中率过低时的降级警示(C4) */}
        <CoverageAlert />

        {/* 第一幕:体检结论 */}
        <Overview />

        {/* 第二幕:为什么 —— 六份证据 */}
        <ActDivider eyebrow="为什么" line="这个判断从哪来？" sub="六份证据，按诊断顺序展开" />
        <CheckupScreen />
        <ViralScreen />
        <ContentScreen />
        <AudienceScreen />
        <GrowthScreen />
        <StandardsScreen />

        {/* 第三幕:怎么办 —— 照镜子 → 找方向 → 规划矩阵 → 本周行动 */}
        <ActDivider eyebrow="怎么办" line="看清现状，才谈得上选方向。" sub="方向从你的文章里长出来，不是通用菜单" />
        {passed ? (
          <>
            <MirrorScreen />
            <PathScreen selectedPathId={selectedPathId} onSelect={setSelectedPathId} />
            <MatrixScreen selectedPathId={selectedPathId} onSelect={setSelectedPathId} />
          </>
        ) : (
          <InsufficientScreen />
        )}
        <ActionScreen />

        <footer className="dash-footer">
          <span>Markdown 报告 · wiki 数据集 · 本看板共用同一份结构化数据</span>
        </footer>
      </main>
    </div>
  );
}
