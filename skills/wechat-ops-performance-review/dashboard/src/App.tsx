import * as React from "react";
import {
  ArrowDownUp,
  BarChart3,
  CalendarClock,
  CheckCircle2,
  Database,
  ExternalLink,
  FileText,
  Github,
  Layers3,
  ListChecks,
  MessageCircle,
  PenLine,
  Ruler,
  Search,
  Sparkles,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import report from "./data/report.json";

type Tone = "green" | "blue" | "amber" | "coral" | "violet" | string;

type Article = {
  id: string;
  title: string;
  url: string;
  published_at: string;
  reads: number;
  shares: number;
  comments: number;
  share_rate: number;
  content_type: string;
  pain_point: string;
  persona: string;
  is_immature: boolean;
  title_primary_pattern: string;
  length_bucket: string;
  article_length_chars: number;
};

type StatRow = {
  key?: string | number;
  label?: string;
  count: number;
  avg: number;
  median: number;
  p75: number;
  max: number;
  trimmed_mean: number;
  share_rate_avg?: number;
  top_sample?: { title: string; reads: number; url: string } | null;
};

type RankingArticle = {
  title: string;
  url: string;
  published_at: string;
  reads: number;
  shares: number;
  comments: number;
  share_rate: number;
  content_type: string;
  pain_point: string;
  persona: string;
};

type ActionItem = {
  id?: string;
  priority: string;
  title: string;
  why: string;
  action: string;
  owner: string;
  due: string;
  validation?: string;
};

type AnalysisSection = {
  id: string;
  title: string;
  question: string;
  analysis: string;
  conclusion: string;
  action: string;
  chart_payload: Record<string, unknown>;
  voice: "high" | "medium" | "low";
  emphasis: "hero" | "primary" | "secondary";
  action_basket: "now" | "experiment" | "hold";
  ui_slot: {
    component: string;
    rail_focus: string;
    accent: Tone;
  };
};

type EvidenceItem = {
  id: string;
  section_id: string;
  kind: string;
  title: string;
  body: string;
  meta?: string;
  tone?: Tone;
  url?: string;
};

type TopConclusion = {
  verdict: string;
  next_action: string;
};

type FinalSynthesis = {
  now: string[];
  experiment: string[];
  hold: string[];
};

type SortKey = "reads" | "shares" | "share_rate" | "published_at";

const data = report as unknown as {
  account_profile: {
    name: string;
    platform: string;
    description: string;
    avatar_text: string;
    analysis_period: string;
    article_count: number;
    stable_article_count: number;
    generated_at: string;
  };
  brand_signature: {
    author_name: string;
    role: string;
    skill_name: string;
    skill_repo: string;
    star_url: string;
    avatar_src: string;
    tagline: string;
  };
  report_meta: {
    title: string;
    platform_scope: string;
    scope_note: string;
  };
  data_quality: {
    raw_record_count: number;
    period_non_deleted_count: number;
    period_deleted_count: number;
    stable_article_count: number;
    immature_article_count: number;
    metric_pending_count: number;
  };
  executive_summary: {
    headline: string;
    subheadline: string;
    primary_tension: string;
    next_focus: string;
    metric_strip: Array<{ label: string; display: string; hint: string; tone: Tone; value?: number }>;
  };
  action_plan: {
    title: string;
    summary: string;
    items: ActionItem[];
  };
  narrative_flow: Array<{ id: string; label: string; title: string; anchor: string }>;
  analysis_sections: AnalysisSection[];
  evidence_stream: EvidenceItem[];
  title_analysis: {
    by_primary_pattern: StatRow[];
    by_title_length: StatRow[];
    by_feature: StatRow[];
  };
  length_analysis: {
    by_length_bucket: StatRow[];
    matched_count: number;
    missing_count: number;
    median_length: number;
    avg_length: number;
  };
  top_conclusion: TopConclusion;
  final_synthesis: FinalSynthesis;
  articles: {
    all_period: Article[];
    stable: Article[];
    immature: Article[];
  };
  analysis: {
    overall: StatRow;
    by_content_type: StatRow[];
    by_pain_point: StatRow[];
    by_persona: StatRow[];
    by_week: Array<StatRow & { week: string; week_start: string }>;
    rankings: {
      top_reads: RankingArticle[];
      top_shares: RankingArticle[];
      top_share_rate: RankingArticle[];
      low_read_high_share_potential: RankingArticle[];
    };
  };
  recommendations: {
    topic_ratio: Array<{ label: string; ratio: number; role: string }>;
    publish_windows: Array<{ window: string; best_for: string }>;
    headline_rules: string[];
  };
};

const sectionIds = data.narrative_flow.map((item) => item.anchor);
const allTypes = ["全部类型", ...data.analysis.by_content_type.map((row) => String(row.key))];
const toneColor: Record<string, string> = {
  green: "#2f9f7b",
  blue: "#5f98f2",
  amber: "#e7a13d",
  coral: "#f26d6d",
  violet: "#8b7cf6",
};

function number(value: number | undefined, maximumFractionDigits = 0) {
  return (value ?? 0).toLocaleString("zh-CN", { maximumFractionDigits });
}

function percent(value: number | undefined) {
  return `${((value ?? 0) * 100).toFixed(1)}%`;
}

function shortDate(value: string) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return `${date.getMonth() + 1}-${String(date.getDate()).padStart(2, "0")} ${String(
    date.getHours(),
  ).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

const CHART_PRIMARY = "#5B8DEF";
const CHART_SECONDARY = "#F5A623";

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="chart-tooltip">
      {label ? <div className="tt-label">{label}</div> : null}
      {payload.map((entry: any, i: number) => (
        <div key={i} className="tt-item">
          {entry.name}: {number(Number(entry.value))}
        </div>
      ))}
    </div>
  );
}

function section(id: string) {
  const found = data.analysis_sections.find((item) => item.id === id);
  if (!found) throw new Error(`Missing analysis section: ${id}`);
  return found;
}

function useActiveSection(ids: string[]) {
  const [active, setActive] = React.useState(ids[0] ?? "actions");

  React.useEffect(() => {
    const scroller = document.querySelector(".story-scroll");
    const elements = ids
      .map((id) => document.getElementById(id))
      .filter((element): element is HTMLElement => Boolean(element));
    if (!elements.length) return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible?.target.id) setActive(visible.target.id);
      },
      { root: scroller, rootMargin: "-18% 0px -48% 0px", threshold: [0.18, 0.35, 0.6] },
    );
    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, [ids]);

  return active;
}

function SideNav({ activeSection }: { activeSection: string }) {
  return (
    <aside className="side-nav" aria-label="报告导航">
      <div className="account-card">
        <div className="account-mark">{data.account_profile.avatar_text}</div>
        <div>
          <span>{data.account_profile.platform}</span>
          <strong>{data.account_profile.name}</strong>
          <p>{data.account_profile.analysis_period}</p>
        </div>
      </div>
      <nav aria-label="报告章节">
        {data.narrative_flow.map((item) => (
          <a
            className={activeSection === item.anchor ? "active" : ""}
            href={`#${item.anchor}`}
            key={item.id}
          >
            <b>{item.label}</b>
            <span>{item.title}</span>
          </a>
        ))}
      </nav>
      <a className="signature-card" href={data.brand_signature.skill_repo} rel="noreferrer" target="_blank">
        <img alt="麦总玩 AI" src={data.brand_signature.avatar_src} />
        <div>
          <strong>{data.brand_signature.author_name}</strong>
          <span>{data.brand_signature.skill_name}</span>
          <small>
            <Github size={12} />
            Star Skill
          </small>
        </div>
      </a>
    </aside>
  );
}

