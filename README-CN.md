# Code Project Guidance Map

[English README](README.md)

Code Project Guidance Map 是一个 Codex plugin + skill，用来让 Codex 在进入一个项目后更快理解代码结构，并把这份理解沉淀到项目根目录的 `AGENTS.md`。

它的主旨不是生成一大篇泛泛的项目文档，而是为 Codex 提供一份短、稳、可持续刷新的“代码模块导航图”：每个模块写清楚能做什么、应该放什么、内部大概是什么结构。后续 Codex 线程会自动读取 `AGENTS.md`，这份模块导航就会变成项目的长期上下文。

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
- 写入可解析的 `sha256:v1` 签名；如果生成元数据或已签名内容无法验证，则触发完整刷新。
- 只更新 marker 区块内部内容，保留 `AGENTS.md` 中其他人工维护内容。

固定 marker 如下：

```markdown
<!-- code-project-guidance-map:start -->
<!-- code-project-guidance-map:end -->
```

每个模块会用简短、适合人读的模块名作为标题，路径和包含内容会单独展示：

- `Module Path`: 模块对应的主要路径或路径列表。
- `Module Capability`: 这个模块提供什么能力。
- `Module Responsibility`: 什么内容应该写在这个模块里。
- `Module Structure`: 这个模块的大概内部结构。
- `Module Contains`: 用紧凑的 `text` 树或列表展示模块里的主要目录/文件。

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
Use $code-project-guidance-map to create or refresh this repository's AGENTS.md module guidance map. I explicitly authorize subagents for this run. First decide the macro module boundaries in the main agent, then spawn subagents for bounded module-internal exploration when a subagent tool is available; do not ask again for subagent approval. If subagents are unavailable, continue locally and report the fallback.
```

## 如何使用

第一次让 Codex 阅读项目并生成指引：

```text
Use $code-project-guidance-map to create the AGENTS.md module guidance map. I explicitly authorize subagents for this run. First decide the macro module boundaries in the main agent, then spawn subagents for bounded module-internal exploration when a subagent tool is available; do not ask again for subagent approval. If subagents are unavailable, continue locally and report the fallback.
```

项目结构有明显变化后刷新指引：

```text
Use $code-project-guidance-map to refresh the module guide based on recent Git changes. I explicitly authorize subagents for this run. First decide the macro module boundaries in the main agent, then spawn subagents for bounded module-internal exploration when a subagent tool is available; do not ask again for subagent approval. If subagents are unavailable, continue locally and report the fallback.
```

做较大功能前，先让 Codex 对齐模块边界：

```text
Use $code-project-guidance-map, then help me identify where this feature should be implemented.
```

v1 需要用户显式调用 skill。它不会承诺在 Codex “刚进入项目的一瞬间”自动弹窗，但生成后的 `AGENTS.md` 会被后续 Codex 线程自动读取，所以实际效果是把第一次阅读项目的成本沉淀下来。

subagents 需要显式授权。上面的推荐 prompt 已经提前授权，所以 Codex 不应该再次停下来询问。主 agent 会先草拟宏观模块地图，然后启动最少必要数量的 subagents，让它们在有边界的路径范围内探索内部结构和证据。subagents 不应该编辑文件，也不应该决定全局模块地图。如果 subagent 工具不可用，主 agent 会在本地完成同样的探索，并在结果里说明 fallback。

## 会产生什么效果

成功运行后，目标项目的 `AGENTS.md` 会出现类似下面的区块：

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

## 开发和验证

修改 skill 或 plugin 后，建议运行：

```powershell
python .agents\skills\code-project-guidance-map\scripts\test_guidance_map.py
python plugins\code-project-guidance-map\skills\code-project-guidance-map\scripts\test_guidance_map.py
python <codex-checkout>\codex-rs\skills\src\assets\samples\skill-creator\scripts\quick_validate.py .agents\skills\code-project-guidance-map
python <codex-checkout>\codex-rs\skills\src\assets\samples\skill-creator\scripts\quick_validate.py plugins\code-project-guidance-map\skills\code-project-guidance-map
python <plugin-creator-skill>\scripts\validate_plugin.py plugins\code-project-guidance-map
```

本机开发时，如果插件已经安装过，改完后重新安装：

```powershell
codex plugin add code-project-guidance-map@code-project-guidance-map
```

然后新开 Codex 线程，让 Codex 重新加载插件。

## 项目主旨

这个项目的目标是让 Codex 从“临时读代码”变成“有项目记忆地协作”。

通过把模块边界、模块职责和放置规则写入 `AGENTS.md`，Codex 后续在同一个项目里工作时，可以更快定位代码、更少猜测模块职责，并更稳定地参与需求实现、重构和代码审查。
