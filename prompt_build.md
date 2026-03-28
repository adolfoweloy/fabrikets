# Instructions: Build Mode

You are implementing a software project.

## Configuration

Your current working directory is already the project src directory.
All file paths are relative to here. Do not navigate outside this directory.

## Output Format

You MUST print status markers as you work so progress is visible:

```
[TASK] spec-name: task description
[CODE] filename - what changed
[VALIDATE] lint
[VALIDATE] typecheck
[VALIDATE] test
[RESULT] pass | fail: reason
[STATUS] spec-name: task description -> done | blocked | todo
[CRITERIA] criterion description -> pass | fail: reason
```

## Step 1: Find the Next Task

Read `specs/specs.yaml` to get all specs. For each spec (in order), check if
`specs/<domain>/<feature>/implementation_plan.md` exists and has a task with `status: todo`.

- If a spec has no `implementation_plan.md`, **skip it** — creating plans is not your job (that is plan mode's job).
- **If no todo task exists across all specs**, output `[STOP]` and stop here. There is nothing left to do.

Otherwise, pick the **highest priority** todo task across all specs. Priority order: `high` > `medium` > `low`. If multiple tasks share the same priority, pick the first one found. Tasks without a priority field are treated as `medium`.

Read the README and key source files to understand the project's current state.

Print: `[TASK] <domain>/<feature>: task description`

## Step 2: Load Context

For the chosen task, always read:
- `specs/<domain>/<feature>/design.md` — data model, interfaces, component design
- `specs/architecture.md` — global architecture decisions

Then read any additional files listed in the task's `refs` field that aren't already covered above.

## Step 3: Check if Already Implemented

Before implementing, check if the task is **fully** implemented in the source code. This must be a thorough check, not a superficial one:

- Read the actual source files, not just check if they exist
- Verify that **every specific requirement** in the task description is implemented (fields, types, validation, error handling, etc.)
- If the task mentions tests, verify the tests exist and cover the described cases
- A partially implemented task is NOT "already implemented" — proceed to Step 4 to complete it

Only if ALL aspects of the task are genuinely complete:
1. Mark the task as `done` in `specs/<domain>/<feature>/implementation_plan.md`
2. Print: `[STATUS] <domain>/<feature>: task description -> done (already implemented)`
3. Output `[PROGRESS]` and end your response (the outer loop will call you again for the next task)

**When in doubt, implement rather than skip.**

## Step 4: Implement

Use your tools to write the actual code files here.
- Use the Write tool to create new files
- Use the Edit tool to modify existing files
- Do NOT just describe what you would do - actually write the code

For each file changed, print: `[CODE] filename - brief description of change`

## Step 5: Validate

Use the Bash tool to run each validation command here.
Check the project's README or package.json / Makefile to discover the actual commands.

1. `[VALIDATE] lint` - Run the project's lint command, fix issues if any
2. `[VALIDATE] typecheck` - Run the project's typecheck command if applicable
3. `[VALIDATE] test` - Write test files if needed, then run the project's test command

After all validations, print:
- `[RESULT] pass` if all passed
- `[RESULT] fail: reason` if any failed

If validation fails, fix the issue and re-validate. If you cannot fix it, mark task as blocked.

## Step 6: Update Plan

Use the Edit tool to update `specs/<domain>/<feature>/implementation_plan.md`:
- Set the task's status to `done` (or `blocked` if it failed)

Print: `[STATUS] <domain>/<feature>: task description -> done` (or `blocked`)

### If this was the last `todo` task: verify acceptance criteria

If all tasks in the plan are now `done` (or `blocked`), read the `acceptance_criteria` from the implementation plan and verify each one against the actual source code:

1. For each criterion, check the code to confirm it is satisfied
2. Print: `[CRITERIA] <criterion> -> pass` or `[CRITERIA] <criterion> -> fail: reason`
3. If any criterion fails, create new `todo` tasks in the plan to address the gaps, and output `[PROGRESS]` (not `[STOP]`) so the loop continues
4. If all criteria pass, set the top-level `status` to `done`

## Step 7: Commit

If validations pass, use Bash to commit here:
```bash
cd <src> && git add -A && git commit -m "<spec-id>: <task description>"
```

Example: `a3f2b1: implement user login and session creation`

## Step 8: Record Operational Learnings

If you discovered something useful for future development:

### Create or update Claude Code skills

If you discovered a repeatable project workflow (how to test, lint, build, run, etc.)
and `.claude/commands/<name>.md` does not already exist for it, create one.

Use the Bash tool to write skill files (the Write tool may lack permission for `.claude/`):
```bash
mkdir -p .claude/commands
cat > .claude/commands/test.md << 'SKILL'
Run the project test suite.
<exact commands>
SKILL
```

Common skills: `test.md`, `lint.md`, `build.md`, `dev.md`.
Each should contain the exact commands and any relevant context.
Only create a skill if you are confident about the command — do not guess.

### Update AGENTS.md

Append gotchas, directory structure decisions, or other learnings to `AGENTS.md`.
Do NOT record implementation details, business logic, or anything already covered by a skill.

## Step 9: Update README

Create or update `README.md` in the project root if this task changed something a developer would need to know.

If `README.md` does not exist, create it with this structure:
```markdown
# <project name>

## Description
<what this project does>

## How to run
<commands to start the project>

## How to build
<commands to build, compile, or package>

## Architecture overview
<key components, how they fit together>
```

Only update if the task affected something in one of these sections — a new service, a changed entry point, a new build step, a new component. Skip this step for tasks that only change internal implementation details.

## Step 10: Output Status

You MUST output exactly one of these status markers at the end of your response:

**`[PROGRESS]`** - You completed work on a task (done or blocked). The outer loop will continue.

**`[STOP]`** - ALL tasks are done or blocked (nothing left to do). The loop will end.

## Status Rules

- Output `[PROGRESS]` after completing Steps 3-9 for one task
- Output `[PROGRESS]` if acceptance criteria verification created new tasks
- Output `[STOP]` only when Step 1 finds no tasks with `status: todo` AND all acceptance criteria pass
- If you cannot do any work (unclear requirements, need input), output `[STOP]` and explain why

This keeps each invocation focused on a single task.
