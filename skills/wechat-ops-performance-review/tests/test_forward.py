"""Tests for forward-looking engine (m8_forward) per DATA_CONTRACT.md §10."""

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

from build_wechat_ops_report import build_dataset
from analyze.m8_forward import build_forward_looking

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _load_good_dataset():
    return build_dataset(FIXTURES)


def test_gate_blocks_paths_and_matrix_when_stable_below_threshold():
    """1. 闸门：stable<15 → passed=False + candidate_paths==[] + by_direction=={}"""
    ds = _load_good_dataset()
    ds2 = copy.deepcopy(ds)
    # 强制截断 stable 到 <15
    if len(ds2["articles"].get("stable", [])) >= 15:
        ds2["articles"]["stable"] = ds2["articles"]["stable"][:10]
    fl = build_forward_looking(ds2)
    assert fl["data_sufficiency"]["passed"] is False
    assert fl["candidate_paths"] == []
    assert fl["content_matrix"]["by_direction"] == {}


def test_signals_complete_fixed_order_and_enums():
    """2. signals 完整：6 个齐全、key 顺序固定、computability/level 合法"""
    ds = _load_good_dataset()
    fl = ds["forward_looking"]
    signals = fl["signals"]
    assert len(signals) == 6
    keys = [s["key"] for s in signals]
    assert keys == [
        "topic_distribution",
        "viral_type",
        "interaction",
        "originality",
        "timeliness_depth",
        "capacity_funnel",
    ]
    allowed_comp = {"直接可算", "正则近似", "需NLP"}
    allowed_level = {"强", "中", "弱"}
    for s in signals:
        assert s["computability"] in allowed_comp
        assert s["level"] in allowed_level


def test_candidate_count_in_range_on_good_fixture():
    """3. 候选数量：达标 fixture → 2≤len≤4"""
    ds = _load_good_dataset()
    paths = ds["forward_looking"]["candidate_paths"]
    assert 2 <= len(paths) <= 4


def test_direction_card_fields_complete_and_feasibility_values():
    """4. 方向卡字段齐全；feasibility 合法；低档有 note"""
    ds = _load_good_dataset()
    paths = ds["forward_looking"]["candidate_paths"]
    allowed_feas = {"顺手", "够得着", "要改造", "阻力大"}
    for p in paths:
        assert p.get("path_name")
        assert p.get("rationale_from_status")
        assert isinstance(p.get("gap"), list) and len(p.get("gap")) > 0
        assert p.get("monetization")
        assert p.get("matrix_hint")
        feas = p.get("feasibility")
        assert feas in allowed_feas
        if feas in ("要改造", "阻力大"):
            assert p.get("feasibility_note") and "改造成本高 ≠ 不推荐" in str(p.get("feasibility_note"))


def test_matrix_two_layers_roles_buckets_schedule():
    """5. 矩阵两层：roles 固定；每个 by_direction 有 buckets(≤6) 与 schedule；桶 topics 非空"""
    ds = _load_good_dataset()
    cm = ds["forward_looking"]["content_matrix"]
    assert cm["roles"] == ["拉新", "养信任", "建专业", "转化", "留存"]
    by_dir = cm["by_direction"]
    assert len(by_dir) >= 2
    for pid, val in by_dir.items():
        buckets = val.get("buckets", [])
        schedule = val.get("schedule", [])
        assert isinstance(buckets, list) and 0 < len(buckets) <= 6
        assert isinstance(schedule, list) and len(schedule) >= 1
        for b in buckets:
            assert b.get("topics") and isinstance(b.get("topics"), list) and len(b["topics"]) > 0
            assert b.get("role") in cm["roles"]


