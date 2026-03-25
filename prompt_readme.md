# Instructions: README Mode

You are creating or updating the README.md for a software project.

## Configuration

Your current working directory is already the project src directory.
All file paths are relative to here. Do not navigate outside this directory.

## Step 1: Understand the Project

Read the project thoroughly:
- `README.md` — if it exists, read the current version to understand what's already documented
- `specs/specs.yaml` — understand what features and components exist
- `specs/architecture.md` — understand the architecture
- For each spec, read `specs/<domain>/<feature>/overview.md` to understand purpose and scope
- `package.json`, `pyproject.toml`, `Cargo.toml`, `Makefile`, etc. — build and dependency config
- `.claude/commands/` — existing skills (document them if useful)
- `AGENTS.md` — operational notes
- Browse the source code: entry points, key modules, directory structure

## Step 2: Write or Update README.md

If `README.md` does not exist, create it. If it does, update it — preserve any manually written
content that is still accurate, and add or correct sections based on what you found.

The README should include these sections (skip any that don't apply):

```markdown
# <project name>

<One-paragraph description of what this project does and why it exists.>

## Getting started

<How to clone, install dependencies, and run the project for the first time.
Include exact commands. If environment variables or config files are needed, document them.>

## How to run

<Commands to start the application in development mode.>

## How to build

<Commands to build, compile, or package for production.>

## How to test

<Commands to run the test suite. Mention test framework and any setup needed.>

## How to lint

<Commands to run linters and formatters.>

## Architecture overview

<Key components, how they fit together, directory structure explanation.
Keep it high-level — link to specs for details if they exist.>

## API reference

<If the project exposes an API, document key endpoints or interfaces.
Skip this section if not applicable.>

## Configuration

<Environment variables, config files, feature flags.
Skip if not applicable.>

## Contributing

<How to contribute: branch naming, PR process, coding standards.
Skip if not applicable or too early.>
```

### Guidelines

- Be concise — a developer should be able to scan the README in 2 minutes
- Include exact commands, not vague instructions ("run the tests" → `npm test`)
- If something requires setup (database, API keys, etc.), document the steps
- Don't repeat what's in spec files — link to them if needed
- If updating, don't remove sections that contain accurate manual content

## Step 3: Commit

```bash
git add README.md
git commit -m "docs: create README" # or "docs: update README"
```

## Step 4: Confirm

Print a brief summary of what you wrote or changed.

Print: `[DONE]`
