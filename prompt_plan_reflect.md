# Instructions: Plan Reflection

You are refining an implementation plan that did not meet quality thresholds. Your job is to address the specific issues identified by validation scoring and improve the plan.

## Configuration

Your current working directory is already the project src directory.
All file paths are relative to here. Do not navigate outside this directory.

## Context

**Spec directory**: {spec_dir}
**Reflection round**: {reflection_round} of {max_reflections}

## Validation Scores

{validation_scores}

## Current Plan

The current implementation plan is at `{spec_dir}/implementation_plan.md`.
The research findings are at `{spec_dir}/research.md`.
The spec files are at `{spec_dir}/overview.md` and `{spec_dir}/requirements.md`.

Read all of these files before making changes.

## Your Task

1. Read the current implementation plan, research.md, and spec files
2. Focus on the **lowest-scoring criteria** and their specific issues
3. Rewrite `{spec_dir}/implementation_plan.md` to address the issues

## Improvement Guidelines

### For low acceptance_criteria_clarity:
- Make each criterion a specific, verifiable statement
- Include expected values, status codes, or observable behaviours
- Remove vague criteria like "works correctly" or "handles errors properly"

### For low task_atomicity_completeness:
- Break large tasks into smaller, self-contained units
- Add specific file paths, function names, field names, types, validation rules
- Include exact error messages, status codes, response formats
- Each task should be executable without creative decisions

### For low requirements_coverage:
- Cross-reference every requirement in requirements.md with plan tasks
- Add tasks for missing non-functional requirements (performance, security, etc.)
- Add test tasks for uncovered edge cases

### For low research_grounding:
- Re-read research.md and update task file paths and interface references
- Use actual function signatures and types from research findings
- Remove assumptions — if research doesn't confirm it, verify by reading the code

### For low dependency_ordering:
- Move foundational tasks (data models, core types, shared utilities) to high priority
- Ensure no task references components created by a later task
- Group related tasks logically

### For low verification_completeness:
- Add a test task after every implementation task that lacks one
- Make test descriptions specific: list test cases, inputs, expected outputs
- Include both happy path and error/edge case tests

## Output

After updating the implementation plan file, output `[DONE]` on its own line.

Do NOT change the plan's top-level `status` field — leave it as-is. The orchestration system manages status transitions.
