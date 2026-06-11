# CI Maintenance

Use CI to keep this plugin and generated `AGENTS.md` guidance reliable without forcing every run to reread the whole project.

## Plugin Repository CI

This repository should validate that the development skill and distributable plugin copy stay aligned:

```powershell
python scripts\sync_plugin_skill.py --check
python scripts\test_sync_plugin_skill.py
python .agents\skills\code-project-guidance-map\scripts\test_guidance_map.py
python plugins\code-project-guidance-map\skills\code-project-guidance-map\scripts\test_guidance_map.py
python -m json.tool plugins\code-project-guidance-map\.codex-plugin\plugin.json
```

## Target Project CI

Target projects can use the skill helper as a lightweight freshness check:

```powershell
python <installed-skill>\scripts\guidance_map.py verify --repo . --fail-on error
```

This fails only when the guidance block is missing, malformed, or has invalid metadata/signature.

For stricter projects, use:

```powershell
python <installed-skill>\scripts\guidance_map.py verify --repo . --fail-on stale
```

That also fails when changed files indicate the guidance should be refreshed.

## Refresh Scope

`verify` classifies changed files into:

- `boundary_rules`: build files, module manifests, workspace configs, and other changes that can affect dependency direction.
- `task_routing`: controllers, routes, APIs, services, DAOs, SQL mappings, jobs, schedules, WebSocket, MQ, and queue files.
- `module_internal`: ordinary code files that usually require only affected module entries to refresh.
- `docs_only`: documentation or CI changes that do not require a guidance refresh.
- `other`: unclassified files that should be reviewed by a maintainer.

The goal is conservative maintenance:

- Do not re-read the whole repository for ordinary module-internal changes.
- Re-evaluate `Module Dependency Rules` only for boundary-sensitive changes.
- Refresh task routing only when entrypoint or layer-flow files changed.
- Keep `AGENTS.md` compact and useful for future agent editing decisions.
