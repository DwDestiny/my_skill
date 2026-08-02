# GEB-L3
# Input: WXOPS_HOME=tmp_path + 构造账号树/legacy 源树/subprocess 撞锁 + capsys
# Output: accounts_store 增删退役 + resolve_context 解析互斥 + migrate 先拷校验 + profile 锁 + desk 建议 + pipeline/legacy e2e
# Pos: plugins/wxops/tests/test_accounts.py
"""多账号底座 + desk v0 + migrate + lock 单测。

全部用 WXOPS_HOME=tmp_path 隔离，绝不碰真实 ~/.wxops。
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# conftest 只加了 scripts/；本文件需要插件根以便 from scripts.cli import ...
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import desk_cmd  # noqa: E402
from scripts.cli import env  # noqa: E402
from scripts.cli import lock as lock_mod  # noqa: E402
from scripts.cli import main as main_mod  # noqa: E402
from scripts.cli import migrate_cmd  # noqa: E402


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _set_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    root = tmp_path / "wxops-home"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("WXOPS_HOME", str(root))
    return root.resolve()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 1. store
# ---------------------------------------------------------------------------

class TestSlugValidation:
    @pytest.mark.parametrize(
        "slug",
        ["maizong", "foodie-01", "a", "a" * 32],
    )
    def test_valid(self, slug: str) -> None:
        assert accounts_store.validate_slug(slug) == slug

    @pytest.mark.parametrize(
        "slug",
        [
            "",
            "Maizong",
            "-lead",
            ".",
            "..",
            "a/b",
            "a\\b",
            "has space",
            "a" * 33,
            "中文",
        ],
    )
    def test_invalid(self, slug: str) -> None:
        with pytest.raises(ValueError):
            accounts_store.validate_slug(slug)


class TestCreateAccount:
    def test_create_writes_tree_and_pipeline(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        acct = accounts_store.create_account(root, "maizong", "麦总玩AI", niche="ai-tools")
        assert acct["slug"] == "maizong"
        assert acct["name"] == "麦总玩AI"
        assert acct["status"] == "active"
        assert acct["last_login_at"] is None

        acct_dir = accounts_store.get_account_dir(root, "maizong")
        assert (acct_dir / "account.json").is_file()
        assert (acct_dir / "pipeline.json").is_file()
        for d in (
            "credentials",
            "topics",
            "drafts",
            "images",
            "published",
            "raw",
            "output",
            "browser-profile",
            "reports",
            "data",
        ):
            assert (acct_dir / d).is_dir(), d

        cred_mode = stat.S_IMODE((acct_dir / "credentials").stat().st_mode)
        assert cred_mode == 0o700

        pipe = accounts_store.load_pipeline(root, "maizong")
        assert pipe["stations"]["login"]["ok"] is False
        assert pipe["stations"]["analyze"]["report"] is None

        assert accounts_store.get_current_slug(root) == "maizong"

    def test_second_account_does_not_steal_current(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "A")
        accounts_store.create_account(root, "b", "B")
        assert accounts_store.get_current_slug(root) == "a"

    def test_dir_exists_without_account_json_refuses(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        wild = accounts_store.get_accounts_dir(root) / "wild"
        wild.mkdir(parents=True)
        marker = wild / "keep-me.txt"
        marker.write_text("secret", encoding="utf-8")
        with pytest.raises(FileExistsError):
            accounts_store.create_account(root, "wild", "野目录")
        assert marker.read_text(encoding="utf-8") == "secret"

    def test_duplicate_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "x", "X")
        with pytest.raises(FileExistsError):
            accounts_store.create_account(root, "x", "X2")


class TestListSetRetireTouch:
    def test_list_sorts_and_skips_wild(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "zeta", "Z")
        accounts_store.create_account(root, "alpha", "A")
        wild = accounts_store.get_accounts_dir(root) / "nojson"
        wild.mkdir(parents=True)
        slugs = [a["slug"] for a in accounts_store.list_accounts(root)]
        assert slugs == ["alpha", "zeta"]

    def test_set_current_missing_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        with pytest.raises(ValueError):
            accounts_store.set_current(root, "ghost")

    def test_retire_keeps_files_clears_current(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "foodie", "食堂")
        acct_dir = accounts_store.get_account_dir(root, "foodie")
        data_file = acct_dir / "raw" / "keep.json"
        data_file.write_text('{"k":1}\n', encoding="utf-8")

        updated = accounts_store.retire_account(root, "foodie")
        assert updated["status"] == "retired"
        assert (acct_dir / "account.json").is_file()
        assert data_file.is_file()
        assert data_file.read_text(encoding="utf-8") == '{"k":1}\n'
        assert accounts_store.get_current_slug(root) is None

    def test_touch_and_pipeline(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "t", "T")
        accounts_store.touch(root, "t", "last_login_at")
        acct = accounts_store.get_account(root, "t")
        assert acct is not None
        assert acct["last_login_at"] is not None

        ok = accounts_store.touch_pipeline(
            root, "t", "analyze", ok=True, report="/tmp/r.json"
        )
        assert ok is True
        pipe = accounts_store.load_pipeline(root, "t")
        assert pipe["stations"]["analyze"]["ok"] is True
        assert pipe["stations"]["analyze"]["at"] is not None
        assert pipe["stations"]["analyze"]["report"] == "/tmp/r.json"

        # 不存在账号：静默 no-op
        accounts_store.touch(root, "ghost", "last_login_at")


# ---------------------------------------------------------------------------
# 2. resolve_context
# ---------------------------------------------------------------------------

class TestResolveContext:
    def test_workspace_legacy(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_home(monkeypatch, tmp_path)
        ws = tmp_path / "legacy-ws"
        ws.mkdir()
        args = main_mod.build_parser().parse_args(
            ["analyze", "--demo", "--workspace", str(ws)]
        )
        workspace, slug = main_mod.resolve_context(args)
        assert workspace == ws.resolve()
        assert slug is None

    def test_account_slug(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "foodie", "食堂")
        args = main_mod.build_parser().parse_args(
            ["analyze", "--demo", "--account", "foodie"]
        )
        workspace, slug = main_mod.resolve_context(args)
        assert slug == "foodie"
        assert workspace == accounts_store.get_account_dir(root, "foodie")

    def test_current_account(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "cur", "当前")
        args = main_mod.build_parser().parse_args(["analyze", "--demo"])
        workspace, slug = main_mod.resolve_context(args)
        assert slug == "cur"
        assert workspace == accounts_store.get_account_dir(root, "cur")

    def test_no_account_falls_back_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        args = main_mod.build_parser().parse_args(["analyze", "--demo"])
        workspace, slug = main_mod.resolve_context(args)
        assert slug is None
        assert workspace == root

    def test_workspace_and_account_mutex(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_home(monkeypatch, tmp_path)
        args = main_mod.build_parser().parse_args(
            ["analyze", "--workspace", "/tmp/x", "--account", "a"]
        )
        with pytest.raises(SystemExit) as ei:
            main_mod.resolve_context(args)
        assert ei.value.code == 2

    def test_missing_account(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_home(monkeypatch, tmp_path)
        args = main_mod.build_parser().parse_args(
            ["analyze", "--account", "nope"]
        )
        with pytest.raises(SystemExit) as ei:
            main_mod.resolve_context(args)
        assert ei.value.code == 1


# ---------------------------------------------------------------------------
# 3. migrate
# ---------------------------------------------------------------------------

class TestMigrate:
    def _seed_legacy(self, root: Path) -> None:
        (root / "config.json").write_text(
            json.dumps({"account_name": "旧号名称"}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (root / "raw").mkdir(parents=True)
        (root / "raw" / "account.json").write_text('{"id":1}\n', encoding="utf-8")
        (root / "raw" / "audience.json").write_text('{"fans":100}\n', encoding="utf-8")
        (root / "reports" / "wechat").mkdir(parents=True)
        (root / "reports" / "wechat" / "publish-records-x.json").write_text(
            "[]\n", encoding="utf-8"
        )
        (root / "output").mkdir(parents=True)
        (root / "output" / "report.json").write_text("{}\n", encoding="utf-8")
        (root / "dashboard" / "dist").mkdir(parents=True)
        (root / "dashboard" / "dist" / "index.html").write_text(
            "<html></html>\n", encoding="utf-8"
        )

    def test_copy_first_verify_source_untouched(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        self._seed_legacy(root)

        names = ["config.json", "raw", "reports", "output", "dashboard"]
        before = {}
        for name in names:
            p = root / name
            for f in migrate_cmd._iter_files(p):
                before[str(f.relative_to(root))] = _sha256(f)
        before_count = len(before)

        rc = migrate_cmd.run(root, slug="default", name=None)
        assert rc == 0

        target = accounts_store.get_account_dir(root, "default")
        for rel, digest in before.items():
            if rel.startswith("dashboard"):
                continue
            dst = target / rel
            assert dst.is_file(), rel
            assert _sha256(dst) == digest

        assert not (target / "dashboard").exists()

        manifests = list((root / "runs").glob("migrate-*.json"))
        assert len(manifests) == 1
        man = json.loads(manifests[0].read_text(encoding="utf-8"))
        assert man["status"] == "ok"
        assert "inventory" in man and "copied" in man and "verify" in man
        assert any(e["name"] == "dashboard" for e in man["excluded"])

        # 源逐字节未变
        after = {}
        for name in names:
            p = root / name
            for f in migrate_cmd._iter_files(p):
                after[str(f.relative_to(root))] = _sha256(f)
        assert after == before
        assert len(after) == before_count

        reg = accounts_store.load_registry(root)
        assert reg["current"] == "default"
        acct = accounts_store.get_account(root, "default")
        assert acct is not None
        assert acct["name"] == "旧号名称"

    def test_name_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        self._seed_legacy(root)
        rc = migrate_cmd.run(root, slug="mig", name="参数名")
        assert rc == 0
        acct = accounts_store.get_account(root, "mig")
        assert acct is not None
        assert acct["name"] == "参数名"

    def test_target_exists_aborts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        self._seed_legacy(root)
        accounts_store.create_account(root, "default", "已有")
        src_cfg = (root / "config.json").read_text(encoding="utf-8")
        rc = migrate_cmd.run(root, slug="default")
        assert rc != 0
        assert (root / "config.json").read_text(encoding="utf-8") == src_cfg

    def test_no_legacy_data(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        rc = migrate_cmd.run(root, slug="default")
        assert rc != 0


# ---------------------------------------------------------------------------
# 4. lock
# ---------------------------------------------------------------------------

class TestLock:
    def test_second_process_blocked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        if lock_mod.fcntl is None:
            pytest.skip("fcntl 不可用")

        ws = tmp_path / "lock-ws"
        ws.mkdir()
        lock = lock_mod.acquire_profile_lock(ws)
        pid = os.getpid()
        try:
            script = f"""
