#!/usr/bin/env python3
# GEB-L3
# Input: Local UI delivery directory, stage metadata, and authored artifacts.
# Output: Draft scaffold, immutable-content snapshots, or deterministic contract diagnostics.
# Pos: Standard-library CLI for structural handoff checks; never judges visual quality or grants approval.

"""UI delivery contract scaffold and deterministic validator (Python 3.10+)."""

import argparse
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


STAGES = (
    ("product-planning", ("product-brief.md", "page-inventory.json")),
    ("ux-architecture", ("ux-map.md", "state-matrix.json", "wireframes.md")),
    ("visual-direction", ("direction-options.md", "style-decision.json")),
    ("design-system", ("design-system.md", "tokens.json", "component-inventory.json")),
    ("high-fidelity", ("high-fidelity.md", "screen-specs.json")),
    ("motion-design", ("motion-spec.md", "motion-map.json")),
    ("frontend-implementation", ("implementation-report.md", "implementation-map.json")),
    ("visual-qa", ("qa-report.md", "qa-matrix.json", "evidence.json", "verdict.json")),
)
KINDS = {"default", "loading", "empty", "error", "permission_denied", "success"}
ELEMENT_ROLES = {"navigation", "control", "content", "decoration"}
ID = re.compile(r"^[a-z][a-z0-9-]*$")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".pdf", ".html"}
RUNTIME_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CACHE_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CACHE_FILES = {".DS_Store"}
SCAFFOLDS = {
    "page-inventory.json": {"pages": [{"id": "", "screen_ids": []}]},
    "state-matrix.json": {"rows": [{"page_id": "", "screen_id": "", "state_id": "", "viewport_id": "", "applicability": "applicable", "behavior": "", "reason": "", "required_elements": [{"id": "", "role": "", "component_id": ""}]}]},
    "style-decision.json": {"options": [{"id": "", "concept_path": "", "source_kind": "concept"}], "selected_id": "", "selection": {"by": "", "evidence": "", "authorization": ""}},
    "tokens.json": {"colors": {}, "typography": {}, "spacing": {}, "layout": {}, "style_sha256": ""},
    "component-inventory.json": {"components": [{"id": "", "revision": "", "master_path": "", "render_mode": "structured", "used_by": []}]},
    "screen-specs.json": {"specs": [{"screen_id": "", "state_id": "", "viewport_id": "", "visual_mode": "full", "asset_path": "", "asset_kind": "design", "element_ids": [], "component_refs": [], "measurements": [], "review": {"by": "", "note": ""}}], "prototypes": []},
    "motion-map.json": {"motions": [{"id": "", "screen_id": "", "state_id": "", "reduced_motion": ""}]},
    "implementation-map.json": {"revision": "", "routes": [{"page_id": "", "route": "", "screen_ids": []}], "implemented_by": "", "runtime_manifest_path": "runtime-manifest.json", "runtime_fingerprint": "", "elements": [], "components": []},
    "qa-matrix.json": {"rows": [{"screen_id": "", "state_id": "", "viewport_id": "", "result": "pending", "evidence_ids": [], "baseline_sha256": "", "comparison_path": "", "element_checks": [], "measurements": []}], "journey_results": []},
    "evidence.json": {"items": [{"id": "", "kind": "", "path": "", "route": "", "viewport_id": "", "state_id": "", "revision": "", "captured_at": "", "source_url": "", "runtime_fingerprint": ""}]},
    "verdict.json": {"verdict": "pending", "by": "", "basis": "", "reviewed_by": "", "open_blockers": []},
}


class ContractError(Exception):
    pass


def fail(message):
    raise ContractError(message)


def required(value, label):
    if not isinstance(value, str) or not value.strip():
        fail(f"{label}: must be a nonempty string")
    return value.strip()


def identifier(value, label):
    if not isinstance(value, str) or not ID.fullmatch(value):
        fail(f"{label}: use lowercase letters, digits and hyphens, starting with a letter")
    return value


def list_of(value, label):
    if not isinstance(value, list):
        fail(f"{label}: must be a list")
    return value


def mapping(value, label):
    if not isinstance(value, dict):
        fail(f"{label}: must be an object")
    return value


def unique(items, label):
    if len(items) != len(set(items)):
        fail(f"{label}: duplicate IDs or rows")


def stage_dir(root, index):
    return root / f"{index + 1:02d}-{STAGES[index][0]}"


def safe_file(base, rel, label, suffixes=None):
    required(rel, label)
    path = PurePosixPath(rel)
    if path.is_absolute() or ".." in path.parts or "." in path.parts or "\\" in rel or rel.startswith("~"):
        fail(f"{label}: path must be relative and stay inside its stage")
    if suffixes and path.suffix.lower() not in suffixes:
        fail(f"{label}: unsupported viewable file type")
    target = base.joinpath(*path.parts)
    cursor = base
    for part in path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            fail(f"{label}: symlinks are not allowed")
    if not target.is_file() or target.stat().st_size == 0:
        fail(f"{label}: missing or empty file {rel}")
    return target


def read_json(path, label):
    if path.is_symlink() or not path.is_file():
        fail(f"{label}: missing regular file")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        fail(f"{label}: invalid JSON: {exc}")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_file_hashes(directory):
    """Freeze every local delivery file, including unlisted prototype dependencies."""
    hashes = {}
    for folder, dirs, files in os.walk(directory, followlinks=False):
        base = Path(folder)
        for name in dirs:
            if (base / name).is_symlink():
                fail(f"{directory.name}: symlink directory is not allowed: {base / name}")
        dirs[:] = sorted(name for name in dirs if name not in CACHE_DIRS)
        for name in sorted(files):
            path = base / name
            if path.is_symlink():
                fail(f"{directory.name}: symlink file is not allowed: {path}")
            if base == directory and name in {"stage.json", "snapshot.json"}:
                continue
            if name in CACHE_FILES or name.endswith(".pyc"):
                continue
            if not path.is_file():
                fail(f"{directory.name}: non-regular delivery file: {path}")
            hashes[path.relative_to(directory).as_posix()] = sha(path)
    return dict(sorted(hashes.items()))


