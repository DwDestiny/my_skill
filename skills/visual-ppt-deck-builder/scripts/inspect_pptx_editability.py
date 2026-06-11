#!/usr/bin/env python3
# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by skills/visual-ppt-deck-builder/scripts/inspect_pptx_editability.py
# Pos: skills/visual-ppt-deck-builder/scripts/inspect_pptx_editability.py
import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Inspect generated PPTX slides for editable text and non-image-only pages."
    )
    parser.add_argument("--pptx", required=True, help="Path to generated .pptx")
    parser.add_argument("--spec", required=True, help="Path to deck_spec.json")
    parser.add_argument("--report", required=True, help="Path to write JSON report")
    parser.add_argument("--min-text-per-slide", type=int, default=3)
    return parser.parse_args()


def read_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(value):
    return re.sub(r"\s+", "", str(value or "")).strip()


def add_text(target, value):
    text = normalize_text(value)
    if text and len(text) >= 2:
        target.append(text)


def collect_expected_texts(slide):
    texts = []
    for key in ["title", "subtitle", "kicker", "claim", "body", "source"]:
        add_text(texts, slide.get(key))

    for point in slide.get("points") or []:
        for key in ["label", "title", "body"]:
            add_text(texts, point.get(key))

    for layer in slide.get("layers") or []:
        for key in ["title", "body"]:
            add_text(texts, layer.get(key))

    for metric in slide.get("metrics") or []:
        for key in ["value", "label", "body"]:
            add_text(texts, metric.get(key))

    for item in slide.get("items") or []:
        for key in ["title", "body"]:
            add_text(texts, item.get(key))

    for phase in slide.get("phases") or []:
        for key in ["period", "title", "body"]:
            add_text(texts, phase.get(key))

    for step in slide.get("steps") or []:
        for key in ["label", "title", "body"]:
            add_text(texts, step.get(key))

    for bullet in slide.get("bullets") or []:
        if isinstance(bullet, dict):
            for key in ["title", "body"]:
                add_text(texts, bullet.get(key))
        else:
            add_text(texts, bullet)

    for value in slide.get("risks") or []:
        add_text(texts, value)
    for value in slide.get("actions") or []:
        add_text(texts, value)

    chart = slide.get("chart") or {}
    for key in ["title", "source", "unit"]:
        add_text(texts, chart.get(key))
    for label in chart.get("labels") or []:
        add_text(texts, str(label).replace("\n", ""))
    for value in chart.get("values") or []:
        add_text(texts, value)

    seen = set()
    unique_texts = []
    for text in texts:
        if text not in seen:
            seen.add(text)
            unique_texts.append(text)
    return unique_texts


def slide_xml_name(index):
    return f"ppt/slides/slide{index}.xml"


def extract_slide_text(xml):
    chunks = re.findall(r"<a:t>(.*?)</a:t>", xml, flags=re.DOTALL)
    return normalize_text("".join(html.unescape(chunk) for chunk in chunks))


def inspect_pptx(pptx_path, spec, min_text_per_slide):
    slides = spec.get("slides") or []
    results = []
    errors = []

    with zipfile.ZipFile(pptx_path) as archive:
        names = set(archive.namelist())
        for index, slide in enumerate(slides, start=1):
            xml_name = slide_xml_name(index)
            if xml_name not in names:
                errors.append(f"slide {index} missing xml: {xml_name}")
                continue

            xml = archive.read(xml_name).decode("utf-8", errors="replace")
            slide_text = extract_slide_text(xml)
            expected_texts = collect_expected_texts(slide)
            missing_texts = [text for text in expected_texts if text not in slide_text]
            text_node_count = len(re.findall(r"<a:t>", xml))
            shape_count = len(re.findall(r"<p:sp[ >]", xml))
            picture_count = len(re.findall(r"<p:pic[ >]", xml))

            slide_errors = []
            if text_node_count < min_text_per_slide and slide.get("layout") not in ["title", "closing", "section"]:
                slide_errors.append(
                    f"slide {index} has too few editable text nodes: {text_node_count}"
                )
            if shape_count == 0:
                slide_errors.append(f"slide {index} has no editable shapes")
            if picture_count > 0 and text_node_count == 0:
                slide_errors.append(f"slide {index} appears image-only")
            if missing_texts:
                slide_errors.append(
                    f"slide {index} missing editable expected texts: {', '.join(missing_texts[:8])}"
                )

            errors.extend(slide_errors)
            results.append(
                {
                    "slide": index,
                    "layout": slide.get("layout", "content"),
                    "semantic_layout": slide.get("semantic_layout"),
                    "text_node_count": text_node_count,
                    "shape_count": shape_count,
                    "picture_count": picture_count,
                    "expected_text_count": len(expected_texts),
                    "missing_texts": missing_texts,
                    "ok": not slide_errors,
                }
            )

    return {
        "ok": not errors,
        "errors": errors,
        "slides": results,
        "slide_count": len(slides),
    }


def main():
    args = parse_args()
    pptx_path = Path(args.pptx)
    spec_path = Path(args.spec)
    report_path = Path(args.report)

    if not pptx_path.exists():
        print(f"missing pptx: {pptx_path}", file=sys.stderr)
        sys.exit(1)
    if not spec_path.exists():
        print(f"missing spec: {spec_path}", file=sys.stderr)
        sys.exit(1)

    report = inspect_pptx(pptx_path, read_json(spec_path), args.min_text_per_slide)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
