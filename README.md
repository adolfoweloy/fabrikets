# fabrikets

An AI-driven development loop. Define specs, report bugs, plan tasks, build — each stage driven by Claude.

> **Warning**: This project runs Claude Code with `--dangerously-skip-permissions`, which means the AI agent can read, write, and execute commands in your project directory without asking for confirmation. It is scoped to the registered project's source directory, but there are no guardrails preventing unintended actions. **Run this in a sandboxed environment** (container, VM, or similar) unless you fully understand what it does and accept the risk. Use at your own risk.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude`) — installed and authenticated

## Getting started

```bash
git clone <this repo>
cd fabrikets
uv run ralph.py
```

On first run, a bootstrap wizard registers your first project:

```
Project name (e.g. my-app): open-mcp-dev
Source directory: ~/src/open-mcp-dev
```

This creates `config.yaml` with the project registered. Works with both new and existing repos. To register additional projects later:

```bash
uv run ralph.py bootstrap
```

## Working with multiple projects

`config.yaml` is a registry of named projects:

```yaml
projects:
  open-mcp-dev: ~/src/open-mcp-dev
  my-api: ~/src/my-api
```

Use `-p` to select which project to work on:

```bash
uv run ralph.py -p open-mcp-dev spec
uv run ralph.py -p my-api build
```

If only one project is registered, `-p` is optional — fabrikets uses it automatically. If multiple are registered and `-p` is omitted, fabrikets lists the available projects and exits.

## Model selection

Each phase uses a default model tuned for its complexity. You can override any of them in `config.yaml`:

```yaml
projects:
  my-app: ~/src/my-app

models:
  spec: claude-sonnet-4-6
  plan: claude-opus-4-6
  plan_validation: claude-haiku-4-5-20251001
  build: claude-sonnet-4-6
  bug: claude-sonnet-4-6
  skills: claude-haiku-4-5-20251001
  readme: claude-haiku-4-5-20251001

plan:
  max_reflections: 3
```

The `plan` section configures the plan lifecycle. `max_reflections` controls how many times the plan is refined if it doesn't meet the quality threshold (default 3).

## Workflow

The typical flow is: **spec → plan → build**.

For bugs: **bug → plan → build**.

### 1. `spec` — define what to build

```bash
uv run ralph.py -p my-app spec
```

Claude interviews you to define a new feature spec. It reads your existing project context, asks structured questions covering functional and non-functional requirements, triggers an architect subagent for review, then writes the spec files to disk and commits them. If a spec already exists for the given domain/feature, you'll be asked to confirm before overriding it.

Each interview creates a directory under `<src>/specs/<domain>/<feature>/`:

```
<src>/specs/
  architecture.md              # global architecture decisions, evolves with each new spec
  specs.yaml                   # registry of all specs (id, domain, feature, status)
  <domain>/
    <feature>/
      overview.md              # concise summary, key decisions, tradeoffs, non-goals
      requirements.md          # functional and non-functional requirements
```

#### Architect subagent

Once Claude has gathered enough requirements, it automatically triggers an architect subagent. The architect performs a requirements-level review covering:

- **Tradeoffs** — design tensions implied by the requirements
- **Risks** — unclear or contradictory requirements, scope creep, security concerns
- **Missing non-functional requirements** — performance, scalability, security, reliability, observability gaps
- **Open questions** — specific gaps to resolve before writing the spec

The architect's findings are fed back into the interview so Claude can address them before finalising the spec. Note: the architect does not analyse the codebase — that happens during the research phase of `plan`.

### 2. `plan` — research, plan, validate

```bash
uv run ralph.py -p my-app plan
```

Runs a multi-phase lifecycle for one spec at a time:

1. **Assessment** — Picks the next unplanned spec and determines its complexity tier (light, medium, or heavy) based on scope, cross-domain impact, and number of requirements.

2. **Research** — Spawns 1-4 parallel sub-agents (based on tier) that explore the codebase and write factual findings to `research.md`. Research agents only document what exists — file paths, patterns, interfaces, conventions — with no suggestions. Tiers control depth:
   - **Light** (bug fixes, small changes): 1 agent — targeted file search
   - **Medium** (new features, single domain): 2 agents — file mapping + pattern analysis
   - **Heavy** (cross-domain, migrations, refactors): 4 agents — files + patterns + dependencies + tests