def init(root):
    if root.exists() or root.is_symlink():
        fail(f"init refuses to overwrite existing path: {root}")
    root.mkdir(parents=True)
    (root / "delivery.json").write_text(json.dumps({
        "schema_version": 2,
        "project": {"id": "", "name": "", "revision": ""},
        "viewports": [{"id": "desktop", "width": 1440, "height": 900},
                      {"id": "mobile", "width": 390, "height": 844}],
        "pages": [], "journeys": [],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for index, (slug, artifacts) in enumerate(STAGES):
        directory = stage_dir(root, index)
        directory.mkdir()
        (directory / "stage.json").write_text(json.dumps({
            "stage": slug, "status": "draft", "reason": "",
            "review": {"verdict": "pending", "by": "", "note": ""},
            "artifacts": list(artifacts),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for artifact in artifacts:
            path = directory / artifact
            if artifact.endswith(".md"):
                path.write_text("# Draft — replace with authored content\n", encoding="utf-8")
            else:
                path.write_text(json.dumps(SCAFFOLDS[artifact], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if slug == "frontend-implementation":
            (directory / "runtime-manifest.json").write_text('{"files": {}}\n', encoding="utf-8")
    print(f"Created schema 2 draft UI delivery at {root}")


def registry(root):
    data = mapping(read_json(root / "delivery.json", "delivery.json"), "delivery.json")
    if data.get("schema_version") not in {1, 2}:
        fail("delivery.json: schema_version must be 1 or 2")
    project = mapping(data.get("project"), "project")
    identifier(project.get("id"), "project.id")
    required(project.get("name"), "project.name")
    required(project.get("revision"), "project.revision")
    viewports = list_of(data.get("viewports"), "viewports")
    vp_ids = []
    widths = {}
    for vp in viewports:
        vp = mapping(vp, "viewport")
        vid = identifier(vp.get("id"), "viewport.id")
        if type(vp.get("width")) is not int or type(vp.get("height")) is not int or vp["width"] <= 0 or vp["height"] <= 0:
            fail(f"viewport {vid}: width and height must be positive integers")
        vp_ids.append(vid)
        widths[vid] = vp["width"]
    unique(vp_ids, "viewports")
    if "mobile" not in widths or widths["mobile"] > 480 or "desktop" not in widths or widths["desktop"] < 800:
        fail("viewports: define desktop width >=800 and mobile width <=480")
    pages = list_of(data.get("pages"), "pages")
    if not pages:
        fail("delivery.json: at least one page is required")
    page_ids, screen_ids, state_ids, combos = [], [], [], set()
    route_by_screen, page_by_screen, states_by_screen = {}, {}, {}
    for page in pages:
        page = mapping(page, "page")
        pid = identifier(page.get("id"), "page.id")
        route = required(page.get("route"), f"page {pid}.route")
        if not route.startswith("/") or route.startswith("//"):
            fail(f"page {pid}.route: must be an app-relative route")
        page_ids.append(pid)
        screens = list_of(page.get("screens"), f"page {pid}.screens")
        if not screens:
            fail(f"page {pid}: at least one screen required")
        for screen in screens:
            screen = mapping(screen, "screen")
            sid = identifier(screen.get("id"), "screen.id")
            screen_ids.append(sid)
            route_by_screen[sid] = route
            page_by_screen[sid] = pid
            states = list_of(screen.get("states"), f"screen {sid}.states")
            kinds, local_states = [], []
            for state in states:
                state = mapping(state, "state")
                stid = identifier(state.get("id"), "state.id")
                kind = state.get("kind")
                if kind not in KINDS:
                    fail(f"state {stid}: unknown kind {kind}")
                state_ids.append(stid)
                local_states.append(stid)
                kinds.append(kind)
                for vid in vp_ids:
                    combos.add((sid, stid, vid))
            if set(kinds) != KINDS:
                fail(f"screen {sid}: declare all six canonical state kinds")
            states_by_screen[sid] = local_states
    unique(page_ids, "page")
    unique(screen_ids, "screen")
    unique(state_ids, "state")
    routes = [page["route"] for page in pages]
    unique(routes, "route")
    journeys = {}
    if data["schema_version"] == 2:
        covered_pages = set()
        for journey in list_of(data.get("journeys"), "journeys"):
            journey = mapping(journey, "journey")
            jid = identifier(journey.get("id"), "journey.id")
            if jid in journeys:
                fail(f"journey: duplicate ID {jid}")
            steps = list_of(journey.get("steps"), f"journey {jid}.steps")
            if not steps:
                fail(f"journey {jid}: at least one step required")
            for step in steps:
                step = mapping(step, f"journey {jid} step")
                sid, state_id = step.get("screen_id"), step.get("state_id")
                if sid not in screen_ids or state_id not in states_by_screen.get(sid, []) or step.get("page_id") != page_by_screen.get(sid):
                    fail(f"journey {jid}: unknown page/screen/state step")
                required(step.get("action"), f"journey {jid}.action")
                covered_pages.add(step["page_id"])
            journeys[jid] = steps
        if covered_pages != set(page_ids):
            fail(f"journeys: uncovered pages {sorted(set(page_ids) - covered_pages)}")
    return {"data": data, "version": data["schema_version"], "journeys": journeys,
            "pages": pages, "page_ids": set(page_ids), "screen_ids": set(screen_ids),
            "state_ids": set(state_ids), "viewports": set(vp_ids), "combos": combos,
            "route_by_screen": route_by_screen, "page_by_screen": page_by_screen,
            "states_by_screen": states_by_screen, "default_states_by_screen": {
                screen["id"]: {state["id"] for state in screen["states"] if state["kind"] == "default"}
                for page in pages for screen in page["screens"]}, "revision": project["revision"]}


def stage_meta(directory, index):
    if directory.is_symlink() or not directory.is_dir():
        fail(f"{STAGES[index][0]}: missing regular stage directory")
    data = mapping(read_json(directory / "stage.json", "stage.json"), "stage.json")
    slug, artifacts = STAGES[index]
    if data.get("stage") != slug:
        fail(f"{slug}: stage.json stage mismatch")
    if data.get("status") not in {"draft", "ready", "blocked", "skipped"}:
        fail(f"{slug}: invalid status")
    if data["status"] in {"draft", "blocked"}:
        fail(f"{slug}: status {data['status']} cannot pass")
    review = mapping(data.get("review"), f"{slug}.review")
    if review.get("verdict") != "approved" or not review.get("by") or not review.get("note"):
        fail(f"{slug}: main controller or human review approval record required")
    if data["status"] == "skipped":
        if slug != "motion-design":
            fail(f"{slug}: critical stage cannot be skipped")
        required(data.get("reason"), f"{slug}.reason")
    listed = list_of(data.get("artifacts"), f"{slug}.artifacts")
    if listed != list(artifacts):
        fail(f"{slug}: artifact list must exactly match contract")
    for name in artifacts:
        path = safe_file(directory, name, f"{slug}/{name}")
        if name.endswith(".md"):
            content = path.read_text(encoding="utf-8").strip()
            if len(content) < 30 or content.startswith("# Draft —"):
                fail(f"{slug}/{name}: draft or insufficient narrative")
        if name.endswith(".json"):
            read_json(path, f"{slug}/{name}")
    return data, artifacts


def matrix(root, reg):
    data = mapping(read_json(stage_dir(root, 1) / "state-matrix.json", "state-matrix.json"), "state-matrix.json")
    rows = list_of(data.get("rows"), "state-matrix.rows")
    seen, applicable = set(), set()
    for row in rows:
        row = mapping(row, "state-matrix row")
        key = (row.get("screen_id"), row.get("state_id"), row.get("viewport_id"))
        if key not in reg["combos"] or row.get("page_id") != reg["page_by_screen"].get(row.get("screen_id")):
            fail(f"state-matrix: unknown page/screen/state/viewport combination {key}")
        if key in seen:
            fail(f"state-matrix: duplicate combination {key}")
        seen.add(key)
        if row.get("applicability") == "applicable":
            required(row.get("behavior"), f"state-matrix {key}.behavior")
            applicable.add(key)
        elif row.get("applicability") == "not_applicable":
            required(row.get("reason"), f"state-matrix {key}.reason")
        else:
            fail(f"state-matrix {key}: invalid applicability")
    if seen != reg["combos"]:
        fail(f"state-matrix: missing {len(reg['combos'] - seen)} declared screen/state/viewport combinations")
    for sid in reg["screen_ids"]:
        for vid in reg["viewports"]:
            if not any((sid, state_id, vid) in applicable for state_id in reg["default_states_by_screen"][sid]):
                fail(f"state-matrix: screen {sid} has no applicable default state for {vid}")
    return applicable


def digest(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        fail(f"{label}: must be a lowercase SHA-256 digest")
    return value


def raster_signature(path, label):
    image = path.read_bytes()
    ext = path.suffix.lower()
    if not ((ext == ".png" and image.startswith(b"\x89PNG\r\n\x1a\n")) or
            (ext in {".jpg", ".jpeg"} and image.startswith(b"\xff\xd8\xff")) or
            (ext == ".webp" and image.startswith(b"RIFF") and image[8:12] == b"WEBP")):
        fail(f"{label}: raster image signature does not match extension")


def v2_requirements(root, reg):
    rows = read_json(stage_dir(root, 1) / "state-matrix.json", "state-matrix.json")["rows"]
    requirements = {}
    for row in rows:
        if row["applicability"] != "applicable":
            continue
        key = (row["screen_id"], row["state_id"], row["viewport_id"])
        elements = list_of(row.get("required_elements"), f"state-matrix {key}.required_elements")
        ids = []
        for element in elements:
            element = mapping(element, f"required element {key}")
            ids.append(identifier(element.get("id"), f"required element {key}.id"))
            if element.get("role") not in ELEMENT_ROLES:
                fail(f"required element {key}/{element['id']}: role must be navigation/control/content/decoration")
            if element["role"] in {"navigation", "control"}:
                identifier(element.get("component_id"), f"required element {key}.component_id")
            elif element.get("component_id") is not None:
                identifier(element["component_id"], f"required element {key}.component_id")
        unique(ids, f"required elements {key}")
        if row["state_id"] in reg["default_states_by_screen"][row["screen_id"]] and not elements:
            fail(f"state-matrix {key}: default state needs required elements")
        requirements[key] = elements
    return requirements


def v2_components(root, reg):
    directory = stage_dir(root, 3)
    data = read_json(directory / "component-inventory.json", "component-inventory.json")
    result = {}
    for component in list_of(data.get("components"), "components"):
        component = mapping(component, "component")
        cid = identifier(component.get("id"), "component.id")
        if cid in result:
            fail(f"component: duplicate ID {cid}")
        required(component.get("revision"), f"component {cid}.revision")
        safe_file(directory, component.get("master_path"), f"component {cid}.master_path")
        if component.get("render_mode") not in {"code", "figma", "structured", "raster"}:
            fail(f"component {cid}: invalid render_mode")
        used_by = list_of(component.get("used_by"), f"component {cid}.used_by")
        if not used_by or len(used_by) != len(set(used_by)) or any(sid not in reg["screen_ids"] for sid in used_by):
            fail(f"component {cid}: used_by must contain unique known screens")
        result[cid] = component
    for key, elements in v2_requirements(root, reg).items():
        for element in elements:
            cid = element.get("component_id")
            if cid:
                component = result.get(cid)
                if not component or key[0] not in component["used_by"]:
                    fail(f"required element {key}/{element['id']}: missing component or used_by")
                if element["role"] in {"navigation", "control"} and component["render_mode"] == "raster":
                    fail(f"required element {key}/{element['id']}: interactive component cannot be raster")
    return result


def v2_specs(root, reg):
    directory = stage_dir(root, 4)
    data = read_json(directory / "screen-specs.json", "screen-specs.json")
    reqs, components = v2_requirements(root, reg), v2_components(root, reg)
    result, defaults = {}, {}
    for spec in list_of(data.get("specs"), "screen-specs.specs"):
        spec = mapping(spec, "screen spec")
        key = (spec.get("screen_id"), spec.get("state_id"), spec.get("viewport_id"))
        if key not in reqs or key in result:
            fail(f"screen-specs: unexpected or duplicate combination {key}")
        expected_ids = {el["id"] for el in reqs[key]}
        ids = list_of(spec.get("element_ids"), f"screen-specs {key}.element_ids")
        if len(ids) != len(set(ids)) or set(ids) != expected_ids:
            fail(f"screen-specs {key}: element_ids differ from required_elements")
        expected_refs = {el["component_id"]: components[el["component_id"]]["revision"]
                         for el in reqs[key] if el.get("component_id")}
        refs = list_of(spec.get("component_refs"), f"screen-specs {key}.component_refs")
        actual_refs = {}
        for ref in refs:
            ref = mapping(ref, "component ref")
            cid = identifier(ref.get("id"), "component ref.id")
            if cid in actual_refs:
                fail(f"screen-specs {key}: duplicate component ref")
            actual_refs[cid] = required(ref.get("revision"), "component ref.revision")
        if actual_refs != expected_refs:
            fail(f"screen-specs {key}: component refs/revisions differ from design system")
        review = mapping(spec.get("review"), f"screen-specs {key}.review")
        required(review.get("by"), f"screen-specs {key}.review.by")
        required(review.get("note"), f"screen-specs {key}.review.note")
        mode = spec.get("visual_mode")
        if mode == "full":
            if spec.get("asset_kind") not in {"design", "render"}:
                fail(f"screen-specs {key}: full visual requires design/render asset")
            image = safe_file(directory, spec.get("asset_path"), f"screen-specs {key}.asset_path", RUNTIME_SUFFIXES)
            raster_signature(image, f"screen-specs {key}.asset_path")
            spec["_baseline_sha256"] = sha(image)
        elif mode == "delta":
            required(spec.get("state_delta"), f"screen-specs {key}.state_delta")
            if spec.get("base_state_id") not in reg["default_states_by_screen"][key[0]]:
                fail(f"screen-specs {key}: delta must refer to a default state")
            if spec.get("asset_path") or spec.get("asset_kind"):
                fail(f"screen-specs {key}: delta cannot pose as a full asset")
        else:
            fail(f"screen-specs {key}: visual_mode must be full or delta")
        measurements = list_of(spec.get("measurements"), f"screen-specs {key}.measurements")
        mids = []
        for item in measurements:
            item = mapping(item, "measurement")
            mids.append(identifier(item.get("id"), "measurement.id"))
            if item.get("element_id") not in expected_ids:
                fail(f"screen-specs {key}: measurement refers to unknown element")
            required(item.get("property"), "measurement.property")
            required(item.get("unit"), "measurement.unit")
            if (type(item.get("expected")) not in {int, float} or type(item.get("tolerance")) not in {int, float}
                    or not math.isfinite(item["expected"]) or not math.isfinite(item["tolerance"]) or item["tolerance"] < 0):
                fail(f"screen-specs {key}: measurement needs numeric expected/nonnegative tolerance")
        unique(mids, f"screen-specs {key}.measurements")
        if key[1] in reg["default_states_by_screen"][key[0]]:
            if mode != "full" or not measurements:
                fail(f"screen-specs {key}: default visual needs full image and a critical measurement")
            defaults[key] = spec
        result[key] = spec
    if set(result) != set(reqs):
        fail(f"screen-specs: missing {len(set(reqs) - set(result))} applicable states")
    for key, spec in result.items():
        if spec["visual_mode"] == "delta" and (key[0], spec["base_state_id"], key[2]) not in defaults:
            fail(f"screen-specs {key}: missing full default baseline")
    for prototype in list_of(data.get("prototypes", []), "screen-specs.prototypes"):
        prototype = mapping(prototype, "prototype")
        if prototype.get("journey_id") not in reg["journeys"]:
            fail("screen-specs prototype: unknown journey")
        safe_file(directory, prototype.get("path"), "screen-specs prototype.path", {".html"})
    return result


def v2_implementation(root, reg):
    directory = stage_dir(root, 6)
    data = mapping(read_json(directory / "implementation-map.json", "implementation-map.json"), "implementation-map.json")
    if data.get("revision") != reg["revision"]:
        fail("implementation-map: revision differs from delivery.json")
    routes = list_of(data.get("routes"), "implementation routes")
    if len(routes) != len(reg["pages"]):
        fail("implementation-map: route count differs from registry")
    seen_routes = set()
    for route in routes:
        route = mapping(route, "implementation route")
        pid = route.get("page_id")
        if pid in seen_routes or pid not in reg["page_ids"]:
            fail("implementation-map: duplicate or unknown page")
        seen_routes.add(pid)
        page = next(p for p in reg["pages"] if p["id"] == pid)
        screens = list_of(route.get("screen_ids"), "implementation screen IDs")
        if route.get("route") != page["route"] or len(screens) != len(set(screens)) or set(screens) != {s["id"] for s in page["screens"]}:
            fail(f"implementation-map: wrong route or screens for {pid}")
    required(data.get("implemented_by"), "implementation-map.implemented_by")
    manifest_path = safe_file(directory, data.get("runtime_manifest_path"), "runtime_manifest_path", {".json"})
    digest(data.get("runtime_fingerprint"), "runtime_fingerprint")
    if sha(manifest_path) != data["runtime_fingerprint"]:
        fail("runtime_fingerprint: does not match runtime manifest")
    manifest = mapping(read_json(manifest_path, "runtime manifest"), "runtime manifest")
    files = mapping(manifest.get("files"), "runtime manifest.files")
    if not files:
        fail("runtime manifest.files: at least one file required")
    for rel, expected_sha in files.items():
        file = safe_file(directory, rel, f"runtime manifest file {rel}")
        digest(expected_sha, f"runtime manifest file {rel} hash")
        if sha(file) != expected_sha:
            fail(f"runtime manifest file {rel}: hash mismatch")
    reqs = v2_requirements(root, reg)
    expected = {(key[0], el["id"]) for key, elements in reqs.items() for el in elements}
    actual = set()
    for item in list_of(data.get("elements"), "implementation elements"):
        item = mapping(item, "implemented element")
        key = (item.get("screen_id"), item.get("element_id"))
        if key in actual:
            fail(f"implementation-map: duplicate element {key}")
        actual.add(key)
        rel = required(item.get("code_path"), f"implementation element {key}.code_path")
        if rel not in files:
            fail(f"implementation element {key}: code_path absent from runtime manifest")
    if actual != expected:
        fail(f"implementation-map: element coverage differs from required elements")
    components = v2_components(root, reg)
    expected_refs = {cid: comp["revision"] for cid, comp in components.items()
                     if any(cid == el.get("component_id") for elements in reqs.values() for el in elements)}
    actual_refs = {}
    for item in list_of(data.get("components"), "implementation components"):
        item = mapping(item, "implementation component")
        cid = identifier(item.get("id"), "implementation component.id")
        if cid in actual_refs:
            fail(f"implementation-map: duplicate component {cid}")
        actual_refs[cid] = required(item.get("revision"), "implementation component.revision")
    if actual_refs != expected_refs:
        fail("implementation-map: component revisions differ from design system")
    return data


def v2_qa(root, reg):
    directory = stage_dir(root, 7)
    reqs = v2_requirements(root, reg)
    specs = v2_specs(root, reg)
    implementation = v2_implementation(root, reg)
    evidence_data = mapping(read_json(directory / "evidence.json", "evidence.json"), "evidence.json")
    evidence = {}
    for item in list_of(evidence_data.get("items"), "evidence.items"):
        item = mapping(item, "evidence item")
        eid = identifier(item.get("id"), "evidence.id")
        if eid in evidence:
            fail(f"evidence: duplicate ID {eid}")
        if item.get("kind") not in {"runtime_capture", "concept", "mock"}:
            fail(f"evidence {eid}: invalid kind")
        file = safe_file(directory, item.get("path"), f"evidence {eid}.path",
                         RUNTIME_SUFFIXES if item["kind"] == "runtime_capture" else IMAGE_SUFFIXES)
        matches = [key for key in reqs if key[1] == item.get("state_id") and key[2] == item.get("viewport_id")]
        if len(matches) != 1 or item.get("route") != reg["route_by_screen"][matches[0][0]]:
            fail(f"evidence {eid}: route/state/viewport mismatch")
        if item.get("revision") != reg["revision"]:
            fail(f"evidence {eid}: revision mismatch")
        if item["kind"] == "runtime_capture":
            raster_signature(file, f"evidence {eid}")
            required(item.get("captured_at"), f"evidence {eid}.captured_at")
            url = urlparse(required(item.get("source_url"), f"evidence {eid}.source_url"))
            if url.scheme not in {"http", "https"} or not url.netloc or url.path != item["route"]:
                fail(f"evidence {eid}: source_url must match route")
            if item.get("runtime_fingerprint") != implementation["runtime_fingerprint"]:
                fail(f"evidence {eid}: runtime fingerprint mismatch")
        evidence[eid] = item
    matrix_data = mapping(read_json(directory / "qa-matrix.json", "qa-matrix.json"), "qa-matrix.json")
    seen = set()
    for row in list_of(matrix_data.get("rows"), "qa-matrix.rows"):
        row = mapping(row, "QA row")
        key = (row.get("screen_id"), row.get("state_id"), row.get("viewport_id"))
        if key not in reqs or key in seen:
            fail(f"qa-matrix: unexpected or duplicate combination {key}")
        seen.add(key)
        if row.get("result") != "pass":
            fail(f"qa-matrix {key}: unresolved result")
        eids = list_of(row.get("evidence_ids"), f"qa-matrix {key}.evidence_ids")
        if any(eid not in evidence for eid in eids):
            fail(f"qa-matrix {key}: unknown evidence ID")
        matching_eids = {eid for eid in eids if eid in evidence and evidence[eid]["kind"] == "runtime_capture"
                         and evidence[eid]["state_id"] == key[1] and evidence[eid]["viewport_id"] == key[2]}
        if not matching_eids:
            fail(f"qa-matrix {key}: matching runtime capture required")
        base = specs[key]
        if base["visual_mode"] == "delta":
            base = specs[(key[0], base["base_state_id"], key[2])]
        if row.get("baseline_sha256") != base["_baseline_sha256"]:
            fail(f"qa-matrix {key}: design baseline hash mismatch")
        safe_file(directory, row.get("comparison_path"), f"qa-matrix {key}.comparison_path",
                  {".md", ".html", ".png", ".jpg", ".jpeg", ".webp"})
        expected_elements = {el["id"] for el in reqs[key]}
        checked = set()
        for check in list_of(row.get("element_checks"), f"qa-matrix {key}.element_checks"):
            check = mapping(check, "element check")
            element_id = check.get("element_id")
            if element_id in checked or element_id not in expected_elements or check.get("result") != "pass" or check.get("evidence_id") not in matching_eids:
                fail(f"qa-matrix {key}: invalid element check {element_id}")
            checked.add(element_id)
        if checked != expected_elements:
            fail(f"qa-matrix {key}: missing element checks")
        expected_measurements = ({item["id"]: item for item in base["measurements"]}
                                 if specs[key]["visual_mode"] == "delta" else {})
        expected_measurements.update({item["id"]: item for item in specs[key]["measurements"]})
        measured = set()
        for check in list_of(row.get("measurements"), f"qa-matrix {key}.measurements"):
            check = mapping(check, "measurement check")
            mid = check.get("id")
            if mid in measured or mid not in expected_measurements or check.get("evidence_id") not in matching_eids:
                fail(f"qa-matrix {key}: invalid measurement check {mid}")
            measured.add(mid)
            actual = check.get("actual")
            target = expected_measurements[mid]
            if type(actual) not in {int, float} or not math.isfinite(actual) or abs(actual - target["expected"]) > target["tolerance"]:
                fail(f"qa-matrix {key}: measurement {mid} outside tolerance")
        if measured != set(expected_measurements):
            fail(f"qa-matrix {key}: missing measurements")
    if seen != set(reqs):
        fail(f"qa-matrix: missing {len(set(reqs) - seen)} applicable cases")
    expected_journeys = {(jid, vp) for jid in reg["journeys"] for vp in reg["viewports"]}
    seen_journeys = set()
    for result in list_of(matrix_data.get("journey_results"), "qa-matrix.journey_results"):
        result = mapping(result, "journey result")
        key = (result.get("journey_id"), result.get("viewport_id"))
        if key not in expected_journeys or key in seen_journeys or result.get("result") != "pass":
            fail(f"journey result {key}: unexpected, duplicate or unresolved")
        seen_journeys.add(key)
        steps = list_of(result.get("steps"), f"journey {key}.steps")
        expected_steps = reg["journeys"][key[0]]
        if len(steps) != len(expected_steps):
            fail(f"journey {key}: step count mismatch")
        for index, (step, expected_step) in enumerate(zip(steps, expected_steps)):
            step = mapping(step, f"journey {key} step {index}")
            if step.get("action") != expected_step["action"]:
                fail(f"journey {key} step {index}: action mismatch")
            required(step.get("observed_result"), f"journey {key} step {index}.observed_result")
            safe_file(directory, step.get("interaction_path"), f"journey {key} step {index}.interaction_path")
            eid = step.get("evidence_id")
            item = evidence.get(eid)
            if not item or item["kind"] != "runtime_capture" or item["state_id"] != expected_step["state_id"] or item["viewport_id"] != key[1] or item["route"] != reg["route_by_screen"][expected_step["screen_id"]]:
                fail(f"journey {key} step {index}: runtime evidence mismatch")
    if seen_journeys != expected_journeys:
        fail("qa-matrix: missing journey viewport results")
    verdict = mapping(read_json(directory / "verdict.json", "verdict.json"), "verdict.json")
    if verdict.get("verdict") != "pass":
        fail("verdict: must be pass")
    required(verdict.get("by"), "verdict.by")
    required(verdict.get("basis"), "verdict.basis")
    reviewer = required(verdict.get("reviewed_by"), "verdict.reviewed_by")
    if reviewer == implementation["implemented_by"]:
        fail("verdict: implementation author cannot self-review")
    if list_of(verdict.get("open_blockers"), "verdict.open_blockers"):
        fail("verdict: open blockers prevent pass")


def semantic(root, index, reg):
    directory = stage_dir(root, index)
    if reg["version"] == 2 and index == 1:
        matrix(root, reg)
        v2_requirements(root, reg)
        return
    if reg["version"] == 2 and index == 3:
        tokens = mapping(read_json(directory / "tokens.json", "tokens.json"), "tokens.json")
        for field in ("colors", "typography", "spacing", "layout"):
            if not mapping(tokens.get(field), f"tokens.{field}"):
                fail(f"tokens.{field}: at least one token required")
        style = read_json(stage_dir(root, 2) / "style-decision.json", "style-decision.json")
        selected = next(option for option in style["options"] if option["id"] == style["selected_id"])
        image = safe_file(stage_dir(root, 2), selected["concept_path"], "selected visual option")
        if tokens.get("style_sha256") != sha(image):
            fail("tokens.style_sha256: selected visual baseline hash mismatch")
        v2_components(root, reg)
        return
    if reg["version"] == 2 and index == 4:
        v2_specs(root, reg)
        return
    if reg["version"] == 2 and index == 6:
        v2_implementation(root, reg)
        return
    if reg["version"] == 2 and index == 7:
        v2_qa(root, reg)
        return
    if index == 0:
        data = mapping(read_json(directory / "page-inventory.json", "page-inventory.json"), "page-inventory.json")
        pages = list_of(data.get("pages"), "page-inventory.pages")
        ids = [p.get("id") for p in pages if isinstance(p, dict)]
        unique(ids, "page-inventory.pages")
        if set(ids) != reg["page_ids"]:
            fail("page-inventory: page IDs must exactly match delivery.json")
        for page in pages:
            target = next(p for p in reg["pages"] if p["id"] == page["id"])
            if set(list_of(page.get("screen_ids"), "screen_ids")) != {s["id"] for s in target["screens"]}:
                fail(f"page-inventory {page['id']}: screen IDs do not match delivery.json")
    elif index == 1:
        matrix(root, reg)
    elif index == 2:
        data = mapping(read_json(directory / "style-decision.json", "style-decision.json"), "style-decision.json")
        options = list_of(data.get("options"), "style options")
        if not options:
            fail("style-decision: at least one visual option required")
        ids = []
        for option in options:
            option = mapping(option, "style option")
            oid = identifier(option.get("id"), "style option.id")
            ids.append(oid)
            if option.get("source_kind") not in {"concept", "provided_reference"}:
                fail(f"style option {oid}: source_kind must be concept or provided_reference")
            concept = safe_file(directory, option.get("concept_path"), f"style option {oid}.concept_path", IMAGE_SUFFIXES)
            if reg["version"] == 2 and option["source_kind"] == "concept":
                if concept.suffix.lower() not in RUNTIME_SUFFIXES:
                    fail(f"style option {oid}: generated concept needs PNG/JPEG/WebP raster")
                raster_signature(concept, f"style option {oid}")
        unique(ids, "style options")
        if data.get("selected_id") not in ids:
            fail("style-decision: selected_id must name a real option")
        selection = mapping(data.get("selection"), "style selection")
        if selection.get("by") not in {"user", "authorized_agent"}:
            fail("style selection: by must be user or authorized_agent")
        required(selection.get("evidence"), "style selection.evidence")
        if selection["by"] == "authorized_agent":
            required(selection.get("authorization"), "style selection.authorization")
    elif index == 3:
        tokens = mapping(read_json(directory / "tokens.json", "tokens.json"), "tokens.json")
        if not mapping(tokens.get("colors"), "tokens.colors"):
            fail("tokens.colors: at least one color required")
        components = mapping(read_json(directory / "component-inventory.json", "component-inventory.json"), "component-inventory.json")
        for component in list_of(components.get("components"), "components"):
            identifier(component.get("id"), "component.id")
            for sid in list_of(component.get("used_by"), "component.used_by"):
                if sid not in reg["screen_ids"]:
                    fail(f"component: unknown screen {sid}")
    elif index == 4:
        data = mapping(read_json(directory / "screen-specs.json", "screen-specs.json"), "screen-specs.json")
        specs = list_of(data.get("specs"), "screen-specs.specs")
        applicable = matrix(root, reg)
        seen = set()
        for spec in specs:
            spec = mapping(spec, "screen spec")
            key = (spec.get("screen_id"), spec.get("state_id"), spec.get("viewport_id"))
            if key not in applicable or key in seen:
                fail(f"screen-specs: unexpected or duplicate combination {key}")
            seen.add(key)
            if spec.get("asset_kind") not in {"mock", "design", "render", "prototype"}:
                fail(f"screen-specs {key}: asset_kind must be mock/design/render/prototype")
            safe_file(directory, spec.get("asset_path"), f"screen-specs {key}.asset_path", IMAGE_SUFFIXES)
        if seen != applicable:
            fail(f"screen-specs: missing {len(applicable - seen)} applicable state/viewport designs")
    elif index == 5:
        data = mapping(read_json(directory / "motion-map.json", "motion-map.json"), "motion-map.json")
        motions = list_of(data.get("motions"), "motion-map.motions")
        ids = []
        for motion in motions:
            motion = mapping(motion, "motion")
            ids.append(identifier(motion.get("id"), "motion.id"))
            if motion.get("screen_id") not in reg["screen_ids"] or motion.get("state_id") not in reg["states_by_screen"].get(motion.get("screen_id"), []):
                fail("motion-map: unknown screen/state")
            required(motion.get("reduced_motion"), "motion.reduced_motion")
        unique(ids, "motion IDs")
    elif index == 6:
        data = mapping(read_json(directory / "implementation-map.json", "implementation-map.json"), "implementation-map.json")
        if data.get("revision") != reg["revision"]:
            fail("implementation-map: revision differs from delivery.json")
        routes = list_of(data.get("routes"), "implementation routes")
        ids = [r.get("page_id") for r in routes if isinstance(r, dict)]
        unique(ids, "implementation page IDs")
        if set(ids) != reg["page_ids"]:
            fail("implementation-map: missing page")
        for route in routes:
            page = next(p for p in reg["pages"] if p["id"] == route["page_id"])
            if route.get("route") != page["route"] or set(list_of(route.get("screen_ids"), "implementation screen IDs")) != {s["id"] for s in page["screens"]}:
                fail(f"implementation-map: wrong route or screens for {page['id']}")
    elif index == 7:
        applicable = matrix(root, reg)
        data = mapping(read_json(directory / "evidence.json", "evidence.json"), "evidence.json")
        items = list_of(data.get("items"), "evidence.items")
        by_id = {}
        for item in items:
            item = mapping(item, "evidence item")
            eid = identifier(item.get("id"), "evidence.id")
            if eid in by_id:
                fail(f"evidence: duplicate ID {eid}")
            if item.get("kind") not in {"runtime_capture", "concept", "mock"}:
                fail(f"evidence {eid}: invalid kind")
            evidence_path = safe_file(directory, item.get("path"), f"evidence {eid}.path",
                                      RUNTIME_SUFFIXES if item["kind"] == "runtime_capture" else IMAGE_SUFFIXES)
            key = (None, item.get("state_id"), item.get("viewport_id"))
            matching = [combo for combo in applicable if combo[1:] == key[1:]]
            if len(matching) != 1 or item.get("route") != reg["route_by_screen"][matching[0][0]]:
                fail(f"evidence {eid}: route/state/viewport not in applicable registry")
            if item.get("revision") != reg["revision"]:
                fail(f"evidence {eid}: revision mismatch")
            if item["kind"] == "runtime_capture":
                required(item.get("captured_at"), f"evidence {eid}.captured_at")
                image = evidence_path.read_bytes()
                ext = evidence_path.suffix.lower()
                if not ((ext == ".png" and image.startswith(b"\x89PNG\r\n\x1a\n")) or
                        (ext in {".jpg", ".jpeg"} and image.startswith(b"\xff\xd8\xff")) or
                        (ext == ".webp" and image.startswith(b"RIFF") and image[8:12] == b"WEBP")):
                    fail(f"evidence {eid}: runtime capture needs a matching image signature")
            by_id[eid] = item
        rows = list_of(mapping(read_json(directory / "qa-matrix.json", "qa-matrix.json"), "qa-matrix.json").get("rows"), "qa-matrix.rows")
        seen = set()
        for row in rows:
            row = mapping(row, "QA row")
            key = (row.get("screen_id"), row.get("state_id"), row.get("viewport_id"))
            if key not in applicable or key in seen:
                fail(f"qa-matrix: unexpected or duplicate combination {key}")
            seen.add(key)
            if row.get("result") != "pass":
                fail(f"qa-matrix {key}: unresolved result")
            eids = list_of(row.get("evidence_ids"), f"qa-matrix {key}.evidence_ids")
            if not eids:
                fail(f"qa-matrix {key}: runtime evidence required")
            if any(eid not in by_id for eid in eids):
                fail(f"qa-matrix {key}: unknown evidence ID")
            if not any(eid in by_id and by_id[eid]["kind"] == "runtime_capture" and
                       by_id[eid]["state_id"] == key[1] and by_id[eid]["viewport_id"] == key[2]
                       for eid in eids):
                fail(f"qa-matrix {key}: no matching runtime capture")
        if seen != applicable:
            fail(f"qa-matrix: missing {len(applicable - seen)} applicable state/viewport cases")
        verdict = mapping(read_json(directory / "verdict.json", "verdict.json"), "verdict.json")
        if verdict.get("verdict") != "pass":
            fail("verdict: final main controller or human verdict must be pass")
        required(verdict.get("by"), "verdict.by")
        required(verdict.get("basis"), "verdict.basis")


def expected_snapshot(root, index, reg):
    directory = stage_dir(root, index)
    meta, _artifacts = stage_meta(directory, index)
    if meta["status"] in {"ready", "skipped"}:
        semantic(root, index, reg)
        if meta["status"] == "skipped" and read_json(directory / "motion-map.json", "motion-map.json").get("motions") != []:
            fail("motion-design: skipped stage must record an empty motions list")
    upstream = {"delivery.json": sha(root / "delivery.json")}
    if index:
        previous = stage_dir(root, index - 1) / "snapshot.json"
        safe_file(previous.parent, "snapshot.json", "previous stage snapshot")
        upstream[STAGES[index - 1][0]] = sha(previous)
    files = stage_file_hashes(directory)
    return {"schema_version": reg["version"], "stage": STAGES[index][0], "status": meta["status"],
            "stage_sha256": sha(directory / "stage.json"),
            "artifacts": files, "upstream": upstream}


def validate(root, through):
    if not root.is_dir() or root.is_symlink():
        fail(f"missing regular delivery directory: {root}")
    reg = registry(root)
    end = len(STAGES) if through is None else [s for s, _ in STAGES].index(through) + 1
    for index in range(end):
        slug = STAGES[index][0]
        snapshot_path = stage_dir(root, index) / "snapshot.json"
        actual = read_json(snapshot_path, f"{slug}/snapshot.json")
        expected = expected_snapshot(root, index, reg)
        if actual != expected:
            fail(f"{slug}: snapshot stale or contract metadata changed; review changes and snapshot again")
    return end


def snapshot(root, slug):
    if not root.is_dir() or root.is_symlink():
        fail(f"missing regular delivery directory: {root}")
    index = [s for s, _ in STAGES].index(slug)
    reg = registry(root)
    if index:
        validate(root, STAGES[index - 1][0])
    result = expected_snapshot(root, index, reg)
    path = stage_dir(root, index) / "snapshot.json"
    if path.is_symlink():
        fail(f"{slug}: snapshot path is a symlink")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tier = "legacy structural gate" if reg["version"] == 1 else "v2 fidelity contract gate"
    print(f"Snapshotted {slug} ({tier}); status remains {result['status']}. Mechanical checks do not prove visual quality.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init").add_argument("directory", type=Path)
    p = sub.add_parser("snapshot")
    p.add_argument("directory", type=Path)
    p.add_argument("--stage", choices=[s for s, _ in STAGES], required=True)
    p = sub.add_parser("validate")
    p.add_argument("directory", type=Path)
    p.add_argument("--through", choices=[s for s, _ in STAGES])
    args = parser.parse_args()
    try:
        if args.command == "init":
            init(args.directory)
        elif args.command == "snapshot":
            snapshot(args.directory, args.stage)
        else:
            count = validate(args.directory, args.through)
            version = registry(args.directory)["version"]
            tier = "legacy structural gate only; v2 fidelity checks were not run" if version == 1 else "v2 fidelity contract gate"
            print(f"Contract valid through {STAGES[count - 1][0]} ({tier}); human visual judgment is separate.")
        return 0
    except (ContractError, OSError, ValueError, TypeError, AttributeError, KeyError, StopIteration) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
