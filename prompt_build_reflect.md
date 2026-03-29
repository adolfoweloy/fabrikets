# Instructions: Build — Reflect and Fix

The implementation scored {score}% against a quality threshold. Your job is to fix the specific issues identified by the reviewer.

This is reflection round {reflection_round} of {max_reflections}.

## Configuration

Your current working directory is the project src directory.

## Your job

1. Read these files:
   - `{spec_dir}/build_context.md` — the original task and all spec context
   - `{spec_dir}/build_implementation.md` — what was implemented
   - `{spec_dir}/build_review.json` — reviewer scores and issues

2. Read the actual source files that need fixing.

3. Prioritise the lowest-scoring criteria. Fix the specific issues listed in each criterion's `issues` array.

   - Do NOT rewrite things that scored 8 or higher — targeted fixes only
   - Focus on the 1-2 criteria with the lowest scores first
   - If `validation_passing` is low, fix the failing tests/lint errors first

4. After fixing, update `{spec_dir}/build_implementation.md`:
   - Add any new or changed files to "Files Changed"
   - Update "Notes for Validator" with what was fixed

5. Append to `{spec_dir}/build_reflection.log` (create if it doesn't exist):

```
## Reflection round {reflection_round}/{max_reflections} (score: {score}%)

### Issues addressed
- <criterion>: <what was fixed>

### Files changed
- <path>: <what changed>
```

6. Output `[DONE]` on its own line when finished.

Do NOT commit — validation will run again after this.
