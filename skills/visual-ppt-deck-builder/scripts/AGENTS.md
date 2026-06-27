# visual-ppt-deck-builder scripts

## Purpose

This directory contains deterministic helpers for visual PPT generation, preview rendering, quality gates, and editability inspection.

## Files

- `build_visual_pptx.js` — builds the final editable PPTX from a deck spec.
- `build_deck_preview.js` — renders preview artifacts for review.
- `build_style_candidates.js` — creates candidate style directions.
- `design_director_qa.js` — checks visual quality against design gates.
- `inspect_pptx_editability.py` — inspects PPTX text and shape editability.
- `render_style_background.py` — renders raster style backgrounds.
- `validate_deck_quality.js` — validates deck structure and layout coverage.

## Local Rules

- Keep generated decks and heavy artifacts out of this directory.
- Preserve CLI compatibility for existing smoke tests.
- When a script changes inputs, outputs, or role, update its GEB-L3 header.

## Verification

```bash
tests/smoke_visual_ppt_deck_builder.sh
```
