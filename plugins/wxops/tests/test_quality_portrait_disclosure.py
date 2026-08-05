# GEB-L3
# Input: fixtures + build_dataset；画像不可得分支通过改写 modules.audience.fans_portrait_available 后重建 sections
# Output: issue #54 数据质量章双覆盖维度披露契约（可用/不可得文案、长度、markdown 口径）
# Pos: plugins/wxops/tests/test_quality_portrait_disclosure.py
"""Issue #54: 数据质量章不得隐瞒粉丝画像缺失。"""

from __future__ import annotations

from pathlib import Path

from build_wechat_ops_report import (
    build_analysis_sections,
    build_dataset,
    render_report,
    validate_dataset,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DATASET_PATH = FIXTURES / "output" / "dataset.json"


def _quality_section(dataset: dict) -> dict:
    for section in dataset["analysis_sections"]:
        if section["id"] == "quality":
            return section
    raise AssertionError("quality section missing")


def _rebuild_quality_sections(dataset: dict) -> dict:
    """Re-run section builder after mutating audience portrait flag; keep dataset consistent."""
    dataset["analysis_sections"] = build_analysis_sections(dataset)
    return dataset


def test_quality_section_discloses_portrait_unavailable():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    dataset["modules"]["audience"]["fans_portrait_available"] = False
    _rebuild_quality_sections(dataset)

    quality = _quality_section(dataset)
    assert "粉丝画像不可得" in quality["analysis"]
    # 不得出现未加限定的「核心指标齐全」
    assert "核心指标齐全" not in quality["conclusion"]
    assert "文章指标齐全" in quality["conclusion"]
    assert "画像" in quality["conclusion"]
    assert "补抓画像" in quality["action"] or "画像" in quality["action"]

    assert len(quality["analysis"]) <= 60
    assert len(quality["conclusion"]) <= 40
    assert len(quality["action"]) <= 30
    assert validate_dataset(dataset) == []


def test_quality_section_portrait_available_regression():
    """默认 fixture 画像可得：保持原措辞，analysis 披露「粉丝画像可用」。"""
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    assert dataset["modules"]["audience"]["fans_portrait_available"] is True

    quality = _quality_section(dataset)
    assert "粉丝画像可用" in quality["analysis"]
    assert "核心指标齐全，仍需保留导出时间和待补动作。" == quality["conclusion"] or (
        quality["conclusion"].endswith("核心指标齐全，仍需保留导出时间和待补动作。")
    )
    # high voice 下 action 可能带「立即」前缀
    assert "每次复盘先刷新后台导出，登录失效先补数据。" in quality["action"]

    assert len(quality["analysis"]) <= 60
    assert len(quality["conclusion"]) <= 40
    assert len(quality["action"]) <= 30
    assert validate_dataset(dataset) == []


def test_render_report_discloses_portrait_unavailable_in_data_scope():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    dataset["modules"]["audience"]["fans_portrait_available"] = False
    _rebuild_quality_sections(dataset)

    report = render_report(dataset, DATASET_PATH)
    assert "粉丝画像：后台画像不可得" in report
    assert "人群结论只能靠文章标签推断" in report
    assert "补抓画像" in report


def test_render_report_discloses_portrait_available_in_data_scope():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    assert dataset["modules"]["audience"]["fans_portrait_available"] is True

    report = render_report(dataset, DATASET_PATH)
    assert "粉丝画像：后台画像可得" in report