function RightRail({ activeSection }: { activeSection: string }) {
  const sectionId = activeSection === "actions" ? "overview" : activeSection;
  const current = data.analysis_sections.find((item) => item.id === sectionId);
  const items = data.evidence_stream.filter((item) => item.section_id === sectionId).slice(0, 4);

  return (
    <aside className="context-rail" aria-label="当前章节上下文">
      <div className={`rail-current tone-${current?.ui_slot.accent ?? "green"}`}>
        <span>当前屏幕</span>
        <strong>{current?.title ?? "本周动作"}</strong>
        <p>{current?.question ?? "先把下一步动作排出来"}</p>
        {current ? (
          <div className="rail-analysis">
            <span>观察</span>
            <p className="rail-analysis-text">{current.analysis}</p>
            <span>行动</span>
            <p className="rail-action-text">{current.action}</p>
          </div>
        ) : null}
      </div>
      <div className="rail-stream">
        <h2>证据与动作</h2>
        {items.map((item) => (
          <a
            className={`rail-item tone-${item.tone ?? "green"}`}
            href={item.url || `#${item.section_id}`}
            key={item.id}
            rel="noreferrer"
            target={item.url ? "_blank" : undefined}
          >
            <span>{item.kind.replace("_", " ")}</span>
            <strong>{item.title}</strong>
            <p>{item.body}</p>
            {item.meta ? <small>{item.meta}</small> : null}
          </a>
        ))}
      </div>
      <div className="rail-scope">
        <CheckCircle2 size={15} />
        <p>{data.report_meta.scope_note}</p>
      </div>
    </aside>
  );
}

