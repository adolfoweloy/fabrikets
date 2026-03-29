# Instructions: Build — Validate

You are running lint, typecheck, and test checks on code that was just implemented.

## Configuration

Your current working directory is already the project src directory.

## Your job

1. Read these files to understand what was implemented:
   - `{spec_dir}/build_context.md` — the task and its spec context
   - `{spec_dir}/build_implementation.md` — what files were changed and any validator notes

2. Discover the project's validation commands by reading build config:
   - `package.json` → `scripts.lint`, `scripts.typecheck`, `scripts.test`
   - `pyproject.toml` → `[tool.pytest.ini_options]`, `[tool.ruff]`, `[tool.mypy]`
   - `Makefile` → lint, test, typecheck targets
   - `AGENTS.md` or `.claude/commands/*.md` — documented commands

3. Run each validation step using the Bash tool:

   **Lint** — run the project's lint command. If it fails due to auto-fixable issues (formatting, import order), fix them with Edit/Write and re-run. Record the final result.

   **Typecheck** — run the typecheck command if one exists. Fix trivial annotation issues if straightforward.

   **Tests** — run the test suite. Focus on tests covering the changed files. If test files were created as part of this task, run those specifically first.

   If a validation step fails and you cannot fix it, record the failure and move on — do not loop endlessly.

4. Write `{spec_dir}/build_validation.md`:

```markdown
## Lint
status: pass | fail
output: <relevant output, or "clean">

## Typecheck
status: pass | fail | skipped: <reason>
output: <relevant output>

## Tests
status: pass | fail
tests_run: N
tests_failed: N
output: <summary — failures only if any>

## Overall
status: pass | fail
notes: <anything the reviewer should know about validation results>
```

5. Output `[DONE]` on its own line when finished.

Do NOT modify implementation files beyond fixing lint/format issues.
Do NOT commit.
