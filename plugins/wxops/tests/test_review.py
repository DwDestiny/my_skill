# GEB-L3
# Input: tmp_path 隔离的 WXOPS_HOME + 手工台账/选题卡/report.json
# Output: review 主链端到端覆盖（达成/偏差/未就绪/无卡/完读人工/禁写 persona）
# Pos: plugins/wxops/tests/test_review.py
"""review 复盘工位单测：零真实网络、零真实 ~/.wxops。"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

# conftest 只加了 scripts/；本文件需要插件根以便 from scripts.cli import ...
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import main as main_mod  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_wxops_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """每测隔离：WXOPS_HOME=tmp，不碰真实 ~/.wxops。"""
    monkeypatch.setenv("WXOPS_HOME", str(tmp_path))


# ---------------------------------------------------------------------------
# helpers（独立自建，不 import test_publish）
# ---------------------------------------------------------------------------


def _write_ledger(
    acct: Path,
    topic: str,
    *,
    title: str = "测试文章标题",
    drafted_at: str = "2026-07-28T09:00:00+08:00",
    content_image_count: int = 2,
) -> Path:
    published = acct / "published"
    published.mkdir(parents=True, exist_ok=True)
    path = published / f"{topic}.json"
    payload = {
        "topic_slug": topic,
        "title": title,
        "author": "测试作者",
        "digest": "摘要",
        "draft_media_id": "DRAFT1",
        "thumb_media_id": "THUMB1",
        "drafted_at": drafted_at,
        "content_image_count": content_image_count,
        "gateway_host": "gw.example.test",
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _write_card(
    acct: Path,
    topic: str,
    *,
    body: str | None = None,
    expected_section: str | None = None,
) -> Path:
    card_dir = acct / "topics" / topic
    card_dir.mkdir(parents=True, exist_ok=True)
    path = card_dir / "card.md"
    if body is not None:
        text = body
    else:
        if expected_section is None:
            expected_section = (
                "## 预期指标\n"
                "\n"
                "- 预计阅读：100-500\n"
                "- 预计完读：≥ 60%\n"
                "- 核心验证点：教程体是否更高完读\n"
            )
        text = (
            f"# 选题卡：{topic}\n"
            "\n"
            "- **状态**：已发布\n"
            "\n"
            f"{expected_section}"
            "\n"
            "## 证据清单\n"
            "\n"
            "- [ ] 证据 1\n"
        )
    path.write_text(text, encoding="utf-8")
    return path


def _write_report_json(
    acct: Path,
    *,
    title: str = "测试文章标题",
    reads: int = 210,
    likes: int = 10,
    zaikan: int = 5,
    shares: int = 5,
    share_rate: float = 0.0238,
    is_immature: bool = False,
    status: str = "published",
    published_at: str = "2026-07-28T10:00:00+08:00",
    extra_articles: list[dict[str, Any]] | None = None,
) -> Path:
    out = acct / "output"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "report.json"
    article = {
        "title": title,
        "reads": reads,
        "likes": likes,
        "zaikan": zaikan,
        "shares": shares,
        "share_rate": share_rate,
        "is_immature": is_immature,
        "status": status,
        "published_at": published_at,
    }
    articles = [article]
    if extra_articles:
        articles.extend(extra_articles)
    payload = {"articles": {"all_period": articles}}
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _setup_account(root: Path, slug: str = "acct-a", name: str | None = None) -> Path:
    accounts_store.create_account(root, slug, name or slug)
    return accounts_store.get_account_dir(root, slug)


def _review_rc(*cli_args: str) -> int:
    return main_mod.main(list(cli_args))


def _report_path(root: Path, slug: str, topic: str) -> Path:
    return (
        accounts_store.get_account_dir(root, slug)
        / "reports"
        / f"review-{topic}.md"
    )


# ---------------------------------------------------------------------------
# 用例
# ---------------------------------------------------------------------------


def test_no_ledger_returns_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup_account(tmp_path, "acct-a")
    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    out = capsys.readouterr().out
    assert rc == 1
    assert "未发布过" in out


def test_achieved_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    acct = _setup_account(tmp_path, "acct-a", name="账号A")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(
        acct,
        "t1",
        expected_section=(
            "## 预期指标\n"
            "\n"
            "- 预计阅读：100-500\n"
            "- 预计完读：≥ 60%\n"
            "- 核心验证点：教程体是否更高完读\n"
        ),
    )
    _write_report_json(acct, title="测试文章标题", reads=300, is_immature=False)

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    out = capsys.readouterr().out
    assert rc == 0
    report = _report_path(tmp_path, "acct-a", "t1")
    assert report.is_file()
    text = report.read_text(encoding="utf-8")
    assert "达成" in text
    assert "实际数据" in text
    assert "预期对照" in text
    assert "✓" in out or "review-t1.md" in out


def test_reads_below_range_deviation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(
        acct,
        "t1",
        expected_section=(
            "## 预期指标\n"
            "\n"
            "- 预计阅读：100-500\n"
            "- 预计完读：≥ 60%\n"
            "- 核心验证点：x\n"
        ),
    )
    _write_report_json(acct, title="测试文章标题", reads=50, is_immature=False)

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    assert rc == 0
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    assert "偏差" in text


def test_missing_report_json_data_not_ready(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(acct, "t1")

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    out = capsys.readouterr().out
    assert rc == 0
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    assert "数据未就绪" in text
    assert "实际数据" not in text
    assert "预期对照" not in text
    assert "数据未就绪" in out


def test_immature_article_data_not_ready(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(acct, "t1")
    _write_report_json(acct, title="测试文章标题", reads=300, is_immature=True)

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    assert rc == 0
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    assert "数据未就绪" in text
    assert "48h" in text or "T+3" in text


def test_title_mismatch_data_not_ready(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(acct, "t1")
    _write_report_json(acct, title="完全不同的另一篇", reads=300, is_immature=False)

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    assert rc == 0
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    assert "数据未就绪" in text
    assert "未覆盖" in text or "明日" in text


def test_no_topic_card_basics_and_actuals(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(
        acct,
        "t1",
        title="测试文章标题",
        drafted_at="2026-07-28T09:00:00+08:00",
        content_image_count=2,
    )
    # 故意不写 card.md
    _write_report_json(acct, title="测试文章标题", reads=300, is_immature=False)

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    out = capsys.readouterr().out
    assert rc == 0
    assert "无选题卡" in out or "跳过预期" in out
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    assert "账号：acct-a" in text
    assert "草稿创建" in text
    assert "图片数" in text
    assert "实际数据" in text
    assert "| 阅读 | 300 |" in text
    assert "预期对照" not in text


def test_completion_rate_manual_no_fabricated_number(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(
        acct,
        "t1",
        expected_section=(
            "## 预期指标\n"
            "\n"
            "- 预计阅读：100-500\n"
            "- 预计完读：≥ 60%\n"
            "- 核心验证点：x\n"
        ),
    )
    _write_report_json(acct, title="测试文章标题", reads=300, is_immature=False)

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    assert rc == 0
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    assert "人工" in text
    # 不得把完读率编成具体百分比数字出现在实际列
    assert "| 预计完读" in text or "预计完读" in text
    # 实际列应为 —，不应出现编造完读如 60% 作为实际值
    for line in text.splitlines():
        if "预计完读" in line and "|" in line:
            # 表格行：| 预计完读：… | — | 人工… |
            parts = [p.strip() for p in line.split("|") if p.strip() != ""]
            if len(parts) >= 2:
                assert parts[1] == "—" or parts[1] == "-"


def test_never_writes_persona(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(acct, "t1")
    _write_report_json(acct, title="测试文章标题", reads=300, is_immature=False)

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    assert rc == 0
    persona = acct / "persona.md"
    assert not persona.exists()

    src = (
        _PLUGIN_ROOT / "scripts" / "cli" / "review_cmd.py"
    ).read_text(encoding="utf-8")
    assert "persona.md" not in src


def test_custom_zaikan_threshold_achieved(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(
        acct,
        "t1",
        expected_section=(
            "## 预期指标\n"
            "\n"
            "- 预计阅读：100-500\n"
            "- 预计完读：≥ 60%\n"
            "- 核心验证点：x\n"
            "- 预计在看：≥ 3\n"
        ),
    )
    _write_report_json(
        acct, title="测试文章标题", reads=300, zaikan=5, is_immature=False
    )

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    assert rc == 0
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    assert "预计在看" in text
    assert "达成" in text
    # 在看行应显示实际 5
    assert any(
        "在看" in line and "5" in line and "达成" in line
        for line in text.splitlines()
    )


def test_share_rate_real_scale(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """share_rate 为小数比例 0.0238 → 展示 2.4%，不得显示 0.0%。"""
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(
        acct,
        "t1",
        expected_section=(
            "## 预期指标\n"
            "\n"
            "- 预计阅读：100-500\n"
            "- 预计完读：≥ 60%\n"
            "- 核心验证点：x\n"
        ),
    )
    _write_report_json(
        acct,
        title="测试文章标题",
        reads=210,
        shares=5,
        share_rate=0.0238,
        is_immature=False,
    )

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    assert rc == 0
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    assert "2.4%" in text
    assert "0.0%" not in text
    assert "| 转发率 | 2.4% |" in text


def test_all_placeholder_card(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """预期指标三行原样占位符 → 待人工判断 + 尚未填写提示，不含「达成」。"""
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(
        acct,
        "t1",
        expected_section=(
            "## 预期指标\n"
            "\n"
            "- 预计阅读：{{对标本号中位数给区间，例：200-400}}\n"
            "- 预计完读：{{例：≥ 60%}}\n"
            "- 核心验证点：{{这篇想验证什么假设，例：教程体在本号是否比观点体完读更高}}\n"
        ),
    )
    _write_report_json(
        acct,
        title="测试文章标题",
        reads=210,
        shares=5,
        share_rate=0.0238,
        is_immature=False,
    )

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    out = capsys.readouterr().out
    assert rc == 0
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    assert "待人工判断" in text
    assert "尚未填写" in text
    assert "选题卡预期指标尚未填写（全部为占位符），本次无机器可判定项。" in text
    # 防回归：原 bug 结论头为「达成（…」；_summary_line 合法文案含「0 项达成」故不能裸断言 not in「达成」
    assert re.search(r"(?m)^达成（", text) is None
    assert re.search(r"(?m)^待人工判断（", text) is not None
    assert "✅ 达成" not in text
    assert "选题卡未填写（占位符未替换）" in text
    assert "尚未填写" in out


def test_mixed_card_filled_and_placeholder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """阅读已填 + 验证点仍占位符 → 阅读机器判定，验证点标未填写。"""
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(
        acct,
        "t1",
        expected_section=(
            "## 预期指标\n"
            "\n"
            "- 预计阅读：100-500\n"
            "- 预计完读：≥ 60%\n"
            "- 核心验证点：{{这篇想验证什么假设，例：教程体在本号是否比观点体完读更高}}\n"
        ),
    )
    _write_report_json(
        acct, title="测试文章标题", reads=300, is_immature=False
    )

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    assert rc == 0
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    # 阅读行达成
    assert any(
        "预计阅读" in line and "300" in line and "达成" in line
        for line in text.splitlines()
    )
    # 验证点未填写
    assert any(
        "核心验证点" in line and "未填写" in line
        for line in text.splitlines()
    )
    assert "达成（机器可判定 1 项中 1 项达成" in text
    # 混合卡不应出「全部为占位符」提示
    assert "全部为占位符" not in text


def test_placeholder_example_numbers_not_parsed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """占位符说明文字里的示例 200-400 不得被当成真实区间（reads=210 防回归）。"""
    acct = _setup_account(tmp_path, "acct-a")
    _write_ledger(acct, "t1", title="测试文章标题")
    _write_card(
        acct,
        "t1",
        expected_section=(
            "## 预期指标\n"
            "\n"
            "- 预计阅读：{{对标本号中位数给区间，例：200-400}}\n"
            "- 预计完读：{{例：≥ 60%}}\n"
            "- 核心验证点：{{这篇想验证什么假设}}\n"
        ),
    )
    _write_report_json(
        acct,
        title="测试文章标题",
        reads=210,
        shares=5,
        share_rate=0.0238,
        is_immature=False,
    )

    rc = _review_rc("review", "--topic", "t1", "--account", "acct-a")
    assert rc == 0
    text = _report_path(tmp_path, "acct-a", "t1").read_text(encoding="utf-8")
    assert "✅ 达成" not in text
    assert "选题卡未填写（占位符未替换）" in text
