# GEB-L3
# Input: tmp WXOPS_HOME 赛道包 fixture + m9 合成 features/dataset
# Output: scoring 二阶覆写 / load 期校验 / scoring_source 留痕 / 零覆写等价断言
# Pos: plugins/wxops/tests/test_niche_scoring_override.py
"""issue #74 PR B：赛道包 interaction_thresholds 覆写验收。

临时 niche 包一律写在 tmp_path（WXOPS_HOME），绝不碰真实 ~/.wxops。
"""
from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

import pytest

from analyze.m9_account_type import _score_types, build_account_type
from analyze.niche_loader import NicheLoadError, load_niche, reset_active
from analyze.scoring_thresholds import (
    DEFAULT_INTERACTION_THRESHOLDS,
    INTERACTION_THRESHOLD_FIELDS,
    InteractionThresholds,
    merge_thresholds,
    validate_threshold_overrides,
)
from build_wechat_ops_report import _resolve_interaction_thresholds


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
BUILTIN_AI = PLUGIN_ROOT / "niches" / "ai-tools" / "niche.json"


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


def _mk_article(
    title: str,
    digest: str = "",
    *,
    reads: int = 10000,
    share_rate: float = 0.01,
    comment_rate: float = 0.001,
    like_rate: float = 0.01,
    length: int = 1500,
) -> dict:
    shares = round(reads * share_rate)
    comments = round(reads * comment_rate)
    likes = round(reads * like_rate)
    return {
        "title": title,
        "digest": digest,
        "reads": reads,
        "shares": shares,
        "comments": comments,
        "likes": likes,
        "old_likes": 0,
        "moment_likes": 0,
        "share_rate": share_rate,
        "comment_rate": comment_rate,
        "like_rate": like_rate,
        "article_length_chars": length,
        "content_type": "泛内容",
        "published_at": "2026-06-01T10:00:00+08:00",
    }


def _mk_dataset(articles: list[dict], *, posts_per_week: float = 2.0) -> dict:
    return {
        "articles": {"stable": articles, "all_period": articles},
        "account_profile": {"publish_frequency": posts_per_week},
        "account": {"cumulate_user": 3000},
        "modules": {"audience": {"city": []}},
    }


def _ip_dataset() -> dict:
    """与 test_account_type._ip_dataset 同量级的个人 IP fixture。"""
    arts = [
        _mk_article(
            f"我踩坑一年后的第 {i} 条判断",
            "我的亲历复盘,聊聊我自己的取舍和立场。",
            share_rate=0.03,
            comment_rate=0.0025,
            like_rate=0.009,
            length=1800,
        )
        for i in range(16)
    ]
    return _mk_dataset(arts, posts_per_week=2.0)


# ───────────────────────── 7a 零覆写等价 ─────────────────────────


def test_no_scoring_resolves_to_platform_default():
    """无 scoring 段 → _resolve 返回平台默认实例。"""
    spec = load_niche("ai-tools")
    assert spec.scoring is None
    assert _resolve_interaction_thresholds(spec) == DEFAULT_INTERACTION_THRESHOLDS


def test_build_account_type_default_arg_equals_explicit_default():
    """不传 thresholds 与显式传入 DEFAULT 结果完全相等（含 scoring_source）。"""
    ds = _ip_dataset()
    a = build_account_type(ds)
    b = build_account_type(ds, thresholds=DEFAULT_INTERACTION_THRESHOLDS)
    assert a == b
    assert a["scoring_source"] == {
        "interaction_thresholds": "platform_default",
        "overridden_fields": [],
    }


def test_merge_empty_overrides_equals_base():
    merged = merge_thresholds(DEFAULT_INTERACTION_THRESHOLDS, {})
    assert merged == DEFAULT_INTERACTION_THRESHOLDS


# ───────────────────────── 7b 部分覆写 ─────────────────────────


