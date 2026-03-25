# Instructions: Skills Discovery

You are analysing a project to create Claude Code skills (slash commands) that document
how to work with this project.

## Configuration

Your current working directory is already the project src directory.
All file paths are relative to here. Do not navigate outside this directory.

## Step 1: Explore the Project

Read the project thoroughly to understand its tooling:
- `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md` — any existing docs
- `package.json`, `Makefile`, `Cargo.toml`, `pyproject.toml`, `Gemfile`, etc. — build config
- `.github/workflows/` — CI configuration (reveals test, lint, build commands)
- `docker-compose.yml`, `Dockerfile` — container setup
- Test directories and test files — understand testing patterns and frameworks
- Linter/formatter config (`.eslintrc`, `ruff.toml`, `.prettierrc`, etc.)

## Step 2: Create Skills

Create `.claude/commands/` directory if it doesn't exist, then write skill files.

Each skill is a markdown file at `.claude/commands/<name>.md` containing instructions
that Claude will follow when the user invokes `/<name>`.

### Required skills (create if you can determine how):

**test.md** — How to run the test suite.
```markdown
Run the project test suite.

<exact command(s) to run tests>

If tests fail, show the failure summary and suggest fixes.
```

**lint.md** — How to run linters/formatters.
```markdown
Run the project linters and formatters.

<exact command(s) to run lint and format checks>

If issues are found, fix them automatically where possible.
```

**build.md** — How to build/compile the project.
```markdown
Build the project.

<exact command(s) to build>

If the build fails, diagnose and suggest fixes.
```

### Optional skills (create if relevant):

**dev.md** — How to start the development server or run the app locally.

**add-test.md** — How to write a new test following project conventions.
```markdown
Write a test for the following: $ARGUMENTS

Follow the existing test patterns in <test directory>.
Use <test framework> and match the style of existing tests.
Run the test after writing it to verify it passes.
```

**db.md** — Database migrations, seeding, or reset commands.

**deploy.md** — Deployment steps if discoverable.

Any other skill that would be useful based on what you find in the project.

### Skill file guidelines

- Keep each skill focused on one workflow
- Include the exact commands, not vague descriptions
- Reference specific config files or directories where relevant
- If a command requires environment setup, document it
- Skills should be self-contained — a developer invoking `/<name>` should get a working result

## Step 3: Update AGENTS.md

If `AGENTS.md` exists, check if it contains information that is now covered by skills.
Do not duplicate — if a skill covers it, remove the redundant entry from AGENTS.md.

If `AGENTS.md` does not exist, create it with a brief note about the skills:
```markdown
# Agent Notes

## Skills
Project skills are defined in `.claude/commands/`. Use `/test`, `/lint`, `/build`, etc.
```

## Step 4: Commit

```bash
git add .claude/ AGENTS.md
git commit -m "chore: create Claude Code project skills"
```

## Step 5: Confirm

List all skills you created and what each one does.

Print: `[DONE]`
