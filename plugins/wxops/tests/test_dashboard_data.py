# GEB-L3
# Input: tmp_path 隔离的 WXOPS_HOME + 手工账号/report 夹具
# Output: _inject_accounts_data 多账号/legacy/清理/损坏容错 覆盖
# Pos: plugins/wxops/tests/test_dashboard_data.py
"""dashboard 多账号数据注入单测：零真实 ~/.wxops、不跑 pnpm/vite。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# conftest 只加了 scripts/；本文件需要插件根以便 from scripts.cli import ...
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import analyze_cmd  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_wxops_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """每测隔离：WXOPS_HOME=tmp，不碰真实 ~/.wxops。"""
    monkeypatch.setenv("WXOPS_HOME", str(tmp_path))


def _write_report(
    path: Path,
    *,
    account_name: str = "测试号",
    generated_at: str = "2026-07-30T18:00:00+08:00",
    article_count: int = 10,
    profile_name: str | None = None,
    account_obj_name: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "meta": {
            "account_name": account_name,
            "generated_at": generated_at,
        },
        "account": {"name": account_obj_name or account_name},
        "account_profile": {"name": profile_name or account_name},
        "data_quality": {"stable_article_count": article_count},
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _setup_account(
    root: Path,
    slug: str,
    name: str,
    *,
    status: str = "active",
    with_report: bool = True,
    article_count: int = 10,
    generated_at: str = "2026-07-30T18:00:00+08:00",
) -> Path:
    """手写 account.json + 可选 report.json，返回账号目录。"""
    acct_dir = root / "accounts" / slug
    acct_dir.mkdir(parents=True, exist_ok=True)
    account = {
        "slug": slug,
        "name": name,
        "status": status,
        "niche": "ai-tools",
    }
    (acct_dir / "account.json").write_text(
        json.dumps(account, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if with_report:
        _write_report(
            acct_dir / "output" / "report.json",
            account_name=name,
            article_count=article_count,
            generated_at=generated_at,
        )
    return acct_dir


def _load_accounts_index(dashboard_dir: Path) -> dict[str, Any]:
    path = dashboard_dir / "public" / "data" / "accounts.json"
    assert path.is_file(), f"missing accounts.json: {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_two_accounts_both_have_report(tmp_path: Path) -> None:
    """双账号都有 report → 两条目、两个 slug.json、current 正确、顺序稳定。"""
    root = tmp_path
    _setup_account(root, "alpha", "阿尔法", article_count=11)
    _setup_account(root, "beta", "贝塔", article_count=22)
    accounts_store.set_current(root, "beta")  # current 注册表；注入 current 用本次 slug

    workspace = accounts_store.get_account_dir(root, "beta")
    dashboard_dir = workspace / "dashboard"
    ok = analyze_cmd._inject_accounts_data(
        workspace, dashboard_dir, root=root, slug="beta"
    )
    assert ok is True

    index = _load_accounts_index(dashboard_dir)
    assert index["current"] == "beta"
    assert "generated_at" in index and isinstance(index["generated_at"], str)

    listed = accounts_store.list_accounts(root)
    listed_slugs = [a["slug"] for a in listed]
    out_slugs = [a["slug"] for a in index["accounts"]]
    assert out_slugs == listed_slugs
    assert out_slugs == ["alpha", "beta"]

    by_slug = {a["slug"]: a for a in index["accounts"]}
    assert by_slug["alpha"]["has_report"] is True
    assert by_slug["alpha"]["name"] == "阿尔法"
    assert by_slug["alpha"]["article_count"] == 11
    assert by_slug["alpha"]["generated_at"] == "2026-07-30T18:00:00+08:00"
    assert by_slug["beta"]["has_report"] is True
    assert by_slug["beta"]["article_count"] == 22

    data_dir = dashboard_dir / "public" / "data"
    assert (data_dir / "alpha.json").is_file()
    assert (data_dir / "beta.json").is_file()
    # 原样复制：内容可读
    alpha_report = json.loads((data_dir / "alpha.json").read_text(encoding="utf-8"))
    assert alpha_report["meta"]["account_name"] == "阿尔法"


def test_one_account_missing_report(tmp_path: Path) -> None:
    """一个有 report、一个没有 → 后者 has_report false 且不生成 json。"""
    root = tmp_path
    _setup_account(root, "alpha", "阿尔法", with_report=True)
    _setup_account(root, "beta", "贝塔", with_report=False)

    workspace = accounts_store.get_account_dir(root, "alpha")
    dashboard_dir = workspace / "dashboard"
    ok = analyze_cmd._inject_accounts_data(
        workspace, dashboard_dir, root=root, slug="alpha"
    )
    assert ok is True

    index = _load_accounts_index(dashboard_dir)
    by_slug = {a["slug"]: a for a in index["accounts"]}
    assert by_slug["alpha"]["has_report"] is True
    assert by_slug["alpha"]["report_url"] == "data/alpha.json"
    assert by_slug["beta"]["has_report"] is False
    assert by_slug["beta"]["report_url"] is None
    assert by_slug["beta"]["generated_at"] is None
    assert by_slug["beta"]["article_count"] is None

    data_dir = dashboard_dir / "public" / "data"
    assert (data_dir / "alpha.json").is_file()
    assert not (data_dir / "beta.json").exists()


def test_retired_account_skipped(tmp_path: Path) -> None:
    """retired 账号完全跳过：不进 accounts 数组、不生成 json。"""
    root = tmp_path
    _setup_account(root, "alpha", "阿尔法", with_report=True)
    _setup_account(root, "gone", "已退号", status="retired", with_report=True)

    workspace = accounts_store.get_account_dir(root, "alpha")
    dashboard_dir = workspace / "dashboard"
    analyze_cmd._inject_accounts_data(
        workspace, dashboard_dir, root=root, slug="alpha"
    )

    index = _load_accounts_index(dashboard_dir)
    slugs = [a["slug"] for a in index["accounts"]]
    assert slugs == ["alpha"]
    assert "gone" not in slugs
    assert not (dashboard_dir / "public" / "data" / "gone.json").exists()


def test_legacy_mode_single_entry(tmp_path: Path) -> None:
    """legacy（slug=None）→ _legacy 单条目、name 优先 account_profile.name。"""
    workspace = tmp_path / "legacy-ws"
    dashboard_dir = workspace / "dashboard"
    _write_report(
        workspace / "output" / "report.json",
        account_name="meta名",
        profile_name="画像优先名",
        account_obj_name="account名",
        article_count=18,
        generated_at="2026-07-30T18:00:00+08:00",
    )

    ok = analyze_cmd._inject_accounts_data(
        workspace, dashboard_dir, root=None, slug=None
    )
    assert ok is True

    index = _load_accounts_index(dashboard_dir)
    assert index["current"] == "_legacy"
    assert len(index["accounts"]) == 1
    entry = index["accounts"][0]
    assert entry["slug"] == "_legacy"
    assert entry["name"] == "画像优先名"
    assert entry["has_report"] is True
    assert entry["report_url"] == "data/_legacy.json"
    assert entry["article_count"] == 18
    assert entry["generated_at"] == "2026-07-30T18:00:00+08:00"
    assert (dashboard_dir / "public" / "data" / "_legacy.json").is_file()


def test_legacy_missing_report_still_writes_index(tmp_path: Path) -> None:
    """legacy 无 report：accounts.json 仍生成，has_report false，name=本账号。"""
    workspace = tmp_path / "legacy-empty"
    dashboard_dir = workspace / "dashboard"
    ok = analyze_cmd._inject_accounts_data(
        workspace, dashboard_dir, root=None, slug=None
    )
    assert ok is False
    index = _load_accounts_index(dashboard_dir)
    assert index["current"] == "_legacy"
    entry = index["accounts"][0]
    assert entry["has_report"] is False
    assert entry["report_url"] is None
    assert entry["name"] == "本账号"
    assert not (dashboard_dir / "public" / "data" / "_legacy.json").exists()


def test_cleanup_only_json_files(tmp_path: Path) -> None:
    """注入前清 stale.json，保留 keep.txt。"""
    root = tmp_path
    _setup_account(root, "alpha", "阿尔法")
    workspace = accounts_store.get_account_dir(root, "alpha")
    data_dir = workspace / "dashboard" / "public" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "stale.json").write_text('{"old": true}\n', encoding="utf-8")
    (data_dir / "keep.txt").write_text("do-not-delete\n", encoding="utf-8")

    analyze_cmd._inject_accounts_data(
        workspace, workspace / "dashboard", root=root, slug="alpha"
    )

    assert not (data_dir / "stale.json").exists()
    assert (data_dir / "keep.txt").is_file()
    assert (data_dir / "keep.txt").read_text(encoding="utf-8") == "do-not-delete\n"
    assert (data_dir / "accounts.json").is_file()
    assert (data_dir / "alpha.json").is_file()


def test_corrupt_report_does_not_crash(tmp_path: Path) -> None:
    """report 非法 JSON → 不抛异常，该号 has_report false，其他号照常。"""
    root = tmp_path
    _setup_account(root, "alpha", "阿尔法", with_report=True)
    bad_dir = _setup_account(root, "broken", "坏号", with_report=False)
    (bad_dir / "output").mkdir(parents=True, exist_ok=True)
    (bad_dir / "output" / "report.json").write_text(
        "{not-valid-json", encoding="utf-8"
    )

    workspace = accounts_store.get_account_dir(root, "alpha")
    dashboard_dir = workspace / "dashboard"
    ok = analyze_cmd._inject_accounts_data(
        workspace, dashboard_dir, root=root, slug="alpha"
    )
    assert ok is True

    index = _load_accounts_index(dashboard_dir)
    by_slug = {a["slug"]: a for a in index["accounts"]}
    assert by_slug["alpha"]["has_report"] is True
    assert by_slug["broken"]["has_report"] is False
    assert by_slug["broken"]["report_url"] is None
    assert (dashboard_dir / "public" / "data" / "alpha.json").is_file()
    assert not (dashboard_dir / "public" / "data" / "broken.json").exists()


def test_report_url_relative_no_leading_slash(tmp_path: Path) -> None:
    """report_url 为不带前导斜杠的相对路径 data/<slug>.json。"""
    root = tmp_path
    _setup_account(root, "maizong", "麦总玩AI")
    workspace = accounts_store.get_account_dir(root, "maizong")
    dashboard_dir = workspace / "dashboard"
    analyze_cmd._inject_accounts_data(
        workspace, dashboard_dir, root=root, slug="maizong"
    )

    index = _load_accounts_index(dashboard_dir)
    entry = index["accounts"][0]
    url = entry["report_url"]
    assert url is not None
    assert not url.startswith("/")
    assert url == "data/maizong.json"
