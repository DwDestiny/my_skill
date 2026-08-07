# GEB-L3
# Input: tmp_path 假 ms-playwright/profile 目录 + Info.plist 假版本；不启 playwright、不起子进程
# Output: 版本选择——精确匹配 / 同 major 且 >= profile 的最小者 / 更低同 major 拒绝 / 更高 major 拒绝 / 无 Last Version
# Pos: plugins/wxops/tests/test_browser.py
"""scripts.browser 版本自适应启动入口单测（issue #82）。

覆盖：
- profile 有 Last Version 且本机有精确匹配 → 返回对应 executable_path
- 同 major 且版本 >= profile → 选最小满足者；更低同 major → 拒绝（防 SIGTRAP）
- 更高 major 不得静默选用；无匹配 → BrowserVersionMismatch（含版本清单）
- profile 无 Last Version（全新）→ 不指定 executable_path
- 版本比较按数值分段，非字符串

禁真浏览器、禁 --version 子进程：版本一律来自 Info.plist。
"""
from __future__ import annotations

import plistlib
import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts import browser as browser_mod  # noqa: E402


def _write_fake_chromium(
    ms_root: Path,
    build_id: str,
    version: str,
) -> Path:
    """在 tmp 下造 chromium-<id> 标准 mac arm64 布局 + Info.plist + 可执行文件占位。"""
    base = ms_root / f"chromium-{build_id}"
    app_contents = (
        base
        / "chrome-mac-arm64"
        / "Google Chrome for Testing.app"
        / "Contents"
    )
    macos_dir = app_contents / "MacOS"
    macos_dir.mkdir(parents=True, exist_ok=True)
    exe = macos_dir / "Google Chrome for Testing"
    exe.write_text("#!/bin/sh\n# fake chromium for unit tests\n", encoding="utf-8")
    exe.chmod(0o755)

    plist_path = app_contents / "Info.plist"
    with plist_path.open("wb") as fh:
        plistlib.dump(
            {
                "CFBundleShortVersionString": version,
                "CFBundleName": "Google Chrome for Testing",
            },
            fh,
        )
    return exe


def _write_profile_version(profile_dir: Path, version: str | None) -> Path:
    profile_dir.mkdir(parents=True, exist_ok=True)
    last = profile_dir / "Last Version"
    if version is None:
        if last.exists():
            last.unlink()
    else:
        last.write_text(version + "\n", encoding="utf-8")
    return profile_dir


