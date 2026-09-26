# GEB-L3
# Input: ui-delivery CLI and isolated synthetic delivery fixtures.
# Output: Contract regression tests for structure, handoffs, provenance, and freshness.
# Pos: Repository-level deterministic test; fixtures are synthetic, not product acceptance evidence.

import base64
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

    def test_init_is_draft_and_repeated_init_does_not_overwrite(self):
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
