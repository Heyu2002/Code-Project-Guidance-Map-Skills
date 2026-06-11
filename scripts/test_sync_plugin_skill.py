#!/usr/bin/env python3
"""Tests for sync_plugin_skill.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sync_plugin_skill


class SyncPluginSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.source = self.repo / sync_plugin_skill.DEFAULT_SOURCE
        self.target = self.repo / sync_plugin_skill.DEFAULT_TARGET
        (self.source / "agents").mkdir(parents=True)
        (self.source / "scripts").mkdir()
        (self.source / "SKILL.md").write_text("---\nname: test\n---\n", encoding="utf-8")
        (self.source / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
        (self.source / "scripts" / "helper.py").write_text("print('ok')\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_sync_copies_source_skill_to_plugin_skill(self) -> None:
        drift = sync_plugin_skill.sync_trees(self.source, self.target)
        self.assertTrue(drift.has_drift)
        self.assertFalse(sync_plugin_skill.compare_trees(self.source, self.target).has_drift)
        self.assertEqual(
            (self.target / "scripts" / "helper.py").read_text(encoding="utf-8"),
            "print('ok')\n",
        )

    def test_compare_reports_missing_changed_and_extra_files(self) -> None:
        (self.target / "agents").mkdir(parents=True)
        (self.target / "SKILL.md").write_text("old\n", encoding="utf-8")
        (self.target / "extra.txt").write_text("extra\n", encoding="utf-8")
        drift = sync_plugin_skill.compare_trees(self.source, self.target)
        self.assertEqual(drift.changed, ("SKILL.md",))
        self.assertEqual(drift.extra, ("extra.txt",))
        self.assertIn("agents/openai.yaml", drift.missing)
        self.assertIn("scripts/helper.py", drift.missing)

    def test_excludes_python_cache_files(self) -> None:
        (self.target / "__pycache__").mkdir(parents=True)
        (self.target / "__pycache__" / "helper.cpython-313.pyc").write_bytes(b"cache")
        drift = sync_plugin_skill.compare_trees(self.source, self.target)
        self.assertNotIn("__pycache__/helper.cpython-313.pyc", drift.extra)

    def test_resolve_under_rejects_paths_outside_repo(self) -> None:
        with self.assertRaises(ValueError):
            sync_plugin_skill.resolve_under(self.repo, self.repo.parent / "outside", "target")


if __name__ == "__main__":
    unittest.main()