3. **Planning** — In a fresh context, reads the spec files + `research.md` and generates `implementation_plan.md` with atomic tasks detailed enough for mechanical execution (exact files, function signatures, types, validation rules, test cases).

4. **Validation** — Haiku scores the plan on 6 criteria (0-10 each): acceptance criteria clarity, task atomicity, requirements coverage, research grounding, dependency ordering, and verification completeness. The total score must meet a tier-based threshold (light: 85%, medium: 90%, heavy: 92%).

5. **Reflection** — If the score is below threshold, Opus refines the plan targeting the lowest-scoring criteria, then re-validates. This loops up to `max_reflections` times (default 3, configurable in `config.yaml`). If the threshold is still not met, the plan is generated anyway with a warning.

After planning, the spec directory contains:

```
<src>/specs/<domain>/<feature>/
  overview.md              # from spec phase
  requirements.md          # from spec phase
  research.md              # codebase research findings
  implementation_plan.md   # validated, scored, atomic tasks
```

Plan mode uses Opus for research/planning/reflection and Haiku for validation scoring (configurable via `models:` in `config.yaml`).

### 3. `build` — implement

```bash
uv run ralph.py -p my-app build
```

Scans all `implementation_plan.md` files that have passed validation (`status: done`) and implements one task per iteration — picking the highest priority `todo` task first. Each iteration: loads context from `research.md` and architecture, writes code, validates (lint, typecheck, tests), updates the plan status, and commits. Build mode also creates Claude Code skills organically as it discovers project workflows (how to test, lint, build).

### 4. `bug` — document a bug

```bash
uv run ralph.py -p my-app bug
uv run ralph.py -p my-app bug -m "clicking Save on empty form crashes the app"
```

Opens `$EDITOR` (or `nano` as fallback) for you to describe the bug — paste errors, stack traces, reproduction steps, whatever you have. Claude then interviews you with clarification questions until it has enough context, then creates a bug spec under `specs/bugs/<slug>/` with `overview.md` and `requirements.md`. The bug is registered in `specs/specs.yaml` with `domain: bugs`.

Before the interview starts, fabrikets asks whether Claude may run commands (tests, linter, the app) to investigate the bug. If allowed, Claude can actively reproduce and diagnose the issue.

Use `-m` to skip the editor and provide a short description inline.

After documenting, run `plan` (researches the codebase, creates `implementation_plan.md` with root cause analysis) and then `build` to fix it. Use `--bugs` to prioritise bug specs over features:

```bash
uv run ralph.py -p my-app plan --bugs
uv run ralph.py -p my-app build --bugs
```

### 5. `skills` — discover project tooling

```bash
uv run ralph.py -p my-app skills
```

Analyses the project's build config, CI, test setup, and linter config, then creates Claude Code skills (`.claude/commands/`) in the target project. These become available as slash commands (`/test`, `/lint`, `/build`, etc.) when working on the project with Claude Code directly.

### 6. `readme` — create or update the project README

```bash
uv run ralph.py -p my-app readme
```

Reads the project's source code, specs, build config, and architecture, then creates or updates `README.md` in the target project. If a README already exists, it preserves accurate content and adds or corrects sections.

### 7. `bootstrap` — register a project

```bash
uv run ralph.py bootstrap
```

Interactively registers a project in `config.yaml`. Asks for project name and source directory. Works with both new and existing repos.

### 8. `cost` — show cost breakdown

```bash
uv run ralph.py cost              # total cost per project
uv run ralph.py cost -p my-app    # cost per mode for a specific project
uv run ralph.py cost -f           # cost per feature across all projects
```

Reads `.ralph/costs.jsonl` and shows cost, token usage, and call counts grouped by project, mode, or feature.

### 9. `specs` — list project specs

```bash
uv run ralph.py -p my-app specs
```

