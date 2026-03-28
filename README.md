# fabrikets

An AI-driven development loop. Define specs, report bugs, plan tasks, build — each stage driven by Claude.

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
  build: claude-sonnet-4-6
  bug: claude-sonnet-4-6
  skills: claude-haiku-4-5-20251001
  readme: claude-haiku-4-5-20251001
```

The defaults above are written to `config.yaml` on first bootstrap.

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
      _interview.md            # interview transcript (conversation log)
      overview.md              # concise summary, key decisions, non-goals
      requirements.md          # functional and non-functional requirements
      design.md                # data model, interfaces, component design
```

#### Architect subagent

Once Claude has gathered enough requirements, it automatically triggers an architect subagent. The architect analyses the requirements and returns a structured review covering:

- **Tradeoffs** — design tensions implied by the requirements
- **Risks** — unclear requirements, scalability cliffs, security concerns, operational issues
- **Open questions** — specific gaps to resolve before writing the spec

The architect's findings are fed back into the interview so Claude can address them before finalising the spec.

### 2. `plan` — break it into tasks

```bash
uv run ralph.py -p my-app plan
```

Reads `specs/architecture.md` and all spec files, then creates `specs/<domain>/<feature>/implementation_plan.md` for each spec. Each task gets a priority (`high`, `medium`, `low`) based on how critical it is — core/foundational work is high, features building on the core are medium, polish and edge cases are low. Also updates `design.md` with any implementation decisions made during planning. Commits after each spec is planned.

Plan mode uses Opus by default for deeper analysis (configurable via the `models:` section in `config.yaml`).

### 3. `build` — implement

```bash
uv run ralph.py -p my-app build
```

Scans all `implementation_plan.md` files and implements one task per iteration — picking the highest priority `todo` task first. Each iteration: loads context, writes code, validates (lint, typecheck, tests), updates the plan status, and commits. Build mode also creates Claude Code skills organically as it discovers project workflows (how to test, lint, build).

### 4. `bug` — document a bug

```bash
uv run ralph.py -p my-app bug
uv run ralph.py -p my-app bug -m "clicking Save on empty form crashes the app"
```

Opens `$EDITOR` (or `nano` as fallback) for you to describe the bug — paste errors, stack traces, reproduction steps, whatever you have. Claude then interviews you with clarification questions until it has enough context, then creates a bug spec under `specs/bugs/<slug>/` with `overview.md` and `requirements.md`. The bug is registered in `specs/specs.yaml` with `domain: bugs`.

Before the interview starts, fabrikets asks whether Claude may run commands (tests, linter, the app) to investigate the bug. If allowed, Claude can actively reproduce and diagnose the issue.

Use `-m` to skip the editor and provide a short description inline.

After documenting, run `plan` (creates `design.md` with root cause analysis + `implementation_plan.md`) and then `build` to fix it. Use `--bugs` to prioritise bug specs over features:

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

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `-p`, `--project` | — | Project name to work on (as registered in `config.yaml`) |
| `-m`, `--message TEXT` | — | Inline bug description (used with `bug` to skip editor) |
| `--bugs` | off | Only process bug specs (used with `build` or `plan`) |
| `--max-iterations N` | `5` | How many specs/tasks to process per run |
| `-d`, `--debug` | off | Show full tool call details from Claude in the terminal |
| `-h`, `--help` | — | Show help message |

## Project layout

```
ralph.py              # the loop runner
prompt_spec.md        # instructions for Claude in spec mode
prompt_architect.md   # instructions for the architect subagent
prompt_plan.md        # instructions for Claude in plan mode
prompt_build.md       # instructions for Claude in build mode
prompt_bug.md         # instructions for Claude in bug mode
prompt_skills.md      # instructions for Claude in skills mode
prompt_readme.md      # instructions for Claude in readme mode
config.yaml           # project registry + model config (not git-tracked)

<src>/                # your project source directory
  specs/
    architecture.md
    specs.yaml
    <domain>/<feature>/
      _interview.md
      overview.md
      requirements.md
      design.md
      implementation_plan.md
    bugs/<slug>/
      overview.md
      requirements.md

.ralph/
  cost.md             # token usage and cost log per run
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
