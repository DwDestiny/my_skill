---
name: wechat-ops-performance-review
description: Use when reviewing WeChat official account performance, refreshing published article metrics, producing an operations diagnosis, or generating a wiki report and local narrative dashboard from公众号后台数据、publish-records JSON、文章台账或运营复盘需求.
---

# WeChat Ops Performance Review

## Core Principle

Turn公众号数据 into a decision report, not a crowded dashboard. The output must answer: what to do next, why the data supports it, how confident the conclusion is, and how to test it next.

## Standard Workflow

1. **Refresh data**: get the latest `reports/wechat/publish-records-*.json`; if login is stale, stop and ask for a fresh scan/login rather than analyzing old data.
2. **Build the contract**: run the report builder so wiki JSON, wiki Markdown, and dashboard data all come from one source.
3. **Analyze**: use average, median, P75, max, trimmed mean, sample count, and confidence. Never turn one爆款 into a rule.
4. **Generate the experience**: produce a low-density narrative report: account overview first, one claim per screen, evidence and action beside each section.
5. **Verify**: run data tests, build the local site, open it, and check desktop/mobile screenshots.

Use `scripts/run_wechat_ops_report.sh` when working in the default local repo layout.

## Required Output Contract

Read `references/report-contract.md` before changing the schema or report experience.

The JSON must include:

- `account_profile`: analyzed account identity, period, article counts, update time.
- `executive_summary`: first-screen judgment and core metrics.
- `action_plan`: 3-5 next actions with why/action/owner/due/validation.
- `analysis_sections`: total-split-total sections, each with conclusion, evidence, action, next test, confidence, and UI slot.
- `title_analysis`: title pattern, title length, and feature performance.
- `length_analysis`: local article length buckets and match quality.
- `confidence_model`: high/medium/low rules and completeness notes.
- `final_synthesis`: do now, test small, do not decide yet.
- `brand_signature`: small source/author card only; never make it the page hero.

## Analysis Rules

- Only analyze WeChat unless the user explicitly expands scope.
- Separate stable articles from recent 48-hour immature articles.
- Classify every article by content type, pain point, persona, title pattern, and length bucket.
- Every section must have a confidence level derived from sample count, distribution skew, and data completeness.
- End with a synthesis board: high-confidence actions, experiments, and hold decisions.

## Experience Rules

- Left top: the analyzed公众号信息, not the Skill author.
- Left bottom: a small source card with author/avatar/Skill/GitHub link.
- Center: scroll-snapping narrative screens; one main visual per screen.
- Right: fixed context rail for current evidence, action, and confidence.
- Avoid card walls, crowded first screens, grey-heavy shells, and text-only explanations.

## Validation

Run these before calling the review complete:

```bash
scripts/run_wechat_ops_report.sh
```

Or manually:

```bash
python3 scripts/social_ops/build_wechat_ops_report.py --check
python3 -m pytest tests/test_wechat_ops_report.py -q
pnpm -C reports/wechat-ops-dashboard build
```

Then open the local dashboard and verify desktop plus mobile: account info is primary, author card is secondary, each screen has a clear visual focus, and every action is backed by confidence.
