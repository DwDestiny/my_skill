# GEB-L3
# Input: WXOPS_HOME=tmp_path + 构造含 unhandled/excluded 的 legacy 源树 + capsys
# Output: issue #51 migrate 差集盘点契约（unhandled 报告/不搬/静默/工作区级排除/运行时 excluded/不变量/软链/常量互斥）
# Pos: plugins/wxops/tests/test_migrate_unhandled.py
"""Issue #51: migrate 清单外条目显式 unhandled，EXCLUDED_META 补全工作区级设施。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import migrate_cmd  # noqa: E402


def _set_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    root = tmp_path / "wxops-home"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("WXOPS_HOME", str(root))
    return root.resolve()


def _seed_legacy_minimal(root: Path) -> None:
    """最小可迁移源：config.json + raw，满足 present 非空。"""
    (root / "config.json").write_text(
        json.dumps({"account_name": "测试号"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / "raw").mkdir(parents=True)
    (root / "raw" / "account.json").write_text('{"id":1}\n', encoding="utf-8")


def _read_manifest(root: Path) -> dict:
    manifests = list((root / "runs").glob("migrate-*.json"))
    assert len(manifests) == 1, f"expected 1 manifest, got {len(manifests)}"
    return json.loads(manifests[0].read_text(encoding="utf-8"))


def test_unhandled_reports_unknown_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    _seed_legacy_minimal(root)

    notes = root / "my-notes"
    notes.mkdir()
    (notes / "a.txt").write_text("a\n", encoding="utf-8")
    (notes / "b.txt").write_text("b\n", encoding="utf-8")
    export = root / "export.csv"
    export_body = "col1,col2\n1,2\n"
    export.write_text(export_body, encoding="utf-8")

    rc = migrate_cmd.run(root, slug="default")
    assert rc == 0

    man = _read_manifest(root)
    by_name = {u["name"]: u for u in man["unhandled"]}
    assert set(by_name) >= {"my-notes", "export.csv"}
    assert by_name["my-notes"]["kind"] == "dir"
    assert by_name["my-notes"]["entries"] == 2
    assert by_name["export.csv"]["kind"] == "file"
    assert by_name["export.csv"]["bytes"] == export.stat().st_size


def test_unhandled_not_copied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    _seed_legacy_minimal(root)

    notes = root / "my-notes"
    notes.mkdir()
    (notes / "a.txt").write_text("a\n", encoding="utf-8")
    (notes / "b.txt").write_text("b\n", encoding="utf-8")
    (root / "export.csv").write_text("x\n", encoding="utf-8")

    rc = migrate_cmd.run(root, slug="default")
    assert rc == 0

    target = accounts_store.get_account_dir(root, "default")
    assert not (target / "my-notes").exists()
    assert not (target / "export.csv").exists()


def test_unhandled_empty_is_silent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    _seed_legacy_minimal(root)
    # 只放 MIGRATE_ITEMS 与 EXCLUDED_META 内的条目
    (root / "dashboard").mkdir()
    (root / "bin").mkdir()
    (root / "gateway.json").write_text("{}\n", encoding="utf-8")

    rc = migrate_cmd.run(root, slug="default")
    assert rc == 0

    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "未识别条目" not in combined

    man = _read_manifest(root)
    assert man["unhandled"] == []


def test_workspace_level_items_go_to_excluded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    _seed_legacy_minimal(root)

    (root / "bin").mkdir()
    (root / "venv").mkdir()
    (root / "niches").mkdir()
    (root / "content").mkdir()
    (root / "gateway.json").write_text(
        '{"bearer_token":"secret"}\n', encoding="utf-8"
    )

    rc = migrate_cmd.run(root, slug="default")
    assert rc == 0

    man = _read_manifest(root)
    excluded_by_name = {e["name"]: e for e in man["excluded"]}
    for name in ("bin", "venv", "niches", "content", "gateway.json"):
        assert name in excluded_by_name, f"{name} missing from excluded"
        assert "reason" in excluded_by_name[name]
        assert name not in {u["name"] for u in man["unhandled"]}

    target = accounts_store.get_account_dir(root, "default")
    for name in ("bin", "venv", "niches", "content", "gateway.json"):
        assert not (target / name).exists()


def test_excluded_is_runtime_not_static(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    _seed_legacy_minimal(root)
    # 故意不放 dashboard/；放一个实际存在的排除项
    (root / "bin").mkdir()
    (root / "bin" / "wxops").write_text("#!/bin/sh\n", encoding="utf-8")

    rc = migrate_cmd.run(root, slug="default")
    assert rc == 0

    man = _read_manifest(root)
    excluded_names = {e["name"] for e in man["excluded"]}
    assert "dashboard" not in excluded_names

    bin_entry = next(e for e in man["excluded"] if e["name"] == "bin")
    assert bin_entry["kind"] == "dir"
    assert "entries" in bin_entry
    assert bin_entry["entries"] == 1


def test_manifest_accounts_for_every_root_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """inventory ∪ excluded ∪ unhandled 恒等于「跑之前」源目录第一层全集。

    用跑前快照比对，而不是拿跑后目录减去 accounts / runs / accounts.json 这类
    黑名单：黑名单只在这些名字跑前不存在时成立——用户跑过一次 migrate 后再跑，
    runs/ 已存在会正常进 excluded，左边有它、右边却把它减掉，断言会假红。
    快照形式既更强（清单交代跑前全集），也不依赖「哪些名字是 migrate 自建的」
    这种会随实现漂移的知识。
    """
    root = _set_home(monkeypatch, tmp_path)
    _seed_legacy_minimal(root)

    # 搬运项已有 config.json + raw；再补排除项 + 未识别项
    (root / "dashboard").mkdir()
    (root / "bin").mkdir()
    (root / "gateway.json").write_text("{}\n", encoding="utf-8")
    notes = root / "my-notes"
    notes.mkdir()
    (notes / "x.txt").write_text("x\n", encoding="utf-8")
    (root / "export.csv").write_text("y\n", encoding="utf-8")

    before = {p.name for p in root.iterdir()}
    rc = migrate_cmd.run(root, slug="default")
    assert rc == 0

    man = _read_manifest(root)
    accounted = (
        {i["name"] for i in man["inventory"]}
        | {e["name"] for e in man["excluded"]}
        | {u["name"] for u in man["unhandled"]}
    )
    assert accounted == before


def test_symlink_not_dereferenced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _set_home(monkeypatch, tmp_path)
    _seed_legacy_minimal(root)
    (root / "loop").symlink_to(root)

    rc = migrate_cmd.run(root, slug="default")
    assert rc == 0

    man = _read_manifest(root)
    loop = next(u for u in man["unhandled"] if u["name"] == "loop")
    assert loop["kind"] == "symlink"
    assert "entries" not in loop
    assert "bytes" not in loop


def test_migrate_items_and_excluded_never_overlap() -> None:
    migrate_names = {n for n, _ in migrate_cmd.MIGRATE_ITEMS}
    excluded_names = {e["name"] for e in migrate_cmd.EXCLUDED_META}
    assert migrate_names & excluded_names == set()
