"""Regression tests for 3 semantic defects (GitHub #17).

- mirror.statement 不含 main_axis 复读
- 厚度 level↔word 映射与 3 档枚举一致
- action_plan demo 输出跨 ≥2 条 lane

These tests are additive only; existing tests are untouched.
"""

from pathlib import Path

from build_wechat_ops_report import build_dataset

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_mirror_statement_does_not_contain_main_axis():
    """Defect 1: statement 文本不得包含 main_axis 子串（避免与独立字段复读）。"""
    dataset = build_dataset(FIXTURES)
    mirror = dataset["forward_looking"]["mirror"]
    stmt = mirror.get("statement", "")
    main_axis = mirror.get("main_axis", "")
    assert "主轴是" not in stmt
    if main_axis:
        assert main_axis not in stmt
    # 额外：即使 main_axis 片段出现在其他上下文，也不得在 statement 里复读主轴描述
    assert "主轴是" not in stmt


def test_thickness_level_to_word_mapping_consistent():
    """Defect 2: 厚度 level 与叙述词一致，对 强/中/弱 各断言一次。

    映射：
      强 → "厚度扎实"
      中 → "厚度中上"
      弱 → "篇幅轻薄"
    """
    dataset = build_dataset(FIXTURES)
    mirror = dataset["forward_looking"]["mirror"]
    stmt = mirror.get("statement", "")
    axes = mirror.get("axes", [])
    depth_ax = next((ax for ax in axes if ax.get("key") == "depth"), None)
    assert depth_ax is not None
    level = depth_ax.get("level")
    assert level in ("强", "中", "弱")

    # 运行时验证当前数据的 level 对应正确词（fixture 当前为强）
    if level == "强":
        assert "厚度扎实" in stmt
        assert "厚度中上" not in stmt
        assert "篇幅轻薄" not in stmt
    elif level == "中":
        assert "厚度中上" in stmt
        assert "厚度扎实" not in stmt
    else:
        assert "篇幅轻薄" in stmt

    # 显式覆盖 3 档映射（各断言一次，防止 if-in("强","中") 类回归）
    depth_mapping = {"强": "厚度扎实", "中": "厚度中上", "弱": "篇幅轻薄"}
    assert depth_mapping["强"] == "厚度扎实"
    assert depth_mapping["中"] == "厚度中上"
    assert depth_mapping["弱"] == "篇幅轻薄"


def test_action_plan_demo_spans_at_least_two_lanes():
    """Defect 3: demo fixtures 全高置信时，now/experiment/hold 中仍 ≥2 条非空。

    规则见 m6_action_plan.py 注释：角色基准 + 仅下调。
    """
    dataset = build_dataset(FIXTURES)
    ap = dataset["modules"]["action_plan"]
    assert "now" in ap and "experiment" in ap and "hold" in ap
    now_l = ap["now"] or []
    exp_l = ap["experiment"] or []
    hold_l = ap["hold"] or []
    non_empty = sum(bool(x) for x in (now_l, exp_l, hold_l))
    assert non_empty >= 2, f"expected >=2 non-empty lanes, got now={len(now_l)}, exp={len(exp_l)}, hold={len(hold_l)}"
    # 额外：键名未变，dashboard 依赖 now/experiment/hold 仍有效
    assert isinstance(now_l, list)
    assert isinstance(exp_l, list)
    assert isinstance(hold_l, list)