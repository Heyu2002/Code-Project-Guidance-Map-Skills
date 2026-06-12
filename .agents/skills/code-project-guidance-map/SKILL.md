---
name: code-project-guidance-map
description: Create or refresh a structured AGENTS.md action map for a repository, including Agent Editing Rules, Task Routing, Module Dependency Rules, and a concise Module Map. Use when the user asks Codex to read a project, map code structure, document module ownership, clarify module dependency boundaries, initialize project guidance, refresh an AGENTS.md project guide, or keep concise project editing guidance up to date from Git changes. When invoked, the main agent must decide macro module boundaries first, then use explicitly authorized subagents for bounded module-internal exploration when available.
---

# Code Project Guidance Map

## Objective

Create or refresh the `code-project-guidance-map` block in the repository root `AGENTS.md`.
The block gives future Codex sessions a concise module guide for the project.

This skill does not run automatically when Codex enters a project. It is invoked by the user. Once the block exists in `AGENTS.md`, Codex will naturally read it through normal AGENTS.md behavior.

## Markers

Manage only the content between these exact markers:

```markdown
<!-- code-project-guidance-map:start -->
<!-- code-project-guidance-map:end -->
```

Do not rewrite content outside the marker block.

## Workflow

1. Locate the repository root.
   - Prefer `git rev-parse --show-toplevel`.
   - If Git is unavailable or the directory is not a Git repository, use the current working directory.

2. Inspect `AGENTS.md` state with:

```bash
python <skill-dir>/scripts/guidance_map.py status --repo <repo-root>
```

Then classify freshness and refresh scope with:

```bash
python <skill-dir>/scripts/guidance_map.py verify --repo <repo-root>
```

3. If `AGENTS.md` is missing or has no guidance block, ask the user whether to read the project and generate the guide. If the user already explicitly requested generation or refresh, treat that as consent and continue.

4. If a guidance block exists:
   - Read its `Generated at` timestamp and `hmac-sha256:v2` signature metadata.
   - Use the script `verify` JSON to inspect Git changes since that timestamp, including committed, staged, unstaged, and untracked files.
   - If the timestamp is missing or invalid, if the signing key is unavailable, or if the signature is missing or invalid, perform a full project read.
   - If `recommended_action` is `refresh_dependency_rules`, re-evaluate `Agent Editing Rules`, `Module Dependency Rules`, and affected module entries.
   - If `recommended_action` is `refresh_task_routing_and_affected_modules`, refresh task routing guidance and affected module entries without re-reading unrelated modules.
   - If `recommended_action` is `refresh_affected_modules`, re-read only affected modules.
   - If `recommended_action` is `none`, report that the guide is current unless the user explicitly asks for a full refresh.
   - If there are no changes, report that the guide is already current unless the user explicitly asks for a full refresh.
   - If changes exist, do an incremental read focused on affected modules and preserve unchanged module entries.

5. Decide the macro module map before delegation.
   - The main agent owns the global module map: choose concise module names, group paths into modules, decide whether the run is full or incremental, and define bounded scopes for any subagents.
   - Do not spawn subagents until this draft macro map exists.
   - Do not delegate the global module-boundary decision.
   - Let the actual code structure drive module boundaries. Do not force a top-level-only or all-directories scheme.
   - Derive project-specific dependency direction rules from the macro map, build files, package names, imports, controllers/services/DAOs, SQL mappings, and domain ownership clues.

6. Delegate module-internal exploration after authorization.
   - Treat any user prompt or default prompt that says `use subagents`, `delegate`, `parallel agents`, or equivalent as explicit authorization. Do not ask again.
   - If the user did not explicitly authorize subagents and the project needs non-trivial reading, ask one concise yes/no question before spawning: `Use subagents for module-internal exploration?`
   - When authorized and a subagent/delegation tool is available, spawn the smallest useful set of explorer subagents after step 5.
   - Give each subagent a module name, bounded path scope, relevant changed files if any, and ask for: key files/directories, module capability evidence, responsibility boundaries, dependency evidence, internal structure, and uncertainty.
   - Subagents must not edit files, update `AGENTS.md`, or decide the global module map.
   - The main agent integrates subagent findings and writes the final guide.
   - If subagents are unavailable or not authorized, perform the same internal exploration locally and mention that fallback in the final response.

