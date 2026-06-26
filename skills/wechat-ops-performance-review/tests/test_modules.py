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
