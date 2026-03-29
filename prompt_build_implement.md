# Instructions: Build — Implement

You are implementing exactly ONE task from a validated implementation plan.

## Configuration

Your current working directory is already the project src directory.
All file paths are relative to here. Do not navigate outside this directory.

## Your job

1. Read `{spec_dir}/build_context.md` — it contains everything you need:
   - The specific task to implement (description, priority, refs)
   - The spec (overview, requirements)
   - Architecture decisions
   - Research findings (exact files, patterns, interfaces, conventions to follow)
   - Plan progress (what's already done, what comes after this)

2. Implement exactly what the task asks. Nothing more, nothing less.
   - Use the Write tool to create new files
   - Use the Edit tool to modify existing files
   - Follow the exact file paths, function signatures, field names, and patterns specified
   - Do NOT run validation commands — that is the next phase's job
   - Do NOT commit

3. After implementing, write `{spec_dir}/build_implementation.md`:

```markdown
## Task
<copy the task description here verbatim>

## Files Changed
- <relative/path/to/file.py> — <what changed and why>
- <relative/path/to/test_file.py> — <what was added/changed>

## Approach
<1-3 sentences explaining key implementation decisions>

## Notes for Validator
<anything the validator should know: test setup needed, env vars, known edge cases, commands to focus on>
```

4. Output `[DONE]` on its own line when finished.