def test_partial_override_only_touches_named_field(tmp_path):
    data = _base_valid_ai_tools()
    data["id"] = "partial-like"
    data["scoring"] = {"interaction_thresholds": {"like_high": 0.02}}
    _write_niche(tmp_path, "partial-like", data)

    spec = load_niche("partial-like")
    assert spec.scoring is not None
    assert spec.scoring.interaction_thresholds == {"like_high": 0.02}

    merged = _resolve_interaction_thresholds(spec)
    assert merged.like_high == 0.02
    default = DEFAULT_INTERACTION_THRESHOLDS
    for f in fields(InteractionThresholds):
        if f.name == "like_high":
            continue
        assert getattr(merged, f.name) == getattr(default, f.name), f.name


# ───────────────────────── 7c 覆写改变判定 ─────────────────────────


def test_override_changes_personal_ip_score():
    """like_rate 落在默认 like_high 与覆写值之间 → personal_ip 分应不同。

    敏感性：若判据恒不命中，两次结果相等 → 本测变红。
    like=0.012 ∈ (0.008, 0.02)；share 压到 0.01 < share_high_ip，避免 OR 分支掩盖。
    """
    default = DEFAULT_INTERACTION_THRESHOLDS
    override = merge_thresholds(default, {"like_high": 0.02})
    assert default.like_high < 0.012 < override.like_high

    # 最小 features：只测互动分支，其余尽量中性
    f = {
        "posts_per_week": 2.0,
        "first_person_ratio": 0.0,
        "story_ratio": 0.0,
        "hotspot_ratio": 0.5,
        "method_ratio": 0.0,
        "monetization_ratio": 0.0,
        "benefit_ratio": 0.0,
        "org_ratio": 0.0,
        "local_ratio": 0.0,
        "city_top_share": 0.0,
        "median_length": 1000,
        "avg_like_rate": 0.012,
        "avg_comment_rate": 0.0005,
        "avg_share_rate": 0.01,  # < share_high_ip 0.025，不走 share 分支
        "sample_count": 20,
    }
    scores_default = _score_types(f, thresholds=default)
    scores_override = _score_types(f, thresholds=override)
    assert scores_default["personal_ip"] != scores_override["personal_ip"], (
        f"敏感性失效：default={scores_default['personal_ip']} "
        f"override={scores_override['personal_ip']}；"
        "like 分支应在默认阈值命中、覆写后不命中"
    )
    assert scores_default["personal_ip"] > scores_override["personal_ip"]


# ───────────────────────── 7d 非法值 load 期 fail ─────────────────────────


@pytest.mark.parametrize(
    "thresholds, expect_snippet",
    [
        ({"like_high": 0}, "like_high"),
        ({"like_high": 1}, "like_high"),
        ({"like_high": -0.1}, "like_high"),
        ({"like_high": "0.02"}, "like_high"),
        ({"like_high": True}, "like_high"),  # bool 陷阱
        ({"share_dominance_ratio": 0.5}, "share_dominance_ratio"),
    ],
)
def test_illegal_threshold_values_fail_at_load(tmp_path, thresholds, expect_snippet):
    data = _base_valid_ai_tools()
    data["id"] = "bad-thr"
    data["scoring"] = {"interaction_thresholds": thresholds}
    path = _write_niche(tmp_path, "bad-thr", data)
    with pytest.raises(NicheLoadError) as ei:
        load_niche("bad-thr")
    msg = str(ei.value)
    assert "scoring.interaction_thresholds" in msg
    assert expect_snippet in msg
    assert str(path.resolve()) in msg or str(path) in msg


def test_interaction_thresholds_not_dict_fails(tmp_path):
    data = _base_valid_ai_tools()
    data["id"] = "bad-thr-type"
    data["scoring"] = {"interaction_thresholds": [0.02]}
    path = _write_niche(tmp_path, "bad-thr-type", data)
    with pytest.raises(NicheLoadError) as ei:
        load_niche("bad-thr-type")
    msg = str(ei.value)
    assert "scoring.interaction_thresholds 为对象" in msg
    assert str(path.resolve()) in msg or str(path) in msg


def test_scoring_not_dict_fails(tmp_path):
    data = _base_valid_ai_tools()
    data["id"] = "bad-scoring-type"
    data["scoring"] = "nope"
    path = _write_niche(tmp_path, "bad-scoring-type", data)
    with pytest.raises(NicheLoadError) as ei:
        load_niche("bad-scoring-type")
    msg = str(ei.value)
    assert "scoring 为对象" in msg
    assert str(path.resolve()) in msg or str(path) in msg


