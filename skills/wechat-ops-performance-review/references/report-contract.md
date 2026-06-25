# Report Contract

## Section Order

Use this order for the narrative report:

1. actions
2. overview
3. content-engine
4. title-structure
5. article-length
6. audience
7. timing
8. evidence
9. quality
10. final-synthesis

## Section Shape

Every `analysis_sections[]` entry must include:

```text
id
title
question
conclusion
evidence
action
next_test
confidence
chart_payload
ui_slot
```

`confidence` must include `level`, `score`, `sample_size`, `completeness`, `distribution_skew`, and `reasons`.

## Visual Contract

- One screen = one major conclusion.
- One screen should contain one primary visual: chart, matrix, ranking, action board, or quality grid.
- Do not make the Skill brand the hero. Put it in a small signature slot.
- Dashboard does not call公众号后台 directly; it reads generated JSON only.
