# Code Project Guidance Map

[English README](README.md)

Code Project Guidance Map 是一个 Codex plugin + skill，用来让 Codex 在进入一个项目后更快理解代码结构，并把这份理解沉淀到项目根目录的 `AGENTS.md`。

它的主旨不是生成一大篇泛泛的项目文档，而是为 Codex 提供一份短、稳、可持续刷新的“代码行动地图”：编辑规则、任务路由、依赖边界和简洁的模块归属。后续 Codex 线程会自动读取 `AGENTS.md`，这份地图就会变成项目的长期上下文。

## 背景

这个插件来自 Codex 仓库中的 feature request：[Feature request: Add a standardized code audit module for modular codebases #26007](https://github.com/openai/codex/issues/26007)。

该 issue 希望 Codex 能为模块化代码库生成并维护标准化的 code audit module，让后续 agent 不必每次都从零重新阅读大量源码。由于这个 feature request 目前仍处于 Open 状态，且暂未看到 assignee、project、milestone 或关联开发 PR，这里先把它单独做成一个可安装的 Codex plugin，用插件方式验证这条工作流是否真正有用。

这个插件也有一部分灵感来自 OpenAI 的文章 [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/)，尤其是其中关于 repository-local knowledge 作为 system of record、`AGENTS.md` 应该是紧凑地图而不是巨型手册，以及 agent legibility 是工程目标的思路。

## 它是做什么的

当你在目标项目里调用这个 skill 时，它会：

- 检查项目根目录是否存在 `AGENTS.md`。
- 检查 `AGENTS.md` 中是否已有本 skill 生成的固定区块。
- 如果没有区块，询问是否需要阅读项目并生成模块指引。
- 如果已有区块，读取上次生成时间，并根据 Git 变化增量刷新受影响模块。
- 由主 agent 决定宏观模块边界；在用户显式授权后，用 subagents 探索模块内部细节。
- 生成 `Agent Editing Rules`、`Task Routing` 和 `Module Dependency Rules` 区块，记录当前项目特有的编辑约束、任务路由和依赖边界。
- 写入插件认证的 `hmac-sha256:v2` 签名；如果生成元数据、签名 key 或已签名内容无法验证，则触发完整刷新。
- 只更新 marker 区块内部内容，保留 `AGENTS.md` 中其他人工维护内容。
- 通过轻量 plugin hooks 在 `SessionStart` 和 `UserPromptSubmit` 时检测指引是否缺失、过期或无法验签，并在代码修改前给 Codex 注入有边界的提醒上下文。

固定 marker 如下：

```markdown
<!-- code-project-guidance-map:start -->
<!-- code-project-guidance-map:end -->
```

生成的区块偏行动导向：

- `Agent Editing Rules`: 高信号的 `[MUST]`、`[SHOULD]`、`[AVOID]` 规则，用来避免未来 Codex 做出明显错误的修改。
- `Task Routing`: 把常见修改映射到未来 Codex 应该先读或编辑的路径和归属模块。
- `Module Dependency Rules`: 当前项目特有的依赖方向、禁止依赖、归属和分层调用规则。
- `Module Map`: 用简短、适合人读的模块名作为标题，路径单独展示。
- `Module Path`: 模块对应的主要路径或路径列表。
- `Owns`: 模块拥有的能力或业务域。
- `Change here when`: 什么时候应该改这个模块。
- `Do not put here`: 哪些职责不应该放进这个模块。
- `Key entry points`: 修改前最应该先读的关键文件或目录。

marker 区块属于插件维护内容，不应该真人手工维护。真人直接修改生成内容会导致签名失效；正确维护方式是重新运行 skill。默认情况下，辅助脚本会在目标仓库之外的 Codex 用户目录中创建一个 repo 级签名 key。团队或 CI 可以通过 `CODE_PROJECT_GUIDANCE_MAP_SECRET` 配置共享 secret，或通过 `CODE_PROJECT_GUIDANCE_MAP_KEY_FILE` 指定 key 文件。

## 快速启动

克隆这个仓库：

```powershell
git clone <repo-url>
cd Code-Project-Guidance-Map-Skills
```

把当前仓库注册为 Codex plugin marketplace：

```powershell
codex plugin marketplace add <absolute-path-to-this-repo>
```

从这个 marketplace 安装插件：

```powershell
codex plugin add code-project-guidance-map@code-project-guidance-map
```

Windows 示例：

```powershell
codex plugin marketplace add D:\work\Code-Project-Guidance-Map-Skills
codex plugin add code-project-guidance-map@code-project-guidance-map
```

安装后，在你想生成代码指引的项目中新开一个 Codex 线程，然后输入：

```text
Use $code-project-guidance-map to create or refresh this repository's AGENTS.md action map, including Agent Editing Rules, Task Routing, Module Dependency Rules, and Module Map. I explicitly authorize subagents for this run. First decide the macro module boundaries in the main agent, then spawn subagents for bounded module-internal exploration when a subagent tool is available; do not ask again for subagent approval. If subagents are unavailable, continue locally and report the fallback.
```

## 如何使用

第一次让 Codex 阅读项目并生成指引：

```text
Use $code-project-guidance-map to create the AGENTS.md action map with Agent Editing Rules, Task Routing, Module Dependency Rules, and Module Map. I explicitly authorize subagents for this run. First decide the macro module boundaries in the main agent, then spawn subagents for bounded module-internal exploration when a subagent tool is available; do not ask again for subagent approval. If subagents are unavailable, continue locally and report the fallback.
```

项目结构有明显变化后刷新指引：

```text
Use $code-project-guidance-map to refresh the AGENTS.md action map based on recent Git changes, including editing rules, task routing, dependency rules, and affected modules. I explicitly authorize subagents for this run. First decide the macro module boundaries in the main agent, then spawn subagents for bounded module-internal exploration when a subagent tool is available; do not ask again for subagent approval. If subagents are unavailable, continue locally and report the fallback.
```

做较大功能前，先让 Codex 对齐模块边界：

```text
Use $code-project-guidance-map, then help me identify where this feature should be implemented.
```

生成和刷新指引仍然由 skill 完成，但安装后的 plugin 现在带有轻量 hooks。`SessionStart` 时，hook 会验证当前仓库的指引区块；如果缺失、过期或无法验签，就给 Codex 注入一段有边界的上下文。`UserPromptSubmit` 时，hook 只会在用户请求看起来是代码修改任务、且指引需要处理时注入上下文。hooks 不会编辑文件，也不会自动刷新 `AGENTS.md`；它只会提醒 Codex 在第一次代码修改前建议运行 `$code-project-guidance-map`。

subagents 需要显式授权。上面的推荐 prompt 已经提前授权，所以 Codex 不应该再次停下来询问。主 agent 会先草拟宏观模块地图，然后启动最少必要数量的 subagents，让它们在有边界的路径范围内探索内部结构和证据。subagents 不应该编辑文件，也不应该决定全局模块地图。如果 subagent 工具不可用，主 agent 会在本地完成同样的探索，并在结果里说明 fallback。

## 会产生什么效果

成功运行后，目标项目的 `AGENTS.md` 会出现类似下面的区块：

````markdown
<!-- code-project-guidance-map:start -->
## Code Project Guidance Map

Generator: code-project-guidance-map
Guide format: action-map:v2
Generated at: 2026-06-11T10:30:00Z
Git baseline: abc1234
Signature key id: repo:1a2b3c4d5e6f7890
Signature: hmac-sha256:<64 lowercase hex chars>

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

这能帮助 Codex 更快回答这些问题：

- 新功能应该写在哪里？
- 某个行为由哪个模块负责？
- 哪些文件变化会影响某个模块？
- 修改前应该先阅读哪些目录？

## 分发给别人使用

这个仓库已经包含可分发的 plugin 包：

- 开发用 skill: `.agents/skills/code-project-guidance-map/`
- 可安装 plugin: `plugins/code-project-guidance-map/`
- plugin manifest: `plugins/code-project-guidance-map/.codex-plugin/plugin.json`
- plugin hooks: `plugins/code-project-guidance-map/hooks/`
- 本地 marketplace: `.agents/plugins/marketplace.json`

别人要安装时，需要拿到这个仓库，然后执行：

```powershell
codex plugin marketplace add <absolute-path-to-this-repo>
codex plugin add code-project-guidance-map@code-project-guidance-map
```

如果你要把它放到团队内部 marketplace，核心动作是：

1. 把这个仓库发布到团队可访问的位置，比如 GitHub、内部 Git 或共享目录。
2. 保留 `plugins/code-project-guidance-map/.codex-plugin/plugin.json`。
3. 保留 `.agents/plugins/marketplace.json`，其中 marketplace 名称为 `code-project-guidance-map`。
4. 告诉使用者先添加 marketplace，再安装 `code-project-guidance-map@code-project-guidance-map`。

## 目录结构

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
        ├── hooks/
        │   ├── guidance_map_hook.py
        │   └── hooks.json
        └── skills/
            └── code-project-guidance-map/
```

## 开发和验证

开发用 skill 是唯一源：

```text
.agents/skills/code-project-guidance-map/
```

修改 skill 后，先同步到可分发的 plugin 副本：

```powershell
python scripts\sync_plugin_skill.py
python scripts\sync_plugin_skill.py --check
```

然后运行验证：

```powershell
python scripts\test_sync_plugin_skill.py
python .agents\skills\code-project-guidance-map\scripts\test_guidance_map.py
python plugins\code-project-guidance-map\skills\code-project-guidance-map\scripts\test_guidance_map.py
python plugins\code-project-guidance-map\hooks\test_guidance_map_hook.py
python <codex-checkout>\codex-rs\skills\src\assets\samples\skill-creator\scripts\quick_validate.py .agents\skills\code-project-guidance-map
python <codex-checkout>\codex-rs\skills\src\assets\samples\skill-creator\scripts\quick_validate.py plugins\code-project-guidance-map\skills\code-project-guidance-map
python <plugin-creator-skill>\scripts\validate_plugin.py plugins\code-project-guidance-map
```

GitHub Actions 和目标项目 `verify` CI 接入方式见 [docs/ci.md](docs/ci.md)。

本机开发时，如果插件已经安装过，改完后重新安装：

```powershell
python <plugin-creator-skill>\scripts\update_plugin_cachebuster.py plugins\code-project-guidance-map
codex plugin add code-project-guidance-map@code-project-guidance-map
```

然后新开 Codex 线程，让 Codex 重新加载插件。

## 项目主旨

这个项目的目标是让 Codex 从“临时读代码”变成“有项目记忆地协作”。

它的目标不是生成完整项目手册，而是提炼后续 agent 最需要的部分：模块边界、依赖方向、归属规则和紧凑导航线索。通过把这些约束写入 `AGENTS.md`，Codex 后续在同一个项目里工作时，可以更快定位代码、更少猜测模块职责，并更稳定地参与需求实现、重构和代码审查。
