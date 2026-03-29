# Instructions: Build — Code Review

You are performing a structured code review of a task implementation. Output a JSON score.

## Configuration

Your current working directory is the project src directory.

## Your job

1. Read these files:
   - `{spec_dir}/build_context.md` — task requirements, spec, architecture, research context
   - `{spec_dir}/build_implementation.md` — what was implemented and how
   - `{spec_dir}/build_validation.md` — lint/typecheck/test results

2. Read the actual source files listed in `build_implementation.md` to evaluate real implementation quality.

3. Score each criterion 0–10:

| Criterion | What to evaluate |
|-----------|-----------------|
| **correctness** | Does the code do exactly what the task requires? All specified fields, types, validation rules, and behaviours implemented correctly? |
| **test_coverage** | Are happy path, edge cases, and failure cases tested? Do tests actually verify behaviour (not just run without crashing)? |
| **validation_passing** | Did lint, typecheck, and tests all pass? Base this directly on `build_validation.md`. Overall "pass" → 10. Partial failures → lower. |
| **error_handling** | Are failure modes handled gracefully? Missing inputs, invalid data, external failures — errors surfaced clearly? |
| **code_quality** | Clean, readable, consistent with project conventions from `build_context.md` research? No dead code, no obvious smells. |
| **acceptance_criteria** | Does this task's implementation satisfy the criteria it is responsible for? |

`total_percent = sum(all scores) / 60 * 100`

4. Write the JSON to `{spec_dir}/build_review.json`:

```json
{
  "scores": {
    "correctness":         { "score": 0, "max": 10, "issues": ["describe exactly what to fix"] },
    "test_coverage":       { "score": 0, "max": 10, "issues": [] },
    "validation_passing":  { "score": 0, "max": 10, "issues": [] },
    "error_handling":      { "score": 0, "max": 10, "issues": [] },
    "code_quality":        { "score": 0, "max": 10, "issues": [] },
    "acceptance_criteria": { "score": 0, "max": 10, "issues": [] }
  },
  "total_percent": 0,
  "summary": "one sentence: overall quality and the single most important issue to fix"
}
```

Be honest and specific. Score 8+ means genuinely good. Score 5 means significant work needed.
Issues must describe exactly what to fix — the reflection phase acts on them directly.

Do NOT output `[DONE]` or other text markers.