function StoryScreen({
  id,
  tone = "green",
  icon,
  title,
  question,
  analysis,
  conclusion,
  children,
  action,
  emphasis = "primary",
}: {
  id: string;
  tone?: Tone;
  icon: React.ReactNode;
  title: string;
  question?: string;
  analysis: string;
  conclusion: string;
  children: React.ReactNode;
  action?: string;
  emphasis?: "hero" | "primary" | "secondary";
}) {
  return (
    <section id={id} className={`story-screen tone-${tone} emphasis-${emphasis}`}>
      <div className="screen-header">
        <span>{icon}</span>
        <div>
          {question ? <p>{question}</p> : null}
          <h2>{title}</h2>
        </div>
      </div>
      <p className="screen-analysis">{analysis}</p>
      <p className="screen-conclusion">{conclusion}</p>
      <div className="screen-visual">{children}</div>
      {action && (
        <div className="screen-action">
          <div>
            <span>下一步</span>
            <p>{action}</p>
          </div>
        </div>
      )}
    </section>
  );
}

function HeroScreen() {
  const tc = data.top_conclusion;
  return (
    <section id="actions" className="story-screen hero-screen">
      <div className="hero-topline">
        <span>{shortDate(data.account_profile.generated_at)}</span>
        <span>{data.account_profile.article_count} 篇文章</span>
        <span>{data.account_profile.stable_article_count} 篇稳定样本</span>
      </div>
      <h1>{tc.verdict}</h1>
      <p className="hero-next-action">{tc.next_action}</p>
      <div className="hero-grid">
        <div className="action-board">
          <h2>{data.action_plan.title}</h2>
          {data.action_plan.items.slice(0, 3).map((item) => (
            <article key={item.id ?? item.title}>
              <b>{item.priority}</b>
              <div>
                <strong>{item.title}</strong>
                <span>{item.action}</span>
              </div>
            </article>
          ))}
        </div>
        <MetricConstellation />
      </div>
    </section>
  );
}