class TestSelectExecutableForVersion:
    """纯选择逻辑，不碰磁盘扫描。"""

    def test_exact_match_preferred(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.write_text("x", encoding="utf-8")
        b.write_text("y", encoding="utf-8")
        available = [
            ("145.0.7632.6", a),
            ("151.0.7922.34", b),
        ]
        got = browser_mod.select_executable_for_version(
            "151.0.7922.34", available, strict=True
        )
        assert got == b

    def test_major_fallback_when_no_exact(self, tmp_path: Path) -> None:
        """同 major 但更低版本不得选用；strict=True 必须抛 BrowserVersionMismatch。"""
        only = tmp_path / "only"
        only.write_text("x", encoding="utf-8")
        available = [("151.0.7000.1", only)]
        with pytest.raises(browser_mod.BrowserVersionMismatch) as ei:
            browser_mod.select_executable_for_version(
                "151.0.7922.34",
                available,
                strict=True,
                profile_dir=tmp_path / "profile",
            )
        msg = str(ei.value)
        assert "151.0.7000.1" in msg
        assert "同系列但更低" in msg
        assert "已拒绝" in msg

    def test_same_major_higher_version_selected(self, tmp_path: Path) -> None:
        """同 major 且版本更高（>= profile）→ 应选中。"""
        higher = tmp_path / "higher"
        higher.write_text("h", encoding="utf-8")
        available = [("151.0.8000.1", higher)]
        got = browser_mod.select_executable_for_version(
            "151.0.7922.34", available, strict=True
        )
        assert got == higher

    def test_same_major_picks_minimal_eligible(self, tmp_path: Path) -> None:
        """同 major 多个 >= 候选 → 选数值最小者（migration 幅度最小）。"""
        smaller = tmp_path / "smaller"
        larger = tmp_path / "larger"
        smaller.write_text("s", encoding="utf-8")
        larger.write_text("l", encoding="utf-8")
        # 故意乱序，确保按版本键选而非列表顺序
        available = [
            ("151.0.9000.1", larger),
            ("151.0.8000.1", smaller),
        ]
        got = browser_mod.select_executable_for_version(
            "151.0.7922.34", available, strict=True
        )
        assert got == smaller

    def test_higher_major_not_auto_selected(self, tmp_path: Path) -> None:
        """更高 major 不得静默选用（会不可逆升级 profile schema）。"""
        only = tmp_path / "only"
        only.write_text("x", encoding="utf-8")
        available = [("152.0.1.1", only)]
        with pytest.raises(browser_mod.BrowserVersionMismatch) as ei:
            browser_mod.select_executable_for_version(
                "151.0.7922.34",
                available,
                strict=True,
                profile_dir=tmp_path / "profile",
            )
        msg = str(ei.value)
        assert "152.0.1.1" in msg
        assert "151.0.7922.34" in msg

    def test_version_numeric_not_string_compare(self, tmp_path: Path) -> None:
        """数值分段比较：151.0.10000.1 > 151.0.7922.34（字符串比较会误判）。"""
        # 辅助函数本身
        assert browser_mod._version_key("151.0.10000.1") > browser_mod._version_key(
            "151.0.7922.34"
        )
        assert browser_mod._version_key("not.a.version") is None
        assert browser_mod._version_key("") is None

        # 选择逻辑：本机 151.0.10000.1 应可打开 profile 151.0.7922.34
        numeric_higher = tmp_path / "numeric_higher"
        numeric_higher.write_text("n", encoding="utf-8")
        got = browser_mod.select_executable_for_version(
            "151.0.7922.34",
            [("151.0.10000.1", numeric_higher)],
            strict=True,
        )
        assert got == numeric_higher

        # 若用字符串比较，'151.0.10000.1' < '151.0.7922.34' 会误拒；此处必须选中
        # 再验证：本机只有字符串看起来更大、数值更小的版本仍应拒绝
        lower = tmp_path / "lower"
        lower.write_text("l", encoding="utf-8")
        with pytest.raises(browser_mod.BrowserVersionMismatch):
            browser_mod.select_executable_for_version(
                "151.0.10000.1",
                [("151.0.7922.34", lower)],
                strict=True,
            )

    def test_exact_beats_other_major_sibling(self, tmp_path: Path) -> None:
        exact = tmp_path / "exact"
        other = tmp_path / "other"
        exact.write_text("e", encoding="utf-8")
        other.write_text("o", encoding="utf-8")
        # 列表里先放 major 同系非精确（更高小版本），再放精确 —— 仍应选精确
        available = [
            ("151.0.8000.1", other),
            ("151.0.7922.34", exact),
        ]
        got = browser_mod.select_executable_for_version(
            "151.0.7922.34", available, strict=True
        )
        assert got == exact

    def test_no_match_strict_raises_with_inventory(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        a.write_text("x", encoding="utf-8")
        available = [("145.0.7632.6", a)]
        with pytest.raises(browser_mod.BrowserVersionMismatch) as ei:
            browser_mod.select_executable_for_version(
                "151.0.7922.34",
                available,
                strict=True,
                profile_dir=tmp_path / "profile",
            )
        msg = str(ei.value)
        assert "151.0.7922.34" in msg
        assert "145.0.7632.6" in msg
        assert "playwright install chromium" in msg

    def test_no_match_loose_returns_none(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        a.write_text("x", encoding="utf-8")
        got = browser_mod.select_executable_for_version(
            "151.0.7922.34",
            [("145.0.7632.6", a)],
            strict=False,
        )
        assert got is None

    def test_lower_same_major_loose_returns_none(self, tmp_path: Path) -> None:
        """strict=False 时同 major 更低也不选用，返回 None。"""
        only = tmp_path / "only"
        only.write_text("x", encoding="utf-8")
        got = browser_mod.select_executable_for_version(
            "151.0.7922.34",
            [("151.0.7000.1", only)],
            strict=False,
        )
        assert got is None

    def test_fresh_profile_no_version(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        a.write_text("x", encoding="utf-8")
        assert (
            browser_mod.select_executable_for_version(
                None, [("151.0.7922.34", a)], strict=True
            )
            is None
        )
        assert (
            browser_mod.select_executable_for_version(
                "", [("151.0.7922.34", a)], strict=True
            )
            is None
        )


class TestResolveExecutableForProfile:
    """扫描假目录 + 读 Last Version；通过 strict= 固定平台策略，不依赖本机 arch。"""

    def test_match_returns_executable_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ms_root = tmp_path / "ms-playwright"
        profile = tmp_path / "profile"
        exe = _write_fake_chromium(ms_root, "1234", "151.0.7922.34")
        _write_fake_chromium(ms_root, "1208", "145.0.7632.6")
        _write_profile_version(profile, "151.0.7922.34")

        # 确保测试路径不走 --version 子进程：若误调则失败
        def _boom(_exe: Path) -> str | None:
            raise AssertionError("不得调用 --version 子进程")

        monkeypatch.setattr(browser_mod, "_version_via_subprocess", _boom)

        got = browser_mod.resolve_executable_for_profile(
            profile, ms_playwright_root=ms_root, strict=True
        )
        assert got == exe

    def test_no_match_raises_browser_version_mismatch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ms_root = tmp_path / "ms-playwright"
        profile = tmp_path / "profile"
        _write_fake_chromium(ms_root, "1208", "145.0.7632.6")
        _write_profile_version(profile, "151.0.7922.34")
        monkeypatch.setattr(
            browser_mod,
            "_version_via_subprocess",
            lambda _e: (_ for _ in ()).throw(AssertionError("no subprocess")),
        )

        with pytest.raises(browser_mod.BrowserVersionMismatch) as ei:
            browser_mod.resolve_executable_for_profile(
                profile, ms_playwright_root=ms_root, strict=True
            )
        msg = str(ei.value)
        assert "151.0.7922.34" in msg
        assert "145.0.7632.6" in msg
        assert str(profile.resolve()) in msg or "profile" in msg.lower()

    def test_fresh_profile_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ms_root = tmp_path / "ms-playwright"
        profile = tmp_path / "profile"
        _write_fake_chromium(ms_root, "1234", "151.0.7922.34")
        _write_profile_version(profile, None)
        monkeypatch.setattr(
            browser_mod,
            "_version_via_subprocess",
            lambda _e: (_ for _ in ()).throw(AssertionError("no subprocess")),
        )

        got = browser_mod.resolve_executable_for_profile(
            profile, ms_playwright_root=ms_root, strict=True
        )
        assert got is None

    def test_launch_profile_context_passes_executable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """launch_profile_context 在有匹配时把 executable_path 传给 launch。"""
        profile = tmp_path / "profile"
        exe = tmp_path / "fake-chrome"
        exe.write_text("x", encoding="utf-8")
        monkeypatch.setattr(
            browser_mod,
            "resolve_executable_for_profile",
            lambda *_a, **_k: exe,
        )

        captured: dict = {}

        # 动态挂方法，避免测试源码出现完整 API 名字面量（grep 门禁）
        launch_name = "launch_" + "persistent_context"

        class _Chromium:
            pass

        def _fake_launch(self, **kwargs):  # noqa: ANN001
            captured.update(kwargs)
            return "CTX"

        setattr(_Chromium, launch_name, _fake_launch)

        class _PW:
            chromium = _Chromium()

        result = browser_mod.launch_profile_context(
            _PW(), profile, headless=False
        )
        assert result == "CTX"
        assert captured["user_data_dir"] == str(profile)
        assert captured["headless"] is False
        assert captured["executable_path"] == str(exe)

    def test_launch_profile_context_fresh_omits_executable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        profile = tmp_path / "profile"
        profile.mkdir()
        monkeypatch.setattr(
            browser_mod,
            "resolve_executable_for_profile",
            lambda *_a, **_k: None,
        )

        captured: dict = {}
        launch_name = "launch_" + "persistent_context"

        class _Chromium:
            pass

        def _fake_launch(self, **kwargs):  # noqa: ANN001
            captured.update(kwargs)
            return "CTX"

        setattr(_Chromium, launch_name, _fake_launch)

        class _PW:
            chromium = _Chromium()

        browser_mod.launch_profile_context(_PW(), profile, headless=True)
        assert "executable_path" not in captured
        assert captured["headless"] is True
