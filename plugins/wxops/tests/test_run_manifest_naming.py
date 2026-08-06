# GEB-L3
# Input: WXOPS_HOME=tmp_path + env.new_run_manifest_path / migrate_cmd.run / batch_cmd.run_all
# Output: issue #72 运行清单毫秒命名与撞名让路契约（目录创建/让路/-ms 精度/双 migrate 双 batch）
# Pos: plugins/wxops/tests/test_run_manifest_naming.py
"""Issue #72: 运行清单毫秒时间戳 + 撞名让路，绝不静默覆盖审计凭证。"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import batch_cmd  # noqa: E402
from scripts.cli import env  # noqa: E402
from scripts.cli import migrate_cmd  # noqa: E402

# <prefix>-YYYYMMDD-HHMMSS-mmm.json（prefix 可含短横线，如 analyze-all）
_MS_NAME = re.compile(r"^.+-\d{8}-\d{6}-\d{3}\.json$")


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
    (root / "raw").mkdir(parents=True, exist_ok=True)
    (root / "raw" / "account.json").write_text('{"id":1}\n', encoding="utf-8")


def test_new_run_manifest_path_creates_runs_dir(tmp_path: Path) -> None:
    root = tmp_path / "wxops"
    root.mkdir()
    assert not (root / "runs").exists()
    path = env.new_run_manifest_path(root, "migrate")
    assert (root / "runs").is_dir()
    assert path.parent == root / "runs"
    assert path.name.startswith("migrate-")
    assert path.suffix == ".json"


def test_new_run_manifest_path_gives_way_on_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "wxops"
    root.mkdir()
    fixed = datetime(2026, 8, 6, 19, 42, 8, 123000)

    class _FrozenDateTime:
        @classmethod
        def now(cls, *args, **kwargs):  # noqa: ARG003
            return fixed

    monkeypatch.setattr(env, "datetime", _FrozenDateTime)

    first = env.new_run_manifest_path(root, "migrate")
    first.write_text("FIRST_MANIFEST\n", encoding="utf-8")
    assert first.name == "migrate-20260806-194208-123.json"

    second = env.new_run_manifest_path(root, "migrate")
    assert second != first
    assert second.name == "migrate-20260806-194208-123-2.json"
    assert first.read_text(encoding="utf-8") == "FIRST_MANIFEST\n"


def test_new_run_manifest_path_has_millisecond_precision(tmp_path: Path) -> None:
    root = tmp_path / "wxops"
    root.mkdir()
    a = env.new_run_manifest_path(root, "migrate")
    # 函数只解析路径不落盘；隔 2ms 保证毫秒位不同，避免同 ms 返回同一候选
    time.sleep(0.002)
    b = env.new_run_manifest_path(root, "migrate")
    assert a != b
    assert _MS_NAME.match(a.name), a.name
    assert _MS_NAME.match(b.name), b.name


def test_migrate_two_runs_same_second_keep_both_manifests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """同一秒内两次迁移，两份审计凭证都必须保留。

    冻结 env.datetime 为同秒不同毫秒，使旧实现（秒级 stamp）必然撞名，
    否则跨秒边界时门禁会沉默失效（测试绿但什么也没测到）。
    只 patch env.datetime；manifest 内 started_at/finished_at 仍走真实时钟。
    """
    root = _set_home(monkeypatch, tmp_path)
    _seed_legacy_minimal(root)

    stamps = iter(
        [
            datetime(2026, 8, 6, 19, 42, 8, 123000),
            datetime(2026, 8, 6, 19, 42, 8, 456000),
        ]
    )

    class _SeqDateTime:
        @classmethod
        def now(cls, *args, **kwargs):  # noqa: ARG003
            return next(stamps)

    monkeypatch.setattr(env, "datetime", _SeqDateTime)

    rc1 = migrate_cmd.run(root, slug="acct-a")
    assert rc1 == 0
    rc2 = migrate_cmd.run(root, slug="acct-b")
    assert rc2 == 0

    manifests = list((root / "runs").glob("migrate-*.json"))
    assert len(manifests) == 2
    names = sorted(p.name for p in manifests)
    assert names[0].endswith("-123.json"), names
    assert names[1].endswith("-456.json"), names
    slugs = {
        json.loads(p.read_text(encoding="utf-8"))["slug"] for p in manifests
    }
    assert slugs == {"acct-a", "acct-b"}


def test_batch_report_path_unique(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """同一秒内两次 batch，两份报告路径必须唯一（毫秒精度，不靠让路）。

    冻结 env.datetime 为同秒不同毫秒，文件名完全确定；旧实现秒级 stamp
    会撞名并覆盖，本门禁必红。
    """
    root = _set_home(monkeypatch, tmp_path)
    accounts_store.create_account(root, "a", "A")

    def alive(_workspace: Path) -> dict:
        return {"alive": True, "error": None, "duration_s": 0.01}

    def ok_runner(_root: Path, _slug: str, _workspace: Path) -> int:
        return 0

    stamps = iter(
        [
            datetime(2026, 8, 6, 19, 42, 8, 111000),
            datetime(2026, 8, 6, 19, 42, 8, 222000),
        ]
    )

    class _SeqDateTime:
        @classmethod
        def now(cls, *args, **kwargs):  # noqa: ARG003
            return next(stamps)

    monkeypatch.setattr(env, "datetime", _SeqDateTime)

    rc1 = batch_cmd.run_all(
        root,
        checker=alive,
        runner=ok_runner,
        sleeper=lambda _s: None,
        interval_range=(0.0, 0.0),
    )
    rc2 = batch_cmd.run_all(
        root,
        checker=alive,
        runner=ok_runner,
        sleeper=lambda _s: None,
        interval_range=(0.0, 0.0),
    )
    assert rc1 == 0
    assert rc2 == 0

    reports = list((root / "runs").glob("analyze-all-*.json"))
    assert len(reports) == 2
    names = sorted(p.name for p in reports)
    assert names == [
        "analyze-all-20260806-194208-111.json",
        "analyze-all-20260806-194208-222.json",
    ]
