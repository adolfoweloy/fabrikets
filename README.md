# fabrikets

An AI-driven development loop. Define specs, plan tasks, build — each stage driven by Claude.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude`) — installed and authenticated

## Getting started

```bash
git clone <this repo>
cd fabrica
uv run ralph.py
```

On first run, a bootstrap wizard registers your first project:

```
Project name (e.g. my-app): open-mcp-dev
Source directory: ~/src/open-mcp-dev
Initial domain group name (e.g. auth, billing, core): auth
```

This creates `config.yaml` with the project registered. To register additional projects later:

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

If only one project is registered, `-p` is optional — ralph uses it automatically. If multiple are registered and `-p` is omitted, ralph lists the available projects and exits.

## Workflow

The typical flow is: **spec → plan → build**.

### 1. `spec` — define what to build

```bash
uv run ralph.py -p my-app
uv run ralph.py -p my-app spec
```

Claude interviews you to define a new feature spec. It reads your existing project context, asks structured questions covering functional and non-functional requirements, triggers an architect subagent for review, then writes the spec files to disk and commits them.

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
uv run ralph.py -p my-app plan --max-iterations 5
```

Reads `specs/architecture.md` and all spec files, then creates `specs/<domain>/<feature>/implementation_plan.md` for each spec. Also updates `design.md` with any implementation decisions made during planning. Commits after each spec is planned.

### 3. `build` — implement

```bash
uv run ralph.py -p my-app build
uv run ralph.py -p my-app build --max-iterations 10
```

Scans all `specs/<domain>/<feature>/implementation_plan.md` files and implements one task per run — writing code, running validation, committing.

### 4. `bug` — document a bug

```bash
uv run ralph.py -p my-app bug
uv run ralph.py -p my-app bug -m "clicking Save on empty form crashes the app"
```

Opens `$EDITOR` (or `nano` as fallback) for you to describe the bug — paste errors, stack traces, reproduction steps, whatever you have. Claude then interviews you with clarification questions until it has enough context, then creates a bug spec under `specs/bugs/<slug>/` with `overview.md` and `requirements.md`. The bug is registered in `specs/specs.yaml` with `domain: bugs`.

Use `-m` to skip the editor and provide a short description inline.

After documenting, run `plan` (creates `design.md` with root cause analysis + `implementation_plan.md`) and then `build` to fix it.

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `-p`, `--project` | — | Project name to work on (as registered in `config.yaml`) |
| `-m`, `--message TEXT` | — | Inline bug description (used with `bug` to skip editor) |
| `--bugs` | off | Only process bug specs (used with `build` or `plan`) |
| `--max-iterations N` | `5` | How many specs/tasks to process per run |
| `-d`, `--debug` | off | Show full tool call details from Claude in the terminal |

## Project layout

```
ralph.py              # the loop runner
prompt_spec.md        # instructions for Claude in spec mode
prompt_architect.md   # instructions for the architect subagent
prompt_plan.md        # instructions for Claude in plan mode
prompt_build.md       # instructions for Claude in build mode
config.yaml           # named project registry

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
