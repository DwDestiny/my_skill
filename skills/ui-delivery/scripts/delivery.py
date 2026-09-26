#!/usr/bin/env python3
# GEB-L3
# Input: Local UI delivery directory, stage metadata, and authored artifacts.
# Output: Draft scaffold, immutable-content snapshots, or deterministic contract diagnostics.
# Pos: Standard-library CLI for structural handoff checks; never judges visual quality or grants approval.

"""UI delivery contract scaffold and deterministic validator (Python 3.10+)."""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath


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
ID = re.compile(r"^[a-z][a-z0-9-]*$")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".pdf", ".html"}
RUNTIME_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
CACHE_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CACHE_FILES = {".DS_Store"}
SCAFFOLDS = {
    "page-inventory.json": {"pages": [{"id": "", "screen_ids": []}]},
    "state-matrix.json": {"rows": [{"page_id": "", "screen_id": "", "state_id": "", "viewport_id": "", "applicability": "applicable", "behavior": "", "reason": ""}]},
    "style-decision.json": {"options": [{"id": "", "concept_path": "", "source_kind": "concept"}], "selected_id": "", "selection": {"by": "", "evidence": "", "authorization": ""}},
    "tokens.json": {"colors": {}},
    "component-inventory.json": {"components": [{"id": "", "used_by": []}]},
    "screen-specs.json": {"specs": [{"screen_id": "", "state_id": "", "viewport_id": "", "asset_path": "", "asset_kind": "design", "notes": ""}]},
    "motion-map.json": {"motions": [{"id": "", "screen_id": "", "state_id": "", "reduced_motion": ""}]},
    "implementation-map.json": {"revision": "", "routes": [{"page_id": "", "route": "", "screen_ids": []}]},
    "qa-matrix.json": {"rows": [{"screen_id": "", "state_id": "", "viewport_id": "", "result": "pending", "evidence_ids": []}]},
    "evidence.json": {"items": [{"id": "", "kind": "", "path": "", "route": "", "viewport_id": "", "state_id": "", "revision": "", "captured_at": ""}]},
    "verdict.json": {"verdict": "pending", "by": "", "basis": ""},
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
        "schema_version": 1,
        "project": {"id": "", "name": "", "revision": ""},
        "viewports": [{"id": "desktop", "width": 1440, "height": 900},
                      {"id": "mobile", "width": 390, "height": 844}],
        "pages": [],
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
    print(f"Created draft UI delivery at {root}")


def registry(root):
    data = mapping(read_json(root / "delivery.json", "delivery.json"), "delivery.json")
    if data.get("schema_version") != 1:
        fail("delivery.json: schema_version must be 1")
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
    return {"data": data, "pages": pages, "page_ids": set(page_ids), "screen_ids": set(screen_ids),
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


def semantic(root, index, reg):
    directory = stage_dir(root, index)
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
            safe_file(directory, option.get("concept_path"), f"style option {oid}.concept_path", IMAGE_SUFFIXES)
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
    return {"schema_version": 1, "stage": STAGES[index][0], "status": meta["status"],
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
    print(f"Snapshotted {slug}; status remains {result['status']}. Mechanical checks do not prove visual quality.")


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
            print(f"Contract valid through {STAGES[count - 1][0]}; human visual judgment is separate.")
        return 0
    except (ContractError, OSError, ValueError, TypeError, AttributeError, KeyError, StopIteration) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
