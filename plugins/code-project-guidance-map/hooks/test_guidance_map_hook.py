#!/usr/bin/env python3
"""Tests for the code-project-guidance-map hook script."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK_SCRIPT = Path(__file__).resolve().parent / "guidance_map_hook.py"
GUIDANCE_MAP = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "code-project-guidance-map"
    / "scripts"
    / "guidance_map.py"
)


GUIDANCE = """### Agent Editing Rules

- [MUST] Keep App changes inside `app`.

### Task Routing

- To add an API: edit `app/routes`.

### Module Dependency Rules

- `app` owns application behavior.

### Module Map

#### App

- Module Path: `app`
- Owns: Application behavior.
- Change here when: Application behavior changes.
- Do not put here: Shared utilities.
- Key entry points: `app/`
"""


class GuidanceMapHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.env = os.environ.copy()
        self.env["CODE_PROJECT_GUIDANCE_MAP_KEY_HOME"] = str(Path(self.tmp.name) / "keys")
        self.env.pop("CODE_PROJECT_GUIDANCE_MAP_SECRET", None)
        self.env.pop("CODE_PROJECT_GUIDANCE_MAP_KEY_FILE", None)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_hook(self, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env,
            check=False,
        )

    def parse_hook_output(self, result: subprocess.CompletedProcess[str]) -> dict[str, object] | None:
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return None
        return json.loads(result.stdout)

    def write_valid_guide(self) -> None:
        guidance_file = Path(self.tmp.name) / "guidance.md"
        guidance_file.write_text(GUIDANCE, encoding="utf-8")
        subprocess.run(
            [
                sys.executable,
                str(GUIDANCE_MAP),
                "update",
                "--repo",
                str(self.repo),
                "--guidance-file",
                str(guidance_file),
                "--timestamp",
                "2030-01-01T00:00:00Z",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env,
            check=True,
        )

    def test_session_start_injects_context_when_guide_missing(self) -> None:
        result = self.run_hook(
            {
                "cwd": str(self.repo),
                "hook_event_name": "SessionStart",
                "model": "test",
                "permission_mode": "default",
                "session_id": "session",
                "source": "startup",
                "transcript_path": None,
            }
        )
        output = self.parse_hook_output(result)
        self.assertIsNotNone(output)
        context = output["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
        self.assertIn("AGENTS.md action map is stale, missing, or unverifiable", context)
        self.assertIn("$code-project-guidance-map", context)

    def test_user_prompt_submit_skips_non_code_prompt(self) -> None:
        result = self.run_hook(
            {
                "cwd": str(self.repo),
                "hook_event_name": "UserPromptSubmit",
                "model": "test",
                "permission_mode": "default",
                "prompt": "Summarize the project at a high level.",
                "session_id": "session",
                "transcript_path": None,
                "turn_id": "turn",
            }
        )
        self.assertIsNone(self.parse_hook_output(result))

    def test_user_prompt_submit_skips_non_code_action_prompt(self) -> None:
        result = self.run_hook(
            {
                "cwd": str(self.repo),
                "hook_event_name": "UserPromptSubmit",
                "model": "test",
                "permission_mode": "default",
                "prompt": "Write a poem about testing.",
                "session_id": "session",
                "transcript_path": None,
                "turn_id": "turn",
            }
        )
        self.assertIsNone(self.parse_hook_output(result))

    def test_user_prompt_submit_injects_context_for_code_edit_when_stale(self) -> None:
        result = self.run_hook(
            {
                "cwd": str(self.repo),
                "hook_event_name": "UserPromptSubmit",
                "model": "test",
                "permission_mode": "default",
                "prompt": "Implement a new REST API endpoint.",
                "session_id": "session",
                "transcript_path": None,
                "turn_id": "turn",
            }
        )
        output = self.parse_hook_output(result)
        self.assertIsNotNone(output)
        context = output["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
        self.assertIn("this looks like a code-edit request", context)
        self.assertIn("$code-project-guidance-map", context)

    def test_user_prompt_submit_injects_context_for_chinese_code_edit(self) -> None:
        result = self.run_hook(
            {
                "cwd": str(self.repo),
                "hook_event_name": "UserPromptSubmit",
                "model": "test",
                "permission_mode": "default",
                "prompt": "实现一个新的接口",
                "session_id": "session",
                "transcript_path": None,
                "turn_id": "turn",
            }
        )
        output = self.parse_hook_output(result)
        self.assertIsNotNone(output)
        context = output["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
        self.assertIn("this looks like a code-edit request", context)

    def test_no_context_when_guide_is_current(self) -> None:
        self.write_valid_guide()
        result = self.run_hook(
            {
                "cwd": str(self.repo),
                "hook_event_name": "SessionStart",
                "model": "test",
                "permission_mode": "default",
                "session_id": "session",
                "source": "startup",
                "transcript_path": None,
            }
        )
        self.assertIsNone(self.parse_hook_output(result))


if __name__ == "__main__":
    unittest.main()
