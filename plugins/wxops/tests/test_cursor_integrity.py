# GEB-L3
# Input: WXOPS_HOME=tmp_path + --workspace 反查 / desk 产物兜底 / 登录判定四级
# Output: resolve_context slug 回填 + analyze 游标写入 + desk 建议与 ~ 图例；零真实账号/浏览器
# Pos: plugins/wxops/tests/test_cursor_integrity.py
"""issue #62 游标完整性：--workspace 反查 slug + desk 产物兜底 + 登录建议四级化。

全部用 WXOPS_HOME=tmp_path 隔离，绝不碰真实 ~/.wxops。
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import desk_cmd  # noqa: E402
from scripts.cli import main as main_mod  # noqa: E402


def _set_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    root = tmp_path / "wxops-home"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("WXOPS_HOME", str(root))
    return root.resolve()


def test_workspace_hits_registered_account(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    accounts_store.create_account(root, "health", "健康")
    ws = root / "accounts" / "health"
    args = main_mod.build_parser().parse_args(
        ["analyze", "--demo", "--workspace", str(ws)]
    )
    workspace, slug = main_mod.resolve_context(args)
    assert slug == "health"
    assert workspace == ws.resolve()


def test_workspace_outside_registry_still_none(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_home(monkeypatch, tmp_path)
    elsewhere = tmp_path / "somewhere-else"
    elsewhere.mkdir()
    args = main_mod.build_parser().parse_args(
        ["analyze", "--demo", "--workspace", str(elsewhere)]
    )
    workspace, slug = main_mod.resolve_context(args)
    assert slug is None
    assert workspace == elsewhere.resolve()
    out = capsys.readouterr().out
    assert "不会更新任何账号游标" in out


def test_workspace_trailing_slash_and_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    accounts_store.create_account(root, "linkme", "软链号")
    real = accounts_store.get_account_dir(root, "linkme")
    link = tmp_path / "linkme-symlink"
    link.symlink_to(real)
    args = main_mod.build_parser().parse_args(
        ["analyze", "--demo", "--workspace", str(link)]
    )
    workspace, slug = main_mod.resolve_context(args)
    assert slug == "linkme"
    assert workspace == link.resolve()


def test_analyze_via_workspace_writes_cursor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    rc = main_mod.main(["accounts", "add", "w", "--name", "W"])
    assert rc == 0
    ws = root / "accounts" / "w"
    rc = main_mod.main(
        ["analyze", "--demo", "--data-only", "--workspace", str(ws)]
    )
    assert rc == 0
    pipe = accounts_store.load_pipeline(root, "w")
    assert pipe["stations"]["analyze"]["at"] is not None
    assert pipe["stations"]["analyze"]["report"]
    assert "report.json" in pipe["stations"]["analyze"]["report"]
    acct = accounts_store.get_account(root, "w")
    assert acct is not None
    assert acct["last_analyze_at"] is not None


def test_desk_alive_fresh_yields_inflight_suggestion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    accounts_store.create_account(root, "busy", "有稿号")
    accounts_store.set_login_health(root, "busy", True)
    acct_dir = accounts_store.get_account_dir(root, "busy")
    (acct_dir / "topics" / "t1").mkdir(parents=True)
    (acct_dir / "topics" / "t1" / "card.md").write_text("c", encoding="utf-8")
    (acct_dir / "drafts" / "d1").mkdir(parents=True)
    (acct_dir / "drafts" / "d1" / "draft.md").write_text("d", encoding="utf-8")

    rc = desk_cmd.run(root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "稿件在途" in out
    assert "wxops login --account busy" not in out


def test_desk_alive_stale_check_suggests_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    accounts_store.create_account(root, "stale", "过期在线")
    when = (datetime.now().astimezone() - timedelta(days=10)).isoformat(
        timespec="seconds"
    )
    accounts_store.set_login_health(root, "stale", True, when=when)

    rc = desk_cmd.run(root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "accounts check stale" in out
    assert "login --account stale" not in out


def test_desk_infers_from_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    accounts_store.create_account(root, "infer", "推断号")
    accounts_store.set_login_health(root, "infer", True)
    acct_dir = accounts_store.get_account_dir(root, "infer")
    (acct_dir / "output").mkdir(parents=True, exist_ok=True)
    (acct_dir / "output" / "report.json").write_text("{}", encoding="utf-8")
    (acct_dir / "raw").mkdir(parents=True, exist_ok=True)
    (acct_dir / "raw" / "x.json").write_text("{}", encoding="utf-8")

    rc = desk_cmd.run(root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "~" in out
    assert "据产物文件推断" in out


def test_desk_never_probed_still_suggests_login(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    accounts_store.create_account(root, "fresh", "新号")

    rc = desk_cmd.run(root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "wxops login --account fresh" in out
    assert "(● = 当前账号)" in out
    assert "据产物文件推断" not in out