7. Write a concise English action guide optimized for future Codex editing.
   - Use this exact section order: `### Agent Editing Rules`, `### Task Routing`, `### Module Dependency Rules`, `### Module Map`.
   - `Agent Editing Rules` is the highest-value section. Write 4-8 project-specific editing constraints with `[MUST]`, `[SHOULD]`, or `[AVOID]` tags. These rules should prevent likely wrong edits.
   - `Task Routing` should answer "where do I edit for this task?" in 4-10 bullets using the shape `- To <task>: edit/read <paths>; ...`.
   - `Module Dependency Rules` should contain 4-10 dependency rules as direct bullets. Prefer rules that help a future agent decide where code belongs and which dependencies are forbidden.
   - Cover layer direction, shared utility constraints, domain ownership, facade/orchestration boundaries, persistence placement, and controller/service/DAO flow when the project provides evidence.
   - Keep rules project-specific. Do not paste example module names such as `common`, `web`, `modules/core`, or `oriot` unless those modules actually exist in the target project.
   - Put all module entries under `### Module Map`.
   - Use a short, human-friendly module name as each `####` heading. Do not put long paths in the heading.
   - Put paths in `Module Path` as a separate field.
   - Each module must include exactly these fields:
     - `Module Path`: primary path or path list.
     - `Owns`: the capability or domain the module owns.
     - `Change here when`: the tasks that should be implemented in this module.
     - `Do not put here`: code or responsibilities that belong elsewhere.
     - `Key entry points`: compact file/directory list, inline when short or fenced `text` when clearer.
   - Prefer operational phrasing over abstract summaries. Future agents should be able to route edits from this block without rereading the whole project.

8. Save the guide body to a temporary file, then update `AGENTS.md` with:

```bash
python <skill-dir>/scripts/guidance_map.py update --repo <repo-root> --guidance-file <temp-guidance.md>
```

The script creates `AGENTS.md` if needed, appends the block if missing, and replaces only the marker block if present.

## Output Format

Use this shape inside the generated block:

````markdown
## Code Project Guidance Map

Generator: code-project-guidance-map
Guide format: action-map:v2
Generated at: <ISO-8601 timestamp>
Git baseline: <HEAD sha or none>
Signature key id: <repo-scoped key id>
Signature algorithm: hmac-sha256:v2
Signature: hmac-sha256:<64 lowercase hex chars>

### Agent Editing Rules

- [MUST] <project-specific editing rule that prevents likely wrong edits>
- [SHOULD] <project-specific preferred edit pattern>
- [AVOID] <project-specific dependency, ownership, or duplication risk>

### Task Routing

- To add a REST API: edit/read `<paths>`; keep behavior in `<owning module>`.
- To change persistence SQL: edit/read `<paths>`; keep SQL beside the owning mapper/DAO.

### Module Dependency Rules

- <project-specific dependency direction or boundary rule>
- <project-specific forbidden dependency or ownership rule>

### Module Map

#### <short module name>

- Module Path: `<primary path or path list>`
- Owns: <one concise English sentence naming the capability/domain this module owns>
- Change here when: <one concise English sentence describing the right edit cases>
- Do not put here: <one concise English sentence naming code that belongs elsewhere>
- Key entry points:

```text
<small file/directory list when useful>
```
````

Keep every module entry compact. Prefer one line per field. Avoid implementation trivia, long file inventories, and broad architecture essays.

## Incremental Update Rules

- Treat the script's `verify.changed_files`, `change_impact`, and `recommended_action` as the update scope.
- Do not re-evaluate `Agent Editing Rules` or `Module Dependency Rules` for ordinary module-internal changes.
- Re-evaluate `Agent Editing Rules` and `Module Dependency Rules` only when `change_impact.boundary_rules` is non-empty or marker metadata/signature/format is invalid.
- Refresh task-routing guidance when `change_impact.task_routing` is non-empty.
- Map changed files back to existing module entries when possible.
- Re-read only affected modules unless the changed files indicate a project-wide restructure.
- Preserve unchanged module entries verbatim when they still match the current project.
- Do a full refresh when:
  - marker metadata is missing or invalid;
  - the `hmac-sha256:v2` signature is missing, invalid, or cannot be verified because the signing key is unavailable;
  - many directories moved or were deleted;
  - build/package manifests changed in ways that alter module boundaries;
  - the existing guide is too stale to safely patch incrementally.

## Safety Rules

- Never edit files other than `AGENTS.md` for a target project unless the user explicitly asks.
- Never remove user-authored `AGENTS.md` content outside the marker block.
- Treat the generated marker block as plugin-owned. Do not manually edit generated block contents; manual edits invalidate the signature and require a plugin refresh.
- If marker structure is malformed, stop and report the issue instead of guessing.
- Do not include secrets, credentials, or private environment details in the generated guide.
- Do not write signing secrets into the repository or `AGENTS.md`. The helper stores a local key outside the target repository by default, or uses `CODE_PROJECT_GUIDANCE_MAP_SECRET` / `CODE_PROJECT_GUIDANCE_MAP_KEY_FILE` when configured.
- Standardize on `AGENTS.md`; do not create or update `Agent.md`.

## Validation

After updating a guide:

1. Re-run `status` to confirm `has_block` is true.
2. Verify `AGENTS.md` still contains any pre-existing content outside the marker block.
3. Summarize whether the run was full or incremental, whether subagents were used or why the workflow fell back to local exploration, how many modules were documented, and which changed files drove an incremental update.
