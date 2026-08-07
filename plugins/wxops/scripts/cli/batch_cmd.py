#!/usr/bin/env python3
# GEB-L3
# Input: wxops root、可选 checker/runner/sleeper/间隔；active 账号列表
# Output: 逐号顺序 analyze --all 批次；runs/analyze-all-*.json + 终端汇总；退出码
# Pos: plugins/wxops/scripts/cli/batch_cmd.py
"""analyze --all 批量编排：前置体检 + 顺序拉数 + 防风控间隔 + 失败隔离 + 批次报告。"""

from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Any, Callable

from . import accounts_store
from . import analyze_cmd
from . import env
from . import health
from . import lock as lock_mod


def _oneline(msg: str) -> str:
    """多行错误信息压成首行（lock 报错首行自带 PID，压缩零信息损失）。"""
    lines = (msg or "").strip().splitlines()
    return lines[0] if lines else ""


def _default_runner(root: Path, slug: str, workspace: Path) -> int:
    """单号分析：持锁 → analyze data_only → 成功时写游标（与 main 单号 analyze 收尾一致）。"""
    profile_lock = lock_mod.acquire_profile_lock(workspace)
    try:
        acct = accounts_store.get_account(root, slug)
        niche = "ai-tools"
        if acct and acct.get("niche"):
            niche = str(acct["niche"])
        # 不注入注册表人工名：由 analyze_cmd 按「显式 override > 后台真名 > config」决定（issue #83）
        rc = analyze_cmd.run(
            workspace=workspace,
            demo=False,
            build_only=False,
            account_name_override=None,
            data_only=True,
            niche=niche,
        )
    finally:
        profile_lock.release()

    if rc == 0:
        accounts_store.touch(root, slug, "last_fetch_at")
        ok_fetch = accounts_store.touch_pipeline(root, slug, "fetch", ok=True)
        if not ok_fetch:
            env.print_warn("pipeline.json fetch 游标写入失败（不影响本次分析）")
        accounts_store.touch(root, slug, "last_analyze_at")
        report_path = str(workspace / "output" / "report.json")
        ok_an = accounts_store.touch_pipeline(
            root, slug, "analyze", ok=True, report=report_path
        )
        if not ok_an:
            env.print_warn("pipeline.json analyze 游标写入失败（不影响本次分析）")
    return rc