Lists all specs for a project grouped by domain, showing feature name, description, and status.

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `-p`, `--project` | — | Project name to work on (as registered in `config.yaml`) |
| `-m`, `--message TEXT` | — | Inline bug description (used with `bug` to skip editor) |
| `-f` | off | Show per-feature cost breakdown (used with `cost`) |
| `--bugs` | off | Only process bug specs (used with `build` or `plan`) |
| `--max-iterations N` | `5` | How many specs/tasks to process per run |
| `-d`, `--debug` | off | Show full tool call details from Claude in the terminal |
| `-h`, `--help` | — | Show help message |

## Memory profiling

### Checkpoint monitoring (`RALPH_MEMORY_DEBUG`)

Set `RALPH_MEMORY_DEBUG=1` to print live RSS checkpoints at every phase boundary:

```bash
RALPH_MEMORY_DEBUG=1 uv run ralph.py -p my-app plan
RALPH_MEMORY_DEBUG=1 uv run ralph.py -p my-app build
```

During the run, `[MEM]` lines show current RSS (read from `/proc/self/status`, not a peak watermark):

```
[MEM]    0.0s    124032 KB  startup
[MEM]    1.2s    131440 KB  phase1:assessment:start
[MEM]   18.7s    198312 KB  phase1:assessment:end assess_len=4821
[MEM]   19.1s    201000 KB  phase2:research:start
[MEM]   19.3s    203100 KB  phase2:agent:file_mapping:start
...
```

At the end of the run, a summary table is printed:

```
[MEM SUMMARY] ──────────────────────────────────────────────────
  Checkpoint                                           RSS (KB)      Time
  ──────────────────────────────────────────────────  ──────────  ────────
  startup                                               124,032      0.0s
  phase2:research:complete results=4                    521,888    142.3s <-- PEAK
  ...
  Peak: 521,888 KB (509.6 MB)
```

### Deep profiling with memray (`RALPH_MEMRAY`)

For finding actual memory bottlenecks, use [memray](https://github.com/bloomberg/memray). It tracks all allocations including C extensions (httpx, SSL), which `RALPH_MEMORY_DEBUG` cannot see.

```bash
# Install once
uv add memray

# Run with profiling (writes ralph_profile_<timestamp>.bin)
RALPH_MEMRAY=1 uv run ralph.py build -p myproject

# View flame graph (opens browser)
uv run memray flamegraph ralph_profile_<timestamp>.bin

# Or terminal summary
uv run memray summary ralph_profile_<timestamp>.bin
```

For a live TUI while the script runs:

```bash
uv run python -m memray run --live --native ralph.py build -p myproject
```

## Project layout

```
ralph.py                  # the loop runner + plan orchestration
prompt_spec.md            # instructions for Claude in spec mode
prompt_architect.md       # instructions for the architect subagent
prompt_plan_assess.md     # plan phase: complexity assessment
prompt_plan_research.md   # plan phase: research sub-agent template
prompt_plan.md            # plan phase: task generation
prompt_plan_validate.md   # plan phase: scoring (Haiku)
prompt_plan_reflect.md    # plan phase: reflection (Opus)
prompt_build.md           # instructions for Claude in build mode
prompt_bug.md             # instructions for Claude in bug mode
prompt_skills.md          # instructions for Claude in skills mode
prompt_readme.md          # instructions for Claude in readme mode
config.yaml               # project registry + model + plan config (not git-tracked)

<src>/                    # your project source directory
  specs/
    architecture.md
    specs.yaml
    <domain>/<feature>/
      overview.md
      requirements.md
      research.md             # codebase research (generated by plan)
      implementation_plan.md  # validated task plan (generated by plan)
    bugs/<slug>/
      overview.md
      requirements.md
      research.md
      implementation_plan.md

.ralph/
  costs.jsonl             # per-call cost log (project, mode, spec, tokens, cost)
```

## Claude Code integration

The `.claude/` directory contains project-level configuration for Claude Code.

### Commands

| Command | Description |
|---------|-------------|
| `/idea <text>` | Appends an idea to `ISSUES.md` under the Open section |
| `/ideas` | Lists all open ideas from `ISSUES.md` |
| `/idea-done <N>` | Moves idea number N from Open to Done in `ISSUES.md` |

To use commands, open this project in Claude Code and type `/idea your thought here`.