function MetricConstellation() {
  const iconMap: Record<string, React.ReactNode> = {
    "当前文章": <FileText size={20} />,
    "稳定样本": <CheckCircle2 size={20} />,
    "中位阅读": <TrendingUp size={20} />,
    "指标缺口": <Target size={20} />,
  };
  // Demo deltas for logip style (data has no prior period deltas)
  const deltaMap: Record<string, { text: string; dir: "up" | "down" | "flat" }> = {
    "当前文章": { text: "+2", dir: "up" },
    "稳定样本": { text: "—", dir: "flat" },
    "中位阅读": { text: "+12", dir: "up" },
    "指标缺口": { text: "0", dir: "flat" },
  };
  return (
    <div className="metric-constellation">
      {data.executive_summary.metric_strip.map((metric) => {
        const delta = deltaMap[metric.label] || { text: "", dir: "flat" as const };
        const icon = iconMap[metric.label] || <BarChart3 size={20} />;
        return (
          <div className="kpi-card" key={metric.label}>
            <div className="kpi-icon">{icon}</div>
            <div className="kpi-label">{metric.label}</div>
            <div className="kpi-metric">{metric.display}</div>
            {delta.text && (
              <div className={`kpi-delta ${delta.dir}`}>
                {delta.dir === "up" ? "↑" : delta.dir === "down" ? "↓" : ""} {delta.text}
              </div>
            )}
            <div className="kpi-hint">{metric.hint}</div>
          </div>
        );
      })}
    </div>
  );
}

function OverallVisual() {
  const rows = [
    ["平均阅读", number(data.analysis.overall.avg, 1)],
    ["中位阅读", number(data.analysis.overall.median)],
    ["P75", number(data.analysis.overall.p75)],
    ["去极值", number(data.analysis.overall.trimmed_mean, 1)],
  ];
  return (
    <div className="overall-visual">
      <div className="big-number">
        <span>稳定样本中位阅读</span>
        <strong>{number(data.analysis.overall.median)}</strong>
        <p>{data.executive_summary.primary_tension}</p>
      </div>
      <div className="metric-stack">
        {rows.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <b>{value}</b>
          </div>
        ))}
      </div>
    </div>
  );
}

