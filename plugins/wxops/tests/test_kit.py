# GEB-L3
# Input: autouse 隔离 WXOPS_HOME=tmp_path + 构造 persona/card/evidence + niches structure.md + capsys
# Output: kit_cmd 四件套门禁（齐备/空壳/占位符/缺件）+ structure 三层回落 + topic 非法 slug + desk 在途列与写稿建议
# Pos: plugins/wxops/tests/test_kit.py
"""kit 写作三件套门禁 + desk 在途列单测。

全部用 WXOPS_HOME=tmp_path 隔离，绝不碰真实 ~/.wxops。
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

# conftest 只加了 scripts/；本文件需要插件根以便 from scripts.cli import ...
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import desk_cmd  # noqa: E402
from scripts.cli import kit_cmd  # noqa: E402
from scripts.cli import main as main_mod  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_wxops_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """每测隔离：WXOPS_HOME=tmp，不碰真实 ~/.wxops。"""
    monkeypatch.setenv("WXOPS_HOME", str(tmp_path))


def _write_persona(root: Path, slug: str, text: str = "这是完整人设，无占位符。") -> Path:
    p = accounts_store.get_account_dir(root, slug) / "persona.md"
    p.write_text(text, encoding="utf-8")
    return p


def _write_topic_files(
    root: Path,
    slug: str,
    topic: str,
    *,
    card: str | None = "选题卡正文，无占位符。",
    evidence: str | None = "证据包正文，无占位符。",
) -> Path:
    topic_dir = accounts_store.get_account_dir(root, slug) / "topics" / topic
    topic_dir.mkdir(parents=True, exist_ok=True)
    if card is not None:
        (topic_dir / "card.md").write_text(card, encoding="utf-8")
    if evidence is not None:
        (topic_dir / "evidence.md").write_text(evidence, encoding="utf-8")
    return topic_dir


# ---------------------------------------------------------------------------
# kit：齐备 / 空壳 / 缺件
# ---------------------------------------------------------------------------


class TestKitReady:
    def test_four_ready_exit_0(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总")
        _write_persona(root, "maizong")
        _write_topic_files(root, "maizong", "claude-code-plugin-guide")

        rc = kit_cmd.run(root, account="maizong", topic="claude-code-plugin-guide")
        out = capsys.readouterr().out
        assert rc == 0
        assert "可开工" in out
        assert "开工体检" in out
        assert "人设" in out
        assert "结构契约" in out
        assert "选题卡" in out
        assert "证据包" in out


class TestKitPersonaShell:
    def test_missing_empty_placeholder(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总")
        # 结构契约走内置，persona 三种分别测

        # 1) 缺失
        rc = kit_cmd.run(root, account="maizong")
        out = capsys.readouterr().out
        assert rc == 1
        assert "缺失" in out
        assert "persona.template.md" in out

        # 2) 空文件
        p = accounts_store.get_account_dir(root, "maizong") / "persona.md"
        p.write_text("   \n\t\n", encoding="utf-8")
        rc = kit_cmd.run(root, account="maizong")
        out = capsys.readouterr().out
        assert rc == 1
        assert "为空" in out

        # 3) 含占位符
        p.write_text("你好 {{账号名}} 继续写", encoding="utf-8")
        rc = kit_cmd.run(root, account="maizong")
        out = capsys.readouterr().out
        assert rc == 1
        assert "占位符" in out
        assert "{{" in out or "未填" in out


class TestKitTopicMissing:
    def test_missing_card_and_evidence(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总")
        _write_persona(root, "maizong")
        # 建目录但不放文件
        topic_dir = (
            accounts_store.get_account_dir(root, "maizong")
            / "topics"
            / "my-topic"
        )
        topic_dir.mkdir(parents=True, exist_ok=True)

        rc = kit_cmd.run(root, account="maizong", topic="my-topic")
        out = capsys.readouterr().out
        assert rc == 1
        assert "topic-card.template.md" in out
        assert "evidence-pack.template.md" in out
        assert "不可开工" in out
        assert "缺 2 件" in out


# ---------------------------------------------------------------------------
# 结构契约三层回落
# ---------------------------------------------------------------------------


class TestKitStructureFallback:
    def test_user_package(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总", niche="ai-tools")
        _write_persona(root, "maizong")
        user_struct = root / "niches" / "ai-tools" / "structure.md"
        user_struct.parent.mkdir(parents=True, exist_ok=True)
        user_struct.write_text("# 用户包结构\n", encoding="utf-8")

        rc = kit_cmd.run(root, account="maizong")
        out = capsys.readouterr().out
        assert rc == 0
        assert "用户包" in out
        assert "通用兜底" not in out or "用户包" in out

    def test_user_dir_no_structure_falls_to_builtin(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总", niche="ai-tools")
        _write_persona(root, "maizong")
        # 用户包目录存在但无 structure.md → 内置包
        (root / "niches" / "ai-tools").mkdir(parents=True, exist_ok=True)
        # 不放 structure.md

        rc = kit_cmd.run(root, account="maizong")
        out = capsys.readouterr().out
        assert rc == 0
        assert "内置包" in out
        assert "ai-tools" in out

    def test_unknown_niche_falls_to_generic(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总", niche="no-such-niche-xyz")
        _write_persona(root, "maizong")

        rc = kit_cmd.run(root, account="maizong")
        out = capsys.readouterr().out
        assert rc == 0
        assert "通用兜底" in out or "兜底" in out
        assert "structure.md" in out  # 警告文案


# ---------------------------------------------------------------------------
# 账号级 / 未知账号 / e2e main
# ---------------------------------------------------------------------------


class TestKitAccountLevel:
    def test_no_topic_two_items(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总")
        _write_persona(root, "maizong")

        rc = kit_cmd.run(root, account="maizong")
        out = capsys.readouterr().out
        assert rc == 0
        assert "人设与结构契约就位" in out
        assert "账号体检" in out
        assert "选题卡" not in out
        assert "证据包" not in out


class TestKitUnknownAccount:
    def test_unknown_account(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总")

        rc = kit_cmd.run(root, account="ghost")
        out = capsys.readouterr().out
        assert rc != 0
        assert "账号不存在" in out


class TestKitMainE2E:
    def test_main_kit_registered(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总")
        _write_persona(root, "maizong")
        _write_topic_files(root, "maizong", "t1")

        rc = main_mod.main(
            ["kit", "--account", "maizong", "--topic", "t1"]
        )
        out = capsys.readouterr().out
        assert rc == 0
        assert "可开工" in out

    def test_main_kit_missing_persona(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总")

        rc = main_mod.main(["kit", "--account", "maizong"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "不可开工" in out or "缺失" in out


class TestKitCurrentAccount:
    def test_uses_current_when_no_account_flag(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总")
        _write_persona(root, "maizong")

        rc = kit_cmd.run(root, account=None)
        out = capsys.readouterr().out
        assert rc == 0
        assert "maizong" in out

    def test_no_current_errors(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        # 空注册表，无 current
        rc = kit_cmd.run(root, account=None)
        out = capsys.readouterr().out
        assert rc != 0
        assert "账号" in out


class TestKitTopicValidation:
    def test_reject_path_traversal(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "maizong", "麦总")
        _write_persona(root, "maizong")

        rc = kit_cmd.run(root, account="maizong", topic="../etc")
        out = capsys.readouterr().out
        assert rc != 0
        assert "不合法" in out or "slug" in out.lower() or "非法" in out


# ---------------------------------------------------------------------------
# desk 在途列
# ---------------------------------------------------------------------------


class TestDeskInFlight:
    def test_counts_and_suggest_write(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "busy", "有内容号")
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        accounts_store.touch(root, "busy", "last_login_at", when=now)
        accounts_store.touch(root, "busy", "last_fetch_at", when=now)

        acct_dir = accounts_store.get_account_dir(root, "busy")
        for t in ("topic-a", "topic-b"):
            d = acct_dir / "topics" / t
            d.mkdir(parents=True, exist_ok=True)
            (d / "card.md").write_text("card", encoding="utf-8")
        draft_d = acct_dir / "drafts" / "draft-1"
        draft_d.mkdir(parents=True, exist_ok=True)
        (draft_d / "draft.md").write_text("draft", encoding="utf-8")

        # 空账号对照
        accounts_store.create_account(root, "empty", "空号")
        accounts_store.touch(root, "empty", "last_login_at", when=now)
        accounts_store.touch(root, "empty", "last_fetch_at", when=now)

        rc = desk_cmd.run(root)
        out = capsys.readouterr().out
        assert rc == 0
        assert "在途" in out
        assert "2 题 1 稿" in out
        assert "稿件在途" in out or "/wxops:write" in out

        # empty：在途为 —，建议含 topics（数据尚新）
        lines = [ln for ln in out.splitlines() if "empty" in ln]
        assert lines, "应有 empty 行"
        assert "—" in lines[0]
        assert "数据尚新" in out
        assert "/wxops:topics" in out

    def test_topics_only_suggests_write(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        accounts_store.create_account(root, "topics-only", "有题无稿")
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        accounts_store.touch(root, "topics-only", "last_login_at", when=now)
        accounts_store.touch(root, "topics-only", "last_fetch_at", when=now)

        d = accounts_store.get_account_dir(root, "topics-only") / "topics" / "t1"
        d.mkdir(parents=True, exist_ok=True)
        (d / "card.md").write_text("c", encoding="utf-8")

        rc = desk_cmd.run(root)
        out = capsys.readouterr().out
        assert rc == 0
        assert "1 题 0 稿" in out
        assert "/wxops:write 开工写稿" in out
