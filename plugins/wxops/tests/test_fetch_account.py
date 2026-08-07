# GEB-L3
# Input: tmp_path workspace + duck-typed 假 page（禁真浏览器、禁子进程）
# Output: fetch_account 嵌套取值 / fail-fast 不写盘 / 头像 page.request 下载 / orchestrator 结构性校验
# Pos: plugins/wxops/tests/test_fetch_account.py
"""fetch_account 取值路径 + 头像下载 + orchestrator 返回值校验（issue #83）。

禁真浏览器、禁子进程、不碰 ~/.wxops 与真实 browser-profile。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.fetch.fetch_account import fetch_account  # noqa: E402
from scripts.fetch import orchestrator as orch_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Fake page / request（duck typing，禁真网络）
# ---------------------------------------------------------------------------


class FakeAPIResponse:
    """Playwright APIResponse 最小 duck type：status / headers / body()。"""

    def __init__(
        self,
        status: int = 404,
        body: bytes = b"",
        content_type: str | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self._body = body
        if headers is not None:
            self.headers = dict(headers)
        else:
            self.headers: dict[str, str] = {}
            if content_type is not None:
                self.headers["content-type"] = content_type

    def body(self) -> bytes:
        return self._body


class FakeAPIRequestContext:
    """Playwright APIRequestContext 最小 duck type：get(url)。"""

    def __init__(
        self,
        response: FakeAPIResponse | None = None,
        *,
        raise_exc: BaseException | None = None,
    ) -> None:
        # 默认失败响应：保证未注入自定义 request 时 avatar_local 仍为 None
        self._response = response if response is not None else FakeAPIResponse(404, b"")
        self._raise_exc = raise_exc
        self.get_calls: list[str] = []

    def get(self, url: str, **kwargs: Any) -> FakeAPIResponse:
        self.get_calls.append(url)
        if self._raise_exc is not None:
            raise self._raise_exc
        return self._response


class FakePage:
    """实现 fetch_account 需要的 url / goto / evaluate / request。

    - 默认：request.get → 404，avatar_local 保持 None（旧用例断言不变）
    - avatar_bytes=...：兼容旧成功路径，request.get → 200 + image/png + 这些字节
    - request=...：注入自定义 FakeAPIRequestContext
    - has_request=False：不挂 request 属性（测 AttributeError 安全降级）
    """

    def __init__(
        self,
        common_data: Any,
        *,
        url: str = "https://mp.weixin.qq.com/?token=1234567890",
        avatar_bytes: list[int] | None = None,
        request: FakeAPIRequestContext | None = None,
        has_request: bool = True,
    ) -> None:
        self.url = url
        self._common_data = common_data
        self._avatar_bytes = avatar_bytes
        self.evaluate_calls: list[tuple[Any, ...]] = []
        self.goto_calls: list[tuple[Any, ...]] = []

        if not has_request:
            # 故意不设 self.request
            return
        if request is not None:
            self.request = request
        elif avatar_bytes is not None:
            # 旧用例 test_full_structure_from_data 依赖 avatar.png + 指定字节
            self.request = FakeAPIRequestContext(
                FakeAPIResponse(200, bytes(avatar_bytes), "image/png")
            )
        else:
            self.request = FakeAPIRequestContext()  # 默认 404

    def goto(self, *args: Any, **kwargs: Any) -> None:
        self.goto_calls.append(args)

    def evaluate(self, script: Any, *args: Any) -> Any:
        self.evaluate_calls.append((script, *args))
        text = script if isinstance(script, str) else str(script)
        if "commonData" in text:
            return self._common_data
        # 旧路径残留：头像已改走 request，evaluate 不应再被用于下载
        return self._avatar_bytes


def _full_common_data(
    *,
    nick: str = "测试账号甲",
    user: str = "gh_test_user_a",
    head: str = "https://example.com/avatar.png",
    with_user_info: bool = True,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "nick_name": nick,
        "user_name": user,
        "head_img": head,
        "alias": user,
    }
    out: dict[str, Any] = {
        "version": 1,
        "uin": 1,
        "data": data,
        "path": "/",
    }
    if with_user_info:
        out["user_info"] = {"nick_name": nick, "head_img": head}
    return out


def _ok_request(
    body: bytes,
    content_type: str | None = "image/jpeg",
    *,
    status: int = 200,
) -> FakeAPIRequestContext:
    return FakeAPIRequestContext(FakeAPIResponse(status, body, content_type))


# ---------------------------------------------------------------------------
# fetch_account
# ---------------------------------------------------------------------------


def test_full_structure_from_data(tmp_path: Path) -> None:
    page = FakePage(_full_common_data(), avatar_bytes=[1, 2, 3])
    result = fetch_account(page, tmp_path)
    assert result["nick_name"] == "测试账号甲"
    assert result["user_name"] == "gh_test_user_a"
    assert result["head_img"] == "https://example.com/avatar.png"
    assert result["avatar_local"] == "raw/avatar.png"
    path = tmp_path / "raw" / "account.json"
    assert path.is_file()
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["nick_name"] == "测试账号甲"
    assert (tmp_path / "raw" / "avatar.png").read_bytes() == bytes([1, 2, 3])


def test_nick_fallback_user_info(tmp_path: Path) -> None:
    cd = _full_common_data()
    del cd["data"]["nick_name"]
    cd["user_info"]["nick_name"] = "回退昵称乙"
    page = FakePage(cd)
    result = fetch_account(page, tmp_path)
    assert result["nick_name"] == "回退昵称乙"
    assert (tmp_path / "raw" / "account.json").is_file()


def test_user_name_fallback_alias(tmp_path: Path) -> None:
    cd = _full_common_data()
    del cd["data"]["user_name"]
    cd["data"]["alias"] = "alias_only_user"
    page = FakePage(cd)
    result = fetch_account(page, tmp_path)
    assert result["user_name"] == "alias_only_user"


def test_missing_nick_raises_and_no_write(tmp_path: Path) -> None:
    cd = _full_common_data()
    del cd["data"]["nick_name"]
    del cd["user_info"]["nick_name"]
    page = FakePage(cd)
    with pytest.raises(RuntimeError, match="account_fetch_failed") as ei:
        fetch_account(page, tmp_path)
    assert "nick_name" in str(ei.value)
    assert "顶层键" in str(ei.value)
    assert not (tmp_path / "raw" / "account.json").exists()


def test_evaluate_none_raises_no_write(tmp_path: Path) -> None:
    page = FakePage(None)
    with pytest.raises(RuntimeError, match="account_fetch_failed") as ei:
        fetch_account(page, tmp_path)
    assert "commonData" in str(ei.value)
    assert "NoneType" in str(ei.value)
    assert not (tmp_path / "raw" / "account.json").exists()


def test_evaluate_non_dict_raises_no_write(tmp_path: Path) -> None:
    page = FakePage("not-a-dict")
    with pytest.raises(RuntimeError, match="account_fetch_failed") as ei:
        fetch_account(page, tmp_path)
    assert "str" in str(ei.value)
    assert not (tmp_path / "raw" / "account.json").exists()


def test_missing_head_img_only_writes_null(tmp_path: Path) -> None:
    cd = _full_common_data()
    del cd["data"]["head_img"]
    del cd["user_info"]["head_img"]
    page = FakePage(cd)
    result = fetch_account(page, tmp_path)
    assert result["nick_name"] == "测试账号甲"
    assert result["user_name"] == "gh_test_user_a"
    assert result["head_img"] is None
    assert result["avatar_local"] is None
    written = json.loads((tmp_path / "raw" / "account.json").read_text(encoding="utf-8"))
    assert written["head_img"] is None
    assert written["avatar_local"] is None


def test_legacy_top_level_only_must_raise(tmp_path: Path) -> None:
    """防回归：只有顶层 nick_name，data/user_info 都没有 → 必须抛错，不退回旧行为。"""
    cd = {
        "version": 1,
        "nick_name": "旧顶层昵称",
        "user_name": "old_top",
        "head_img": "https://example.com/old.png",
        "data": {"other": 1},
        "user_info": {"other": 2},
    }
    page = FakePage(cd)
    with pytest.raises(RuntimeError, match="account_fetch_failed"):
        fetch_account(page, tmp_path)
    assert not (tmp_path / "raw" / "account.json").exists()


def test_data_not_dict_falls_to_user_info(tmp_path: Path) -> None:
    cd = {
        "version": 1,
        "data": "broken",
        "user_info": {
            "nick_name": "来自user_info",
            "head_img": "https://example.com/ui.png",
        },
    }
    # user_name 只能从 data 取：data 非 dict 时 user_name 会失败
    page = FakePage(cd)
    with pytest.raises(RuntimeError, match="user_name"):
        fetch_account(page, tmp_path)
    assert not (tmp_path / "raw" / "account.json").exists()

    # data 补上 user_name 后：nick_name/head_img 走 user_info 回退，应成功
    cd2 = {
        "version": 1,
        "data": {"user_name": "gh_from_data"},
        "user_info": {
            "nick_name": "来自user_info",
            "head_img": "https://example.com/ui.png",
        },
    }
    page2 = FakePage(cd2)
    result = fetch_account(page2, tmp_path)
    assert result["nick_name"] == "来自user_info"
    assert result["user_name"] == "gh_from_data"
    assert result["head_img"] == "https://example.com/ui.png"


def test_data_and_user_info_both_unusable_raises(tmp_path: Path) -> None:
    cd = {"version": 1, "data": ["x"], "user_info": "y"}
    page = FakePage(cd)
    with pytest.raises(RuntimeError, match="account_fetch_failed"):
        fetch_account(page, tmp_path)
    assert not (tmp_path / "raw" / "account.json").exists()


def test_blank_nick_name_raises(tmp_path: Path) -> None:
    cd = _full_common_data(nick="   ")
    cd["user_info"]["nick_name"] = "   "
    page = FakePage(cd)
    with pytest.raises(RuntimeError, match="nick_name"):
        fetch_account(page, tmp_path)
    assert not (tmp_path / "raw" / "account.json").exists()


def test_values_are_stripped(tmp_path: Path) -> None:
    cd = _full_common_data(nick="  昵称带空格  ", user="  gh_space  ", head="  https://example.com/a.png  ")
    page = FakePage(cd)
    result = fetch_account(page, tmp_path)
    assert result["nick_name"] == "昵称带空格"
    assert result["user_name"] == "gh_space"
    assert result["head_img"] == "https://example.com/a.png"


# ---------------------------------------------------------------------------
# 头像下载：page.request.get（issue #83 验收标准 5 后半条）
# ---------------------------------------------------------------------------


def test_avatar_jpeg_saved(tmp_path: Path) -> None:
    body = b"\xff\xd8\xff\xe0fake-jpeg"
    page = FakePage(_full_common_data(), request=_ok_request(body, "image/jpeg"))
    result = fetch_account(page, tmp_path)
    assert result["avatar_local"] == "raw/avatar.jpg"
    avatar_path = tmp_path / "raw" / "avatar.jpg"
    assert avatar_path.is_file()
    assert avatar_path.read_bytes() == body
    assert len(avatar_path.read_bytes()) == len(body)


def test_avatar_png_saved(tmp_path: Path) -> None:
    body = b"\x89PNGfake"
    page = FakePage(_full_common_data(), request=_ok_request(body, "image/png"))
    result = fetch_account(page, tmp_path)
    assert result["avatar_local"] == "raw/avatar.png"
    assert (tmp_path / "raw" / "avatar.png").read_bytes() == body


def test_avatar_content_type_with_params(tmp_path: Path) -> None:
    body = b"jpeg-with-params"
    page = FakePage(
        _full_common_data(),
        request=_ok_request(body, "image/jpeg; charset=binary"),
    )
    result = fetch_account(page, tmp_path)
    assert result["avatar_local"] == "raw/avatar.jpg"
    assert (tmp_path / "raw" / "avatar.jpg").read_bytes() == body


def test_avatar_unknown_content_type_falls_back_jpg(tmp_path: Path) -> None:
    body = b"octet-stream-body"
    # 缺失 content-type
    page_missing = FakePage(
        _full_common_data(head="https://example.com/a1"),
        request=_ok_request(body, None),
    )
    r1 = fetch_account(page_missing, tmp_path)
    assert r1["avatar_local"] == "raw/avatar.jpg"
    assert (tmp_path / "raw" / "avatar.jpg").read_bytes() == body

    # application/octet-stream
    ws2 = tmp_path / "ws2"
    ws2.mkdir()
    page_octet = FakePage(
        _full_common_data(head="https://example.com/a2"),
        request=_ok_request(body, "application/octet-stream"),
    )
    r2 = fetch_account(page_octet, ws2)
    assert r2["avatar_local"] == "raw/avatar.jpg"
    assert (ws2 / "raw" / "avatar.jpg").read_bytes() == body


def test_avatar_non_200_best_effort(tmp_path: Path) -> None:
    page = FakePage(
        _full_common_data(),
        request=FakeAPIRequestContext(FakeAPIResponse(403, b"forbidden", "image/jpeg")),
    )
    result = fetch_account(page, tmp_path)
    assert result["avatar_local"] is None
    assert result["nick_name"] == "测试账号甲"
    assert result["user_name"] == "gh_test_user_a"
    written = json.loads((tmp_path / "raw" / "account.json").read_text(encoding="utf-8"))
    assert written["nick_name"] == "测试账号甲"
    assert written["avatar_local"] is None
    # 不得落任何 avatar 文件
    assert not (tmp_path / "raw" / "avatar.jpg").exists()
    assert not (tmp_path / "raw" / "avatar.png").exists()


def test_avatar_empty_body_best_effort(tmp_path: Path) -> None:
    page = FakePage(
        _full_common_data(),
        request=_ok_request(b"", "image/jpeg"),
    )
    result = fetch_account(page, tmp_path)
    assert result["avatar_local"] is None
    assert result["nick_name"] == "测试账号甲"
    written = json.loads((tmp_path / "raw" / "account.json").read_text(encoding="utf-8"))
    assert written["avatar_local"] is None
    assert not (tmp_path / "raw" / "avatar.jpg").exists()


def test_avatar_request_raises_best_effort(tmp_path: Path) -> None:
    page = FakePage(
        _full_common_data(),
        request=FakeAPIRequestContext(raise_exc=RuntimeError("network boom")),
    )
    result = fetch_account(page, tmp_path)
    assert result["avatar_local"] is None
    assert result["nick_name"] == "测试账号甲"
    written = json.loads((tmp_path / "raw" / "account.json").read_text(encoding="utf-8"))
    assert written["nick_name"] == "测试账号甲"
    assert written["avatar_local"] is None


def test_avatar_no_request_attr_best_effort(tmp_path: Path) -> None:
    page = FakePage(_full_common_data(), has_request=False)
    # 不得抛 AttributeError
    result = fetch_account(page, tmp_path)
    assert result["avatar_local"] is None
    assert result["nick_name"] == "测试账号甲"
    assert (tmp_path / "raw" / "account.json").is_file()


def test_avatar_failure_warns_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    page = FakePage(
        _full_common_data(),
        request=FakeAPIRequestContext(FakeAPIResponse(403, b"no", "image/jpeg")),
    )
    result = fetch_account(page, tmp_path)
    assert result["avatar_local"] is None
    err = capsys.readouterr().err
    assert "警告" in err
    assert "头像" in err
    assert "403" in err or "非 200" in err


# ---------------------------------------------------------------------------
# orchestrator 结构性校验（mock 全链路，禁真浏览器）
# ---------------------------------------------------------------------------


class _FakePlaywrightCM:
    def __enter__(self) -> Any:
        return MagicMock(name="playwright")

    def __exit__(self, *args: Any) -> None:
        return None


def test_orchestrator_audience_available_false_is_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """fetch_audience 返回 available=False 的 dict → orchestrator 不得判失败。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    profile = tmp_path / "profile"
    profile.mkdir()

    account_payload = {
        "nick_name": "编排测试号",
        "user_name": "gh_orch",
        "head_img": None,
        "avatar_local": None,
    }
    audience_payload = {"available": False, "cumulate_user": None}
    trend_payload = {"ok": True}

    monkeypatch.setattr(orch_mod, "sync_playwright", lambda: _FakePlaywrightCM())
    monkeypatch.setattr(orch_mod, "time", MagicMock(sleep=MagicMock()))
    # run() 内部通过闭包式 _import_* 取依赖；直接 patch 其 __import__ 路径模块
    import fetch.fetch_account as fa
    import fetch.fetch_audience as fau
    import fetch.fetch_content_trend as fct
    import fetch.session as sess
    import export_wechat_publish_records as exp
    import scripts.browser as browser_mod

    monkeypatch.setattr(fa, "fetch_account", lambda page, ws: account_payload)
    monkeypatch.setattr(fau, "fetch_audience", lambda page, ws: audience_payload)
    monkeypatch.setattr(fct, "fetch_content_trend", lambda page, ws: trend_payload)
    monkeypatch.setattr(sess, "open_logged_in_page", lambda context: (MagicMock(), "tok"))
    monkeypatch.setattr(exp, "_fetch_publish_payload", lambda page, token: {})
    monkeypatch.setattr(
        exp, "_process_publish_payload", lambda payload: ([], [], {})
    )

    def _write_export(ws, records, **kwargs):
        out = Path(ws) / "raw" / "publish-export.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("{}", encoding="utf-8")
        return out

    monkeypatch.setattr(exp, "write_export", _write_export)
    monkeypatch.setattr(
        browser_mod,
        "launch_profile_context",
        lambda playwright, profile_dir, headless=True: MagicMock(close=MagicMock()),
    )

    # 也 patch 可能的 scripts.* 路径（_import_* 第二候选）
    try:
        import scripts.fetch.fetch_account as sfa
        import scripts.fetch.fetch_audience as sfau
        import scripts.fetch.fetch_content_trend as sfct
        import scripts.fetch.session as ssess
        import scripts.export_wechat_publish_records as sexp

        monkeypatch.setattr(sfa, "fetch_account", lambda page, ws: account_payload)
        monkeypatch.setattr(sfau, "fetch_audience", lambda page, ws: audience_payload)
        monkeypatch.setattr(sfct, "fetch_content_trend", lambda page, ws: trend_payload)
        monkeypatch.setattr(ssess, "open_logged_in_page", lambda context: (MagicMock(), "tok"))
        monkeypatch.setattr(sexp, "_fetch_publish_payload", lambda page, token: {})
        monkeypatch.setattr(
            sexp, "_process_publish_payload", lambda payload: ([], [], {})
        )
        monkeypatch.setattr(sexp, "write_export", _write_export)
    except ImportError:
        pass

    result = orch_mod.run(workspace, profile, headless=True)
    assert result["status"] == "ok", result
    assert result["account"] == account_payload
    assert "raw_dir" in result
    assert "publish_export" in result
    assert "captured_at" in result


