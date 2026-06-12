#!/usr/bin/env python3
"""Codex hooks for code-project-guidance-map.

The hooks are intentionally read-only. They verify the generated AGENTS.md block
and add bounded model context when the guide is stale or unverifiable.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
GUIDANCE_MAP = PLUGIN_ROOT / "skills" / "code-project-guidance-map" / "scripts" / "guidance_map.py"

ACTION_PATTERNS = (
    r"\b(add|change|modify|edit|implement|fix|refactor|update|delete|remove|write|create)\b",
    r"(新增|修改|实现|修复|重构|更新|删除|创建|调整|改一下|写一个)",
)

CODE_CONTEXT_PATTERNS = (
    r"\b(api|endpoint|controller|service|dao|repository|mapper|sql|schema|migration|test|bug|feature)\b",
    r"(接口|控制器|服务|数据库|持久化|模块|功能|代码|测试|报错|问题|缺陷|逻辑)",
)

DIRECT_CODE_PATTERNS = (
    r"\b(src|app|lib|packages|modules|web|server|client|frontend|backend)/",
    r"\.(py|js|jsx|ts|tsx|java|kt|go|rs|cs|php|rb|sql|xml|yaml|yml|toml|json)\b",
)


def read_input() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def hook_output(event_name: str, additional_context: str | None) -> None:
    if not additional_context:
        return
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event_name,
                    "additionalContext": additional_context,
                }
            },
            ensure_ascii=False,
        )
    )


def pattern_matches(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def prompt_looks_like_code_edit(prompt: str) -> bool:
    lowered = prompt.casefold()
    if pattern_matches(DIRECT_CODE_PATTERNS, lowered):
        return True
    return pattern_matches(ACTION_PATTERNS, lowered) and pattern_matches(CODE_CONTEXT_PATTERNS, lowered)


def verify_repo(cwd: str) -> tuple[dict[str, Any] | None, str | None]:
    if not GUIDANCE_MAP.exists():
        return None, f"guidance helper is missing at {GUIDANCE_MAP}"
    result = subprocess.run(
        [sys.executable, str(GUIDANCE_MAP), "verify", "--repo", cwd],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stream = result.stdout.strip() or result.stderr.strip()
    try:
        parsed = json.loads(stream) if stream else {}
    except json.JSONDecodeError:
        return None, stream or f"verify exited with code {result.returncode}"
    if result.returncode not in (0, 1):
        return parsed, parsed.get("error") or f"verify exited with code {result.returncode}"
    return parsed, None


def actionable_change_summary(verification: dict[str, Any]) -> str:
    action = verification.get("recommended_action") or "review"
    reasons = verification.get("reasons") or []
    reason_text = "; ".join(str(reason) for reason in reasons[:3]) or "guidance map needs review."
    changed = verification.get("changed_files") or []
    changed_text = ""
    if changed:
        preview = ", ".join(str(path) for path in changed[:8])
        suffix = " ..." if len(changed) > 8 else ""
        changed_text = f" Changed files: {preview}{suffix}."
    return f"{reason_text} Recommended action: {action}.{changed_text}"


def context_for(event_name: str, verification: dict[str, Any] | None, error: str | None) -> str | None:
    if error:
        return (
            "Code Project Guidance Map hook: AGENTS.md action map could not be verified. "
            f"{error}. Before the first code edit, suggest running $code-project-guidance-map to refresh it."
        )
    if not verification:
        return None

    has_problem = bool(verification.get("stale")) or verification.get("severity") == "error"
    if not has_problem:
        return None

    summary = actionable_change_summary(verification)
    if event_name == "UserPromptSubmit":
        return (
            "Code Project Guidance Map hook: this looks like a code-edit request, and the repository "
            f"AGENTS.md action map is stale or unverifiable. {summary} Before editing code, use "
            "$code-project-guidance-map to refresh the guidance map, or explicitly explain why the edit can proceed without it."
        )
    return (
        "Code Project Guidance Map hook: this repository's AGENTS.md action map is stale, missing, "
        f"or unverifiable. {summary} Before the first code edit in this thread, suggest running "
        "$code-project-guidance-map."
    )


def main() -> int:
    payload = read_input()
    event_name = payload.get("hook_event_name")
    if event_name not in {"SessionStart", "UserPromptSubmit"}:
        return 0

    prompt = str(payload.get("prompt") or "")
    if event_name == "UserPromptSubmit":
        if "$code-project-guidance-map" in prompt or "code-project-guidance-map" in prompt:
            return 0
        if not prompt_looks_like_code_edit(prompt):
            return 0

    cwd = str(payload.get("cwd") or ".")
    verification, error = verify_repo(cwd)
    hook_output(event_name, context_for(event_name, verification, error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
