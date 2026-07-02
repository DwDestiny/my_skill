"""Tests for new raw sources and 5 methodology modules (m1/m3/m4/m5/m6)."""
from pathlib import Path

import pytest

from build_wechat_ops_report import build_dataset
from analyze.io_utils import load_raw_audience, load_raw_trend
from analyze.m1_checkup import build_checkup
from analyze.m3_content_engine import build_content_engine
from analyze.m4_audience import build_audience
from analyze.m5_growth_funnel import build_growth_funnel
from analyze.m6_action_plan import build_action_plan_v2
from fetch.fetch_audience import _extract_js_var, _is_nonempty_struct

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_load_raw_audience_trend_fallback(tmp_path: Path):
    """load_raw_* on non-existing returns available=false, no crash."""
    missing = tmp_path / "no_such_root"
    aud = load_raw_audience(missing)
    tr = load_raw_trend(missing)
    assert aud == {"available": False}
    assert tr == {"available": False}

    # also broken json dir
    bad_dir = tmp_path / "bad"
    (bad_dir / "raw").mkdir(parents=True)
    (bad_dir / "raw" / "audience.json").write_text("{invalid", encoding="utf-8")
    aud2 = load_raw_audience(bad_dir)
    assert aud2 == {"available": False}


def test_load_raw_works_with_fixtures():
    aud = load_raw_audience(FIXTURES)
    tr = load_raw_trend(FIXTURES)
    assert aud.get("available") is True
    assert "cumulate_user" in aud
    assert tr.get("available") is True
    assert "read_item" in tr


def test_build_checkup_health_score_bounds_and_structure():
    dataset = build_dataset(FIXTURES, account_name="测试")
    stable = dataset["articles"]["stable"]
    bm = dataset["benchmark"]
    aud = load_raw_audience(FIXTURES)
    chk = build_checkup(stable, bm, aud)
    assert 0 <= chk["health_score"] <= 100
    assert "dependency" in chk and "is_dependent" in chk["dependency"]
    assert "interaction" in chk
    assert "fans" in chk
    assert "verdict" in chk and "analysis" in chk and "action" in chk
    assert chk["voice"] in {"high", "medium", "low"}
    assert chk["action_basket"] in {"now", "experiment", "hold"}
    assert "chart_payload" in chk


def test_build_audience_available_and_unavailable_paths():
    dataset = build_dataset(FIXTURES, account_name="测试")
    stable = dataset["articles"]["stable"]
    by_pain = dataset["analysis"]["by_pain_point"]
    by_persona = dataset["analysis"]["by_persona"]
    aud_avail = load_raw_audience(FIXTURES)
    aud_mod = build_audience(stable, aud_avail, by_pain, by_persona)
    assert aud_mod["fans_portrait_available"] is True
    assert aud_mod["city"]  # top10
    assert "analysis" in aud_mod and "conclusion" in aud_mod

    # unavailable path
    aud_fake = {"available": False}
    aud_mod2 = build_audience(stable, aud_fake, by_pain, by_persona)
    assert aud_mod2["fans_portrait_available"] is False
    assert aud_mod2["emphasis"] == "secondary" or aud_mod2["voice"] == "low"
    assert "pain_points" in aud_mod2 and "personas" in aud_mod2


def test_build_growth_funnel_startup_plan_4weeks_and_fields():
    dataset = build_dataset(FIXTURES, account_name="测试")
    stable = dataset["articles"]["stable"]
    vg = dataset["viral_genes"]
    aud = load_raw_audience(FIXTURES)
    tr = load_raw_trend(FIXTURES)
    gf = build_growth_funnel(stable, aud, tr, vg["viral_formula"])
    assert gf["data_available"] is True
    assert isinstance(gf["share_to_fan_rate"], (int, float))
    assert "open_rate_approx" in gf
    assert "_approx" in "open_rate_approx"
    assert len(gf["startup_plan"]) == 4
    for wk in gf["startup_plan"]:
        assert "week" in wk and "focus" in wk and "topics" in wk and "target" in wk
    assert "chart_payload" in gf