def test_orchestrator_rejects_non_dict_audience(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """结构性断言：audience 非 dict → failed（对照 available=false 合法路径）。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    profile = tmp_path / "profile"
    profile.mkdir()

    account_payload = {
        "nick_name": "编排测试号",
        "user_name": "gh_orch",
        "head_img": None,
        "avatar_local": None,
    }

    def _write_export(ws, records, **kwargs):
        out = Path(ws) / "raw" / "publish-export.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("{}", encoding="utf-8")
        return out

    monkeypatch.setattr(orch_mod, "sync_playwright", lambda: _FakePlaywrightCM())
    monkeypatch.setattr(orch_mod, "time", MagicMock(sleep=MagicMock()))

    import fetch.fetch_account as fa
    import fetch.fetch_audience as fau
    import fetch.fetch_content_trend as fct
    import fetch.session as sess
    import export_wechat_publish_records as exp
    import scripts.browser as browser_mod

    monkeypatch.setattr(fa, "fetch_account", lambda page, ws: account_payload)
    monkeypatch.setattr(fau, "fetch_audience", lambda page, ws: "not-a-dict")
    monkeypatch.setattr(fct, "fetch_content_trend", lambda page, ws: {"ok": True})
    monkeypatch.setattr(sess, "open_logged_in_page", lambda context: (MagicMock(), "tok"))
    monkeypatch.setattr(exp, "_fetch_publish_payload", lambda page, token: {})
    monkeypatch.setattr(
        exp, "_process_publish_payload", lambda payload: ([], [], {})
    )
    monkeypatch.setattr(exp, "write_export", _write_export)
    monkeypatch.setattr(
        browser_mod,
        "launch_profile_context",
        lambda playwright, profile_dir, headless=True: MagicMock(close=MagicMock()),
    )

    try:
        import scripts.fetch.fetch_account as sfa
        import scripts.fetch.fetch_audience as sfau
        import scripts.fetch.fetch_content_trend as sfct
        import scripts.fetch.session as ssess
        import scripts.export_wechat_publish_records as sexp

        monkeypatch.setattr(sfa, "fetch_account", lambda page, ws: account_payload)
        monkeypatch.setattr(sfau, "fetch_audience", lambda page, ws: "not-a-dict")
        monkeypatch.setattr(sfct, "fetch_content_trend", lambda page, ws: {"ok": True})
        monkeypatch.setattr(ssess, "open_logged_in_page", lambda context: (MagicMock(), "tok"))
        monkeypatch.setattr(sexp, "_fetch_publish_payload", lambda page, token: {})
        monkeypatch.setattr(
            sexp, "_process_publish_payload", lambda payload: ([], [], {})
        )
        monkeypatch.setattr(sexp, "write_export", _write_export)
    except ImportError:
        pass

    result = orch_mod.run(workspace, profile, headless=True)
    assert result["status"] == "failed"
    assert "audience" in str(result.get("error", "")).lower() or "dict" in str(
        result.get("error", "")
    )
