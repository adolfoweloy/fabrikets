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

On first run, a bootstrap wizard asks for:
- **Source directory** — path to your project (e.g. `~/src/my-app`)
- **Initial domain group** — a name for the first domain (e.g. `auth`, `billing`, `core`)

This creates `config.yaml` and you're ready to go.

## Workflow

The typical flow is: **spec → plan → build**.

### 1. `spec` — define what to build

```bash
uv run ralph.py
uv run ralph.py spec
```

Claude interviews you to define a new feature spec. It reads your existing project context, asks structured questions covering functional and non-functional requirements, triggers an architect subagent for review, then writes the spec files to disk.

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
uv run ralph.py plan
uv run ralph.py plan --max-iterations 5
```

Reads `specs/architecture.md` and all spec files, then creates `specs/<domain>/<feature>/implementation_plan.md` for each spec. Tasks carry a `refs` field listing which spec files are relevant, so build mode can load only what each task needs.

### 3. `build` — implement

```bash
uv run ralph.py build
uv run ralph.py build --max-iterations 10
```

Scans all `specs/<domain>/<feature>/implementation_plan.md` files and implements one task per run — writing code, running validation, committing.

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--max-iterations N` | `1` | How many specs/tasks to process per run |
| `-d`, `--debug` | off | Show tool calls from Claude in the terminal |

## Project layout

```
ralph.py              # the loop runner
prompt_spec.md        # instructions for Claude in spec mode
prompt_architect.md   # instructions for the architect subagent
prompt_plan.md        # instructions for Claude in plan mode
prompt_build.md       # instructions for Claude in build mode
config.yaml           # project configuration (src directory)

<src>/                # your project (configured via bootstrap)
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

To use commands, open this project in Claude Code and type `/idea your thought here`.