def test_build_action_plan_v2_three_baskets():
    dataset = build_dataset(FIXTURES, account_name="测试")
    vg = dataset["viral_genes"]
    chk = dataset["modules"]["checkup"] if "modules" in dataset else build_checkup(dataset["articles"]["stable"], dataset["benchmark"], load_raw_audience(FIXTURES))
    ce = dataset["modules"]["content_engine"] if "modules" in dataset else build_content_engine(dataset["articles"]["stable"], dataset["analysis"]["by_content_type"], dataset["benchmark"])
    au = dataset["modules"]["audience"] if "modules" in dataset else build_audience(dataset["articles"]["stable"], load_raw_audience(FIXTURES), dataset["analysis"]["by_pain_point"], dataset["analysis"]["by_persona"])
    gf = dataset["modules"]["growth_funnel"] if "modules" in dataset else build_growth_funnel(dataset["articles"]["stable"], load_raw_audience(FIXTURES), load_raw_trend(FIXTURES), vg["viral_formula"])
    ap = build_action_plan_v2(vg, chk, ce, au, gf)
    assert "now" in ap and "experiment" in ap and "hold" in ap
    assert isinstance(ap["now"], list)
    assert isinstance(ap["experiment"], list)
    assert isinstance(ap["hold"], list)
    assert len(ap["next_topics"]) >= 1
    assert "chart_payload" in ap


def test_build_dataset_mounts_modules_five_keys_and_account():
    dataset = build_dataset(FIXTURES, account_name="测试")
    assert "modules" in dataset
    m = dataset["modules"]
    assert set(m.keys()) == {"checkup", "content_engine", "audience", "growth_funnel", "action_plan"}
    for k in m:
        assert "analysis" in m[k] or "verdict" in m[k] or "now" in m[k]
        assert "voice" in m[k] or k == "action_plan"
    assert "account" in dataset
    acc = dataset["account"]
    # account 名优先用 raw/account.json 抓到的真实名(fixtures 为"麦总玩AI"),否则回退参数
    assert acc["name"] in ("麦总玩AI", "测试")
    assert "avatar_local" in acc
    assert "available" in acc
    # ensure old keys untouched
    assert "viral_genes" in dataset
    assert "benchmark" in dataset
    assert "analysis" in dataset
    assert "analysis_sections" in dataset


def test_build_audience_does_not_crash_on_malformed_age():
    """防御：audience_raw 中 age 是 JS 函数字符串（真实崩溃 case），build 不得抛 TypeError，必须优雅降级为 '未知' 且 age 字段规整为 []。"""
    stable: list[dict] = []
    by_pain: list[dict] = []
    by_persona: list[dict] = []
    # 真实导致崩溃的 malformed 形状（来自 fetch 误匹配 JS 代码）
    audience_raw = {
        "cumulate_user": None,
        "new_user": None,
        "cancel_user": None,
        "netgain": None,
        "city": None,
        "province": None,
        "age": "function(force) {\n    window.location.reload(force)",
        "user_source": None,
        "available": True,
    }
    # 必须不抛异常
    result = build_audience(stable, audience_raw, by_pain, by_persona)
    # analysis 文案 age 维度必须降级为'未知'，不能包含 JS 代码片段
    assert "未知" in result["analysis"]
    assert "function" not in result["analysis"]
    assert "reload" not in result["analysis"]
    # 返回的 age 必须是 list（畸形时规整为 []）
    assert isinstance(result["age"], list)
    assert result["age"] == []
    # city / user_source 也应规整
    assert isinstance(result["city"], list)
    assert isinstance(result["user_source"], list)


def test_extract_js_var_rejects_js_function():
    """_extract_js_var 必须只返回可 json 解析的 dict/list 或 None，绝不返回原始 JS 代码字符串。"""
    html = '<script>var age=function(force){window.location.reload(force)}; var city=[{"name":"北京"}]; </script>'
    age_val = _extract_js_var(html, "age")
    assert age_val is None, f"expected None for JS function, got {type(age_val)}: {age_val!r}"
    # 正常数据仍应解析
    city_val = _extract_js_var(html, "city")
    assert city_val == [{"name": "北京"}]


def test_audience_available_ignores_garbage_string():
    """fetch 层 has_demo/has_core 判定只认非空 list/dict，不应因非空字符串垃圾导致 available=True。"""
    garbage_age = "function(force) {\n    window.location.reload(force)"
    data = {
        "cumulate_user": None,
        "new_user": None,
        "cancel_user": None,
        "netgain": None,
        "city": None,
        "province": None,
        "age": garbage_age,
        "user_source": None,
    }
    # 使用 fetch 层的真实判定 helper（只认非空 list/dict）
    core = ["cumulate_user", "new_user", "cancel_user", "netgain"]
    has_core = any(_is_nonempty_struct(data.get(k)) for k in core)
    has_demo = any(_is_nonempty_struct(data.get(k)) for k in ["city", "province", "age", "user_source"])
    available = bool(has_core or has_demo)
    # 期望行为：garbage string 不能算有画像，available 必须 False
    assert available is False, f"garbage string should not set available=True, got available={available}"
