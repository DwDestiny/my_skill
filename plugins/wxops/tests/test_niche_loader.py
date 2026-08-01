# GEB-L3
# Input: 内置 niches / tmp WXOPS_HOME 覆盖与坏包 fixture
# Output: niche_loader 解析序、校验、懒加载行为断言
# Pos: plugins/wxops/tests/test_niche_loader.py
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from analyze import niche_loader
from analyze.niche_loader import (
    NicheLoadError,
    get_active,
    load_niche,
    reset_active,
    set_active,
)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
BUILTIN_AI = PLUGIN_ROOT / "niches" / "ai-tools" / "niche.json"
BUILTIN_GENERIC = PLUGIN_ROOT / "niches" / "_generic" / "niche.json"


@pytest.fixture(autouse=True)
def _isolate_active_and_home(tmp_path, monkeypatch):
    """每测隔离：WXOPS_HOME=tmp，清空 active，不碰真实 ~/.wxops。"""
    monkeypatch.setenv("WXOPS_HOME", str(tmp_path))
    reset_active()
    yield
    reset_active()


def _write_niche(home: Path, niche_id: str, data: dict) -> Path:
    p = home / "niches" / niche_id / "niche.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _base_valid_ai_tools() -> dict:
    return json.loads(BUILTIN_AI.read_text(encoding="utf-8"))


def test_load_ai_tools_and_generic_ok():
    ai = load_niche("ai-tools")
    assert ai.id == "ai-tools"
    assert ai.name == "AI 工具与编程"
    assert ai.requested_id == "ai-tools"
    assert len(ai.content_type_names) == 6
    assert "风险/账号/额度焦虑" in ai.content_type_names

    gen = load_niche("_generic")
    assert gen.id == "_generic"
    assert gen.content_types.rules == []
    assert gen.content_type_names == ["综合内容"]
    assert gen.pain_point_names == ["读者关注与谈资"]
    assert gen.persona_names == ["大盘读者"]
    assert gen.title_patterns.risk.terms == []
    assert gen.title_patterns.release.subject_terms == []
    assert gen.title_patterns.release.action_terms == []


def test_user_home_override_wins(tmp_path):
    data = _base_valid_ai_tools()
    data["name"] = "用户覆盖 AI 工具"
    data["content_types"]["names"] = list(data["content_types"]["names"]) + ["用户自定义题材"]
    # fallback.type 仍在 names 里；补一条 names 后 rules 仍合法
    data["content_types"]["names"] = [
        "风险/账号/额度焦虑",
        "价格/额度/羊毛情报",
        "模型发布/能力解读",
        "AI 编程/Agent 工作流",
        "产品/副业/商业化",
        "泛 AI 热点/效率工具",
        "用户自定义题材",
    ]
    _write_niche(tmp_path, "ai-tools", data)

    spec = load_niche("ai-tools")
    assert spec.name == "用户覆盖 AI 工具"
    assert "用户自定义题材" in spec.content_type_names
    # 确认不是内置包
    builtin = json.loads(BUILTIN_AI.read_text(encoding="utf-8"))
    assert builtin["name"] != "用户覆盖 AI 工具"


def test_missing_id_falls_back_to_generic(tmp_path, capsys):
    spec = load_niche("no-such-niche-xyz")
    err = capsys.readouterr().err
    assert "⚠ 未找到赛道包 no-such-niche-xyz，已回落 _generic 通用兜底" in err
    assert spec.id == "_generic"
    assert spec.requested_id == "no-such-niche-xyz"


def test_bad_package_missing_names(tmp_path):
    data = _base_valid_ai_tools()
    del data["content_types"]["names"]
    path = _write_niche(tmp_path, "bad-names", data)
    # 改 id 与目录一致
    data["id"] = "bad-names"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(NicheLoadError) as ei:
        load_niche("bad-names")
    msg = str(ei.value)
    assert str(path.resolve()) in msg or str(path) in msg
    assert "content_types.names" in msg


def test_bad_package_mapped_value_not_in_names(tmp_path):
    data = _base_valid_ai_tools()
    data["id"] = "bad-map"
    data["pain_points"]["by_content_type"]["风险/账号/额度焦虑"] = "不存在的痛点"
    path = _write_niche(tmp_path, "bad-map", data)
    with pytest.raises(NicheLoadError) as ei:
        load_niche("bad-map")
    msg = str(ei.value)
    assert str(path.resolve()) in msg or str(path) in msg
    assert "pain_points.by_content_type 值" in msg or "pain_points.names" in msg


def test_bad_package_title_pattern_keys_set_mismatch(tmp_path):
    data = _base_valid_ai_tools()
    data["id"] = "bad-keys"
    data["title_patterns"]["keys"] = list(data["title_patterns"]["keys"])[:-1]  # 少一项
    path = _write_niche(tmp_path, "bad-keys", data)
    with pytest.raises(NicheLoadError) as ei:
        load_niche("bad-keys")
    msg = str(ei.value)
    assert str(path.resolve()) in msg or str(path) in msg
    assert "title_patterns.keys" in msg


def test_bad_package_invalid_title_regex(tmp_path):
    data = _base_valid_ai_tools()
    data["id"] = "bad-regex"
    data["content_types"]["fallback"]["title_regex"] = "(unclosed"
    path = _write_niche(tmp_path, "bad-regex", data)
    with pytest.raises(NicheLoadError) as ei:
        load_niche("bad-regex")
    msg = str(ei.value)
    assert str(path.resolve()) in msg or str(path) in msg
    assert "title_regex" in msg


def test_bad_package_schema_version(tmp_path):
    data = _base_valid_ai_tools()
    data["id"] = "bad-ver"
    data["niche_schema_version"] = 99
    path = _write_niche(tmp_path, "bad-ver", data)
    with pytest.raises(NicheLoadError) as ei:
        load_niche("bad-ver")
    msg = str(ei.value)
    assert str(path.resolve()) in msg or str(path) in msg
    assert "niche_schema_version" in msg


def test_get_active_lazy_loads_ai_tools():
    assert niche_loader._active is None
    spec = get_active()
    assert spec.id == "ai-tools"
    assert spec.requested_id == "ai-tools"
    # 再次 get 返回同一实例
    assert get_active() is spec


def test_set_active_overrides_lazy_default():
    gen = load_niche("_generic")
    set_active(gen)
    assert get_active().id == "_generic"


def test_unknown_top_and_group_fields_warn(tmp_path, capsys):
    """契约 §8：顶层 + 组内未知字段 → 警告后忽略，包仍可加载。"""
    data = _base_valid_ai_tools()
    data["id"] = "unk-fields"
    data["schema_extra"] = {"x": 1}
    data["title_patterns"]["experimental"] = False
    data["title_patterns"]["slots"]["risk"]["color"] = "red"
    path = _write_niche(tmp_path, "unk-fields", data)
    spec = load_niche("unk-fields")
    assert spec.id == "unk-fields"
    err = capsys.readouterr().err
    assert f"赛道包 {path}" in err or "含未知字段" in err
    assert "schema_extra" in err
    assert "experimental" in err or "title_patterns.experimental" in err
    assert "color" in err or "risk.color" in err
