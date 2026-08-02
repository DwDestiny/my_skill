# GEB-L3
# Input: tmp_path 隔离的 WXOPS_HOME + mock 网关
# Output: publish 主链 dry-run / --go / 红线 / 纯函数 覆盖
# Pos: plugins/wxops/tests/test_publish.py
"""publish 主链单测：零真实网络、零真实 ~/.wxops。"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path
from typing import Any

import pytest

# conftest 只加了 scripts/；本文件需要插件根以便 from scripts.cli import ...
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

_PUBLISH_DIR = _PLUGIN_ROOT / "scripts" / "publish"
if str(_PUBLISH_DIR) not in sys.path:
    sys.path.insert(0, str(_PUBLISH_DIR))

from draft_builder import build_crop_box, build_draft_article  # noqa: E402
from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import main as main_mod  # noqa: E402
from wechat_gateway_client import WechatGatewayClient  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_wxops_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """每测隔离：WXOPS_HOME=tmp，清掉网关环境变量，不碰真实 ~/.wxops。"""
    monkeypatch.setenv("WXOPS_HOME", str(tmp_path))
    monkeypatch.delenv("WECHAT_GATEWAY_BASE_URL", raising=False)
    monkeypatch.delenv("WECHAT_GATEWAY_BEARER_TOKEN", raising=False)


# ---------------------------------------------------------------------------
# helpers（纯标准库，不依赖 Pillow / sips）
# ---------------------------------------------------------------------------


def _minimal_png(width: int = 100, height: int = 80) -> bytes:
    """最小可被 read_png_size 解析的 PNG 头（≥24 字节）。"""
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x02\x00\x00\x00"
        + struct.pack(">I", 0)
        + b"IEND"
        + struct.pack(">I", 0)
    )


def _minimal_jpeg(width: int = 900, height: int = 383) -> bytes:
    """最小可被 read_jpeg_size 解析的 JPEG（SOI + SOF0 + EOI）。"""
    return (
        b"\xff\xd8"  # SOI
        + b"\xff\xc0"
        + struct.pack(">H", 17)
        + b"\x08"  # SOF0, len=17, precision=8
        + struct.pack(">HH", height, width)  # height, width
        + b"\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01"
        + b"\xff\xd9"  # EOI
    )


def _write_credentials(
    acct_dir: Path,
    *,
    app_id: str = "wxTESTAPPID",
    app_secret: str = "secret-value-do-not-leak",
    mode: int = 0o600,
) -> Path:
    cred_dir = acct_dir / "credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)
    path = cred_dir / "wechat.json"
    path.write_text(
        json.dumps({"app_id": app_id, "app_secret": app_secret}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    path.chmod(mode)
    return path


def _write_gateway(
    root: Path,
    *,
    base_url: str = "https://gw.example.test",
    bearer_token: str = "bearer-token-do-not-leak",
) -> Path:
    path = root / "gateway.json"
    path.write_text(
        json.dumps(
            {"base_url": base_url, "bearer_token": bearer_token},
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _setup_topic(
    root: Path,
    slug: str,
    topic: str,
    *,
    name: str | None = None,
    draft: str | None = None,
    audit: str | None = "审核结论：放行\n",
    cover: bool = True,
    cover_w: int = 900,
    cover_h: int = 383,
    content_images: dict[str, bytes] | None = None,
    credentials: bool = True,
    app_id: str = "wxTESTAPPID",
    app_secret: str = "secret-value-do-not-leak",
    cred_mode: int = 0o600,
    gateway: bool = True,
) -> Path:
    """铺齐选题目录；返回账号目录。"""
    accounts_store.create_account(root, slug, name or slug)
    acct = accounts_store.get_account_dir(root, slug)

    draft_dir = acct / "drafts" / topic
    draft_dir.mkdir(parents=True, exist_ok=True)
    if draft is None:
        draft = "# 测试标题\n\n正文一段。\n"
    (draft_dir / "draft.md").write_text(draft, encoding="utf-8")
    if audit is not None:
        (draft_dir / "audit.md").write_text(audit, encoding="utf-8")

    img_dir = acct / "images" / topic
    img_dir.mkdir(parents=True, exist_ok=True)
    if cover:
        (img_dir / "cover.jpg").write_bytes(_minimal_jpeg(cover_w, cover_h))
    if content_images:
        for fname, data in content_images.items():
            (img_dir / fname).write_bytes(data)

    if credentials:
        _write_credentials(
            acct, app_id=app_id, app_secret=app_secret, mode=cred_mode
        )
    if gateway:
        _write_gateway(root)
    return acct


def _install_gateway_mocks(
    monkeypatch: pytest.MonkeyPatch,
    *,
    draft_media_id: str = "DRAFT1",
    thumb_media_id: str = "THUMB1",
    content_url: str = "https://mmbiz.qpic.cn/fake",
) -> list[dict[str, Any]]:
    """monkeypatch WechatGatewayClient 两方法；返回调用记录。"""
    calls: list[dict[str, Any]] = []

    def fake_upload(
        self: Any,
        app_id: str,
        app_secret: str,
        upload_kind: str,
        file_path: Path,
    ) -> dict[str, Any]:
        calls.append(
            {
                "method": "upload_material",
                "app_id": app_id,
                "app_secret": app_secret,
                "upload_kind": upload_kind,
                "file_path": str(file_path),
            }
        )
        if upload_kind == "content_image":
            return {"url": content_url}
        if upload_kind == "thumb":
            return {"media_id": thumb_media_id}
        raise AssertionError(f"unexpected upload_kind={upload_kind!r}")

    def fake_add_draft(
        self: Any,
        app_id: str,
        app_secret: str,
        articles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        calls.append(
            {
                "method": "add_draft",
                "app_id": app_id,
                "app_secret": app_secret,
                "articles": articles,
            }
        )
        return {"media_id": draft_media_id}

    monkeypatch.setattr(WechatGatewayClient, "upload_material", fake_upload)
    monkeypatch.setattr(WechatGatewayClient, "add_draft", fake_add_draft)
    return calls


# ---------------------------------------------------------------------------
# 1–3：主链 dry-run / 零网络 / --go
# ---------------------------------------------------------------------------


def test_dry_run_full_green(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup_topic(
        tmp_path,
        "acct-a",
        "t1",
        draft="# 你好世界\n\n正文。\n![图](fig1.png)\n",
        content_images={"fig1.png": _minimal_png()},
    )
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a"]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "发布预检" in out
    assert "✓" in out
    assert "动作清单" in out or "将上传" in out
    assert "--go" in out
    html = (
        accounts_store.get_account_dir(tmp_path, "acct-a")
        / "output"
        / "t1"
        / "draft.html"
    )
    assert html.is_file()
    assert html.stat().st_size > 0


def test_dry_run_zero_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import requests

    def boom(*_a: Any, **_k: Any) -> None:
        raise AssertionError("dry-run 不许碰网络")

    monkeypatch.setattr(requests.Session, "post", boom)
    monkeypatch.setattr(requests.Session, "get", boom)

    _setup_topic(tmp_path, "acct-a", "t1")
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a"]
    )
    assert rc == 0
    _ = capsys.readouterr()


def test_go_mock_gateway_writes_ledger(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _setup_topic(
        tmp_path,
        "acct-a",
        "t1",
        draft="# Go标题\n\n有图。\n![x](fig1.png)\n",
        content_images={"fig1.png": _minimal_png()},
        app_id="wxAAA",
        app_secret="secret-aaa",
    )
    _install_gateway_mocks(monkeypatch)
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a", "--go"]
    )
    out = capsys.readouterr().out
    assert rc == 0, out
    ledger_path = (
        accounts_store.get_account_dir(tmp_path, "acct-a")
        / "published"
        / "t1.json"
    )
    assert ledger_path.is_file()
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert data["draft_media_id"] == "DRAFT1"
    assert data["thumb_media_id"] == "THUMB1"
    assert data["topic_slug"] == "t1"
    assert data["title"] == "Go标题"
    assert "drafted_at" in data
    assert "content_image_count" in data
    assert "gateway_host" in data
    assert "草稿已入箱" in out


# ---------------------------------------------------------------------------
# 4–5：双账号隔离
# ---------------------------------------------------------------------------


def test_dual_account_isolation_forward(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _setup_topic(
        tmp_path,
        "acct-a",
        "t1",
        name="号A",
        app_id="wxAAA",
        app_secret="secret-aaa",
        gateway=True,
    )
    # B 仅建账号+凭证，gateway 已由 A 的 setup 写过
    accounts_store.create_account(tmp_path, "acct-b", "号B")
    acct_b = accounts_store.get_account_dir(tmp_path, "acct-b")
    draft_dir = acct_b / "drafts" / "t1"
    draft_dir.mkdir(parents=True, exist_ok=True)
    (draft_dir / "draft.md").write_text("# B题\n\n正文\n", encoding="utf-8")
    (draft_dir / "audit.md").write_text("放行\n", encoding="utf-8")
    img_dir = acct_b / "images" / "t1"
    img_dir.mkdir(parents=True, exist_ok=True)
    (img_dir / "cover.jpg").write_bytes(_minimal_jpeg())
    _write_credentials(acct_b, app_id="wxBBB", app_secret="secret-bbb")

    calls = _install_gateway_mocks(monkeypatch)
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a", "--go"]
    )
    assert rc == 0, capsys.readouterr().out
    add_calls = [c for c in calls if c["method"] == "add_draft"]
    assert add_calls
    assert add_calls[0]["app_id"] == "wxAAA"


def test_dual_account_isolation_reverse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _setup_topic(
        tmp_path,
        "acct-a",
        "t1",
        name="号A",
        app_id="wxAAA",
        app_secret="secret-aaa",
    )
    accounts_store.create_account(tmp_path, "acct-b", "号B")
    acct_b = accounts_store.get_account_dir(tmp_path, "acct-b")
    draft_dir = acct_b / "drafts" / "t1"
    draft_dir.mkdir(parents=True, exist_ok=True)
    (draft_dir / "draft.md").write_text("# B题\n\n正文\n", encoding="utf-8")
    (draft_dir / "audit.md").write_text("放行\n", encoding="utf-8")
    img_dir = acct_b / "images" / "t1"
    img_dir.mkdir(parents=True, exist_ok=True)
    (img_dir / "cover.jpg").write_bytes(_minimal_jpeg())
    _write_credentials(acct_b, app_id="wxBBB", app_secret="secret-bbb")

    calls = _install_gateway_mocks(monkeypatch)
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-b", "--go"]
    )
    assert rc == 0, capsys.readouterr().out
    assert calls
    for c in calls:
        assert c["app_id"] == "wxBBB"
        assert "wxAAA" not in json.dumps(c, ensure_ascii=False)
    add_calls = [c for c in calls if c["method"] == "add_draft"]
    assert add_calls[0]["app_id"] == "wxBBB"


# ---------------------------------------------------------------------------
# 6：接口面积红线
# ---------------------------------------------------------------------------


def test_gateway_interface_surface_no_publish_mass() -> None:
    names = [
        n
        for n in dir(WechatGatewayClient)
        if callable(getattr(WechatGatewayClient, n, None)) and not n.startswith("_")
    ]
    allowed = {"upload_material", "add_draft"}
    for n in names:
        lower = n.lower()
        if any(k in lower for k in ("publish", "mass", "send")):
            if n not in allowed:
                pytest.fail(f"网关 client 出现禁止方法：{n}")
    # 除两方法外不应有 publish/mass/send 名
    extra = set(names) - allowed
    for n in extra:
        lower = n.lower()
        assert "publish" not in lower
        assert "mass" not in lower
        assert "send" not in lower

    src = (_PLUGIN_ROOT / "scripts" / "cli" / "publish_cmd.py").read_text(
        encoding="utf-8"
    )
    assert "freepublish" not in src
    assert "mass" not in src


# ---------------------------------------------------------------------------
# 7–11：硬伤
# ---------------------------------------------------------------------------


def test_missing_credentials_exit_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup_topic(tmp_path, "acct-a", "t1", credentials=False)
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a"]
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "凭证" in out
    assert "credentials/wechat.json" in out or "配置" in out


def test_credentials_mode_644_needs_chmod(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup_topic(tmp_path, "acct-a", "t1", cred_mode=0o644)
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a"]
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "chmod 600" in out


def test_go_ledger_excludes_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret = "super-secret-app-secret-xyz"
    token = "super-secret-bearer-token-xyz"
    _setup_topic(
        tmp_path,
        "acct-a",
        "t1",
        app_id="wxAAA",
        app_secret=secret,
    )
    # 覆盖 gateway token
    _write_gateway(tmp_path, bearer_token=token)
    _install_gateway_mocks(monkeypatch)
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a", "--go"]
    )
    out = capsys.readouterr().out
    assert rc == 0, out
    ledger_text = (
        accounts_store.get_account_dir(tmp_path, "acct-a")
        / "published"
        / "t1.json"
    ).read_text(encoding="utf-8")
    assert secret not in ledger_text
    assert token not in ledger_text
    assert secret not in out
    assert token not in out


def test_missing_cover_exit_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup_topic(tmp_path, "acct-a", "t1", cover=False)
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a"]
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "cover.jpg" in out


def test_missing_draft_exit_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    accounts_store.create_account(tmp_path, "acct-a", "号A")
    acct = accounts_store.get_account_dir(tmp_path, "acct-a")
    # 只铺 cover + cred + gateway，不写 draft
    img_dir = acct / "images" / "t1"
    img_dir.mkdir(parents=True, exist_ok=True)
    (img_dir / "cover.jpg").write_bytes(_minimal_jpeg())
    _write_credentials(acct)
    _write_gateway(tmp_path)
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a"]
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "draft.md" in out


# ---------------------------------------------------------------------------
# 12–14：软警告 / 标题 / 网关
# ---------------------------------------------------------------------------


def test_missing_audit_warn_dry_run_ok(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup_topic(tmp_path, "acct-a", "t1", audit=None)
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a"]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "放行" in out or "审计" in out or "主编" in out
    assert "⚠" in out


def test_title_override_and_h1_fallback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup_topic(
        tmp_path,
        "acct-a",
        "t1",
        draft="# 草稿一级标题\n\n正文\n",
    )
    rc = main_mod.main(
        [
            "publish",
            "--topic",
            "t1",
            "--account",
            "acct-a",
            "--title",
            "CLI覆盖标题",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "CLI覆盖标题" in out

    # 不给 --title 时取 H1
    rc2 = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a"]
    )
    out2 = capsys.readouterr().out
    assert rc2 == 0
    assert "草稿一级标题" in out2


def test_gateway_missing_dry_run_ok_go_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _setup_topic(tmp_path, "acct-a", "t1", gateway=False)
    rc = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a"]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "网关" in out
    assert "⚠" in out

    _install_gateway_mocks(monkeypatch)
    rc2 = main_mod.main(
        ["publish", "--topic", "t1", "--account", "acct-a", "--go"]
    )
    out2 = capsys.readouterr().out
    assert rc2 == 1
    assert "网关" in out2


# ---------------------------------------------------------------------------
# 15–16：纯函数
# ---------------------------------------------------------------------------


def test_build_crop_box_three_cases() -> None:
    # 图更宽 → 裁 x
    s1 = build_crop_box(1800, 383, 2.35)
    assert s1 == "0.249986_0.000000_0.750014_1.000000"
    parts = [float(x) for x in s1.split("_")]
    assert parts[1] == pytest.approx(0.0)
    assert parts[3] == pytest.approx(1.0)
    assert parts[0] == pytest.approx(0.249986, abs=1e-6)
    assert parts[2] == pytest.approx(0.750014, abs=1e-6)

    # 图更高（方图）→ 裁 y
    s2 = build_crop_box(900, 900, 2.35)
    assert s2 == "0.000000_0.287234_1.000000_0.712766"
    parts2 = [float(x) for x in s2.split("_")]
    assert parts2[0] == pytest.approx(0.0)
    assert parts2[2] == pytest.approx(1.0)
    assert parts2[1] == pytest.approx(0.287234, abs=1e-6)
    assert parts2[3] == pytest.approx(0.712766, abs=1e-6)

    # 恰好 2.35:1
    s3 = build_crop_box(2350, 1000, 2.35)
    assert s3 == "0.000000_0.000000_1.000000_1.000000"


def test_build_draft_article_digest_and_flags() -> None:
    base = dict(
        title="T",
        author="A",
        content="<html></html>",
        thumb_media_id="THUMB",
        content_source_url=" https://example.com ",
        pic_crop_235_1="0_0_1_1",
        pic_crop_1_1="0_0_1_1",
    )
    a1 = build_draft_article(
        **base,
        digest="",
        need_open_comment=5,
        only_fans_can_comment=0,
    )
    assert "digest" not in a1
    assert a1["need_open_comment"] == 1
    assert a1["only_fans_can_comment"] == 0
    assert a1["content_source_url"] == "https://example.com"

    a2 = build_draft_article(
        **base,
        digest="  摘要正文  ",
        need_open_comment=0,
        only_fans_can_comment=5,
    )
    assert a2["digest"] == "摘要正文"
    assert a2["need_open_comment"] == 0
    assert a2["only_fans_can_comment"] == 1

    a3 = build_draft_article(
        **base,
        digest="   \n\t  ",
        need_open_comment=0,
        only_fans_can_comment=0,
    )
    assert "digest" not in a3
