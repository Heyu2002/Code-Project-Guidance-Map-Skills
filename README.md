# Code Project Guidance Map

[中文说明](README-CN.md)

Code Project Guidance Map is a Codex plugin and skill that helps Codex understand a repository faster and preserve that understanding in the repository root `AGENTS.md`.

Its purpose is not to generate broad project documentation. It creates a compact, durable, refreshable code module guidance map for Codex: each module explains what it can do, what belongs there, and how it is roughly structured. Future Codex sessions can read `AGENTS.md` automatically, so the module map becomes reusable project context.

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
- Store a parseable `sha256:v1` signature and force a full refresh if generated metadata or signed content no longer verifies.
- Update only the content inside the marker block while preserving all human-written `AGENTS.md` content outside it.

The fixed marker block is:

```markdown
<!-- code-project-guidance-map:start -->
<!-- code-project-guidance-map:end -->
```

Each module entry uses a short human-readable module name as the heading, with paths and included parts shown separately:

- `Module Path`: the primary path or path list for the module.
- `Module Capability`: what capability the module provides.
- `Module Responsibility`: what code belongs in the module.
- `Module Structure`: the module's rough internal structure.
- `Module Contains`: a compact `text` tree or list of the main directories/files in the module.

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
Use $code-project-guidance-map to create or refresh the AGENTS.md module guidance map for this repository.
```

## Usage

Generate the guide when Codex first joins a project:

```text
Use $code-project-guidance-map to create the AGENTS.md module guidance map.
```

Refresh the guide after meaningful structure changes:

```text
Use $code-project-guidance-map to refresh the module guide based on recent Git changes.
```

Use the guide before larger feature work:

```text
Use $code-project-guidance-map, then help me identify where this feature should be implemented.
```

v1 requires explicit user invocation. It does not promise an automatic popup the instant Codex enters a project, but once the guide is generated, later Codex sessions can read `AGENTS.md` automatically.

## Result

After a successful run, the target repository gets an `AGENTS.md` block like this:

````markdown
<!-- code-project-guidance-map:start -->
## Code Project Guidance Map

Generator: code-project-guidance-map
Generated at: 2026-06-11T10:30:00Z
Git baseline: abc1234
Signature algorithm: sha256:v1
Signature: sha256:<64 lowercase hex chars>

### Core

- Module Path: `src/core`
- Module Capability: Provides core business rules and domain workflows.
- Module Responsibility: Contains reusable business logic, state transitions, and domain services.
- Module Structure: Organized around domain models, service functions, and lightweight coordination logic.
- Module Contains:

```text
src/core/
├── models/
├── services/
└── index.ts
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
├── .agents/
│   ├── plugins/
│   │   └── marketplace.json
│   └── skills/
│       └── code-project-guidance-map/
├── docs/
│   └── codex-skills-research.md
└── plugins/
    └── code-project-guidance-map/
        ├── .codex-plugin/
        │   └── plugin.json
        └── skills/
            └── code-project-guidance-map/
```

## Development And Validation

After changing the skill or plugin, run:

```powershell
python .agents\skills\code-project-guidance-map\scripts\test_guidance_map.py
python plugins\code-project-guidance-map\skills\code-project-guidance-map\scripts\test_guidance_map.py
python <codex-checkout>\codex-rs\skills\src\assets\samples\skill-creator\scripts\quick_validate.py .agents\skills\code-project-guidance-map
python <codex-checkout>\codex-rs\skills\src\assets\samples\skill-creator\scripts\quick_validate.py plugins\code-project-guidance-map\skills\code-project-guidance-map
python <plugin-creator-skill>\scripts\validate_plugin.py plugins\code-project-guidance-map
```

If the plugin is already installed locally, reinstall it after changes:

```powershell
codex plugin add code-project-guidance-map@code-project-guidance-map
```

Then start a new Codex thread so Codex loads the updated plugin.

## Project Intent

This project aims to move Codex from temporary source reading toward reusable project memory.

By writing module boundaries, responsibilities, and placement rules into `AGENTS.md`, later Codex sessions can locate code faster, guess less about module ownership, and participate more reliably in feature work, refactoring, and code review.
