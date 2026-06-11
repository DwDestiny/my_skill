# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by tests/test_geb_project_doc_system.py
# Pos: tests/test_geb_project_doc_system.py
import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "geb-project-doc-system"
AUDIT_SCRIPT = SKILL_DIR / "scripts" / "audit_geb_docs.py"
UPDATE_SCRIPT = SKILL_DIR / "scripts" / "update_file_headers.py"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MIGRATION_FILE = SKILL_DIR / "references" / "migration.md"
OPENAI_METADATA_FILE = SKILL_DIR / "agents" / "openai.yaml"
README_FILE = REPO_ROOT / "README.md"
INSTALL_SCRIPT = REPO_ROOT / "scripts" / "install_geb_project_doc_system.sh"


class GebProjectDocSystemTests(unittest.TestCase):
    def run_script(self, script_path, *args, check=True):
        result = subprocess.run(
            ["python3", str(script_path), *map(str, args)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(
                f"{script_path.name} failed with {result.returncode}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def test_audit_detects_missing_l1_and_l3(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            src_dir = project_dir / "src"
            src_dir.mkdir()
            (src_dir / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")

            result = self.run_script(AUDIT_SCRIPT, project_dir, "--json", check=False)

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertFalse(report["ok"])
            self.assertIn("missing_l1_doc", {item["code"] for item in report["findings"]})
            self.assertIn("missing_l3_header", {item["code"] for item in report["findings"]})

    def test_update_headers_is_dry_run_by_default_and_apply_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            src_dir = project_dir / "src"
            src_dir.mkdir()
            file_path = src_dir / "app.py"
            original = "def run():\n    return 1\n"
            file_path.write_text(original, encoding="utf-8")

            dry_run = self.run_script(UPDATE_SCRIPT, project_dir, "--json")

            self.assertEqual(file_path.read_text(encoding="utf-8"), original)
            dry_report = json.loads(dry_run.stdout)
            self.assertEqual(dry_report["planned_updates"], 1)
            self.assertEqual(dry_report["applied_updates"], 0)

            apply_once = self.run_script(UPDATE_SCRIPT, project_dir, "--apply", "--json")
            apply_report = json.loads(apply_once.stdout)
            updated = file_path.read_text(encoding="utf-8")
            self.assertEqual(apply_report["applied_updates"], 1)
            self.assertIn("Input:", updated)
            self.assertIn("Output:", updated)
            self.assertIn("Pos:", updated)

            apply_twice = self.run_script(UPDATE_SCRIPT, project_dir, "--apply", "--json")
            second_report = json.loads(apply_twice.stdout)
            self.assertEqual(second_report["planned_updates"], 0)
            self.assertEqual(file_path.read_text(encoding="utf-8"), updated)

    def test_audit_detects_duplicate_l3_headers(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            (project_dir / "AGENTS.md").write_text("# Project Rules\n", encoding="utf-8")
            src_dir = project_dir / "src"
            src_dir.mkdir()
            duplicate_header = textwrap.dedent(
                """\
                # GEB-L3
                # Input: request
                # Output: response
                # Pos: service

                # GEB-L3
                # Input: request
                # Output: response
                # Pos: service

                def run():
                    return 1
                """
            )
            (src_dir / "app.py").write_text(duplicate_header, encoding="utf-8")

            result = self.run_script(AUDIT_SCRIPT, project_dir, "--json", check=False)

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertIn("duplicate_l3_header", {item["code"] for item in report["findings"]})

    def test_audit_requires_l2_for_large_source_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            (project_dir / "AGENTS.md").write_text("# Project Rules\n", encoding="utf-8")
            src_dir = project_dir / "src"
            src_dir.mkdir()
            for index in range(4):
                (src_dir / f"module_{index}.py").write_text(
                    textwrap.dedent(
                        f"""\
                        # GEB-L3
                        # Input: module {index} input
                        # Output: module {index} output
                        # Pos: src/module_{index}.py

                        def run():
                            return {index}
                        """
                    ),
                    encoding="utf-8",
                )

            result = self.run_script(AUDIT_SCRIPT, project_dir, "--json", check=False)

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertIn("missing_l2_doc", {item["code"] for item in report["findings"]})

    def test_skill_documents_first_run_bootstrap(self):
        skill_text = SKILL_FILE.read_text(encoding="utf-8")
        migration_text = MIGRATION_FILE.read_text(encoding="utf-8")
        openai_metadata_text = OPENAI_METADATA_FILE.read_text(encoding="utf-8")
        readme_text = README_FILE.read_text(encoding="utf-8")
        install_script_text = INSTALL_SCRIPT.read_text(encoding="utf-8")

        self.assertIn("## First-run Bootstrap", skill_text)
        self.assertIn("first-run inventory", skill_text)
        self.assertIn("Agent runtime", skill_text)
        self.assertIn("first-run inventory", openai_metadata_text)
        self.assertIn("safe bootstrap", openai_metadata_text)
        self.assertIn("before writing bulk project docs", openai_metadata_text)
        self.assertIn("## First-run Inventory", migration_text)
        self.assertIn("secrets", migration_text)
        self.assertIn("sessions", migration_text)
        self.assertIn("worktrees", migration_text)
        self.assertIn("## First-time Bootstrap", readme_text)
        self.assertIn("sample project", readme_text)
        self.assertIn("First-run bootstrap", install_script_text)
        self.assertIn("first-run inventory", install_script_text)

    def test_first_run_bootstrap_handles_mixed_and_high_risk_repositories(self):
        skill_text = SKILL_FILE.read_text(encoding="utf-8")
        migration_text = MIGRATION_FILE.read_text(encoding="utf-8")
        readme_text = README_FILE.read_text(encoding="utf-8")

        self.assertIn("mixed workspace", skill_text)
        self.assertIn("trading or runtime-critical repository", skill_text)
        self.assertIn("product subproject", skill_text)
        self.assertIn("reference code", migration_text)
        self.assertIn("generated assets", migration_text)
        self.assertIn("Do not treat audit findings as a to-do list", migration_text)
        self.assertIn("mixed workspaces", readme_text)
        self.assertIn("high-risk runtime paths", readme_text)

    def test_audit_and_update_skip_runtime_generated_and_session_paths(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            (project_dir / "AGENTS.md").write_text("# Project Rules\n", encoding="utf-8")

            for directory in (
                "sessions",
                "logs",
                "cache",
                "generated_assets",
                "secrets",
                "credentials",
                "tokens",
                ".claude/worktrees/demo",
            ):
                path = project_dir / directory
                path.mkdir(parents=True)
                (path / "tool.py").write_text("def unsafe():\n    return 1\n", encoding="utf-8")

            source_dir = project_dir / "src"
            source_dir.mkdir()
            (source_dir / "safe_tool.py").write_text("def safe():\n    return 1\n", encoding="utf-8")

            audit_result = self.run_script(AUDIT_SCRIPT, project_dir, "--json", check=False)
            audit_report = json.loads(audit_result.stdout)
            finding_paths = {item["path"] for item in audit_report["findings"]}
            self.assertIn("src/safe_tool.py", finding_paths)
            self.assertNotIn("sessions/tool.py", finding_paths)
            self.assertNotIn("logs/tool.py", finding_paths)
            self.assertNotIn("cache/tool.py", finding_paths)
            self.assertNotIn("generated_assets/tool.py", finding_paths)
            self.assertNotIn("secrets/tool.py", finding_paths)
            self.assertNotIn("credentials/tool.py", finding_paths)
            self.assertNotIn("tokens/tool.py", finding_paths)
            self.assertNotIn(".claude/worktrees/demo/tool.py", finding_paths)

            dry_run = self.run_script(UPDATE_SCRIPT, project_dir, "--json")
            dry_report = json.loads(dry_run.stdout)
            self.assertEqual(dry_report["planned_files"], ["src/safe_tool.py"])

    def test_update_skips_trading_and_runtime_critical_paths(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            (project_dir / "AGENTS.md").write_text("# Project Rules\n", encoding="utf-8")

            high_risk_files = [
                project_dir / "runtime" / "session_runner.py",
                project_dir / "remote" / "run_round.sh",
                project_dir / "gateway" / "order.py",
                project_dir / "scripts" / "htx_live.py",
            ]
            for path in high_risk_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("def risky():\n    return 1\n", encoding="utf-8")

            research_dir = project_dir / "research"
            research_dir.mkdir()
            (research_dir / "notebook_tool.py").write_text("def research():\n    return 1\n", encoding="utf-8")

            dry_run = self.run_script(UPDATE_SCRIPT, project_dir, "--json")
            dry_report = json.loads(dry_run.stdout)
            self.assertEqual(dry_report["planned_files"], ["research/notebook_tool.py"])


if __name__ == "__main__":
    unittest.main()
