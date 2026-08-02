# GEB-L3
# Input: WXOPS_HOME=tmp_path + 非空 browser-profile + mock _probe/checker/runner/sleeper + ProfileLockError
# Output: check_login 短路与三态 + cmd_check 写回 + run_all 批次 ok/fail/skip/撞锁 + main 互斥 + desk 登录列
# Pos: plugins/wxops/tests/test_health_batch.py
"""登录态生命周期（B1/B2）+ 批量编排（D1-D5）单测。

全部用 WXOPS_HOME=tmp_path 隔离，绝不碰真实 ~/.wxops；禁真浏览器真睡眠。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import accounts_cmd  # noqa: E402
from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import batch_cmd  # noqa: E402
from scripts.cli import desk_cmd  # noqa: E402
from scripts.cli import health  # noqa: E402
from scripts.cli import lock as lock_mod  # noqa: E402
from scripts.cli import main as main_mod  # noqa: E402


def _set_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    root = tmp_path / "wxops-home"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("WXOPS_HOME", str(root))
    return root.resolve()


def _nonempty_profile(workspace: Path) -> Path:
    """建非空 browser-profile，绕过 check_login 短路。"""
    profile = workspace / "browser-profile"
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "dummy").write_text("x", encoding="utf-8")
    return profile


# ---------------------------------------------------------------------------
# 1. check_login 短路
# ---------------------------------------------------------------------------


class TestCheckLoginShortCircuit:
    def test_no_profile_skips_probe(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "A")
        workspace = accounts_store.get_account_dir(root, "a")
        # create_account 建了空 browser-profile → 短路

        def boom(*_a, **_k):
            raise AssertionError("_probe 不应被调用")

        monkeypatch.setattr(health, "_probe", boom)
        result = health.check_login(workspace)
        assert result["alive"] is False
        assert "从未登录" in (result["error"] or "")
        assert result["duration_s"] == 0.0


# ---------------------------------------------------------------------------
# 2. check_login 三态
# ---------------------------------------------------------------------------


class TestCheckLoginProbeStates:
    def test_token_alive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "A")
        workspace = accounts_store.get_account_dir(root, "a")
        _nonempty_profile(workspace)
        monkeypatch.setattr(health, "_probe", lambda *_a, **_k: "tok123")
        result = health.check_login(workspace)
        assert result["alive"] is True
        assert result["error"] is None

    def test_token_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "A")
        workspace = accounts_store.get_account_dir(root, "a")
        _nonempty_profile(workspace)
        monkeypatch.setattr(health, "_probe", lambda *_a, **_k: None)
        result = health.check_login(workspace)
        assert result["alive"] is False
        assert result["error"]

    def test_probe_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "A")
        workspace = accounts_store.get_account_dir(root, "a")
        _nonempty_profile(workspace)

        def raise_timeout(*_a, **_k):
            raise RuntimeError("超时")

        monkeypatch.setattr(health, "_probe", raise_timeout)
        result = health.check_login(workspace)
        assert result["alive"] is False
        assert result["error"]


# ---------------------------------------------------------------------------
# 3-4. cmd_check
# ---------------------------------------------------------------------------


class TestCmdCheck:
    def test_one_alive_one_dead(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "号A")
        accounts_store.create_account(root, "b", "号B")

        def fake_checker(workspace: Path) -> dict:
            slug = workspace.name
            if slug == "a":
                return {"alive": True, "error": None, "duration_s": 1.2}
            return {"alive": False, "error": "掉线", "duration_s": 2.3}

        sleeps: list[float] = []

        def record_sleep(s: float) -> None:
            sleeps.append(s)

        rc = accounts_cmd.cmd_check(
            root, checker=fake_checker, sleeper=record_sleep
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "● 在线" in out
        assert "○ 掉线" in out
        assert "wxops login --account b" in out

        acct_a = accounts_store.get_account(root, "a")
        acct_b = accounts_store.get_account(root, "b")
        assert acct_a is not None and acct_a.get("login_alive") is True
        assert acct_a.get("last_check_at")
        assert acct_b is not None and acct_b.get("login_alive") is False
        assert acct_b.get("last_check_at")

        assert len(sleeps) == 1
        assert 1.0 <= sleeps[0] <= 3.0

    def test_missing_slug(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "A")
        rc = accounts_cmd.cmd_check(root, "nope")
        assert rc == 1


# ---------------------------------------------------------------------------
# 5-7. run_all
# ---------------------------------------------------------------------------


class TestRunAll:
    def test_main_scenario(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        for s, n in [("a", "A"), ("b", "B"), ("c", "C")]:
            accounts_store.create_account(root, s, n)

        def fake_checker(workspace: Path) -> dict:
            slug = workspace.name
            if slug in ("a", "c"):
                return {"alive": True, "error": None, "duration_s": 0.5}
            return {"alive": False, "error": "登录态掉线", "duration_s": 0.1}

        def fake_runner(root_p: Path, slug: str, workspace: Path) -> int:
            if slug == "a":
                return 0
            if slug == "c":
                return 1
            return 1

        sleeps: list[float] = []

        def record_sleep(s: float) -> None:
            sleeps.append(s)

        rc = batch_cmd.run_all(
            root,
            checker=fake_checker,
            runner=fake_runner,
            sleeper=record_sleep,
            interval_range=(30.0, 90.0),
        )
        assert rc == 1
        out = capsys.readouterr().out
        assert "批次汇总" in out

        runs = list((root / "runs").glob("analyze-all-*.json"))
        assert len(runs) == 1
        payload = json.loads(runs[0].read_text(encoding="utf-8"))
        by_slug = {r["slug"]: r["status"] for r in payload["accounts"]}
        assert by_slug == {"a": "ok", "b": "skipped", "c": "failed"}
        assert payload["summary"] == {"ok": 1, "failed": 1, "skipped": 1}

        assert len(sleeps) == 1
        assert 30.0 <= sleeps[0] <= 90.0

    def test_runner_exception_continues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "A")
        accounts_store.create_account(root, "b", "B")

        def fake_checker(workspace: Path) -> dict:
            return {"alive": True, "error": None, "duration_s": 0.1}

        def boom_then_ok(root_p: Path, slug: str, workspace: Path) -> int:
            if slug == "a":
                raise RuntimeError("boom")
            return 0

        sleeps: list[float] = []
        rc = batch_cmd.run_all(
            root,
            checker=fake_checker,
            runner=boom_then_ok,
            sleeper=lambda s: sleeps.append(s),
            interval_range=(30.0, 90.0),
        )
        # a failed, b ok → failed > 0 → exit 1
        assert rc == 1
        runs = list((root / "runs").glob("analyze-all-*.json"))
        payload = json.loads(runs[0].read_text(encoding="utf-8"))
        by_slug = {r["slug"]: r["status"] for r in payload["accounts"]}
        assert by_slug["a"] == "failed"
        assert by_slug["b"] == "ok"
        assert payload["summary"]["failed"] == 1
        assert payload["summary"]["ok"] == 1
        # a executed then sleep before b
        assert len(sleeps) == 1

    def test_all_offline_no_sleep(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "A")
        accounts_store.create_account(root, "b", "B")

        def dead(workspace: Path) -> dict:
            return {"alive": False, "error": "掉线", "duration_s": 0.0}

        sleeps: list[float] = []
        rc = batch_cmd.run_all(
            root,
            checker=dead,
            runner=lambda *_a, **_k: 0,
            sleeper=lambda s: sleeps.append(s),
        )
        assert rc == 1
        runs = list((root / "runs").glob("analyze-all-*.json"))
        payload = json.loads(runs[0].read_text(encoding="utf-8"))
        assert payload["summary"] == {"ok": 0, "failed": 0, "skipped": 2}
        assert sleeps == []


# ---------------------------------------------------------------------------
# 8. main 互斥
# ---------------------------------------------------------------------------


class TestMainMutex:
    def test_analyze_all_account(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_home(monkeypatch, tmp_path)
        assert main_mod.main(["analyze", "--all", "--account", "x"]) == 2

    def test_analyze_all_demo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_home(monkeypatch, tmp_path)
        assert main_mod.main(["analyze", "--all", "--demo"]) == 2

    def test_login_all_account(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_home(monkeypatch, tmp_path)
        assert main_mod.main(["login", "--all", "--account", "x"]) == 2

    def test_analyze_all_build_mutex(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_home(monkeypatch, tmp_path)
        assert main_mod.main(["analyze", "--all", "--build"]) == 2


# ---------------------------------------------------------------------------
# 9. login 单号写回 login_alive
# ---------------------------------------------------------------------------


class TestLoginSingleAccountHealth:
    def test_login_single_account_sets_login_alive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "A")

        def fake_login(workspace, headless=False):  # noqa: ARG001
            return 0

        monkeypatch.setattr(main_mod.login_cmd, "run", fake_login)
        rc = main_mod.main(["login", "--account", "a"])
        assert rc == 0
        acct = accounts_store.get_account(root, "a")
        assert acct is not None
        assert acct["login_alive"] is True
        assert acct.get("last_check_at")


# ---------------------------------------------------------------------------
# 10. run_all 撞锁 reason 单行且不误加补登录
# ---------------------------------------------------------------------------


class TestRunAllLockSkipReason:
    def test_run_all_lock_skip_reason_single_line(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "a", "A")

        def locked_checker(workspace: Path) -> dict:  # noqa: ARG001
            raise lock_mod.ProfileLockError(
                "账号浏览器登录态正被进程 12345 使用（login 与拉数互斥）。\n"
                "请等待该进程结束后重试。\n"
                "锁文件：/tmp/x.lock"
            )

        rc = batch_cmd.run_all(
            root,
            checker=locked_checker,
            runner=lambda *_a, **_k: 0,
            sleeper=lambda _s: None,
        )
        assert rc == 1
        runs = list((root / "runs").glob("analyze-all-*.json"))
        assert len(runs) == 1
        payload = json.loads(runs[0].read_text(encoding="utf-8"))
        entry = payload["accounts"][0]
        assert entry["status"] == "skipped"
        reason = entry["reason"] or ""
        assert "\n" not in reason
        assert "12345" in reason
        assert "login --account" not in reason

        out = capsys.readouterr().out
        assert "login --account" not in out


# ---------------------------------------------------------------------------
# 11. desk 登录列
# ---------------------------------------------------------------------------


class TestDeskLoginAlive:
    def test_login_alive_three_states(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        root = _set_home(monkeypatch, tmp_path)
        accounts_store.create_account(root, "alive", "在线号")
        accounts_store.create_account(root, "dead", "掉线号")
        accounts_store.create_account(root, "unk", "未检号")

        # 未检号给 last_login_at，走时间戳推断
        accounts_store.touch(root, "unk", "last_login_at")
        accounts_store.set_login_health(root, "alive", True)
        accounts_store.set_login_health(root, "dead", False)

        rc = desk_cmd.run(root)
        assert rc == 0
        out = capsys.readouterr().out
        assert "● 在线" in out
        assert "○ 掉线" in out
        # 缺失 login_alive → 时间戳推断（今天 / 从未 等，不应是 ● 在线/○ 掉线 for unk 行）
        lines = [ln for ln in out.splitlines() if "unk" in ln]
        assert lines, "应有 unk 行"
        assert "● 在线" not in lines[0]
        assert "○ 掉线" not in lines[0]
        assert "今天" in lines[0] or "昨天" in lines[0] or "天前" in lines[0]