def test_validate_threshold_overrides_bool_before_numeric():
    """单元层：bool 不得被当成 1.0 放过。"""
    with pytest.raises(ValueError, match="布尔"):
        validate_threshold_overrides({"like_high": True})


# ───────────────────────── 7e 未知键 warn ─────────────────────────


def test_unknown_threshold_key_warns_and_ignored(tmp_path, capsys):
    data = _base_valid_ai_tools()
    data["id"] = "typo-thr"
    data["scoring"] = {"interaction_thresholds": {"like_hight": 0.02}}  # 故意拼错
    path = _write_niche(tmp_path, "typo-thr", data)
    spec = load_niche("typo-thr")
    err = capsys.readouterr().err
    assert "含未知字段" in err
    assert "like_hight" in err
    assert str(path) in err or "typo-thr" in err
    # 未知键被忽略 → 无合法覆写 → 合成结果 == 默认
    assert _resolve_interaction_thresholds(spec) == DEFAULT_INTERACTION_THRESHOLDS
    # scoring 段存在但 validated 为空 → interaction_thresholds 为 None
    assert spec.scoring is not None
    assert spec.scoring.interaction_thresholds is None


# ───────────────────────── 7f 字段归类守卫 ─────────────────────────


def test_interaction_threshold_fields_match_dataclass():
    names = frozenset(f.name for f in fields(InteractionThresholds))
    assert names == INTERACTION_THRESHOLD_FIELDS


# ───────────────────────── 7g scoring_source 留痕 ─────────────────────────


def test_scoring_source_platform_default_without_override():
    result = build_account_type(_ip_dataset())
    assert result["scoring_source"] == {
        "interaction_thresholds": "platform_default",
        "overridden_fields": [],
    }


def test_scoring_source_niche_override_lists_fields():
    thr = merge_thresholds(DEFAULT_INTERACTION_THRESHOLDS, {"like_high": 0.02, "comment_high": 0.003})
    result = build_account_type(_ip_dataset(), thresholds=thr)
    assert result["scoring_source"]["interaction_thresholds"] == "niche_override"
    assert result["scoring_source"]["overridden_fields"] == ["comment_high", "like_high"]


def test_scoring_source_value_compare_not_arg_presence():
    """传入与默认逐字段相同的新实例 → 仍是 platform_default。"""
    twin = InteractionThresholds(
        like_high=DEFAULT_INTERACTION_THRESHOLDS.like_high,
        comment_high=DEFAULT_INTERACTION_THRESHOLDS.comment_high,
        share_high_ip=DEFAULT_INTERACTION_THRESHOLDS.share_high_ip,
        share_high_ks=DEFAULT_INTERACTION_THRESHOLDS.share_high_ks,
        brand_quiet_share=DEFAULT_INTERACTION_THRESHOLDS.brand_quiet_share,
        brand_quiet_comment=DEFAULT_INTERACTION_THRESHOLDS.brand_quiet_comment,
        share_dominance_ratio=DEFAULT_INTERACTION_THRESHOLDS.share_dominance_ratio,
    )
    assert twin is not DEFAULT_INTERACTION_THRESHOLDS
    assert twin == DEFAULT_INTERACTION_THRESHOLDS
    result = build_account_type(_ip_dataset(), thresholds=twin)
    assert result["scoring_source"] == {
        "interaction_thresholds": "platform_default",
        "overridden_fields": [],
    }


# ───────────────────────── 端到端链路 ─────────────────────────


def test_full_chain_load_resolve_build(tmp_path):
    """load_niche → resolve → build_account_type，scoring_source 正确。"""
    data = _base_valid_ai_tools()
    data["id"] = "chain-like"
    data["scoring"] = {"interaction_thresholds": {"like_high": 0.02}}
    _write_niche(tmp_path, "chain-like", data)

    spec = load_niche("chain-like")
    thr = _resolve_interaction_thresholds(spec)
    assert thr.like_high == 0.02
    result = build_account_type(_ip_dataset(), thresholds=thr)
    assert result["scoring_source"] == {
        "interaction_thresholds": "niche_override",
        "overridden_fields": ["like_high"],
    }