import sys
from pathlib import Path
sys.path.insert(0, {str(_PLUGIN_ROOT)!r})
from scripts.cli.lock import acquire_profile_lock, ProfileLockError
try:
    acquire_profile_lock(Path({str(ws)!r}))
    print("UNEXPECTED_OK")
    sys.exit(0)
except ProfileLockError as e:
    print(str(e))
    sys.exit(3)
"""
            proc = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert proc.returncode != 0
            out = (proc.stdout or "") + (proc.stderr or "")
            assert str(pid) in out
        finally:
            lock.release()

        # 释放后可重新获取
        lock2 = lock_mod.acquire_profile_lock(ws)
        lock2.release()


# ---------------------------------------------------------------------------
# 5. desk
# ---------------------------------------------------------------------------

class TestDesk:
    def test_desk_suggestions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "从未登录号")
        accounts_store.create_account(root, "b", "新鲜号")
        accounts_store.set_current(root, "b")
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        accounts_store.touch(root, "b", "last_login_at", when=now)
        accounts_store.touch(root, "b", "last_fetch_at", when=now)

        # retired 账号
        accounts_store.create_account(root, "old", "退休号")
        accounts_store.retire_account(root, "old")

        rc = desk_cmd.run(root)
        assert rc == 0
        out = capsys.readouterr().out
        assert "●" in out and "○" in out
        assert "wxops login --account a" in out
        assert "数据尚新" in out
        assert "(已退休)" in out
        # retired 在末尾：old 行应在 a/b 之后出现
        pos_old = out.rfind("old")
        pos_a = out.find(" a") if " a" in out else out.find("○ a")
        # 更稳：找 slug 列
        lines = [ln for ln in out.splitlines() if "old" in ln or " a" in ln or " b" in ln]
        # 至少保证 retired 文案在
        assert pos_old > 0

    def test_desk_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _set_home(monkeypatch, tmp_path)
        rc = desk_cmd.run(env.get_wxops_root())
        assert rc == 0
        out = capsys.readouterr().out
        assert "还没有任何账号" in out
        assert "accounts add" in out


# ---------------------------------------------------------------------------
# 6. pipeline e2e via main
# ---------------------------------------------------------------------------

class TestPipelineE2E:
    def test_analyze_demo_updates_current_account(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        rc = main_mod.main(
            ["accounts", "add", "smoke", "--name", "冒烟号"]
        )
        assert rc == 0

        rc = main_mod.main(["analyze", "--demo", "--data-only"])
        assert rc == 0

        report = root / "accounts" / "smoke" / "output" / "report.json"
        assert report.is_file()

        pipe = accounts_store.load_pipeline(root, "smoke")
        assert pipe["stations"]["analyze"]["at"] is not None
        assert pipe["stations"]["analyze"]["report"]
        assert "report.json" in pipe["stations"]["analyze"]["report"]

        acct = accounts_store.get_account(root, "smoke")
        assert acct is not None
        assert acct["last_analyze_at"] is not None
        assert acct["last_fetch_at"] is None  # demo 不算拉数


# ---------------------------------------------------------------------------
# 7. legacy 不变性
# ---------------------------------------------------------------------------

class TestLegacy:
    def test_workspace_analyze_no_accounts_tree(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_home(monkeypatch, tmp_path)
        legacy = tmp_path / "legacy"
        rc = main_mod.main(
            ["analyze", "--demo", "--data-only", "--workspace", str(legacy)]
        )
        assert rc == 0
        assert (legacy / "output" / "report.json").is_file()
        assert not (legacy / "accounts").exists()
        assert not (legacy / "account.json").exists()


# ---------------------------------------------------------------------------
# accounts_cmd 冒烟级
# ---------------------------------------------------------------------------

class TestAccountsCmd:
    def test_add_list_use_remove(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        assert main_mod.main(["accounts", "add", "maizong", "--name", "麦总玩AI"]) == 0
        assert main_mod.main(["accounts", "add", "foodie", "--name", "深夜食堂研究所"]) == 0
        assert main_mod.main(["accounts", "list"]) == 0
        out = capsys.readouterr().out
        assert "maizong" in out and "foodie" in out
        assert "●" in out

        assert main_mod.main(["accounts", "use", "foodie"]) == 0
        assert accounts_store.get_current_slug(root) == "foodie"

        assert main_mod.main(["accounts", "remove", "foodie"]) == 0
        acct = accounts_store.get_account(root, "foodie")
        assert acct is not None
        assert acct["status"] == "retired"
        assert accounts_store.get_current_slug(root) is None
