# GEB-L3
# Input: tmp_path 隔离 WXOPS_HOME + 自造 wechat-ops-report-*.json；不碰真实账号数据
# Output: dedup bigram Jaccard 三档 / object 窗口 / summary 排除 / 只读 stable
# Pos: plugins/wxops/tests/test_dedup.py
"""选题去重闸 dedup 单测。"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import dedup_cmd  # noqa: E402
from scripts.cli import main as main_mod  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_wxops_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WXOPS_HOME", str(tmp_path))


def _setup(root: Path, slug: str = "demo", niche: str = "health") -> Path:
    accounts_store.create_account(root, slug, "演示号", niche=niche)
    out = accounts_store.get_account_dir(root, slug) / "output"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _write_report(
    output_dir: Path,
    name: str,
    stable: list[dict],
    *,
    deleted: list[dict] | None = None,
    mtime: float | None = None,
) -> Path:
    payload = {
        "articles": {
            "all_period": stable,
            "stable": stable,
            "immature": [],
            "deleted": deleted or [],
        }
    }
    path = output_dir / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    if mtime is not None:
        # 两参 utime
        import os

        os.utime(path, (mtime, mtime))
    return path


def _art(
    title: str,
    *,
    date_s: str = "2026-06-01",
    digest: str = "",
    url: str = "https://mp.weixin.qq.com/s/fake",
    reads: int = 1,
) -> dict:
    return {
        "title": title,
        "digest": digest,
        "url": url,
        "published_at": date_s,
        "reads": reads,
    }


class TestSimilarity:
    def test_block_high_sim(self, tmp_path: Path) -> None:
        out = _setup(tmp_path)
        base = "隔夜菜到底能不能吃我查了国标之后的结论"
        # 只差几个字 → sim 应 ≥ 0.75
        near = "隔夜菜到底能不能吃我查了国标后的结论"
        sim = dedup_cmd.jaccard_sim(base, near)
        assert sim >= 0.75, f"sim={sim}"
        _write_report(
            out,
            "wechat-ops-report-2026-08-01.json",
            [_art(near, date_s="2026-05-01")],
        )
        rc_verdict = dedup_cmd.evaluate(base, dedup_cmd.load_stable_articles(out / "wechat-ops-report-2026-08-01.json"))
        assert rc_verdict[0] == "BLOCK"

        rc = dedup_cmd.run(
            tmp_path, account="demo", title=base, as_json=True
        )
        assert rc == 1

    def test_warn_mid_sim(self, tmp_path: Path) -> None:
        out = _setup(tmp_path)
        published = "隔夜菜能不能吃其实答案并不简单"
        query = "隔夜菜能不能吃其实答案很简单"
        sim = dedup_cmd.jaccard_sim(query, published)
        assert 0.45 <= sim < 0.75, f"sim={sim}，请调标题使落在 WARN 区"
        _write_report(
            out,
            "wechat-ops-report-2026-08-01.json",
            [_art(published, date_s="2026-05-28")],
        )
        verdict, matches = dedup_cmd.evaluate(
            query,
            dedup_cmd.load_stable_articles(out / "wechat-ops-report-2026-08-01.json"),
        )
        assert verdict == "WARN"
        assert matches
        rc = dedup_cmd.run(tmp_path, account="demo", title=query)
        assert rc == 0  # WARN 不阻塞

    def test_object_hit_low_sim_warn(self, tmp_path: Path) -> None:
        out = _setup(tmp_path)
        published = "夏天冰箱里的剩菜如何处理更安心"
        query = "周末聚餐后如何安排饮食更轻松"
        sim = dedup_cmd.jaccard_sim(query, published)
        assert sim < 0.45, f"sim={sim} 应低于 0.45"
        today = date(2026, 8, 6)
        _write_report(
            out,
            "wechat-ops-report-2026-08-01.json",
            [
                _art(
                    published,
                    date_s="2026-06-01",
                    digest="聊聊隔夜菜的存放与加热习惯",
                )
            ],
        )
        arts = dedup_cmd.load_stable_articles(out / "wechat-ops-report-2026-08-01.json")
        verdict, matches = dedup_cmd.evaluate(
            query, arts, object_term="隔夜菜", today=today
        )
        assert verdict == "WARN"
        assert matches[0].reason == "object"
        rc = dedup_cmd.run(
            tmp_path,
            account="demo",
            title=query,
            object_term="隔夜菜",
            today=today,
        )
        assert rc == 0

    def test_unrelated_pass(self, tmp_path: Path) -> None:
        out = _setup(tmp_path)
        _write_report(
            out,
            "wechat-ops-report-2026-08-01.json",
            [_art("三伏天这三样菜清爽不腻", date_s="2026-07-01")],
        )
        query = "通勤路上怎么用耳机学英语更高效"
        verdict, matches = dedup_cmd.evaluate(
            query,
            dedup_cmd.load_stable_articles(out / "wechat-ops-report-2026-08-01.json"),
            today=date(2026, 8, 6),
        )
        assert verdict == "PASS"
        assert matches == []
        rc = dedup_cmd.run(tmp_path, account="demo", title=query)
        assert rc == 0

    def test_object_older_than_180_pass(self, tmp_path: Path) -> None:
        out = _setup(tmp_path)
        today = date(2026, 8, 6)
        old = (today - timedelta(days=200)).isoformat()
        published = "冰箱收纳的五个小习惯"
        query = "客厅收纳如何更省事"
        sim = dedup_cmd.jaccard_sim(query, published)
        assert sim < 0.45, f"sim={sim}"
        _write_report(
            out,
            "wechat-ops-report-2026-08-01.json",
            [_art(published, date_s=old, digest="关于隔夜菜的长期讨论归档")],
        )
        arts = dedup_cmd.load_stable_articles(out / "wechat-ops-report-2026-08-01.json")
        verdict, _ = dedup_cmd.evaluate(
            query, arts, object_term="隔夜菜", today=today
        )
        assert verdict == "PASS"


class TestLibrarySelection:
    def test_prefer_json_over_summary(self, tmp_path: Path) -> None:
        out = _setup(tmp_path)
        # summary 更新（mtime 更大）但应被排除
        full = _write_report(
            out,
            "wechat-ops-report-2026-08-01.json",
            [_art("完整库标题甲乙丙丁戊己庚")],
            mtime=time.time() - 100,
        )
        summary = out / "wechat-ops-report-2026-08-01.summary.json"
        summary.write_text(
            json.dumps(
                {
                    "articles": {
                        "stable": [_art("摘要库不该被读到的标题")]
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        import os

        os.utime(summary, (time.time(), time.time()))
        chosen = dedup_cmd.find_latest_report(out)
        assert chosen is not None
        assert chosen.name == full.name
        assert ".summary." not in chosen.name

        # 端到端：应命中完整库而非 summary
        query = "完整库标题甲乙丙丁戊己庚"  # 完全相同 → BLOCK
        rc = dedup_cmd.run(tmp_path, account="demo", title=query, as_json=True)
        assert rc == 1

    def test_only_stable_not_deleted(self, tmp_path: Path) -> None:
        out = _setup(tmp_path)
        deleted_title = "已被删除的撞车标题完全一样的字"
        _write_report(
            out,
            "wechat-ops-report-2026-08-01.json",
            stable=[_art("稳定池里的普通标题无关内容")],
            deleted=[_art(deleted_title)],
        )
        # 对 deleted 标题查询 → 不应 BLOCK（deleted 不参与）
        query = deleted_title
        arts = dedup_cmd.load_stable_articles(out / "wechat-ops-report-2026-08-01.json")
        assert all(a.title != deleted_title for a in arts)
        verdict, _ = dedup_cmd.evaluate(query, arts)
        assert verdict == "PASS"

    def test_missing_report_exit_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _setup(tmp_path)
        # 不写 report
        rc = dedup_cmd.run(tmp_path, account="demo", title="任意标题")
        assert rc == 2
        out = capsys.readouterr().out
        assert "analyze" in out or "已发布库" in out


class TestCliWiring:
    def test_main_dedup_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = _setup(tmp_path)
        _write_report(
            out,
            "wechat-ops-report-2026-08-01.json",
            [_art("完全无关的天文观测笔记")],
        )
        rc = main_mod.main(
            [
                "dedup",
                "--account",
                "demo",
                "--title",
                "厨房收纳三个小技巧",
                "--json",
            ]
        )
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["verdict"] == "PASS"
        assert payload["library_size"] == 1


class TestNormalizeAndBigrams:
    def test_normalize_strips_punct_and_space(self) -> None:
        a = dedup_cmd.normalize_title("隔夜菜，能不能吃？")
        b = dedup_cmd.normalize_title("隔夜菜能不能吃")
        assert a == b

    def test_short_string_bigrams(self) -> None:
        assert dedup_cmd.bigrams("中") == {"中"}
        assert dedup_cmd.bigrams("") == set()
        assert "ab" in dedup_cmd.bigrams("abc")
