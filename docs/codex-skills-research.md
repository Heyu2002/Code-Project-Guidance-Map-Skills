# Codex Skills Research

Source: local checkout `D:\project\Heyu2002\codex`.

This note captures the practical skill design rules learned from:

- System sample skills in `codex-rs/skills/src/assets/samples`
- Repository skills in `.codex/skills`
- Skill loading, rendering, and injection code in `codex-rs/core-skills`
- Skill API documentation in `codex-rs/app-server/README.md`

## Runtime Model

A Codex skill is a directory containing `SKILL.md`. At session start, Codex exposes only each skill's name, description, and path in the model-visible skill list. When a user explicitly invokes a skill, for example with `$skill-name`, Codex injects the full `SKILL.md` into context.

Main scan locations:

- Repo skill: `.agents/skills/<skill-name>/SKILL.md`
- User skill: `$CODEX_HOME/skills/<skill-name>/SKILL.md`
- User skill, newer location: `$HOME/.agents/skills/<skill-name>/SKILL.md`
- System skill cache: `$CODEX_HOME/skills/.system/<skill-name>/SKILL.md`
- Plugin skill: `<plugin-root>/skills/<skill-name>/SKILL.md`
- App-server runtime roots: `skills/extraRoots/set`

Loading behavior:

- Scan depth is capped at 6.
- Each root scans at most 2000 directories.
- Hidden directories are skipped.
- Repo, user, and admin skills follow symlinked directories. System skills do not.
- Invalid non-system skills appear in load errors. Invalid system skills are ignored.
- Render priority for the model-visible skill list is system, admin, repo, then user.

## Required Files

Minimal skill:

```text
<skill-name>/
  SKILL.md
```

Recommended skill:

```text
<skill-name>/
  SKILL.md
  agents/
    openai.yaml
  scripts/
  references/
  assets/
```

Core `SKILL.md` frontmatter:

```yaml
---
name: skill-name
description: Dense trigger description. Include what this skill does and when to use it.
---
```

Constraints:

- Use lowercase hyphen-case names with letters, digits, and hyphens.
- Keep `name` at 64 characters or less.
- Keep `description` at 1024 characters or less.
- Put trigger information in `description`; do not rely on a body section named "When to use".
- Use the body for workflow, scripts, references, stop conditions, and output rules.
- Legacy `metadata.short-description` is still parsed, but UI metadata should live in `agents/openai.yaml`.

Optional `agents/openai.yaml`:

```yaml
interface:
  display_name: "Display Name"
  short_description: "25 to 64 character UI description"
  icon_small: "./assets/small.svg"
  icon_large: "./assets/large.png"
  brand_color: "#3B82F6"
  default_prompt: "Use $skill-name to ..."

dependencies:
  tools:
    - type: "mcp"
      value: "github"
      description: "GitHub MCP server"
      transport: "streamable_http"
      url: "https://example.com/mcp"

policy:
  allow_implicit_invocation: true
```

Metadata notes:

- Icon paths must resolve under the skill `assets/` directory.
- Plugin skills may reference shared plugin-level `assets/` with relative paths that stay under plugin assets.
- `brand_color` must be `#RRGGBB`.
- `default_prompt` is capped at 1024 characters and should usually mention `$skill-name`.
- `policy.allow_implicit_invocation: false` disables default implicit inclusion but still allows explicit invocation.

## Authoring Principles

1. Keep `SKILL.md` compact.
   Skill descriptions are rendered under a budget and can be shortened. Full skill bodies also consume context after invocation.

2. Use progressive disclosure.
   Keep core workflow in `SKILL.md`. Move detailed references, API notes, schemas, examples, or provider-specific instructions into directly linked files under `references/`.

3. Script repeated or fragile work.
   Put repeatable API queries, file scans, conversions, parsers, and validators in `scripts/`. Add focused tests or at least a dry run.

4. Do not overbuild simple guideline skills.
   The `code-review-*` skills in Codex are intentionally tiny. Some useful skills are only a few rules.

5. Write stop conditions and safety boundaries.
   The strongest operational skills make it clear when to continue, when to stop, and which actions require user confirmation.

6. Avoid auxiliary documentation inside the skill directory.
   Do not add README, changelog, installation guide, or process notes unless they are direct execution resources.

## Patterns From Codex

`babysit-pr`:

- Best pattern for complex automation.
- Uses a watcher script as the source of truth.
- `SKILL.md` defines objectives, inputs, command modes, CI classification, review handling, git safety, stop conditions, and output expectations.
- `references/` holds heuristics and API notes.
- `scripts/` includes tests.

`codex-issue-digest`:

- Best pattern for "collect data, then render a fixed report contract".
- The collector JSON is the source of truth.
- `SKILL.md` defines summary mode, details mode, table shape, source line, and attention markers.

`code-review` plus `code-review-*`:

- Best pattern for composable rules.
- One orchestrator skill delegates to narrow sub-skills.
- Small sub-skills can be stronger than one large undifferentiated instruction file.

`update-v8-version`:

- Best pattern for repo-specific operational workflow.
- Lists concrete files and commands.
- Separates normal release validation from failure investigation.

System sample skills:

- `skill-creator`: canonical process for creating skills.
- `openai-docs`: MCP dependency plus official-docs and fallback-reference workflow.
- `imagegen`: built-in tool first, CLI fallback only when requested, local post-processing helpers.
- `plugin-creator`: scaffold scripts, manifest validation, and marketplace workflow.

## Validation

Basic validation:

```powershell
python D:\project\Heyu2002\codex\codex-rs\skills\src\assets\samples\skill-creator\scripts\quick_validate.py <skill-directory>
```

If a skill has scripts, run representative script tests or dry runs. The more a script touches external APIs, Git, CI, or file conversion, the more important deterministic tests become.

Complex skills should also be forward-tested with realistic user prompts in a clean context. Pass the skill and the raw task; do not pass expected answers or prior conclusions.

## Implemented Project Direction

The concrete skill now uses repo-level auto-discovery:

```text
.agents/
  skills/
    code-project-guidance-map/
      SKILL.md
      agents/openai.yaml
      references/
      scripts/
```

Plugin-level distribution:

```text
.codex-plugin/
  plugin.json
skills/
  code-project-guidance-map/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/
assets/
```

Private local user skill:

```text
$CODEX_HOME/skills/code-project-guidance-map/
  SKILL.md
  agents/openai.yaml
```

Inputs needed before implementation:

- Objective: create or refresh a concise `AGENTS.md` project editing action map.
- Invocation model: explicit user invocation; no automatic project-entry hook in v1.
- Output artifact: a marker-delimited `AGENTS.md` block with editing rules, task routing, dependency rules, and module ownership entries.
- Script-backed behavior: marker parsing, Git delta detection, and safe `AGENTS.md` block replacement.
