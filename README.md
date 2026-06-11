# Code Project Guidance Map

[中文说明](README-CN.md)

Code Project Guidance Map is a Codex plugin and skill that helps Codex understand a repository faster and preserve that understanding in the repository root `AGENTS.md`.

Its purpose is not to generate broad project documentation. It creates a compact, durable, refreshable action map for Codex: editing rules, task routing, dependency boundaries, and concise module ownership. Future Codex sessions can read `AGENTS.md` automatically, so the map becomes reusable project context.

## Background

This plugin comes from the Codex repository feature request: [Feature request: Add a standardized code audit module for modular codebases #26007](https://github.com/openai/codex/issues/26007).

That issue asks Codex to generate and maintain a standardized code audit module for modular codebases, so later agents do not need to reread large parts of the source tree from scratch. Because the feature request is still open and does not currently show an assignee, project, milestone, or linked implementation PR, this repository implements the workflow as a standalone Codex plugin first.

Part of the inspiration also comes from OpenAI's article [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/), especially its framing of repository-local knowledge as the system of record, `AGENTS.md` as a compact map rather than a giant manual, and agent legibility as an engineering goal.

## What It Does

When you invoke this skill in a target repository, it will:

- Check whether the repository root has an `AGENTS.md`.
- Check whether `AGENTS.md` already contains this skill's generated marker block.
- Ask whether Codex should read the project and generate the guide when the block is missing.
- Read the previous generation time and incrementally refresh affected modules when the block already exists.
- Keep macro module boundary decisions in the main agent while using explicitly authorized subagents for module-internal exploration.
- Generate `Agent Editing Rules`, `Task Routing`, and `Module Dependency Rules` sections that capture project-specific editing constraints, routing hints, and dependency boundaries.
- Store a parseable `sha256:v1` signature and force a full refresh if generated metadata or signed content no longer verifies.
- Update only the content inside the marker block while preserving all human-written `AGENTS.md` content outside it.

The fixed marker block is:

```markdown
<!-- code-project-guidance-map:start -->
<!-- code-project-guidance-map:end -->
```

The generated block is action-oriented:

- `Agent Editing Rules`: high-signal `[MUST]`, `[SHOULD]`, and `[AVOID]` rules that prevent likely wrong edits.
- `Task Routing`: common changes mapped to the paths and owning modules a future Codex session should read or edit.
- `Module Dependency Rules`: project-specific dependency direction, forbidden dependency, ownership, and layer-flow rules.
- `Module Map`: short human-readable module names with paths shown separately.
- `Module Path`: the primary path or path list for the module.
- `Owns`: the capability or domain owned by the module.
- `Change here when`: when future edits should land in the module.
- `Do not put here`: responsibilities that belong elsewhere.
- `Key entry points`: compact files or directories to read first.

## Quick Start

Clone this repository:

```powershell
git clone <repo-url>
cd Code-Project-Guidance-Map-Skills
```

Register this repository as a Codex plugin marketplace:

```powershell
codex plugin marketplace add <absolute-path-to-this-repo>
```

Install the plugin from that marketplace:

```powershell
codex plugin add code-project-guidance-map@code-project-guidance-map
```

Windows example:

```powershell
codex plugin marketplace add D:\work\Code-Project-Guidance-Map-Skills
codex plugin add code-project-guidance-map@code-project-guidance-map
```

After installation, open a new Codex thread in the project you want to document and invoke:

```text
Use $code-project-guidance-map to create or refresh this repository's AGENTS.md action map, including Agent Editing Rules, Task Routing, Module Dependency Rules, and Module Map. I explicitly authorize subagents for this run. First decide the macro module boundaries in the main agent, then spawn subagents for bounded module-internal exploration when a subagent tool is available; do not ask again for subagent approval. If subagents are unavailable, continue locally and report the fallback.
```

## Usage

Generate the guide when Codex first joins a project:

```text
Use $code-project-guidance-map to create the AGENTS.md action map with Agent Editing Rules, Task Routing, Module Dependency Rules, and Module Map. I explicitly authorize subagents for this run. First decide the macro module boundaries in the main agent, then spawn subagents for bounded module-internal exploration when a subagent tool is available; do not ask again for subagent approval. If subagents are unavailable, continue locally and report the fallback.
```

Refresh the guide after meaningful structure changes:

```text
Use $code-project-guidance-map to refresh the AGENTS.md action map based on recent Git changes, including editing rules, task routing, dependency rules, and affected modules. I explicitly authorize subagents for this run. First decide the macro module boundaries in the main agent, then spawn subagents for bounded module-internal exploration when a subagent tool is available; do not ask again for subagent approval. If subagents are unavailable, continue locally and report the fallback.
```

Use the guide before larger feature work:

```text
Use $code-project-guidance-map, then help me identify where this feature should be implemented.
```

v1 requires explicit user invocation. It does not promise an automatic popup the instant Codex enters a project, but once the guide is generated, later Codex sessions can read `AGENTS.md` automatically.

Subagents are explicit. The recommended prompts above authorize them up front, so Codex should not stop to ask again. The main agent first drafts the macro module map, then spawns the smallest useful set of subagents with bounded path scopes for internal structure and evidence. Subagents must not edit files or decide the global module map. If subagent tools are unavailable, the main agent completes the same exploration locally and reports the fallback.

## Result

After a successful run, the target repository gets an `AGENTS.md` block like this:

````markdown
<!-- code-project-guidance-map:start -->
## Code Project Guidance Map

Generator: code-project-guidance-map
Guide format: action-map:v2
Generated at: 2026-06-11T10:30:00Z
Git baseline: abc1234
Signature algorithm: sha256:v1
Signature: sha256:<64 lowercase hex chars>

### Agent Editing Rules

- [MUST] Put new scheduling business rules in `src/core/scheduling`; expose them through API modules only after service behavior exists.
- [MUST] Keep persistence SQL beside the owning mapper or repository path.
- [SHOULD] Reuse existing services before adding new orchestration.
- [AVOID] Adding business or web dependencies to shared utility modules.

### Task Routing

- To add a REST API: edit `src/api`; call services from `src/core` instead of duplicating business logic.
- To change scheduling rules: edit `src/core/scheduling`; update matching tests before touching API response shape.
- To change persistence SQL: edit `src/persistence` and matching mapper resources.
- To change frontend-facing response shape: edit `src/api` DTOs and adapters.

### Module Dependency Rules

- Shared utilities are the lowest-level code and must not depend on business, web, or persistence modules.
- API modules call services; services own business rules; persistence modules own storage adapters and SQL.
- Frontend-facing facades should orchestrate existing services instead of duplicating domain behavior.
- Build/package boundary changes require re-checking this entire action map.

### Module Map

#### Scheduling

- Module Path: `src/core/scheduling`
- Owns: Scheduling rules, shift rotation decisions, and scheduling-domain service behavior.
- Change here when: A task changes how schedules are calculated, validated, or persisted through domain services.
- Do not put here: HTTP response shaping, frontend-only DTOs, or generic shared helpers.
- Key entry points:

```text
src/core/scheduling/
  services/
  strategies/
  tests/
```
<!-- code-project-guidance-map:end -->
````

This helps Codex answer questions such as:

- Where should a new feature be implemented?
- Which module owns a behavior?
- Which file changes affect a module?
- Which directories should be read before editing?

## Distribution

This repository already contains a distributable plugin package:

- Development skill: `.agents/skills/code-project-guidance-map/`
- Installable plugin: `plugins/code-project-guidance-map/`
- Plugin manifest: `plugins/code-project-guidance-map/.codex-plugin/plugin.json`
- Local marketplace: `.agents/plugins/marketplace.json`

To install the plugin, users need access to this repository and then run:

```powershell
codex plugin marketplace add <absolute-path-to-this-repo>
codex plugin add code-project-guidance-map@code-project-guidance-map
```

To publish it through a team marketplace:

1. Publish this repository somewhere the team can access, such as GitHub, an internal Git server, or a shared directory.
2. Keep `plugins/code-project-guidance-map/.codex-plugin/plugin.json`.
3. Keep `.agents/plugins/marketplace.json`; its marketplace name is `code-project-guidance-map`.
4. Tell users to add the marketplace first and then install `code-project-guidance-map@code-project-guidance-map`.

## Repository Layout

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── .agents/
│   ├── plugins/
│   │   └── marketplace.json
│   └── skills/
│       └── code-project-guidance-map/
├── docs/
│   ├── ci.md
│   └── codex-skills-research.md
├── scripts/
│   ├── sync_plugin_skill.py
│   └── test_sync_plugin_skill.py
└── plugins/
    └── code-project-guidance-map/
        ├── .codex-plugin/
        │   └── plugin.json
        └── skills/
            └── code-project-guidance-map/
```

## Development And Validation

The development skill is the source of truth:

```text
.agents/skills/code-project-guidance-map/
```

After changing the skill, sync it into the distributable plugin copy:

```powershell
python scripts\sync_plugin_skill.py
python scripts\sync_plugin_skill.py --check
```

Then validate:

```powershell
python scripts\test_sync_plugin_skill.py
python .agents\skills\code-project-guidance-map\scripts\test_guidance_map.py
python plugins\code-project-guidance-map\skills\code-project-guidance-map\scripts\test_guidance_map.py
python <codex-checkout>\codex-rs\skills\src\assets\samples\skill-creator\scripts\quick_validate.py .agents\skills\code-project-guidance-map
python <codex-checkout>\codex-rs\skills\src\assets\samples\skill-creator\scripts\quick_validate.py plugins\code-project-guidance-map\skills\code-project-guidance-map
python <plugin-creator-skill>\scripts\validate_plugin.py plugins\code-project-guidance-map
```

See [docs/ci.md](docs/ci.md) for GitHub Actions and target-project `verify` CI guidance.

If the plugin is already installed locally, reinstall it after changes:

```powershell
python <plugin-creator-skill>\scripts\update_plugin_cachebuster.py plugins\code-project-guidance-map
codex plugin add code-project-guidance-map@code-project-guidance-map
```

Then start a new Codex thread so Codex loads the updated plugin.

## Project Intent

This project aims to move Codex from temporary source reading toward reusable project memory.

The goal is not to produce a complete project manual. The plugin compiles the parts of a codebase that later agents need most: module boundaries, dependency direction, ownership rules, and compact navigation cues. By writing those constraints into `AGENTS.md`, later Codex sessions can locate code faster, guess less about module ownership, and participate more reliably in feature work, refactoring, and code review.
