#!/usr/bin/env python3
"""Tests for guidance_map.py."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import guidance_map


class GuidanceMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def guidance_text(self, owns: str = "A") -> str:
        return (
            "### Agent Editing Rules\n\n"
            "- [MUST] Keep App changes inside `app` unless routing says otherwise.\n"
            "- [SHOULD] Reuse existing services before adding orchestration.\n\n"
            "### Task Routing\n\n"
            "- To add an API: edit `app/routes`; keep behavior in `app/services`.\n\n"
            "### Module Dependency Rules\n\n"
            "- `app` owns application behavior and may depend on shared utilities.\n\n"
            "### Module Map\n\n"
            "#### App\n\n"
            "- Module Path: `app`\n"
            f"- Owns: {owns}\n"
            "- Change here when: B\n"
            "- Do not put here: C\n"
            "- Key entry points:\n\n"
            "```text\n"
            "app/\n"
            "```\n"
        )

    def write_guidance(self, text: str | None = None) -> Path:
        path = self.repo / "guidance.md"
        path.write_text(text or self.guidance_text(), encoding="utf-8")
        return path

    def test_update_creates_agents_when_missing(self) -> None:
        result = guidance_map.update(self.repo, self.write_guidance(), "2026-01-01T00:00:00Z")
        text = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(result["has_block"])
        self.assertIn(guidance_map.START_MARKER, text)
        self.assertIn("Generator: code-project-guidance-map", text)
        self.assertIn("Guide format: action-map:v2", text)
        self.assertIn("Signature algorithm: sha256:v1", text)
        self.assertRegex(text, r"Signature: sha256:[0-9a-f]{64}")
        self.assertIn("- Owns: A", text)

    def test_status_validates_signature(self) -> None:
        guidance_map.update(self.repo, self.write_guidance(), "2026-01-01T00:00:00Z")
        result = guidance_map.status(self.repo)
        self.assertTrue(result["signature_valid"])
        self.assertFalse(result["requires_full_read"])

        agents_path = self.repo / "AGENTS.md"
        text = agents_path.read_text(encoding="utf-8").replace("Owns: A", "Owns: changed")
        agents_path.write_text(text, encoding="utf-8")
        tampered = guidance_map.status(self.repo)
        self.assertFalse(tampered["signature_valid"])
        self.assertTrue(tampered["requires_full_read"])

    def test_update_appends_block_when_agents_has_no_block(self) -> None:
        (self.repo / "AGENTS.md").write_text("# Existing\n\nKeep this.\n", encoding="utf-8")
        guidance_map.update(self.repo, self.write_guidance(), "2026-01-01T00:00:00Z")
        text = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Existing\n\nKeep this."))
        self.assertIn(guidance_map.START_MARKER, text)

    def test_update_replaces_block_and_preserves_outside_content(self) -> None:
        old_block = guidance_map.render_block("old", "2025-01-01T00:00:00Z", "abc123")
        (self.repo / "AGENTS.md").write_text(f"before\n\n{old_block}\nafter\n", encoding="utf-8")
        guidance_map.update(self.repo, self.write_guidance(self.guidance_text("new")), "2026-01-01T00:00:00Z")
        text = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("before", text)
        self.assertIn("after", text)
        self.assertIn("new", text)
        self.assertNotIn("old", text)
        self.assertEqual(text.count(guidance_map.START_MARKER), 1)

    def test_status_reports_invalid_signature_time(self) -> None:
        block = guidance_map.render_block("body", "2026-01-01T00:00:00Z", "abc123")
        block = block.replace("Generated at: 2026-01-01T00:00:00Z", "Generated at: not-a-date")
        (self.repo / "AGENTS.md").write_text(block, encoding="utf-8")
        result = guidance_map.status(self.repo)
        self.assertTrue(result["has_block"])
        self.assertFalse(result["generated_at_valid"])
        self.assertTrue(result["requires_full_read"])

    def test_status_reports_unsupported_guide_format(self) -> None:
        block = guidance_map.render_block("body", "2026-01-01T00:00:00Z", "abc123")
        block = block.replace("Guide format: action-map:v2\n", "")
        (self.repo / "AGENTS.md").write_text(block, encoding="utf-8")
        result = guidance_map.status(self.repo)
        self.assertTrue(result["has_block"])
        self.assertFalse(result["guide_format_valid"])
        self.assertTrue(result["requires_full_read"])

    def test_update_rejects_missing_required_sections(self) -> None:
        path = self.write_guidance("### Module Map\n\n#### App\n\n- Module Path: `app`\n")
        with self.assertRaises(guidance_map.GuidanceMapError):
            guidance_map.update(self.repo, path, "2026-01-01T00:00:00Z")

    def test_update_rejects_required_sections_out_of_order(self) -> None:
        text = (
            "### Task Routing\n\n"
            "- To add an API: edit `app/routes`.\n\n"
            "### Agent Editing Rules\n\n"
            "- [MUST] Keep App changes inside `app` unless routing says otherwise.\n\n"
            "### Module Dependency Rules\n\n"
            "- `app` owns application behavior and may depend on shared utilities.\n\n"
            "### Module Map\n\n"
            "#### App\n\n"
            "- Module Path: `app`\n"
            "- Owns: A\n"
            "- Change here when: B\n"
            "- Do not put here: C\n"
            "- Key entry points: `app/`\n"
        )
        path = self.write_guidance(text)
        with self.assertRaises(guidance_map.GuidanceMapError):
            guidance_map.update(self.repo, path, "2026-01-01T00:00:00Z")

    def test_status_handles_non_git_project(self) -> None:
        result = guidance_map.status(self.repo)
        self.assertFalse(result["git_available"])
        self.assertEqual(result["current_head"], "none")
        self.assertEqual(result["changed_files"], [])

    def test_classify_changed_files_by_refresh_scope(self) -> None:
        impact = guidance_map.classify_changed_files(
            [
                "pom.xml",
                "src/main/java/app/controller/UserController.java",
                "src/main/java/app/model/User.java",
                "docs/notes.md",
                ".github/workflows/ci.yml",
                "unknown.file",
            ]
        )
        self.assertEqual(impact["boundary_rules"], ["pom.xml"])
        self.assertEqual(impact["task_routing"], ["src/main/java/app/controller/UserController.java"])
        self.assertEqual(impact["module_internal"], ["src/main/java/app/model/User.java"])
        self.assertEqual(impact["docs_only"], ["docs/notes.md", ".github/workflows/ci.yml"])
        self.assertEqual(impact["other"], ["unknown.file"])

    def test_verify_missing_block_requires_full_refresh(self) -> None:
        result = guidance_map.verify(self.repo)
        self.assertEqual(result["severity"], "error")
        self.assertEqual(result["recommended_action"], "full_refresh")
        self.assertTrue(result["stale"])

    def test_malformed_markers_raise(self) -> None:
        text = f"{guidance_map.START_MARKER}\nmissing end"
        with self.assertRaises(guidance_map.GuidanceMapError):
            guidance_map.find_block(text)


@unittest.skipIf(shutil.which("git") is None, "git is not installed")
class GuidanceMapGitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test User")
        (self.repo / "committed.txt").write_text("initial\n", encoding="utf-8")
        self.git("add", "committed.txt")
        self.git("commit", "-m", "initial")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def commit_guide(self) -> None:
        body = (
            "### Agent Editing Rules\n\n"
            "- [MUST] Keep App changes inside `app`.\n\n"
            "### Task Routing\n\n"
            "- To add an API: edit `app/routes`.\n\n"
            "### Module Dependency Rules\n\n"
            "- `app` owns application behavior.\n\n"
            "### Module Map\n\n"
            "#### App\n\n"
            "- Module Path: `app`\n"
            "- Owns: Application behavior.\n"
            "- Change here when: Application behavior changes.\n"
            "- Do not put here: Shared utilities.\n"
            "- Key entry points: `app/`\n"
        )
        block = guidance_map.render_block(body, "2030-01-01T00:00:00Z", "abc123")
        (self.repo / "AGENTS.md").write_text(block, encoding="utf-8")
        self.git("add", "AGENTS.md")
        self.git("commit", "-m", "guide")

    def test_changed_files_include_committed_staged_unstaged_and_untracked(self) -> None:
        (self.repo / "new_commit.txt").write_text("new\n", encoding="utf-8")
        self.git("add", "new_commit.txt")
        self.git("commit", "-m", "new commit")
        (self.repo / "staged.txt").write_text("staged\n", encoding="utf-8")
        self.git("add", "staged.txt")
        (self.repo / "committed.txt").write_text("changed\n", encoding="utf-8")
        (self.repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")

        block = guidance_map.render_block("body", "2000-01-01T00:00:00Z", "abc123")
        (self.repo / "AGENTS.md").write_text(block, encoding="utf-8")
        result = guidance_map.status(self.repo)

        changed = set(result["changed_files"])
        self.assertIn("new_commit.txt", changed)
        self.assertIn("staged.txt", changed)
        self.assertIn("committed.txt", changed)
        self.assertIn("untracked.txt", changed)

    def test_clean_repo_with_later_timestamp_has_no_changes(self) -> None:
        block = guidance_map.render_block("body", "2030-01-01T00:00:00Z", "abc123")
        (self.repo / "AGENTS.md").write_text(block, encoding="utf-8")
        self.git("add", "AGENTS.md")
        self.git("commit", "-m", "guide")
        result = guidance_map.status(self.repo)
        self.assertEqual(result["changed_files"], [])

    def test_verify_boundary_sensitive_changes_refresh_dependency_rules(self) -> None:
        self.commit_guide()
        (self.repo / "pom.xml").write_text("<project />\n", encoding="utf-8")
        result = guidance_map.verify(self.repo)
        self.assertEqual(result["recommended_action"], "refresh_dependency_rules")
        self.assertTrue(result["stale"])
        self.assertEqual(result["change_impact"]["boundary_rules"], ["pom.xml"])

    def test_verify_task_routing_changes_refresh_routing(self) -> None:
        self.commit_guide()
        path = self.repo / "src/main/java/app/controller/UserController.java"
        path.parent.mkdir(parents=True)
        path.write_text("class UserController {}\n", encoding="utf-8")
        result = guidance_map.verify(self.repo)
        self.assertEqual(result["recommended_action"], "refresh_task_routing_and_affected_modules")
        self.assertTrue(result["stale"])
        self.assertEqual(result["change_impact"]["task_routing"], ["src/main/java/app/controller/UserController.java"])

    def test_verify_module_internal_changes_refresh_affected_modules(self) -> None:
        self.commit_guide()
        path = self.repo / "src/main/java/app/model/User.java"
        path.parent.mkdir(parents=True)
        path.write_text("class User {}\n", encoding="utf-8")
        result = guidance_map.verify(self.repo)
        self.assertEqual(result["recommended_action"], "refresh_affected_modules")
        self.assertTrue(result["stale"])
        self.assertEqual(result["change_impact"]["module_internal"], ["src/main/java/app/model/User.java"])

    def test_verify_docs_only_changes_do_not_mark_stale(self) -> None:
        self.commit_guide()
        path = self.repo / "docs/notes.md"
        path.parent.mkdir(parents=True)
        path.write_text("# notes\n", encoding="utf-8")
        result = guidance_map.verify(self.repo)
        self.assertEqual(result["recommended_action"], "none")
        self.assertFalse(result["stale"])
        self.assertEqual(result["severity"], "info")


class GuidanceMapCliTests(unittest.TestCase):
    def test_status_cli_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(guidance_map.__file__).resolve()
            result = subprocess.run(
                [sys.executable, str(script), "status", "--repo", tmp],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            parsed = json.loads(result.stdout)
            self.assertIn("repo_root", parsed)

    def test_verify_cli_can_fail_on_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(guidance_map.__file__).resolve()
            result = subprocess.run(
                [sys.executable, str(script), "verify", "--repo", tmp, "--fail-on", "error"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            parsed = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(parsed["recommended_action"], "full_refresh")


if __name__ == "__main__":
    unittest.main()
