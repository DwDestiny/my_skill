#!/usr/bin/env python3
# GEB-L3
# Input: wxops root；只读 accounts/pipeline 与 topics/*/card.md、drafts/*/draft.md 在途计数
# Output: 终端六列表格（登录/数据/报告/在途/下一步建议）；零写盘；exit 0
# Pos: plugins/wxops/scripts/cli/desk_cmd.py
"""desk 编辑部总控台：只读展示各账号流水线状态、在途内容与下一步建议。"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from . import accounts_store
from . import env

# login_alive 真探测结论的可信窗口：超过则不再当在线用，建议复检而非重扫码
_LOGIN_CHECK_FRESH_DAYS = 3


def _parse_ts(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        text = str(iso).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            return dt.astimezone()
        return dt.astimezone()
    except Exception:
        return None


def _is_stale(iso: str | None, days: int = 7) -> bool:
    dt = _parse_ts(iso)
    if dt is None:
        return True
    return datetime.now().astimezone() - dt > timedelta(days=days)


def _mtime_iso(path: Path) -> str | None:
    """文件/目录 mtime → ISO 字符串；不存在或读失败返回 None。只读。"""
    try:
        if not path.exists():
            return None
        ts = path.stat().st_mtime
    except Exception:
        return None
    return datetime.fromtimestamp(ts).astimezone().replace(microsecond=0).isoformat()


def _latest_raw_mtime(acct_dir: Path) -> str | None:
    """raw/ 下最新普通文件的 mtime（不递归子目录）。只读；无文件返回 None。"""
    raw = acct_dir / "raw"
    best: float | None = None
    try:
        if not raw.is_dir():
            return None
        for p in raw.iterdir():
            if not p.is_file():
                continue
            try:
                m = p.stat().st_mtime
            except Exception:
                continue
            if best is None or m > best:
                best = m
    except Exception:
        return None
    if best is None:
        return None
    return datetime.fromtimestamp(best).astimezone().replace(microsecond=0).isoformat()


def _col_login(account: dict[str, Any], pipe: dict[str, Any]) -> str:
    # 优先引用 accounts check 真探测结果
    if account.get("login_alive") is True:
        return "● 在线"
    if account.get("login_alive") is False:
        return "○ 掉线"
    ts = None
    login_st = (pipe.get("stations") or {}).get("login") or {}
    if login_st.get("at"):
        ts = login_st.get("at")
    elif account.get("last_login_at"):
        ts = account.get("last_login_at")
    if not ts:
        return "从未登录"
    return accounts_store.humanize_ts(str(ts))


def _col_data(
    account: dict[str, Any], pipe: dict[str, Any], acct_dir: Path
) -> tuple[str, bool]:
    ts = None
    fetch_st = (pipe.get("stations") or {}).get("fetch") or {}
    if fetch_st.get("at"):
        ts = fetch_st.get("at")
    elif account.get("last_fetch_at"):
        ts = account.get("last_fetch_at")
    if ts:
        return accounts_store.humanize_ts(str(ts)), False
    inferred = _latest_raw_mtime(acct_dir)
    if inferred:
        return "~" + accounts_store.humanize_ts(inferred), True
    return "—", False


def _col_report(
    account: dict[str, Any], pipe: dict[str, Any], acct_dir: Path
) -> tuple[str, bool]:
    ts = None
    analyze_st = (pipe.get("stations") or {}).get("analyze") or {}
    if analyze_st.get("at"):
        ts = analyze_st.get("at")
    elif account.get("last_analyze_at"):
        ts = account.get("last_analyze_at")
    if ts:
        return accounts_store.humanize_ts(str(ts)), False
    inferred = _mtime_iso(acct_dir / "output" / "report.json")
    if inferred:
        return "~" + accounts_store.humanize_ts(inferred), True
    return "—", False


def _count_in_flight(root: Path, slug: str) -> tuple[int, int]:
    """扫 topics/*/card.md 与 drafts/*/draft.md 个数。只读。"""
    try:
        acct_dir = accounts_store.get_account_dir(root, slug)
    except ValueError:
        return 0, 0
    n = len(list(acct_dir.glob("topics/*/card.md")))
    m = len(list(acct_dir.glob("drafts/*/draft.md")))
    return n, m


def _col_in_flight(n: int, m: int) -> str:
    if n == 0 and m == 0:
        return "—"
    return f"{n} 题 {m} 稿"


def _suggest_next(
    account: dict[str, Any],
    pipe: dict[str, Any],
    acct_dir: Path,
    n_topics: int = 0,
    m_drafts: int = 0,
) -> str:
    slug = str(account.get("slug") or "")
    if account.get("status") == "retired":
        return "(已退休)"

    # 真探测掉线：最高优先（retired 之后）
    if account.get("login_alive") is False:
        return f"wxops login --account {slug}"

    alive = account.get("login_alive") is True
    if alive:
        # 探测结论过期：去复检，不是去重扫码（重扫码在「已在线」这行是自相矛盾的）
        if _is_stale(account.get("last_check_at"), days=_LOGIN_CHECK_FRESH_DAYS):
            return f"wxops accounts check {slug}"
        # 在线且新鲜：登录不再是瓶颈，落到在途/数据分支
    else:
        # 从未探测过：回落游标 / account.json 时间戳
        last_login = account.get("last_login_at")
        login_st = (pipe.get("stations") or {}).get("login") or {}
        if login_st.get("at"):
            last_login = login_st.get("at") or last_login
        if not last_login:
            return f"wxops login --account {slug}"

    last_fetch = account.get("last_fetch_at")
    fetch_st = (pipe.get("stations") or {}).get("fetch") or {}
    if fetch_st.get("at"):
        last_fetch = fetch_st.get("at") or last_fetch
    if not last_fetch:
        last_fetch = _latest_raw_mtime(acct_dir)

    # 在途内容优先于数据陈旧建议
    if m_drafts > 0:
        return "稿件在途：/wxops:write 终审或 /wxops:illustrate 配图"
    if n_topics > 0:
        return "/wxops:write 开工写稿"

    if last_fetch is None or _is_stale(str(last_fetch), days=7):
        return f"wxops analyze --account {slug}"
    return "数据尚新：/wxops:topics 选题"


def run(root: Path) -> int:
    """只读总控台。任何情况下不写文件。"""
    accounts = accounts_store.list_accounts(root)
    env.print_header("wxops 编辑部总控台")

    if not accounts:
        env.print_warn("还没有任何账号。")
        env.print_guide_next('wxops accounts add <slug> --name "<显示名>"')
        if accounts_store.has_legacy_layout(root):
            env.print_info("检测到旧版单账号数据，可运行：wxops migrate")
        return 0

    current = accounts_store.get_current_slug(root)

    # 活跃在前、retired 末尾；同组按 slug
    active = [a for a in accounts if a.get("status") != "retired"]
    retired = [a for a in accounts if a.get("status") == "retired"]
    active.sort(key=lambda a: str(a.get("slug", "")))
    retired.sort(key=lambda a: str(a.get("slug", "")))
    ordered = active + retired

    headers = ["账号", "登录", "数据", "报告", "在途", "下一步"]
    rows: list[list[str]] = []
    any_inferred = False
    for acct in ordered:
        slug = str(acct.get("slug") or "")
        pipe = accounts_store.load_pipeline(root, slug)
        n_topics, m_drafts = _count_in_flight(root, slug)
        try:
            acct_dir = accounts_store.get_account_dir(root, slug)
        except ValueError:
            acct_dir = root / "accounts" / slug
        mark = "●" if slug == current and acct.get("status") != "retired" else "○"
        # retired 即使是 current 也用 ○（规格：行首用 ○）
        if acct.get("status") == "retired":
            mark = "○"
        data_col, data_inf = _col_data(acct, pipe, acct_dir)
        report_col, report_inf = _col_report(acct, pipe, acct_dir)
        if data_inf or report_inf:
            any_inferred = True
        rows.append(
            [
                f"{mark} {slug}",
                _col_login(acct, pipe),
                data_col,
                report_col,
                _col_in_flight(n_topics, m_drafts),
                _suggest_next(acct, pipe, acct_dir, n_topics, m_drafts),
            ]
        )

    widths = [accounts_store.display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], accounts_store.display_width(cell))

    def fmt_row(cols: list[str]) -> str:
        return "  ".join(
            accounts_store.pad_display(c, widths[i]) for i, c in enumerate(cols)
        )

    print(fmt_row(headers))
    for row in rows:
        print(fmt_row(row))
    print(
        "(● = 当前账号)"
        if not any_inferred
        else "(● = 当前账号；~ = 据产物文件推断，游标未写)"
    )
    return 0
