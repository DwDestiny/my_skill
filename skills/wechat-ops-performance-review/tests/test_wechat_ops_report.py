from pathlib import Path

from build_wechat_ops_report import CONTENT_TYPES, build_dataset, render_report, validate_dataset


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DATASET_PATH = FIXTURES / "output" / "dataset.json"


def test_wechat_ops_report_dataset_is_complete():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    errors = validate_dataset(dataset)
    assert errors == []
    assert dataset["meta"]["platform_scope"] == "wechat_only"
    assert dataset["data_quality"]["period_non_deleted_count"] > 0
    assert dataset["data_quality"]["metric_pending_count"] == 0
    assert len(dataset["action_items"]) == 5
    assert dataset["report_meta"]["platform_scope"] == "wechat_only"
    assert dataset["executive_summary"]["headline"]
    assert len(dataset["action_plan"]["items"]) == 5
    assert dataset["template_slots"]["layout"] == "left_nav_center_story_right_context"
    assert dataset["visual_tokens"]["layout"] == "three_column_report_shell"
    assert dataset["account_profile"]["name"] == "样例运营号"
    assert dataset["brand_signature"]["skill_name"] == "wechat-ops-performance-review"
    assert dataset["confidence_model"]["levels"]
    assert dataset["title_analysis"]["by_primary_pattern"]
    assert dataset["length_analysis"]["by_length_bucket"]
    assert "now" in dataset["final_synthesis"]
    assert "experiment" in dataset["final_synthesis"]
    assert "hold" in dataset["final_synthesis"]
    assert dataset["evidence_stream"]
    assert [section["id"] for section in dataset["analysis_sections"]] == [
        "overview",
        "content-engine",
        "title-structure",
        "article-length",
        "audience",
        "timing",
        "evidence",
        "quality",
        "final-synthesis",
    ]
    topc = dataset.get("top_conclusion", {})
    assert topc.get("verdict")
    assert len(str(topc.get("verdict", ""))) <= 8
    assert topc.get("next_action")
    assert len(str(topc.get("next_action", ""))) <= 24


def test_every_analysis_section_has_narrative_contract():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    for section in dataset["analysis_sections"]:
        assert section["question"]
        assert section.get("analysis")
        assert section["conclusion"]
        assert section["action"]
        assert isinstance(section["chart_payload"], dict)
        assert section["ui_slot"]["component"]
        assert section["ui_slot"]["rail_focus"]
        assert section["voice"] in {"high", "medium", "low"}
        assert section["emphasis"] in {"hero", "primary", "secondary"}
        assert section["action_basket"] in {"now", "experiment", "hold"}
        # sample char limits
        assert len(str(section.get("analysis", ""))) <= 60
        assert len(str(section.get("conclusion", ""))) <= 40


def test_template_contract_is_self_describing():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    assert dataset["template_slots"]["left_nav"]["source"] == "narrative_flow"
    assert dataset["template_slots"]["hero"]["source"] == "executive_summary"
    assert dataset["template_slots"]["right_rail"]["source"] == "evidence_stream"
    assert dataset["template_slots"]["evidence_table"]["source"] == "articles.stable"
    assert {item["section_id"] for item in dataset["evidence_stream"]} <= {
        "overview",
        "content-engine",
        "title-structure",
        "article-length",
        "audience",
        "timing",
        "evidence",
        "quality",
        "final-synthesis",
    }


def test_content_type_stats_match_stable_articles():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    stable = dataset["articles"]["stable"]
    by_type_count = sum(row["count"] for row in dataset["analysis"]["by_content_type"])

    assert [row["key"] for row in dataset["analysis"]["by_content_type"]] == CONTENT_TYPES
    assert by_type_count == len(stable)
    assert all(not article["is_immature"] for article in stable)


def test_every_period_article_has_operating_tags_and_metrics():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    for article in dataset["articles"]["all_period"]:
        assert article["content_type"]
        assert article["pain_point"]
        assert article["persona"]
        assert article["published_at"]
        assert article["title_structure"]["primary_pattern"]
        assert article["length_bucket"]
        assert isinstance(article["reads"], int)
        assert isinstance(article["shares"], int)
        assert isinstance(article["comments"], int)


def test_title_and_length_analysis_are_usable():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    stable = dataset["articles"]["stable"]
    matched_lengths = [article for article in stable if article["article_length_chars"] > 0]

    assert matched_lengths
    assert sum(row["count"] for row in dataset["title_analysis"]["by_primary_pattern"]) == len(stable)
    assert sum(row["count"] for row in dataset["length_analysis"]["by_length_bucket"]) == len(stable)
    assert any(row["key"] != "未匹配正文" and row["count"] > 0 for row in dataset["length_analysis"]["by_length_bucket"])


def test_wiki_report_starts_with_weekly_actions_and_links_dataset():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    report = render_report(dataset, DATASET_PATH)
    body_after_frontmatter = report.split("---", 2)[-1].lstrip()

    assert body_after_frontmatter.startswith("## 本周先做这 5 件事")
    assert str(DATASET_PATH) in report
    assert "分析平台：只看微信公众号" in report
    assert "头条、Twitter/X" in report


def test_top_conclusion_and_final_baskets_and_redline():
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    report = render_report(dataset, DATASET_PATH)
    topc = dataset.get("top_conclusion", {})
    assert topc.get("verdict")
    assert len(str(topc.get("verdict", ""))) <= 8
    assert topc.get("next_action")
    assert len(str(topc.get("next_action", ""))) <= 24
    fs = dataset.get("final_synthesis", {})
    assert set(fs.keys()) >= {"now", "experiment", "hold"}
    # red line: zero occurrences of forbidden words
    forbidden_count = sum(report.count(w) for w in ["置信度", "高置信", "中置信", "低置信"])
    assert forbidden_count == 0, "found forbidden words in report: %d" % forbidden_count
