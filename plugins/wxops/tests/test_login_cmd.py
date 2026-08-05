# GEB-L3
# Input: 假 page stub + monkeypatch time.sleep / token 探测参数；不启 playwright
# Output: _confirm_token 四场景：快路径零 goto、首轮 goto 得 token、三轮仍无 token、goto 异常不崩溃
# Pos: plugins/wxops/tests/test_login_cmd.py
"""login_cmd._confirm_token 登录成功判定单测（issue #53）。

覆盖：快路径、扫码后延迟跳转回归、真未登录、goto 异常容错。
禁真浏览器、禁真 sleep。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import login_cmd  # noqa: E402


class _FakePage:
    """最小 page stub：url + 可配置的 goto 行为序列。"""

    def __init__(
        self,
        initial_url: str = "",
        *,
        goto_urls: list[str] | None = None,
        goto_errors: list[BaseException | None] | None = None,
    ) -> None:
        self.url = initial_url
        self.goto_calls: list[dict[str, Any]] = []
        self._goto_urls = list(goto_urls or [])
        self._goto_errors = list(goto_errors or [])
        self._goto_i = 0

    def goto(self, url: str, **kwargs: Any) -> None:
        self.goto_calls.append({"url": url, **kwargs})
        i = self._goto_i
        self._goto_i += 1
        if i < len(self._goto_errors) and self._goto_errors[i] is not None:
            raise self._goto_errors[i]  # type: ignore[misc]
        if i < len(self._goto_urls):
            self.url = self._goto_urls[i]


class TestConfirmToken:
    def test_fast_path_has_token_no_goto(self) -> None:
        """初始 URL 已带 token → 成功且不调用 goto。"""
        page = _FakePage(
            "https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token=1234567890&lang=zh_CN"
        )
        token = login_cmd._confirm_token(page)
        assert token == "1234567890"
        assert len(page.goto_calls) == 0

    def test_delayed_redirect_first_goto_gets_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """本 issue 回归：按回车时无 token，第一次主动 goto 后出现 token。"""
        monkeypatch.setattr(login_cmd.time, "sleep", lambda *_a, **_k: None)
        page = _FakePage(
            "https://mp.weixin.qq.com/",
            goto_urls=[
                "https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token=9988776655&lang=zh_CN"
            ],
        )
        token = login_cmd._confirm_token(page)
        assert token == "9988776655"
        assert len(page.goto_calls) == 1
        assert page.goto_calls[0]["url"] == login_cmd._MP_HOME_URL
        assert page.goto_calls[0]["wait_until"] == "domcontentloaded"
        assert page.goto_calls[0]["timeout"] == login_cmd._TOKEN_PROBE_TIMEOUT_MS

    def test_truly_offline_three_gotos(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """所有轮次均无 token → None，且 goto 恰好 3 次。"""
        sleeps: list[float] = []

        def fake_sleep(s: float) -> None:
            sleeps.append(s)

        monkeypatch.setattr(login_cmd.time, "sleep", fake_sleep)
        page = _FakePage(
            "https://mp.weixin.qq.com/",
            goto_urls=[
                "https://mp.weixin.qq.com/",
                "https://mp.weixin.qq.com/",
                "https://mp.weixin.qq.com/",
            ],
        )
        token = login_cmd._confirm_token(page)
        assert token is None
        assert len(page.goto_calls) == login_cmd._TOKEN_RETRY_ROUNDS
        assert len(page.goto_calls) == 3
        # 仅在轮次之间 sleep，最后一轮不 sleep
        assert len(sleeps) == login_cmd._TOKEN_RETRY_ROUNDS - 1
        assert all(s == login_cmd._TOKEN_RETRY_INTERVAL_S for s in sleeps)

    def test_goto_exception_continues_and_survives(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """某轮 goto 抛异常不得崩溃；后续轮次继续，最终按结果返回。"""
        monkeypatch.setattr(login_cmd.time, "sleep", lambda *_a, **_k: None)
        # 第 1 轮 goto 失败（URL 仍无 token）；第 2 轮成功带 token
        page = _FakePage(
            "https://mp.weixin.qq.com/",
            goto_urls=[
                "https://mp.weixin.qq.com/",  # 本应在第 1 轮后设置，但 goto 会先 raise
                "https://mp.weixin.qq.com/cgi-bin/home?token=5555444433",
            ],
            goto_errors=[
                TimeoutError("Navigation timeout"),
                None,
            ],
        )
        token = login_cmd._confirm_token(page)
        assert token == "5555444433"
        assert len(page.goto_calls) == 2

    def test_goto_all_exceptions_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """三轮 goto 全抛异常 → 不崩溃，返回 None。"""
        monkeypatch.setattr(login_cmd.time, "sleep", lambda *_a, **_k: None)
        page = _FakePage(
            "https://mp.weixin.qq.com/",
            goto_errors=[
                RuntimeError("net::ERR"),
                TimeoutError("timeout"),
                Exception("boom"),
            ],
        )
        token = login_cmd._confirm_token(page)
        assert token is None
        assert len(page.goto_calls) == 3
