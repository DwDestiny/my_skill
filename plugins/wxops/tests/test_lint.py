# GEB-L3
# Input: tmp_path 隔离 WXOPS_HOME + 自造 compliance.json / 假账号；不碰 ~/.wxops、不起浏览器
# Output: lint 引擎三种 match / exclude / unless / softeners / 行号 / 退出码 / 三层回落 / schema 校验
# Pos: plugins/wxops/tests/test_lint.py
"""稿件合规闸 lint 单测。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from scripts.cli import accounts_store  # noqa: E402
from scripts.cli import compliance_lib  # noqa: E402
from scripts.cli import lint_cmd  # noqa: E402
from scripts.cli import main as main_mod  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_wxops_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WXOPS_HOME", str(tmp_path))


def _write_compliance(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _base_spec(**overrides) -> dict:
    data = {
        "compliance_schema_version": 1,
        "id": "fixture",
        "name": "测试合规包",
        "softeners": ["有助于", "可能"],
        "rules": [],
    }
    data.update(overrides)
    return data


def _rule(rid: str, level: str, title: str, match: dict, **kw) -> dict:
    return {
        "id": rid,
        "level": level,
        "title": title,
        "why": kw.get("why", f"为什么-{rid}"),
        "fix": kw.get("fix", f"怎么改-{rid}"),
        "match": match,
    }


def _setup_account(root: Path, slug: str = "demo", niche: str = "fixture") -> None:
    accounts_store.create_account(root, slug, "演示号", niche=niche)


def _load_user_spec(root: Path, niche: str, data: dict) -> compliance_lib.ComplianceSpec:
    path = _write_compliance(root / "niches" / niche / "compliance.json", data)
    return compliance_lib.load_compliance(path, layer="用户包", niche_shown=niche)


# ---------------------------------------------------------------------------
# 三种 match 类型
# ---------------------------------------------------------------------------


class TestMatchTypes:
    def test_terms_regex_cooccur_each_once(self, tmp_path: Path) -> None:
        data = _base_spec(
            rules=[
                _rule(
                    "disease-name",
                    "BLOCK",
                    "疾病名",
                    {"type": "terms", "terms": ["高血压", "糖尿病"]},
                ),
                _rule(
                    "unsourced",
                    "BLOCK",
                    "无出处",
                    {
                        "type": "regex",
                        "scope": "sentence",
                        "patterns": ["研究表明"],
                        "unless": ["《", "指南"],
                    },
                ),
                _rule(
                    "efficacy",
                    "BLOCK",
                    "功效",
                    {
                        "type": "cooccur",
                        "scope": "sentence",
                        "strip_softeners": False,
                        "left": ["降", "缓解"],
                        "right": ["血压", "血糖"],
                    },
                ),
            ]
        )
        spec = _load_user_spec(tmp_path, "fixture", data)
        text = "第一行无事。\n研究表明有效。\n这道菜能降血压。"
        # 注意：第三句有 降×血压 cooccur；没有 terms 的病名
        # 补病名到另一行
        text = "高血压要注意。\n研究表明有效。\n这道菜能降血压。"
        hits = compliance_lib.scan_text(spec, text)
        ids = {h.rule_id for h in hits}
        assert "disease-name" in ids
        assert "unsourced" in ids
        assert "efficacy" in ids
        assert len(hits) == 3


# ---------------------------------------------------------------------------
# exclude_matches：老毛病 不中，荔枝病 中（同一用例）
# ---------------------------------------------------------------------------


class TestExcludeMatches:
    def test_exclude_and_real_disease_same_doc(self, tmp_path: Path) -> None:
        data = _base_spec(
            rules=[
                _rule(
                    "disease-suffix",
                    "BLOCK",
                    "疾病后缀",
                    {
                        "type": "regex",
                        "patterns": [r"[\u4e00-\u9fa5]{1,5}(病|症)"],
                        "exclude_matches": ["毛病", "老毛病"],
                    },
                )
            ]
        )
        spec = _load_user_spec(tmp_path, "fixture", data)
        # 「老毛病」整段命中后被 exclude 丢掉；继续扫，最终因「荔枝病」落命中
        # （pattern 贪心时 matched 可能是「又查出荔枝病」，关键是规则命中且不是老毛病）
        text = "老毛病反复。又查出荔枝病。"
        hits = compliance_lib.scan_text(spec, text)
        assert len(hits) == 1
        assert "荔枝病" in hits[0].matched
        assert hits[0].matched not in ("毛病", "老毛病")

        # 仅有被排除词时整篇不命中
        hits_only = compliance_lib.scan_text(spec, "老毛病反复发作而已。")
        assert hits_only == []


# ---------------------------------------------------------------------------
# unless
# ---------------------------------------------------------------------------


class TestUnless:
    def test_unless_blocks_when_in_same_sentence(self, tmp_path: Path) -> None:
        data = _base_spec(
            rules=[
                _rule(
                    "unsourced-claim",
                    "BLOCK",
                    "无出处",
                    {
                        "type": "regex",
                        "scope": "sentence",
                        "patterns": ["研究表明"],
                        "unless": ["《", "指南"],
                    },
                )
            ]
        )
        spec = _load_user_spec(tmp_path, "fixture", data)

        hits_bare = compliance_lib.scan_text(spec, "研究表明这样吃更好。")
        assert len(hits_bare) == 1
        assert hits_bare[0].matched == "研究表明"

        hits_shield = compliance_lib.scan_text(
            spec, "《中国居民膳食指南（2022）》研究表明这样吃更好。"
        )
        assert hits_shield == []


# ---------------------------------------------------------------------------
# strip_softeners
# ---------------------------------------------------------------------------


class TestStripSofteners:
    def test_softener_stripped_then_cooccur(self, tmp_path: Path) -> None:
        data = _base_spec(
            softeners=["有助于", "可能"],
            rules=[
                _rule(
                    "efficacy-claim",
                    "BLOCK",
                    "功效宣称",
                    {
                        "type": "cooccur",
                        "scope": "sentence",
                        "strip_softeners": True,
                        "left": ["降"],
                        "right": ["血压"],
                    },
                )
            ]
        )
        spec = _load_user_spec(tmp_path, "fixture", data)
        # 抹掉「有助于」后「降」×「血压」共现
        hits = compliance_lib.scan_text(spec, "每天喝这个有助于降血压。")
        assert len(hits) == 1
        assert hits[0].matched == "降×血压"


# ---------------------------------------------------------------------------
# scope: sentence —— unless 在另一句不救场
# ---------------------------------------------------------------------------


class TestSentenceScope:
    def test_unless_in_other_sentence_does_not_shield(self, tmp_path: Path) -> None:
        data = _base_spec(
            rules=[
                _rule(
                    "unsourced-claim",
                    "BLOCK",
                    "无出处",
                    {
                        "type": "regex",
                        "scope": "sentence",
                        "patterns": ["研究表明"],
                        "unless": ["《", "指南"],
                    },
                )
            ]
        )
        spec = _load_user_spec(tmp_path, "fixture", data)
        text = "请参考《中国居民膳食指南》。研究表明这样吃更好。"
        hits = compliance_lib.scan_text(spec, text)
        assert len(hits) == 1
        assert hits[0].matched == "研究表明"


# ---------------------------------------------------------------------------
# 每规则每篇只报一次
# ---------------------------------------------------------------------------


class TestOncePerRule:
    def test_multiple_terms_only_first(self, tmp_path: Path) -> None:
        data = _base_spec(
            rules=[
                _rule(
                    "disease-name",
                    "BLOCK",
                    "疾病名",
                    {"type": "terms", "terms": ["高血压", "糖尿病", "痛风"]},
                )
            ]
        )
        spec = _load_user_spec(tmp_path, "fixture", data)
        text = "高血压要注意。\n糖尿病也要。\n痛风同样。"
        hits = compliance_lib.scan_text(spec, text)
        assert len(hits) == 1
        assert hits[0].matched == "高血压"


# ---------------------------------------------------------------------------
# YAML frontmatter 跳过但行号保留
# ---------------------------------------------------------------------------


class TestFrontmatter:
    def test_frontmatter_skipped_line_numbers_original(self, tmp_path: Path) -> None:
        data = _base_spec(
            rules=[
                _rule(
                    "disease-name",
                    "BLOCK",
                    "疾病名",
                    {"type": "terms", "terms": ["高血压"]},
                )
            ]
        )
        spec = _load_user_spec(tmp_path, "fixture", data)
        text = "---\ntitle: 测试\nniche: health\n---\n\n正文提到高血压要小心。\n"
        hits = compliance_lib.scan_text(spec, text)
        assert len(hits) == 1
        # 行：1--- 2title 3niche 4--- 5空 6正文 → 高血压在第 6 行
        assert hits[0].line == 6

        # frontmatter 内的词不命中
        text_fm = "---\ntitle: 高血压专题\n---\n\n今天讲时令菜。\n"
        hits_fm = compliance_lib.scan_text(spec, text_fm)
        assert hits_fm == []


# ---------------------------------------------------------------------------
# 退出码 0/1/2
# ---------------------------------------------------------------------------


class TestExitCodes:
    def test_exit_0_1_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        _setup_account(root, "demo", niche="fixture")
        data = _base_spec(
            rules=[
                _rule(
                    "disease-name",
                    "BLOCK",
                    "疾病名",
                    {"type": "terms", "terms": ["高血压"]},
                ),
                _rule(
                    "soft-fear",
                    "WARN",
                    "软恐吓",
                    {"type": "terms", "terms": ["千万别"]},
                ),
            ]
        )
        _write_compliance(root / "niches" / "fixture" / "compliance.json", data)

        # 0：无命中
        rc = lint_cmd.run(root, account="demo", text="今天菜市场人真多")
        assert rc == 0

        # 0：仅 WARN
        rc = lint_cmd.run(root, account="demo", text="千万别空腹喝冰水")
        assert rc == 0

        # 1：有 BLOCK
        rc = lint_cmd.run(root, account="demo", text="高血压的人注意")
        assert rc == 1

        # 2：账号不存在
        rc = lint_cmd.run(root, account="no-such", text="x")
        assert rc == 2

        # 2：无输入
        rc = lint_cmd.run(root, account="demo")
        assert rc == 2


# ---------------------------------------------------------------------------
# 三层回落
# ---------------------------------------------------------------------------


class TestThreeLayerFallback:
    def test_user_over_builtin_over_generic(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = tmp_path
        # 伪造 skill_dir 内置包
        fake_skill = tmp_path / "fake_skill"
        builtin = fake_skill / "niches" / "demo-niche" / "compliance.json"
        generic = fake_skill / "niches" / "_generic" / "compliance.json"
        _write_compliance(
            builtin,
            _base_spec(
                id="demo-niche",
                name="内置",
                rules=[
                    _rule(
                        "builtin-only",
                        "BLOCK",
                        "内置词",
                        {"type": "terms", "terms": ["内置标记词XYZ"]},
                    )
                ],
            ),
        )
        _write_compliance(
            generic,
            _base_spec(
                id="_generic",
                name="通用",
                rules=[
                    _rule(
                        "generic-only",
                        "BLOCK",
                        "通用词",
                        {"type": "terms", "terms": ["通用标记词ABC"]},
                    )
                ],
            ),
        )
        monkeypatch.setattr(
            "scripts.cli.env.get_skill_dir", lambda: fake_skill
        )
        # 也要让 compliance_lib 通过 env 拿到——lint 用 env.get_skill_dir
        from scripts.cli import env as env_mod

        monkeypatch.setattr(env_mod, "get_skill_dir", lambda: fake_skill)

        _setup_account(root, "demo", niche="demo-niche")

        # 1) 无用户包 → 内置
        rc = lint_cmd.run(root, account="demo", text="这里有内置标记词XYZ")
        assert rc == 1
        rc = lint_cmd.run(root, account="demo", text="这里有通用标记词ABC")
        assert rc == 0  # 内置包没有这条

        # 2) 用户包覆盖
        _write_compliance(
            root / "niches" / "demo-niche" / "compliance.json",
            _base_spec(
                id="demo-niche",
                name="用户",
                rules=[
                    _rule(
                        "user-only",
                        "BLOCK",
                        "用户词",
                        {"type": "terms", "terms": ["用户标记词UVW"]},
                    )
                ],
            ),
        )
        rc = lint_cmd.run(root, account="demo", text="这里有用户标记词UVW")
        assert rc == 1
        rc = lint_cmd.run(root, account="demo", text="这里有内置标记词XYZ")
        assert rc == 0  # 用户包不含内置词

        # 3) 未知赛道 → 通用兜底
        accounts_store.create_account(root, "other", "另一号", niche="no-such-niche")
        rc = lint_cmd.run(root, account="other", text="这里有通用标记词ABC")
        assert rc == 1


# ---------------------------------------------------------------------------
# schema 校验
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_version_level_required_match_type(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"

        # version ≠ 1
        _write_compliance(
            path,
            _base_spec(compliance_schema_version=2, rules=[]),
        )
        with pytest.raises(compliance_lib.ComplianceLoadError, match="compliance_schema_version"):
            compliance_lib.load_compliance(path, layer="用户包", niche_shown="x")

        # level 非法
        _write_compliance(
            path,
            _base_spec(
                rules=[
                    _rule(
                        "x",
                        "ERROR",  # type: ignore[arg-type]
                        "坏",
                        {"type": "terms", "terms": ["a"]},
                    )
                ]
            ),
        )
        # 直接构造会过 _rule 的 type 检查；手动写
        bad = _base_spec(
            rules=[
                {
                    "id": "x",
                    "level": "ERROR",
                    "title": "坏",
                    "why": "w",
                    "fix": "f",
                    "match": {"type": "terms", "terms": ["a"]},
                }
            ]
        )
        _write_compliance(path, bad)
        with pytest.raises(compliance_lib.ComplianceLoadError, match="level"):
            compliance_lib.load_compliance(path, layer="用户包", niche_shown="x")

        # 缺必填
        bad2 = {
            "compliance_schema_version": 1,
            "id": "x",
            # 缺 name
            "softeners": [],
            "rules": [],
        }
        _write_compliance(path, bad2)
        with pytest.raises(compliance_lib.ComplianceLoadError, match="name"):
            compliance_lib.load_compliance(path, layer="用户包", niche_shown="x")

        # match.type 未知
        bad3 = _base_spec(
            rules=[
                {
                    "id": "x",
                    "level": "BLOCK",
                    "title": "t",
                    "why": "w",
                    "fix": "f",
                    "match": {"type": "magic", "terms": ["a"]},
                }
            ]
        )
        _write_compliance(path, bad3)
        with pytest.raises(compliance_lib.ComplianceLoadError, match="match.type"):
            compliance_lib.load_compliance(path, layer="用户包", niche_shown="x")

    def test_cli_schema_error_exit_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        _setup_account(root, "demo", niche="fixture")
        _write_compliance(
            root / "niches" / "fixture" / "compliance.json",
            _base_spec(compliance_schema_version=99, rules=[]),
        )
        rc = lint_cmd.run(root, account="demo", text="hello")
        assert rc == 2
        err = capsys.readouterr().out
        assert "校验失败" in err or "compliance_schema_version" in err


# ---------------------------------------------------------------------------
# CLI 接线：main + --json
# ---------------------------------------------------------------------------


class TestCliWiring:
    def test_main_lint_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        _setup_account(root, "demo", niche="fixture")
        _write_compliance(
            root / "niches" / "fixture" / "compliance.json",
            _base_spec(
                rules=[
                    _rule(
                        "disease-name",
                        "BLOCK",
                        "疾病名",
                        {"type": "terms", "terms": ["高血压"]},
                    )
                ]
            ),
        )
        rc = main_mod.main(
            ["lint", "--account", "demo", "--text", "高血压注意", "--json"]
        )
        assert rc == 1
        out = capsys.readouterr().out
        payload = json.loads(out)
        assert payload["verdict"] == "BLOCK"
        assert payload["counts"]["BLOCK"] == 1
        assert payload["hits"][0]["rule_id"] == "disease-name"

    def test_draft_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = tmp_path
        _setup_account(root, "demo", niche="fixture")
        _write_compliance(
            root / "niches" / "fixture" / "compliance.json",
            _base_spec(rules=[]),
        )
        draft = tmp_path / "draft.md"
        draft.write_text("# 标题\n\n正文无风险。\n", encoding="utf-8")
        rc = lint_cmd.run(root, account="demo", draft=str(draft))
        assert rc == 0
