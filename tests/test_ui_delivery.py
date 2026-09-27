# GEB-L3
# Input: ui-delivery CLI and isolated synthetic delivery fixtures.
# Output: Contract regression tests for structure, handoffs, provenance, and freshness.
# Pos: Repository-level deterministic test; fixtures are synthetic, not product acceptance evidence.

import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/ui-delivery/scripts/delivery.py"
STAGES = [
    "product-planning", "ux-architecture", "visual-direction", "design-system",
    "high-fidelity", "motion-design", "frontend-implementation", "visual-qa",
]
KINDS = ["default", "loading", "empty", "error", "permission_denied", "success"]
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/pZsAAAAASUVORK5CYII=")


def cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def put_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class DeliveryContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "delivery"
        result = cli("init", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def stage(self, index):
        return self.root / f"{index:02d}-{STAGES[index - 1]}"

    def make_ready_fixture(self):
        """Only a synthetic contract fixture; it makes no claim about visual quality."""
        pages = [{"id": "home", "route": "/", "screens": [{"id": "home-hero", "states": [
            {"id": f"home-hero-{kind.replace('_', '-')}", "kind": kind} for kind in KINDS
        ]}]}]
        put_json(self.root / "delivery.json", {"schema_version": 1, "project": {
            "id": "synthetic-project", "name": "Synthetic fixture", "revision": "fixture-r1"
        }, "viewports": [{"id": "desktop", "width": 1440, "height": 900},
                         {"id": "mobile", "width": 390, "height": 844}], "pages": pages})
        inventory = {"pages": [{"id": "home", "screen_ids": ["home-hero"]}]}
        put_json(self.stage(1) / "page-inventory.json", inventory)
        rows = []
        specs = []
        qa_rows = []
        evidence = []
        for kind in KINDS:
            state_id = f"home-hero-{kind.replace('_', '-')}"
            for viewport in ("desktop", "mobile"):
                rows.append({"page_id": "home", "screen_id": "home-hero", "state_id": state_id,
                             "viewport_id": viewport, "applicability": "applicable", "behavior": "fixture behavior"})
                image_path = f"assets/{kind}-{viewport}.png"
                (self.stage(5) / "assets").mkdir(exist_ok=True)
                (self.stage(5) / image_path).write_bytes(b"synthetic design bytes")
                specs.append({"screen_id": "home-hero", "state_id": state_id,
                              "viewport_id": viewport, "asset_path": image_path, "asset_kind": "mock"})
                evidence_path = f"captures/{kind}-{viewport}.png"
                (self.stage(8) / "captures").mkdir(exist_ok=True)
                (self.stage(8) / evidence_path).write_bytes(PNG)
                eid = f"capture-{kind.replace('_', '-')}-{viewport}"
                evidence.append({"id": eid, "kind": "runtime_capture", "path": evidence_path,
                                 "route": "/", "viewport_id": viewport, "state_id": state_id,
                                 "revision": "fixture-r1", "captured_at": "2026-01-01T00:00:00Z"})
                qa_rows.append({"screen_id": "home-hero", "state_id": state_id,
                                "viewport_id": viewport, "result": "pass", "evidence_ids": [eid]})
        put_json(self.stage(2) / "state-matrix.json", {"rows": rows})
        (self.stage(3) / "concepts").mkdir(exist_ok=True)
        (self.stage(3) / "concepts/option-a.png").write_bytes(b"synthetic concept bytes")
        (self.stage(3) / "concepts/option-b.png").write_bytes(b"synthetic alternative concept bytes")
        put_json(self.stage(3) / "style-decision.json", {"options": [
            {"id": "a", "concept_path": "concepts/option-a.png", "source_kind": "concept"},
            {"id": "b", "concept_path": "concepts/option-b.png", "source_kind": "concept"}],
            "selected_id": "a", "selection": {"by": "user", "evidence": "Fixture decision record"}})
        put_json(self.stage(4) / "tokens.json", {"colors": {"primary": "#123456"}})
        put_json(self.stage(4) / "component-inventory.json", {"components": [{"id": "hero", "used_by": ["home-hero"]}]})
        put_json(self.stage(5) / "screen-specs.json", {"specs": specs})
        put_json(self.stage(6) / "motion-map.json", {"motions": [{"id": "hero-enter", "screen_id": "home-hero", "state_id": "home-hero-default", "reduced_motion": "static"}]})
        put_json(self.stage(7) / "implementation-map.json", {"routes": [{"page_id": "home", "route": "/", "screen_ids": ["home-hero"]}], "revision": "fixture-r1"})
        put_json(self.stage(8) / "qa-matrix.json", {"rows": qa_rows})
        put_json(self.stage(8) / "evidence.json", {"items": evidence})
        put_json(self.stage(8) / "verdict.json", {"verdict": "pass", "by": "fixture-reviewer", "basis": "Synthetic contract fixture only"})
        for i in range(1, 9):
            stage = self.stage(i)
            for doc in stage.glob("*.md"):
                doc.write_text("# Synthetic fixture\n\nFilled contract narrative.\n", encoding="utf-8")
            data = json.loads((stage / "stage.json").read_text(encoding="utf-8"))
            data["status"] = "ready"
            data["review"] = {"verdict": "approved", "by": "fixture-reviewer", "note": "Synthetic contract fixture"}
            put_json(stage / "stage.json", data)
            result = cli("snapshot", self.root, "--stage", STAGES[i - 1])
            self.assertEqual(result.returncode, 0, result.stderr)

    def upgrade_v2_fixture(self):
        """Upgrade synthetic v1 data to the stricter v2 shape and resnapshot."""
        self.make_ready_fixture()
        path = self.root / "delivery.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["schema_version"] = 2
        data["journeys"] = [{"id": "visit-home", "steps": [{
            "page_id": "home", "screen_id": "home-hero", "state_id": "home-hero-default", "action": "open home"
        }]}]
        put_json(path, data)
        matrix_path = self.stage(2) / "state-matrix.json"
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        for row in matrix["rows"]:
            row["required_elements"] = [{"id": "shell", "role": "navigation", "component_id": "shell"}]
        put_json(matrix_path, matrix)
        style = json.loads((self.stage(3) / "style-decision.json").read_text(encoding="utf-8"))
        for option in style["options"]:
            (self.stage(3) / option["concept_path"]).write_bytes(PNG)
        chosen = next(x for x in style["options"] if x["id"] == style["selected_id"])
        style_sha = hashlib.sha256((self.stage(3) / chosen["concept_path"]).read_bytes()).hexdigest()
        put_json(self.stage(4) / "tokens.json", {"colors": {"primary": "#123456"},
                 "typography": {"body": "16px"}, "spacing": {"base": "8px"},
                 "layout": {"content": "1200px"}, "style_sha256": style_sha})
        (self.stage(4) / "shell.md").write_text("# Shell component\n\nNavigation specification.\n")
        put_json(self.stage(4) / "component-inventory.json", {"components": [{
            "id": "shell", "revision": "r1", "master_path": "shell.md", "render_mode": "code", "used_by": ["home-hero"]
        }]})
        specs_path = self.stage(5) / "screen-specs.json"
        specs = json.loads(specs_path.read_text(encoding="utf-8"))
        for spec in specs["specs"]:
            spec["element_ids"] = ["shell"]
            spec["component_refs"] = [{"id": "shell", "revision": "r1"}]
            spec["review"] = {"by": "fixture-designer", "note": "Synthetic screen review"}
            spec["measurements"] = []
            if spec["state_id"] == "home-hero-default":
                spec["visual_mode"] = "full"
                spec["asset_kind"] = "design"
                spec["measurements"] = [{"id": "gutter", "element_id": "shell", "property": "left-gap",
                                          "expected": 16, "unit": "px", "tolerance": 2}]
                (self.stage(5) / spec["asset_path"]).write_bytes(PNG)
            else:
                spec["visual_mode"] = "delta"
                spec["base_state_id"] = "home-hero-default"
                spec["state_delta"] = "State-specific feedback in the same shell"
                spec.pop("asset_path")
                spec.pop("asset_kind")
        put_json(specs_path, specs)
        implementation_path = self.stage(7) / "implementation-map.json"
        implementation = json.loads(implementation_path.read_text(encoding="utf-8"))
        (self.stage(7) / "src").mkdir()
        (self.stage(7) / "src/Shell.tsx").write_text("export const Shell = () => null;\n")
        code_sha = hashlib.sha256((self.stage(7) / "src/Shell.tsx").read_bytes()).hexdigest()
        put_json(self.stage(7) / "runtime-manifest.json", {"files": {"src/Shell.tsx": code_sha}})
        fingerprint = hashlib.sha256((self.stage(7) / "runtime-manifest.json").read_bytes()).hexdigest()
        implementation.update({"implemented_by": "fixture-developer", "runtime_manifest_path": "runtime-manifest.json",
                               "runtime_fingerprint": fingerprint, "elements": [{"screen_id": "home-hero",
                               "element_id": "shell", "code_path": "src/Shell.tsx"}],
                               "components": [{"id": "shell", "revision": "r1"}]})
        put_json(implementation_path, implementation)
        evidence_path = self.stage(8) / "evidence.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        for item in evidence["items"]:
            item["source_url"] = "http://localhost:3000/"
            item["runtime_fingerprint"] = fingerprint
        put_json(evidence_path, evidence)
        qa_path = self.stage(8) / "qa-matrix.json"
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        baseline = {spec["viewport_id"]: hashlib.sha256((self.stage(5) / spec["asset_path"]).read_bytes()).hexdigest()
                    for spec in specs["specs"] if spec["visual_mode"] == "full"}
        for row in qa["rows"]:
            row["baseline_sha256"] = baseline[row["viewport_id"]]
            row["element_checks"] = [{"element_id": "shell", "result": "pass", "evidence_id": row["evidence_ids"][0]}]
            row["measurements"] = [{"id": "gutter", "actual": 16, "evidence_id": row["evidence_ids"][0]}]
            row["comparison_path"] = "comparison.md"
        (self.stage(8) / "comparison.md").write_text(
            "# Synthetic comparison\n\nDesign baseline and runtime capture reviewed side by side.\n")
        (self.stage(8) / "interaction.txt").write_text("Opened home and observed shell.\n")
        qa["journey_results"] = [{"journey_id": "visit-home", "viewport_id": vp,
                                  "result": "pass", "steps": [{"action": "open home",
                                  "observed_result": "shell visible", "interaction_path": "interaction.txt",
                                  "evidence_id": f"capture-default-{vp}"}]}
                                 for vp in ("desktop", "mobile")]
        put_json(qa_path, qa)
        verdict_path = self.stage(8) / "verdict.json"
        verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
        verdict.update({"reviewed_by": "fixture-reviewer", "open_blockers": []})
        put_json(verdict_path, verdict)
        for slug in STAGES:
            result = cli("snapshot", self.root, "--stage", slug)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_v2_complete_synthetic_contract(self):
        self.upgrade_v2_fixture()
        self.assertEqual(cli("validate", self.root).returncode, 0)

    def test_v2_missing_journey_page_fails(self):
        self.upgrade_v2_fixture()
        path = self.root / "delivery.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["journeys"] = []
        put_json(path, data)
        self.assertNotEqual(cli("validate", self.root).returncode, 0)

    def test_v2_declared_tablet_requires_journey_result(self):
        self.upgrade_v2_fixture()
        delivery_path = self.root / "delivery.json"
        delivery = json.loads(delivery_path.read_text(encoding="utf-8"))
        delivery["viewports"].append({"id": "tablet", "width": 768, "height": 1024})
        put_json(delivery_path, delivery)
        for index, filename, member in (
            (2, "state-matrix.json", "rows"),
            (5, "screen-specs.json", "specs"),
            (8, "evidence.json", "items"),
            (8, "qa-matrix.json", "rows"),
        ):
            path = self.stage(index) / filename
            data = json.loads(path.read_text(encoding="utf-8"))
            clones = []
            for item in data[member]:
                if item["viewport_id"] != "mobile":
                    continue
                clone = json.loads(json.dumps(item))
                clone["viewport_id"] = "tablet"
                if member == "items":
                    clone["id"] = clone["id"].replace("mobile", "tablet")
                if member == "rows" and index == 8:
                    clone["evidence_ids"] = [eid.replace("mobile", "tablet") for eid in clone["evidence_ids"]]
                    for check in clone["element_checks"]:
                        check["evidence_id"] = check["evidence_id"].replace("mobile", "tablet")
                    for check in clone["measurements"]:
                        check["evidence_id"] = check["evidence_id"].replace("mobile", "tablet")
                clones.append(clone)
            data[member].extend(clones)
            put_json(path, data)
        for slug in STAGES[:-1]:
            result = cli("snapshot", self.root, "--stage", slug)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = cli("snapshot", self.root, "--stage", "visual-qa")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing journey viewport", result.stderr)
        qa_path = self.stage(8) / "qa-matrix.json"
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        tablet_result = json.loads(json.dumps(next(item for item in qa["journey_results"]
                                                if item["viewport_id"] == "mobile")))
        tablet_result["viewport_id"] = "tablet"
        for step in tablet_result["steps"]:
            step["evidence_id"] = step["evidence_id"].replace("mobile", "tablet")
        qa["journey_results"].append(tablet_result)
        put_json(qa_path, qa)
        result = cli("snapshot", self.root, "--stage", "visual-qa")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(cli("validate", self.root).returncode, 0)

    def test_v2_missing_element_and_wrong_component_version_fail(self):
        self.upgrade_v2_fixture()
        path = self.stage(5) / "screen-specs.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["specs"][0]["element_ids"] = []
        put_json(path, data)
        self.assertNotEqual(cli("snapshot", self.root, "--stage", "high-fidelity").returncode, 0)
        data["specs"][0]["element_ids"] = ["shell"]
        data["specs"][0]["component_refs"][0]["revision"] = "r2"
        put_json(path, data)
        self.assertNotEqual(cli("snapshot", self.root, "--stage", "high-fidelity").returncode, 0)

    def test_v2_changed_baseline_and_self_review_fail(self):
        self.upgrade_v2_fixture()
        path = self.stage(8) / "qa-matrix.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["rows"][0]["baseline_sha256"] = "0" * 64
        put_json(path, data)
        self.assertNotEqual(cli("snapshot", self.root, "--stage", "visual-qa").returncode, 0)
        data["rows"][0]["baseline_sha256"] = data["rows"][1]["baseline_sha256"]
        put_json(path, data)
        verdict_path = self.stage(8) / "verdict.json"
        verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
        verdict["reviewed_by"] = "fixture-developer"
        put_json(verdict_path, verdict)
        self.assertNotEqual(cli("snapshot", self.root, "--stage", "visual-qa").returncode, 0)

    def test_v2_missing_spacing_measurement_and_outside_tolerance_fail(self):
        self.upgrade_v2_fixture()
        path = self.stage(5) / "screen-specs.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        default = next(x for x in data["specs"] if x["state_id"] == "home-hero-default")
        default["measurements"] = []
        put_json(path, data)
        result = cli("snapshot", self.root, "--stage", "high-fidelity")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("critical measurement", result.stderr)
        default["measurements"] = [{"id": "gutter", "element_id": "shell", "property": "left-gap",
                                    "expected": 16, "unit": "px", "tolerance": 2}]
        put_json(path, data)
        qa_path = self.stage(8) / "qa-matrix.json"
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        qa["rows"][0]["measurements"][0]["actual"] = 30
        put_json(qa_path, qa)
        result = cli("snapshot", self.root, "--stage", "visual-qa")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside tolerance", result.stderr)

    def test_v2_raster_navigation_and_modified_manifest_file_fail(self):
        self.upgrade_v2_fixture()
        path = self.stage(4) / "component-inventory.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["components"][0]["render_mode"] = "raster"
        put_json(path, data)
        result = cli("snapshot", self.root, "--stage", "design-system")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be raster", result.stderr)
        data["components"][0]["render_mode"] = "code"
        put_json(path, data)
        (self.stage(7) / "src/Shell.tsx").write_text("export const Shell = () => 'changed';\n")
        result = cli("snapshot", self.root, "--stage", "frontend-implementation")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hash mismatch", result.stderr)

    def test_v2_cta_alias_cannot_bypass_interactive_component_gate(self):
        self.upgrade_v2_fixture()
        matrix_path = self.stage(2) / "state-matrix.json"
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        for row in matrix["rows"]:
            row["required_elements"][0]["role"] = "cta"
        put_json(matrix_path, matrix)
        component_path = self.stage(4) / "component-inventory.json"
        components = json.loads(component_path.read_text(encoding="utf-8"))
        components["components"][0]["render_mode"] = "raster"
        put_json(component_path, components)
        result = cli("snapshot", self.root, "--stage", "ux-architecture")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("role must be", result.stderr)
        for row in matrix["rows"]:
            row["required_elements"][0]["role"] = "control"
        put_json(matrix_path, matrix)
        self.assertEqual(cli("snapshot", self.root, "--stage", "ux-architecture").returncode, 0)
        self.assertEqual(cli("snapshot", self.root, "--stage", "visual-direction").returncode, 0)
        result = cli("snapshot", self.root, "--stage", "design-system")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be raster", result.stderr)

    def test_v2_missing_click_log_and_unknown_evidence_fail(self):
        self.upgrade_v2_fixture()
        path = self.stage(8) / "qa-matrix.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["journey_results"][0]["steps"][0]["interaction_path"] = "missing.txt"
        put_json(path, data)
        self.assertNotEqual(cli("snapshot", self.root, "--stage", "visual-qa").returncode, 0)
        data["journey_results"][0]["steps"][0]["interaction_path"] = "interaction.txt"
        data["rows"][0]["evidence_ids"].append("nonexistent")
        put_json(path, data)
        result = cli("snapshot", self.root, "--stage", "visual-qa")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown evidence", result.stderr)

    def test_v2_generated_concept_requires_raster_signature(self):
        self.upgrade_v2_fixture()
        (self.stage(3) / "concepts/option-a.png").write_bytes(b"not an image")
        result = cli("snapshot", self.root, "--stage", "visual-direction")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("signature", result.stderr)

    def test_init_is_draft_and_repeated_init_does_not_overwrite(self):
        self.assertEqual(json.loads((self.root / "delivery.json").read_text())["schema_version"], 2)
        marker = self.root / "01-product-planning/product-brief.md"
        marker.write_text("my notes", encoding="utf-8")
        result = cli("init", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(encoding="utf-8"), "my notes")
        self.assertNotEqual(cli("validate", self.root).returncode, 0)

    def test_ready_synthetic_contract_closes_all_gates(self):
        self.make_ready_fixture()
        result = cli("validate", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("legacy structural gate only", result.stdout)

    def test_missing_required_file_fails(self):
        self.make_ready_fixture()
        (self.stage(5) / "screen-specs.json").unlink()
        self.assertNotEqual(cli("validate", self.root).returncode, 0)

    def test_stale_upstream_snapshot_fails(self):
        self.make_ready_fixture()
        p = self.stage(1) / "product-brief.md"
        p.write_text(p.read_text(encoding="utf-8") + "Changed upstream\n", encoding="utf-8")
        self.assertNotEqual(cli("validate", self.root).returncode, 0)

    def test_referenced_image_replacement_invalidates_snapshot(self):
        self.make_ready_fixture()
        (self.stage(5) / "assets/default-desktop.png").write_bytes(b"replaced design")
        self.assertNotEqual(cli("validate", self.root).returncode, 0)

    def test_nested_prototype_css_replacement_invalidates_snapshot(self):
        self.make_ready_fixture()
        stage = self.stage(5)
        prototype = stage / "assets/prototype"
        prototype.mkdir()
        (prototype / "index.html").write_text(
            '<html><link rel="stylesheet" href="style.css"><body>Fixture</body></html>\n',
            encoding="utf-8",
        )
        css = prototype / "style.css"
        css.write_text("body { color: black; }\n", encoding="utf-8")
        spec_path = stage / "screen-specs.json"
        specs = json.loads(spec_path.read_text(encoding="utf-8"))
        specs["specs"][0]["asset_path"] = "assets/prototype/index.html"
        specs["specs"][0]["asset_kind"] = "prototype"
        put_json(spec_path, specs)
        for slug in STAGES[4:]:
            result = cli("snapshot", self.root, "--stage", slug)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(cli("validate", self.root).returncode, 0)
        css.write_text("body { color: red; }\n", encoding="utf-8")
        result = cli("validate", self.root)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertIn("high-fidelity", result.stderr)

    def test_all_states_not_applicable_cannot_pass(self):
        self.make_ready_fixture()
        p = self.stage(2) / "state-matrix.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        for row in data["rows"]:
            row["applicability"] = "not_applicable"
            row["reason"] = "Fixture claims no states"
        put_json(p, data)
        self.assertNotEqual(cli("validate", self.root).returncode, 0)

    def test_extra_business_state_kind_is_allowed(self):
        self.make_ready_fixture()
        delivery = self.root / "delivery.json"
        data = json.loads(delivery.read_text(encoding="utf-8"))
        data["pages"][0]["screens"][0]["states"].append({"id": "home-hero-streaming", "kind": "loading"})
        put_json(delivery, data)
        # The extra state is valid in the registry; the matrix now needs a row for it.
        result = cli("snapshot", self.root, "--stage", "product-planning")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = cli("snapshot", self.root, "--stage", "ux-architecture")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("state-matrix", result.stderr)

    def test_runtime_capture_needs_image_signature(self):
        self.make_ready_fixture()
        (self.stage(8) / "captures/default-desktop.png").write_bytes(b"fake")
        result = cli("validate", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("image", result.stderr)

    def test_malformed_registry_fails_without_traceback(self):
        p = self.root / "delivery.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["pages"] = [42]
        put_json(p, data)
        result = cli("validate", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)

    def test_unselected_style_fails(self):
        self.make_ready_fixture()
        p = self.stage(3) / "style-decision.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["selected_id"] = ""
        put_json(p, data)
        self.assertNotEqual(cli("validate", self.root).returncode, 0)

    def test_agent_style_choice_requires_recorded_authorization(self):
        self.make_ready_fixture()
        p = self.stage(3) / "style-decision.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["selection"] = {"by": "authorized_agent", "evidence": "Agent chose option a"}
        put_json(p, data)
        result = cli("validate", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("authorization", result.stderr)

    def test_single_visual_option_can_be_snapshotted(self):
        self.make_ready_fixture()
        p = self.stage(3) / "style-decision.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["options"] = data["options"][:1]
        put_json(p, data)
        result = cli("snapshot", self.root, "--stage", "visual-direction")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_critical_stage_cannot_be_skipped(self):
        self.make_ready_fixture()
        p = self.stage(5) / "stage.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["status"] = "skipped"
        data["reason"] = "No design tool"
        put_json(p, data)
        result = cli("validate", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("critical stage", result.stderr)

    def test_motion_skip_needs_reason(self):
        self.make_ready_fixture()
        p = self.stage(6) / "stage.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["status"] = "skipped"
        data["reason"] = ""
        put_json(p, data)
        result = cli("validate", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reason", result.stderr)

    def test_skipped_motion_files_still_invalidate_snapshot(self):
        self.make_ready_fixture()
        stage = self.stage(6)
        meta_path = stage / "stage.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["status"] = "skipped"
        meta["reason"] = "No additional motion in this synthetic fixture"
        put_json(meta_path, meta)
        put_json(stage / "motion-map.json", {"motions": []})
        (stage / "motion-spec.md").write_text(
            "# No additional motion\n\nStatic feedback was reviewed for this synthetic fixture.\n",
            encoding="utf-8",
        )
        for slug in STAGES[5:]:
            result = cli("snapshot", self.root, "--stage", slug)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(cli("validate", self.root).returncode, 0)
        original_spec = (stage / "motion-spec.md").read_text(encoding="utf-8")
        (stage / "motion-spec.md").write_text(
            "# No additional motion\n\nChanged synthetic rationale after snapshot.\n",
            encoding="utf-8",
        )
        result = cli("validate", self.root)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertIn("motion-design", result.stderr)
        (stage / "motion-spec.md").write_text(original_spec, encoding="utf-8")
        put_json(stage / "motion-map.json", {"motions": [], "note": "Changed after snapshot"})
        result = cli("validate", self.root)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertIn("motion-design", result.stderr)

    def test_mock_does_not_count_as_runtime_evidence(self):
        self.make_ready_fixture()
        p = self.stage(8) / "evidence.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["items"][0]["kind"] = "mock"
        put_json(p, data)
        self.assertNotEqual(cli("validate", self.root).returncode, 0)

    def test_invalid_status_fails(self):
        self.make_ready_fixture()
        p = self.stage(4) / "stage.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["status"] = "done"
        put_json(p, data)
        self.assertNotEqual(cli("validate", self.root).returncode, 0)

    def test_missing_state_coverage_fails(self):
        self.make_ready_fixture()
        p = self.stage(2) / "state-matrix.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["rows"].pop()
        put_json(p, data)
        self.assertNotEqual(cli("validate", self.root).returncode, 0)

    def test_path_traversal_absolute_and_symlink_escape_fail(self):
        self.make_ready_fixture()
        p = self.stage(3) / "style-decision.json"
        original = json.loads(p.read_text(encoding="utf-8"))
        outside = Path(self.tmp.name) / "outside.png"
        outside.write_bytes(b"outside")
        for bad in ("../../outside.png", str(outside), "concepts/link.png"):
            if bad == "concepts/link.png":
                (self.stage(3) / bad).symlink_to(outside)
            data = json.loads(json.dumps(original))
            data["options"][0]["concept_path"] = bad
            put_json(p, data)
            self.assertNotEqual(cli("validate", self.root).returncode, 0, bad)


if __name__ == "__main__":
    unittest.main()