def _rel_to_root(root: Path, path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    try:
        return str(p.resolve().relative_to(root.resolve()))
    except Exception:
        return str(p)


def run_all(
    root: Path,
    *,
    checker: Callable[[Path], dict[str, Any]] | None = None,
    runner: Callable[[Path, str, Path], int] | None = None,
    sleeper: Callable[[float], None] | None = None,
    interval_range: tuple[float, float] = (30.0, 90.0),
) -> int:
    """全部 active 账号顺序批量拉数出报告。"""
    check_fn = checker or health.check_login
    run_fn = runner or _default_runner
    sleep_fn = sleeper or time.sleep

    accounts = [
        a
        for a in accounts_store.list_accounts(root)
        if a.get("status") == "active"
    ]
    accounts.sort(key=lambda a: str(a.get("slug", "")))
    if not accounts:
        env.print_warn("还没有任何账号。")
        env.print_guide_next('wxops accounts add <slug> --name "<显示名>"')
        return 1

    started_at = accounts_store.now_iso()
    results: list[dict[str, Any]] = []

    env.print_header("批量分析（analyze --all）")

    for i, acct in enumerate(accounts):
        slug = str(acct.get("slug") or "")
        workspace = accounts_store.get_account_dir(root, slug)
        t0 = time.monotonic()
        entry: dict[str, Any] = {
            "slug": slug,
            "status": "skipped",
            "reason": None,
            "report": None,
            "duration_s": 0.0,
        }
        executed = False

        # 1. 前置体检
        try:
            health_result = check_fn(workspace)
        except lock_mod.ProfileLockError as e:
            entry["status"] = "skipped"
            entry["reason"] = _oneline(str(e))
            entry["duration_s"] = round(time.monotonic() - t0, 3)
            results.append(entry)
            continue

        if not health_result.get("alive"):
            err = health_result.get("error") or "登录态掉线"
            entry["status"] = "skipped"
            entry["reason"] = f"{err} → wxops login --account {slug}"
            entry["duration_s"] = round(
                float(health_result.get("duration_s") or 0.0), 3
            )
            results.append(entry)
            continue

        # 2. 活号执行
        try:
            rc = run_fn(root, slug, workspace)
            executed = True
            duration = round(time.monotonic() - t0, 3)
            if rc == 0:
                report = workspace / "output" / "report.json"
                entry["status"] = "ok"
                entry["reason"] = None
                entry["report"] = str(report)
                entry["duration_s"] = duration
            else:
                entry["status"] = "failed"
                entry["reason"] = f"分析失败（退出码 {rc}）"
                entry["duration_s"] = duration
        except Exception as e:
            executed = True
            entry["status"] = "failed"
            entry["reason"] = _oneline(str(e)) or e.__class__.__name__
            entry["duration_s"] = round(time.monotonic() - t0, 3)

        results.append(entry)

        # 3. 防风控间隔：本号真实拉数 且 后面还有待跑号
        if executed and i < len(accounts) - 1:
            lo, hi = interval_range
            delay = random.uniform(lo, hi)
            print(f"⏳ 防风控间隔 {int(delay)}s 后继续下一账号…")
            sleep_fn(delay)

    finished_at = accounts_store.now_iso()
    summary = {
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
    }

    # 批次报告
    report_path = env.new_run_manifest_path(root, "analyze-all")
    payload = {
        "version": 1,
        "kind": "analyze-all",
        "started_at": started_at,
        "finished_at": finished_at,
        "interval_range_s": [interval_range[0], interval_range[1]],
        "accounts": results,
        "summary": summary,
    }
    accounts_store.atomic_write_json(report_path, payload)

    # 终端汇总
    env.print_header("批次汇总")
    display_rows: list[tuple[str, str, str, str]] = []
    for r in results:
        slug = r["slug"]
        if r["status"] == "ok":
            icon = "✓"
            label = "报告已更新"
            detail = _rel_to_root(root, r.get("report")) or "—"
        elif r["status"] == "skipped":
            icon = "○"
            label = "已跳过"
            # 掉线跳过的 reason 记录时已含补登录命令；撞锁跳过的 reason
            # 是单行占用信息，不追加补登录提示（该等进程结束而非重扫码）
            detail = r.get("reason") or f"登录态掉线 → wxops login --account {slug}"
        else:
            icon = "✗"
            label = "拉取失败"
            detail = r.get("reason") or "未知错误"
        display_rows.append((icon, slug, label, detail))

    # 对齐：icon+slug 列、label 列、detail 列
    col1 = [f"{icon} {slug}" for icon, slug, _, _ in display_rows]
    col2 = [label for _, _, label, _ in display_rows]
    col3 = [detail for _, _, _, detail in display_rows]
    w1 = max((accounts_store.display_width(c) for c in col1), default=8)
    w2 = max((accounts_store.display_width(c) for c in col2), default=8)
    for c1, c2, c3 in zip(col1, col2, col3):
        print(
            f"{accounts_store.pad_display(c1, w1)}  "
            f"{accounts_store.pad_display(c2, w2)}  "
            f"{c3}"
        )

    rel_report = _rel_to_root(root, report_path) or str(report_path)
    print()
    print(
        f"{summary['ok']} 成功 · {summary['failed']} 失败 · {summary['skipped']} 跳过"
        f" · 批次报告：{rel_report}"
    )

    if summary["ok"] > 0 and summary["failed"] == 0:
        return 0
    return 1