def test_neutrality_only_on_render_strings_no_forbidden_tokens():
    """6. 中立性：只遍历渲染字符串字段，禁止出现 置信度 / 裸英文片段 / feasibility含%"""
    ds = _load_good_dataset()
    fl = ds["forward_looking"]

    render_strings = []

    # mirror.statement
    render_strings.append(fl["mirror"].get("statement", ""))

    # axes notes
    for ax in fl["mirror"].get("axes", []):
        render_strings.append(ax.get("note", "") or "")

    # each candidate card render fields (NOT id or structural keys)
    for p in fl["candidate_paths"]:
        render_strings.append(p.get("path_name", ""))
        render_strings.append(p.get("rationale_from_status", ""))
        for g in p.get("gap", []) or []:
            render_strings.append(str(g))
        render_strings.append(p.get("feasibility_note") or "")
        render_strings.append(p.get("monetization", ""))
        render_strings.append(p.get("matrix_hint", ""))

    # content_matrix buckets.rhythm + schedule.focus (NOT ids, weights, keys)
    for val in fl["content_matrix"]["by_direction"].values():
        for b in val.get("buckets", []):
            render_strings.append(b.get("rhythm", ""))
        for sch in val.get("schedule", []):
            render_strings.append(sch.get("focus", ""))

    forbidden = "置信度"
    bare_en = ["path-", "role:", "affinity", "weight"]
    for s in render_strings:
        s = str(s)
        assert forbidden not in s
        for token in bare_en:
            assert token not in s
    # feasibility 字段本身不含 %
    for p in fl["candidate_paths"]:
        assert "%" not in str(p.get("feasibility", ""))


def test_demo_runnable_from_fixtures_dir():
    """7. demo 可跑：fixtures → candidate_paths ≥2"""
    ds = build_dataset(FIXTURES)
    paths = ds["forward_looking"]["candidate_paths"]
    assert len(paths) >= 2


def test_does_not_break_existing_top_level_fields():
    """8. 不破坏旧字段：build_dataset 后原有顶层键仍在"""
    ds = _load_good_dataset()
    required_old = [
        "meta",
        "data_quality",
        "articles",
        "analysis",
        "viral_genes",
        "modules",
        "account_profile",
        "benchmark",
    ]
    for k in required_old:
        assert k in ds, f"missing original top level key: {k}"
    # forward_looking is new appended
    assert "forward_looking" in ds


def test_content_matrix_deterministic_across_hashseeds():
    """9. content_matrix 确定性回归：不同 PYTHONHASHSEED 下跨进程完全一致（锁死防 set 迭代顺序回退）"""
    cwd = Path(__file__).resolve().parents[1]
    seeds = ["0", "1", "2"]
    outputs: list[bytes] = []

    child_code = (
        "import sys\n"
        'sys.path.insert(0, "scripts")\n'
        "import json\n"
        "from pathlib import Path\n"
        "from build_wechat_ops_report import build_dataset\n"
        "from analyze.m8_forward import build_forward_looking\n"
        "\n"
        'dataset = build_dataset(Path("fixtures"))\n'
        "fl = build_forward_looking(dataset)\n"
        'cm = fl.get("content_matrix", {})\n'
        's = json.dumps(cm, sort_keys=True, ensure_ascii=False)\n'
        "print(s)\n"
    )

    for seed in seeds:
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = seed
        result = subprocess.run(
            [sys.executable, "-c", child_code],
            cwd=str(cwd),
            env=env,
            capture_output=True,
        )
        assert result.returncode == 0, f"seed {seed} subprocess failed: {result.stderr.decode('utf-8', errors='replace')}"
        outputs.append(result.stdout.rstrip(b"\n\r"))

    # 完全 byte-identical 断言，失败时指出具体哪两个 seed 不一致
    assert outputs[0] == outputs[1], f"seed {seeds[0]} and {seeds[1]} content_matrix json not byte-identical"
    assert outputs[1] == outputs[2], f"seed {seeds[1]} and {seeds[2]} content_matrix json not byte-identical"
    assert outputs[0] == outputs[2], f"seed {seeds[0]} and {seeds[2]} content_matrix json not byte-identical"
