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
```

## Step 1: Study Requirements

Read `specs/specs.yaml` to get the list of specs. For each relevant spec, read its content at `specs/<id>/spec.md`.
Also read the README and key source files here to understand the project's current state.

## Step 2: Load Implementation Plan

Read `implementation_plan.md` at the root of this repository. The plan uses YAML format with specs and tasks.

## Step 3: Pick a Task

Find the first task with `status: todo` from a spec with `status: todo`.
Print: `[TASK] spec-name: task description`

Before implementing, check if the task is already implemented in the source code. If so:
1. Mark the task as `done` in `implementation_plan.md`
2. Print: `[STATUS] spec-name: task description -> done (already implemented)`
3. Output `[PROGRESS]` and end your response (the outer loop will call you again for the next task)

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

## Step 6: Commit

If validations pass, use Bash to commit here:
```bash
cd <src> && git add -A && git commit -m "<spec-id>: <task description>"
```

Example: `a3f2b1: implement user login and session creation`

## Step 7: Update Plan

Use the Edit tool to update `implementation_plan.md`:
- Set the task's status to `done` (or `blocked` if it failed)
- If all tasks in a spec are done, set the spec's status to `done`

Print: `[STATUS] spec-name: task description -> done` (or `blocked`)

## Step 8: Record Operational Learnings

If you discovered something useful for future development, append to `AGENTS.md`:
- Build/tooling commands
- Common gotchas
- Directory structure decisions

Do NOT record implementation details or business logic.

## Step 9: Output Status

You MUST output exactly one of these status markers at the end of your response:

**`[PROGRESS]`** - You completed work on a task (done or blocked). The outer loop will continue.

**`[STOP]`** - ALL tasks are done or blocked (nothing left to do). The loop will end.

## Status Rules

- Output `[PROGRESS]` after completing Steps 3-8 for one task
- Output `[STOP]` only when Step 3 finds no tasks with `status: todo`
- If you cannot do any work (unclear requirements, need input), output `[STOP]` and explain why

This keeps each invocation focused on a single task.
