#!/usr/bin/env python3
# GEB-L3
# Input: wxops root、account slug、--title、可选 --object/--json；读 accounts/<slug>/output/wechat-ops-report-*.json
# Output: 选题去重闸终端/JSON（含 object_checked）；无 --object 时只做标题相似度并告警；exit 0=PASS/WARN，1=BLOCK，2=用法/缺库
# Pos: plugins/wxops/scripts/cli/dedup_cmd.py
"""dedup 选题去重闸：bigram Jaccard 标题相似度；核心对象查重依赖 --object，不传则只做相似度并显式告警。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from . import accounts_store
from . import env

Verdict = Literal["PASS", "WARN", "BLOCK"]

# 归一化时剥离的标点（任务书字面集合 + 常见变体）
_PUNCT_CHARS = (
    "｜|·—–-—～~！!？?。，,、：:；;"
    "\"'“”‘’「」『』（）()【】[]…《》#"
    "\u3000"  # 全角空格会在 isspace 里清，这里冗余无妨
)
_PUNCT_TABLE = str.maketrans({c: "" for c in _PUNCT_CHARS})


@dataclass
class LibraryArticle:
    title: str
    digest: str
    url: str
    date_str: str
    date_obj: date | None
    reads: int


@dataclass
class Match:
    title: str
    date: str
    url: str
    reads: int
    sim: float
    reason: Literal["similar", "object"]


def normalize_title(s: str) -> str:
    """比较前归一化：去空白、全角→半角、去标点、保留数字。"""
    if not s:
        return ""
    # 全角 ASCII → 半角
    chars: list[str] = []
    for ch in s:
        code = ord(ch)
        if code == 0x3000:
            continue  # 全角空格
        if 0xFF01 <= code <= 0xFF5E:
            chars.append(chr(code - 0xFEE0))
        else:
            chars.append(ch)
    t = "".join(chars)
    t = t.translate(_PUNCT_TABLE)
    t = "".join(ch for ch in t if not ch.isspace())
    return t


def bigrams(s: str) -> set[str]:
    if len(s) < 2:
        return set(s) if s else set()
    return {s[i : i + 2] for i in range(len(s) - 1)}


def jaccard_sim(a: str, b: str) -> float:
    na, nb = normalize_title(a), normalize_title(b)
    A, B = bigrams(na), bigrams(nb)
    if not A and not B:
        return 1.0 if na == nb else 0.0
    if not A or not B:
        return 0.0
    inter = len(A & B)
    union = len(A | B)
    if union == 0:
        return 0.0
    return inter / union


def _parse_date(raw: Any) -> tuple[str, date | None]:
    if raw is None:
        return "", None
    s = str(raw).strip()
    if not s:
        return "", None
    # 取前 10 位 YYYY-MM-DD
    head = s[:10]
    try:
        return head, date.fromisoformat(head)
    except ValueError:
        pass
    for fmt in ("%Y/%m/%d", "%Y.%m.%d", "%Y年%m月%d日"):
        try:
            d = datetime.strptime(s[:16], fmt).date()
            return d.isoformat(), d
        except ValueError:
            continue
    return s, None


def find_latest_report(output_dir: Path) -> Path | None:
    """取 wechat-ops-report-*.json 中 mtime 最新者；排除 .summary.。"""
    if not output_dir.is_dir():
        return None
    candidates: list[Path] = []
    for p in output_dir.iterdir():
        if not p.is_file():
            continue
        name = p.name
        if not name.startswith("wechat-ops-report-"):
            continue
        if not name.endswith(".json"):
            continue
        if ".summary." in name:
            continue
        candidates.append(p)
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0]


def load_stable_articles(report_path: Path) -> list[LibraryArticle]:
    """读 report JSON 的 articles.stable。结构不符抛 ValueError。"""
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"无法解析已发布库：{e}") from e
    if not isinstance(data, dict):
        raise ValueError("报告顶层必须为对象")
    articles = data.get("articles")
    if not isinstance(articles, dict):
        raise ValueError("articles 必须为对象（含 stable 等键），不是数组")
    stable = articles.get("stable")
    if not isinstance(stable, list):
        raise ValueError("articles.stable 必须为数组")
    out: list[LibraryArticle] = []
    for item in stable:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "")
        digest = str(item.get("digest") or "")
        url = str(item.get("url") or "")
        date_raw = item.get("published_at")
        if date_raw is None:
            date_raw = item.get("date")
        date_str, date_obj = _parse_date(date_raw)
        reads_raw = item.get("reads", 0)
        try:
            reads = int(reads_raw) if reads_raw is not None else 0
        except (TypeError, ValueError):
            reads = 0
        out.append(
            LibraryArticle(
                title=title,
                digest=digest,
                url=url,
                date_str=date_str,
                date_obj=date_obj,
                reads=reads,
            )
        )
    return out


def object_hits_article(obj: str, art: LibraryArticle) -> bool:
    if not obj:
        return False
    return obj in (art.title or "") or obj in (art.digest or "")


def evaluate(
    title: str,
    library: list[LibraryArticle],
    *,
    object_term: str | None = None,
    today: date | None = None,
    warn_days: int = 180,
) -> tuple[Verdict, list[Match], bool]:
    """三档判定。同时命中多篇时按 sim 最高排序，最多返回 5 条。

    返回 (verdict, matches, object_checked)。
    object_checked 为 True 仅当调用方显式传入非空 object_term；
    未传时不做任何对象回落匹配，只走标题相似度。
    """
    today = today or date.today()
    cutoff = today - timedelta(days=warn_days)
    obj = (object_term or "").strip() or None
    object_checked = obj is not None
    scored: list[Match] = []

    for art in library:
        if not art.title:
            continue
        sim = jaccard_sim(title, art.title)
        reason: Literal["similar", "object"] | None = None

        if sim >= 0.45:
            # BLOCK(≥0.75) 与 相似 WARN(≥0.45) 均走 similar；不限 180 天
            reason = "similar"
        elif obj is not None:
            # 仅当显式 --object 时做核心对象命中；+ 距今 < 180 天 → WARN（无日期不纳入）
            if (
                object_hits_article(obj, art)
                and art.date_obj is not None
                and art.date_obj >= cutoff
            ):
                reason = "object"

        if reason is None:
            continue

        scored.append(
            Match(
                title=art.title,
                date=art.date_str,
                url=art.url,
                reads=art.reads,
                sim=round(sim, 4),
                reason=reason,
            )
        )

    scored.sort(key=lambda m: m.sim, reverse=True)
    top = scored[:5]
    if not top:
        return "PASS", [], object_checked
    if any(m.sim >= 0.75 for m in top):
        return "BLOCK", top, object_checked
    return "WARN", top, object_checked


def _resolve_account(root: Path, account: str | None) -> tuple[str, dict[str, Any]] | int:
    slug_raw = (account or "").strip() or None
    if slug_raw is None:
        current = accounts_store.get_current_slug(root)
        if not current:
            env.print_error(
                "未指定账号，且没有当前账号。"
                "请先 wxops accounts add 或给 --account。"
            )
            return 2
        slug_raw = current
    try:
        slug = accounts_store.validate_slug(slug_raw)
    except ValueError as e:
        env.print_error(str(e))
        return 2
    acct = accounts_store.get_account(root, slug)
    if acct is None:
        env.print_error(f"账号不存在：{slug}")
        slugs = [str(a.get("slug", "")) for a in accounts_store.list_accounts(root)]
        if slugs:
            env.print_info("可用账号：" + "、".join(slugs))
        else:
            env.print_info("当前没有任何账号。")
        return 2
    return slug, acct


def _fmt_reads(n: int) -> str:
    return f"{n} 阅读"


_OBJECT_UNCHECKED_WARN = (
    "未提供 --object，本次只比对了标题相似度，没有做核心对象查重。\n"
    "  同一个对象换个说法写（如「隔夜菜」vs「剩菜」），这次不会拦住。\n"
    "  建议补 --object <核心对象> 重跑。"
)


def _print_human(
    *,
    niche: str,
    title: str,
    library_size: int,
    library_file: str,
    verdict: Verdict,
    matches: list[Match],
    object_checked: bool,
) -> None:
    env.print_header(f"选题去重闸：{niche} / 「{title}」")
    print(f"已发布库：{library_size} 篇（{library_file}）")
    print()
    if verdict == "BLOCK":
        print("BLOCK  标题撞车")
    elif verdict == "WARN":
        print("WARN  同对象近期写过" if any(m.reason == "object" for m in matches) else "WARN  标题过近")
    else:
        print("PASS  未见明显撞车")
    print()
    for m in matches:
        date_part = m.date or "日期未知"
        print(f"  相似 {m.sim:.2f}  {date_part}  {m.title}   {_fmt_reads(m.reads)}")
        if m.url:
            print(f"             {m.url}")
    print()
    if not object_checked:
        env.print_warn(_OBJECT_UNCHECKED_WARN)
    if verdict == "BLOCK":
        if matches:
            d = matches[0].date or "某日"
            print(f"结论：这篇几乎就是 {d} 那篇，别再写。")
        else:
            print("结论：与已发布标题高度撞车，别再写。")
    elif verdict == "WARN":
        print(
            "结论：可以写，但必须换切入角，并在文中标注上一篇的日期与链接。"
        )
    else:
        print("结论：可通过，未见明显重复选题。")


def run(
    root: Path,
    account: str | None = None,
    title: str | None = None,
    object_term: str | None = None,
    as_json: bool = False,
    today: date | None = None,
) -> int:
    resolved = _resolve_account(root, account)
    if isinstance(resolved, int):
        return resolved
    slug, acct = resolved
    niche_id = str(acct.get("niche") or "ai-tools")

    if not title or not str(title).strip():
        env.print_error("请用 --title 提供待查标题。")
        return 2
    title = str(title).strip()
    obj = (object_term or "").strip() or None

    acct_dir = accounts_store.get_account_dir(root, slug)
    output_dir = acct_dir / "output"
    report = find_latest_report(output_dir)
    if report is None:
        env.print_error(
            f"未找到已发布库（{output_dir}/wechat-ops-report-*.json）。"
            "请先跑 wxops analyze 产出报告。"
        )
        return 2
    try:
        library = load_stable_articles(report)
    except ValueError as e:
        env.print_error(str(e))
        env.print_info("请先跑 wxops analyze 产出结构正确的报告。")
        return 2

    verdict, matches, object_checked = evaluate(
        title, library, object_term=obj, today=today
    )
    lib_rel = f"output/{report.name}"

    if as_json:
        payload = {
            "verdict": verdict,
            "query": title,
            "object": obj,
            "object_checked": object_checked,
            "account": slug,
            "niche": niche_id,
            "library_size": len(library),
            "library_file": report.name,
            "matches": [
                {
                    "title": m.title,
                    "date": m.date,
                    "url": m.url,
                    "reads": m.reads,
                    "sim": m.sim,
                    "reason": m.reason,
                }
                for m in matches
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_human(
            niche=niche_id,
            title=title,
            library_size=len(library),
            library_file=lib_rel,
            verdict=verdict,
            matches=matches,
            object_checked=object_checked,
        )

    if verdict == "BLOCK":
        return 1
    return 0


def run_from_args(args: Any) -> int:
    if getattr(args, "workspace", None):
        root = Path(args.workspace).expanduser().resolve()
    else:
        root = env.get_wxops_root()
    return run(
        root,
        account=getattr(args, "account", None),
        title=getattr(args, "title", None),
        object_term=getattr(args, "object", None),
        as_json=bool(getattr(args, "json", False)),
    )
