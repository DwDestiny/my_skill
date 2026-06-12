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
ONBOARD_SCRIPT = SKILL_DIR / "scripts" / "onboard_geb_project_doc_system.py"


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

    def run_onboarding(self, *args, check=True):
        result = subprocess.run(
            ["python3", str(ONBOARD_SCRIPT), *map(str, args)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(
                f"{ONBOARD_SCRIPT.name} failed with {result.returncode}\n"
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

    def test_first_run_bootstrap_defines_initialization_deliverables(self):
        skill_text = SKILL_FILE.read_text(encoding="utf-8")
        migration_text = MIGRATION_FILE.read_text(encoding="utf-8")

        required_phrases = [
            "inventory report",
            "priority list",
            "exclusion list",
            "verification log",
            "first safe batch",
            "stop after inventory",
        ]

        for phrase in required_phrases:
            self.assertIn(phrase, skill_text)
            self.assertIn(phrase, migration_text)

    def test_skill_guides_user_through_agent_setup_project_selection_and_acceptance(self):
        skill_text = SKILL_FILE.read_text(encoding="utf-8")
        readme_text = README_FILE.read_text(encoding="utf-8")
        install_script_text = INSTALL_SCRIPT.read_text(encoding="utf-8")

        required_phrases = [
            "User Onboarding Flow",
            "detected agents",
            "requires user selection",
            "global prompt snippet",
            "project candidate list",
            "requires user confirmation",
            "digitalization plan",
            "acceptance report",
            "estimated token savings",
        ]

        for phrase in required_phrases:
            self.assertIn(phrase, skill_text)

        for phrase in (
            "User Onboarding Flow",
            "detect local agents",
            "choose which agents to configure",
            "project candidate list",
            "acceptance report",
        ):
            self.assertIn(phrase, readme_text)

        for phrase in (
            "Onboarding flow",
            "detected agents",
            "Choose which agent entries to configure",
            "project candidate list",
            "acceptance report",
        ):
            self.assertIn(phrase, install_script_text)

    def test_skill_defines_write_side_documentation_contract(self):
        skill_text = SKILL_FILE.read_text(encoding="utf-8")
        readme_text = README_FILE.read_text(encoding="utf-8")
        install_script_text = INSTALL_SCRIPT.read_text(encoding="utf-8")

        required_phrases = [
            "Write-side Contract",
            "new project",
            "create or update the L1 root guide",
            "new or expanded module",
            "create or update the L2 folder guide",
            "new source file",
            "add a short L3 header",
            "documentation is part of the change",
        ]

        for phrase in required_phrases:
            self.assertIn(phrase, skill_text)

        lower_readme_text = readme_text.lower()
        lower_install_script_text = install_script_text.lower()
        for phrase in (
            "Write-side Contract",
            "new project",
            "new source file",
        ):
            self.assertIn(phrase, readme_text)
            self.assertIn(phrase, install_script_text)
        self.assertIn("documentation is part of the change", lower_readme_text)
        self.assertIn("documentation is part of the change", lower_install_script_text)

    def test_onboarding_detects_agents_and_requires_selection_before_writing(self):
        with tempfile.TemporaryDirectory() as home_dir:
            home_path = Path(home_dir)
            codex_doc = home_path / ".codex" / "AGENTS.md"
            claude_doc = home_path / ".claude" / "CLAUDE.md"
            gemini_doc = home_path / ".gemini" / "GEMINI.md"
            codex_doc.parent.mkdir(parents=True)
            claude_doc.parent.mkdir(parents=True)
            gemini_doc.parent.mkdir(parents=True)
            codex_doc.write_text("# Codex rules\n", encoding="utf-8")
            claude_doc.write_text("# Claude rules\n", encoding="utf-8")
            gemini_doc.write_text(
                "## GEB 项目文档规范\n"
                "写文件时也按 GEB 记录，初始化时使用 `geb-project-doc-system` Skill。\n",
                encoding="utf-8",
            )

            detect_result = self.run_onboarding(
                "--home",
                home_path,
                "--skill-source",
                SKILL_DIR,
                "--json",
            )

            report = json.loads(detect_result.stdout)
            agents_by_name = {agent["name"]: agent for agent in report["detected_agents"]}
            agent_names = set(agents_by_name)
            self.assertIn("codex", agent_names)
            self.assertIn("claude", agent_names)
            self.assertTrue(agents_by_name["gemini"]["prompt_review_required"])
            self.assertFalse(agents_by_name["gemini"]["managed_snippet_installed"])
            self.assertTrue(report["requires_user_selection"])
            self.assertEqual(report["configured_agents"], [])
            self.assertNotIn("GEB_PROJECT_DOC_SYSTEM_START", codex_doc.read_text(encoding="utf-8"))

            apply_result = self.run_onboarding(
                "--home",
                home_path,
                "--skill-source",
                SKILL_DIR,
                "--agents",
                "codex",
                "--apply",
                "--json",
            )

            applied_report = json.loads(apply_result.stdout)
            self.assertEqual(applied_report["configured_agents"], ["codex"])
            self.assertTrue((home_path / ".codex" / "skills" / "geb-project-doc-system").exists())
            codex_text = codex_doc.read_text(encoding="utf-8")
            self.assertIn("GEB_PROJECT_DOC_SYSTEM_START", codex_text)
            self.assertIn("写文件时也按 GEB 记录", codex_text)
            self.assertNotIn("GEB_PROJECT_DOC_SYSTEM_START", claude_doc.read_text(encoding="utf-8"))

    def test_onboarding_can_install_project_hook_and_report_project_candidate(self):
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as project_dir:
            project_path = Path(project_dir)
            hooks_dir = project_path / ".git" / "hooks"
            hooks_dir.mkdir(parents=True)
            (project_path / "AGENTS.md").write_text("# Project rules\n", encoding="utf-8")

            result = self.run_onboarding(
                "--home",
                home_dir,
                "--skill-source",
                SKILL_DIR,
                "--project",
                project_path,
                "--install-hooks",
                "--apply",
                "--json",
            )

            report = json.loads(result.stdout)
            resolved_project_path = str(project_path.resolve())
            self.assertEqual(report["configured_hooks"], [resolved_project_path])
            self.assertEqual(report["project_candidates"][0]["path"], resolved_project_path)
            hook_text = (hooks_dir / "pre-commit").read_text(encoding="utf-8")
            self.assertIn("audit_geb_docs.py", hook_text)
            self.assertIn(resolved_project_path, report["next_steps"][0])

    def test_skill_documents_productized_onboarding_entrypoint(self):
        skill_text = SKILL_FILE.read_text(encoding="utf-8")
        readme_text = README_FILE.read_text(encoding="utf-8")
        install_script_text = INSTALL_SCRIPT.read_text(encoding="utf-8")

        required_phrases = [
            "onboard_geb_project_doc_system.py",
            "no writes without --apply",
            "standard agents only",
            "plugin runtimes separately",
            "pre-commit hook",
            "acceptance report",
        ]

        for phrase in required_phrases:
            self.assertIn(phrase, skill_text)
            self.assertIn(phrase, readme_text)

        self.assertIn("onboard_geb_project_doc_system.py", install_script_text)
        self.assertNotIn("skill_dirs=(", install_script_text)
        self.assertNotIn("一键安装到本机常见 Agent 目录", readme_text)
        self.assertNotIn("Install into common local agent skill directories", readme_text)

    def test_audit_and_update_skip_runtime_generated_and_session_paths(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            (project_dir / "AGENTS.md").write_text("# Project Rules\n", encoding="utf-8")

            for directory in (
                "sessions",
                "logs",
                "cache",
                "site",
                "artifacts",
                "dist-electron",
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
            self.assertNotIn("site/tool.py", finding_paths)
            self.assertNotIn("artifacts/tool.py", finding_paths)
            self.assertNotIn("dist-electron/tool.py", finding_paths)
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
