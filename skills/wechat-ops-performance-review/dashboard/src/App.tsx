import * as React from "react";
import {
  Activity,
  Compass,
  Dna,
  Layers3,
  Users,
  TrendingUp,
  ListChecks,
  Target,
  Github,
  Star,
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
import report from "./data/report.json";

const data: any = report;

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

/* ===================== 七模块导航 ===================== */
const MODULES = [
  { id: "overview", no: "", label: "概览", icon: Compass, star: false },
  { id: "checkup", no: "01", label: "账号体检", icon: Activity, star: false },
  { id: "viral", no: "02", label: "爆款基因", icon: Dna, star: true },
  { id: "content", no: "03", label: "内容引擎", icon: Layers3, star: false },
  { id: "audience", no: "04", label: "读者画像", icon: Users, star: false },
  { id: "growth", no: "05", label: "涨粉漏斗", icon: TrendingUp, star: false },
  { id: "action", no: "06", label: "行动计划", icon: ListChecks, star: false },
  { id: "standards", no: "07", label: "量化标准", icon: Target, star: false },
];

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

/* ===================== 左栏 ===================== */
function SideNav({ active }: { active: string }) {
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

      <nav className="sn-nav" aria-label="诊断科目">
        {MODULES.map((m) => (
          <a
            key={m.id}
            href={`#${m.id}`}
            className={`sn-item${active === m.id ? " active" : ""}${m.star ? " star" : ""}`}
          >
            <span className="sn-no">{m.no || <m.icon size={15} />}</span>
            <span className="sn-label">{m.label}</span>
            {m.star ? <Dna className="sn-star" size={13} /> : null}
          </a>
        ))}
      </nav>

      <div className="sn-author">
        <div className="sn-author-name">
          <img className="av" src="/avatar-demo.png" alt="" />
          {sig.author_name ?? "麦总玩AI"}
        </div>
        <a className="sn-star-btn" href={repo} target="_blank" rel="noreferrer">
          <Github size={14} />
          <span>Star on GitHub</span>
          <Star className="star" size={13} />
        </a>
      </div>
    </aside>
  );
}

/* ===================== 概览 bento(健康分主块 + 阶段结论) ===================== */