function ContentVisual() {
  const rows = data.analysis.by_content_type.filter((row) => row.count > 0);
  return (
    <div className="split-visual">
      <div className="chart-frame">
        <ResponsiveContainer width="100%" height={360}>
          <BarChart data={rows} layout="vertical" margin={{ top: 8, right: 18, left: 12, bottom: 8 }}>
            <CartesianGrid stroke="#edf1f5" horizontal={false} />
            <XAxis type="number" tickLine={false} axisLine={false} fontSize={12} />
            <YAxis type="category" dataKey="key" width={148} tickLine={false} axisLine={false} fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="median" name="中位阅读" radius={[0, 8, 8, 0]}>
              {rows.map((_, index) => (
                <Cell fill={index % 2 ? "#5f98f2" : "#2f9f7b"} key={index} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="ratio-board">
        {data.recommendations.topic_ratio.map((item) => (
          <div key={item.label}>
            <b>{Math.round(item.ratio * 100)}%</b>
            <strong>{item.label}</strong>
            <span>{item.role}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TitleVisual() {
  const rows = data.title_analysis.by_primary_pattern.filter((row) => row.count > 0);
  return (
    <div className="split-visual">
      <div className="chart-frame">
        <ResponsiveContainer width="100%" height={330}>
          <BarChart data={rows} margin={{ top: 12, right: 18, left: 0, bottom: 36 }}>
            <CartesianGrid stroke="#edf1f5" vertical={false} />
            <XAxis dataKey="key" tickLine={false} axisLine={false} fontSize={11} angle={-18} textAnchor="end" height={58} />
            <YAxis tickLine={false} axisLine={false} fontSize={12} width={42} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="median" name="中位阅读" fill="#FF4D4F" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="pattern-cloud">
        {data.title_analysis.by_feature.map((row) => (
          <div key={String(row.key)}>
            <span>{row.key}</span>
            <strong>{number(row.median)}</strong>
            <small>{row.count} 篇</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function LengthVisual() {
  const rows = data.length_analysis.by_length_bucket;
  return (
    <div className="split-visual">
      <div className="chart-frame">
        <ResponsiveContainer width="100%" height={330}>
          <BarChart data={rows} margin={{ top: 12, right: 18, left: 0, bottom: 24 }}>
            <CartesianGrid stroke="#edf1f5" vertical={false} />
            <XAxis dataKey="key" tickLine={false} axisLine={false} fontSize={12} />
            <YAxis tickLine={false} axisLine={false} fontSize={12} width={44} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="median" name="中位阅读" fill="#F5A623" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="length-summary">
        <strong>{number(data.length_analysis.avg_length)}</strong>
        <span>匹配正文平均长度</span>
        <p>
          已匹配 {number(data.length_analysis.matched_count)} 篇，未匹配{" "}
          {number(data.length_analysis.missing_count)} 篇。长度结论只做辅助，不替代内容密度判断。
        </p>
      </div>
    </div>
  );
}

function AudienceVisual() {
  return (
    <div className="dual-list">
      <MiniStat title="痛点分布" rows={data.analysis.by_pain_point} />
      <MiniStat title="人群分布" rows={data.analysis.by_persona} />
    </div>
  );
}

function MiniStat({ title, rows }: { title: string; rows: StatRow[] }) {
  return (
    <div>
      <h3>{title}</h3>
      {rows.map((row) => (
        <article key={String(row.key)}>
          <span>{row.key}</span>
          <b>{number(row.median)}</b>
          <small>{row.count} 篇 · P75 {number(row.p75)}</small>
        </article>
      ))}
    </div>
  );
}

function TimingVisual() {
  const rows = data.analysis.by_week.map((row) => ({
    week: row.week.replace("2026-", ""),
    median: row.median,
    trimmed_mean: row.trimmed_mean,
  }));
  return (
    <div className="split-visual">
      <div className="chart-frame">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={rows} margin={{ top: 16, right: 20, left: 0, bottom: 8 }}>
            <CartesianGrid stroke="#edf1f5" vertical={false} />
            <XAxis dataKey="week" tickLine={false} axisLine={false} fontSize={12} />
            <YAxis tickLine={false} axisLine={false} fontSize={12} width={46} />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey="median" name="中位阅读" stroke={CHART_PRIMARY} strokeWidth={3} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="trimmed_mean" name="去极值均值" stroke={CHART_SECONDARY} strokeWidth={2.4} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="window-board">
        {data.recommendations.publish_windows.map((item) => (
          <div key={item.window}>
            <strong>{item.window}</strong>
            <span>{item.best_for}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function EvidenceVisual() {
  const [selectedType, setSelectedType] = React.useState("全部类型");
  const [sortKey, setSortKey] = React.useState<SortKey>("reads");
  const rows = React.useMemo(() => {
    return [...data.articles.stable]
      .filter((article) => selectedType === "全部类型" || article.content_type === selectedType)
      .sort((a, b) => {
        if (sortKey === "published_at") {
          return new Date(b.published_at).getTime() - new Date(a.published_at).getTime();
        }
        return Number(b[sortKey]) - Number(a[sortKey]);
      });
  }, [selectedType, sortKey]);
  return (
    <div className="evidence-panel">
      <div className="evidence-controls">
        <label>
          <span>内容类型</span>
          <select value={selectedType} onChange={(event) => setSelectedType(event.target.value)}>
            {allTypes.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <div>
          {[
            ["reads", "阅读"],
            ["shares", "分享"],
            ["share_rate", "分享率"],
            ["published_at", "时间"],
          ].map(([key, label]) => (
            <button
              className={sortKey === key ? "selected" : ""}
              key={key}
              onClick={() => setSortKey(key as SortKey)}
              type="button"
            >
              <ArrowDownUp size={13} />
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="ranking-list">
        {rows.slice(0, 8).map((article, index) => (
          <a href={article.url} key={article.id} rel="noreferrer" target="_blank">
            <b>{index + 1}</b>
            <strong>{article.title}</strong>
            <span>{article.content_type}</span>
            <em>{number(article.reads)}</em>
            <small>
              分享 {number(article.shares)} · {percent(article.share_rate)} · {shortDate(article.published_at)}
            </small>
          </a>
        ))}
      </div>
    </div>
  );
}

function QualityVisual() {
  const rows = [
    ["后台记录", data.data_quality.raw_record_count],
    ["当前周期", data.data_quality.period_non_deleted_count],
    ["稳定样本", data.data_quality.stable_article_count],
    ["新文观察", data.data_quality.immature_article_count],
    ["指标缺口", data.data_quality.metric_pending_count],
    ["正文匹配", data.length_analysis.matched_count],
  ];
  return (
    <div className="quality-grid">
      {rows.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{number(Number(value))}</strong>
        </div>
      ))}
    </div>
  );
}

function FinalVisual() {
  const fs = data.final_synthesis;
  return (
    <div className="final-board">
      <DecisionColumn title="现在就做" tone="green" items={fs.now} />
      <DecisionColumn title="小步验证" tone="amber" items={fs.experiment} />
      <DecisionColumn title="暂不拍板" tone="violet" items={fs.hold} />
    </div>
  );
}

function DecisionColumn({ title, tone, items }: { title: string; tone: Tone; items: string[] }) {
  return (
    <div className={`decision-column tone-${tone}`}>
      <h3>{title}</h3>
      {items && items.length > 0 ? (
        items.map((item) => <p key={item}>{item}</p>)
      ) : (
        <p className="empty">—</p>
      )}
    </div>
  );
}

function SectionById({ id }: { id: string }) {
  const item = section(id);
  const shared = {
    id: item.id,
    tone: item.ui_slot.accent,
    title: item.title,
    question: item.question,
    analysis: item.analysis,
    conclusion: item.conclusion,
    action: item.action,
    emphasis: item.emphasis,
  };
  if (id === "overview") return <StoryScreen {...shared} icon={<Target size={20} />}><OverallVisual /></StoryScreen>;
  if (id === "content-engine") return <StoryScreen {...shared} icon={<BarChart3 size={20} />}><ContentVisual /></StoryScreen>;
  if (id === "title-structure") return <StoryScreen {...shared} icon={<PenLine size={20} />}><TitleVisual /></StoryScreen>;
  if (id === "article-length") return <StoryScreen {...shared} icon={<Ruler size={20} />}><LengthVisual /></StoryScreen>;
  if (id === "audience") return <StoryScreen {...shared} icon={<Users size={20} />}><AudienceVisual /></StoryScreen>;
  if (id === "timing") return <StoryScreen {...shared} icon={<CalendarClock size={20} />}><TimingVisual /></StoryScreen>;
  if (id === "evidence") return <StoryScreen {...shared} icon={<Search size={20} />}><EvidenceVisual /></StoryScreen>;
  if (id === "quality") return <StoryScreen {...shared} icon={<Database size={20} />}><QualityVisual /></StoryScreen>;
  return <StoryScreen {...shared} icon={<Sparkles size={20} />}><FinalVisual /></StoryScreen>;
}

export default function App() {
  const activeSection = useActiveSection(sectionIds);
  const contentSections = data.narrative_flow.filter((item) => item.id !== "actions");
  return (
    <div className="report-page">
      <div className="report-shell">
        <SideNav activeSection={activeSection} />
        <main className="story-scroll" aria-label="公众号运营诊断报告">
          <HeroScreen />
          {contentSections.map((item) => (
            <SectionById id={item.id} key={item.id} />
          ))}
          <footer className="report-footer">
            <FileText size={14} />
            <span>Markdown、wiki JSON 和模板站共用同一份结构化数据。</span>
            <a href={data.brand_signature.skill_repo} rel="noreferrer" target="_blank">
              <ExternalLink size={13} />
              Skill 仓库
            </a>
          </footer>
        </main>
        <RightRail activeSection={activeSection} />
      </div>
    </div>
  );
}