/* ===================== 爆款基因卡(signature) ===================== */
function ViralGeneCard() {
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

/* ===================== 概览首屏 ===================== */
function Overview() {
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
  const selRate = useCountUp((bm.topic_select_rate ?? 0) * 100);

  return (
    <section id="overview" className="screen overview">
      {/* ① 账号信息条 */}
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
            微信公众号 · {String(meta.period_start ?? "").slice(0, 10)} 起 · 累计{" "}
            {fmtNum(acc.cumulate_user)} 粉
          </p>
        </div>
      </header>

      {/* ②③ bento:健康分主块(大) + 阶段结论(次) */}
      <div className="ov-bento">
        <div className="ov-health">
          <div
            className="ovh-ring"
            style={{ background: `conic-gradient(${MACARON.mint} ${Math.min(100, checkup.health_score ?? 0)}%, #ece7df 0)` }}
          >
            <div className="ovh-core">
              <strong>{Math.round(score)}</strong>
              <span>健康分</span>
            </div>
          </div>
          <div className="ovh-stats">
            <div>
              <b>{fmtNum(Math.round(fans))}</b>
              <span>累计粉丝</span>
            </div>
            <div>
              <b>{Math.round(selRate)}%</b>
              <span>选题有效率</span>
            </div>
            <div>
              <b>+{recentNet}</b>
              <span>近 7 天净增</span>
            </div>
          </div>
        </div>

        <div className="ov-stage">
          <span className="ovs-label">当前阶段</span>
          <h2>{top.verdict ?? checkup.verdict ?? "数据分析中"}</h2>
          <p>{top.support ?? checkup.action ?? ""}</p>
        </div>
      </div>

      {/* ④ 爆款密码(signature,全宽收尾) */}
      <ViralGeneCard />
    </section>
  );
}

/* ===================== 模块屏壳 ===================== */
function Screen({
  id,
  no,
  title,
  question,
  conclusion,
  action,
  children,
}: {
  id: string;
  no: string;
  title: string;
  question?: string;
  conclusion?: string;
  action?: string;
  children: React.ReactNode;
}) {
  const { ref, seen } = useInView<HTMLDivElement>();
  return (
    <section id={id} className="screen module">
      <header className="mod-head">
        <span className="mod-no">{no}</span>
        <h2>{title}</h2>
        {question ? <p>{question}</p> : null}
      </header>
      <div className={`mod-body${seen ? " in" : ""}`} ref={ref as any}>
        <div className="mod-visual">{children}</div>
        {(conclusion || action) && (
          <aside className="mod-aside">
            {conclusion ? (
              <div className="mod-concl">
                <span className="tag">结论</span>
                <p>{conclusion}</p>
              </div>
            ) : null}
            {action ? (
              <div className="mod-action">
                <span className="tag tag-act">下一步</span>
                <p>{action}</p>
              </div>
            ) : null}
          </aside>
        )}
      </div>
    </section>
  );
}

/* ===================== 01 账号体检 ===================== */
function CheckupScreen() {
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
  const inters = [
    { label: "在看率", value: pct(inter.zaikan_rate, 1), color: MACARON.mint },
    { label: "分享率", value: pct(inter.share_rate, 1), color: MACARON.blush },
    { label: "评论率", value: pct(inter.comment_rate, 1), color: MACARON.butter },
  ];
  return (
    <Screen id="checkup" no="01" title="账号体检" question="账号现在什么状态？" conclusion={c.verdict} action={c.action}>
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
        <div className="checkup-inter">
          {inters.map((r) => (
            <div key={r.label} className="ichip" style={{ ["--c" as any]: r.color }}>
              <strong>{r.value}</strong>
              <span>{r.label}</span>
            </div>
          ))}
        </div>
      </div>
    </Screen>
  );
}

/* ===================== 02 爆款基因(四象限) ===================== */
function ViralScreen() {
  const vg = data.viral_genes ?? {};
  const bm = data.benchmark ?? {};
  const points = (vg.quadrant ?? []).map((a: any) => ({
    x: a.reads,
    y: (a.share_rate ?? 0) * 100,
    q: a.quadrant,
    title: a.title,
  }));
  const counts = vg.quadrant_counts ?? {};
  const order = ["爆款", "标题党", "深度遗珠", "平稳"];
  return (
    <Screen
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
          <ResponsiveContainer width="100%" height={360}>
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
                content={({ active, payload }: any) => {
                  if (!active || !payload?.length) return null;
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
                  <Cell key={i} fill={QUADRANT_COLOR[p.q] ?? MACARON.sky} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div className="quadrant-legend">
          {order.map((q) => (
            <div key={q} className="qleg">
              <i style={{ background: QUADRANT_COLOR[q] }} />
              <span>{q}</span>
              <b>{counts[q] ?? 0}</b>
            </div>
          ))}
          <p className="qhint">高读高享=爆款，高读低享=标题党，低读高享=深度遗珠。</p>
        </div>
      </div>
    </Screen>
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
  const ce = data.modules?.content_engine ?? {};
  const topics = (ce.by_topic ?? [])
    .filter((t: any) => (t.count ?? 0) > 0)
    .sort((a: any, b: any) => (b.median ?? 0) - (a.median ?? 0));
  const max = Math.max(...topics.map((t: any) => t.median ?? 0), 1);
  const rows = topics.map((t: any) => ({ label: t.key, value: t.median ?? 0 }));
  const ratio = ce.recommended_ratio ?? [];
  return (
    <Screen id="content" no="03" title="内容引擎" question="哪些题材拉新，哪些建心智？" conclusion={ce.conclusion} action={ce.action}>
      <div className="content-wrap">
        <RankBars rows={rows} max={max} unit=" 中位阅读" />
        <div className="ratio-strip">
          {ratio.slice(0, 5).map((r: any, i: number) => (
            <div key={r.topic} className="ratio-item" style={{ ["--c" as any]: SERIES[i % SERIES.length] }}>
              <b>{pct(r.ratio)}</b>
              <span>{r.topic}</span>
            </div>
          ))}
        </div>
      </div>
    </Screen>
  );
}

/* ===================== 04 读者画像 ===================== */
function AudienceScreen() {
  const au = data.modules?.audience ?? {};
  const available = au.fans_portrait_available;
  const city = (au.city ?? []).slice(0, 8);
  const maxCity = Math.max(...city.map((c: any) => c.value ?? 0), 1);
  const age = au.age ?? [];
  const src = au.user_source ?? [];
  return (
    <Screen id="audience" no="04" title="读者画像" question="你的读者到底是谁？" conclusion={au.conclusion} action={au.action}>
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
    </Screen>
  );
}

/* ===================== 05 涨粉漏斗 ===================== */
function GrowthScreen() {
  const g = data.modules?.growth_funnel ?? {};
  const trend = (g.netgain_trend ?? []).map((r: any) => ({
    date: String(r.date ?? "").slice(5),
    netgain: r.netgain ?? 0,
  }));
  const plan = g.startup_plan ?? [];
  return (
    <Screen id="growth" no="05" title="涨粉漏斗" question="怎么涨粉、怎么起号？" conclusion={g.conclusion} action={g.action}>
      <div className="growth-wrap">
        <div className="growth-chart">
          <h4>粉丝净增趋势</h4>
          <ResponsiveContainer width="100%" height={320}>
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
        <div className="startup-plan">
          <h4>起号计划表</h4>
          <ol>
            {plan.map((w: any, i: number) => (
              <li key={i} style={{ ["--c" as any]: SERIES[i % SERIES.length] }}>
                <span className="wk">W{w.week ?? i + 1}</span>
                <div>
                  <strong>{w.focus}</strong>
                  <small>{Array.isArray(w.topics) ? w.topics.join("、") : w.topics}</small>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </Screen>
  );
}

/* ===================== 06 行动计划 ===================== */
function ActionScreen() {
  const a = data.modules?.action_plan ?? {};
  const cols = [
    { key: "now", title: "现在就做", items: a.now ?? [], tone: MACARON.mint },
    { key: "experiment", title: "小步验证", items: a.experiment ?? [], tone: MACARON.butter },
    { key: "hold", title: "暂不拍板", items: a.hold ?? [], tone: MACARON.lavender },
  ];
  return (
    <Screen
      id="action"
      no="06"
      title="行动计划"
      question="下周具体做什么？"
      conclusion={a.analysis}
      action={Array.isArray(a.next_topics) ? `下周选题：${a.next_topics.slice(0, 2).join("；")}` : undefined}
    >
      <div className="action-baskets">
        {cols.map((c) => (
          <div key={c.key} className="basket" style={{ ["--c" as any]: c.tone }}>
            <h4>{c.title}</h4>
            <ul>
              {(c.items.length ? c.items : ["暂无"]).map((it: any, i: number) => (
                <li key={i}>{typeof it === "string" ? it : it.title ?? it.text ?? JSON.stringify(it)}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Screen>
  );
}

/* ===================== 07 量化标准 ===================== */
function StandardsScreen() {
  const bm = data.benchmark ?? {};
  const cards = [
    { label: "爆款阅读门槛", value: fmtNum(bm.viral_read_threshold), hint: "≥ 本号均值 1.5 倍", c: MACARON.mint },
    { label: "爆款分享率门槛", value: pct(bm.viral_share_threshold, 1), hint: "≥ 中位 2 倍", c: MACARON.blush },
    { label: "在看率门槛", value: pct(bm.viral_zaikan_threshold, 0), hint: "优质传播线", c: MACARON.butter },
    { label: "选题有效率", value: pct(bm.topic_select_rate, 0), hint: "超本号均值文章占比", c: MACARON.lavender },
  ];
  return (
    <Screen
      id="standards"
      no="07"
      title="量化标准"
      question="怎么算爆款？"
      conclusion="爆款看本号相对值：阅读≥均值1.5倍 且 分享率≥中位2倍 且 在看≥5%。"
      action="每月追踪选题有效率是否上行，反映选题能力进步。"
    >
      <div className="standards-grid">
        {cards.map((c) => (
          <div key={c.label} className="std-card" style={{ ["--c" as any]: c.c }}>
            <b>{c.value}</b>
            <strong>{c.label}</strong>
            <small>{c.hint}</small>
          </div>
        ))}
      </div>
    </Screen>
  );
}

/* ===================== App ===================== */
export default function App() {
  const ids = MODULES.map((m) => m.id);
  const active = useActiveSection(ids);
  return (
    <div className="page">
      <SideNav active={active} />
      <main className="main-scroll" aria-label="公众号运营诊断">
        <Overview />
        <CheckupScreen />
        <ViralScreen />
        <ContentScreen />
        <AudienceScreen />
        <GrowthScreen />
        <ActionScreen />
        <StandardsScreen />
        <footer className="dash-footer">
          <span>Markdown 报告 · wiki 数据集 · 本看板共用同一份结构化数据</span>
        </footer>
      </main>
    </div>
  );
}
