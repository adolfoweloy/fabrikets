# Instructions: Plan Validation

You are scoring an implementation plan against quality criteria. Your job is to evaluate the plan objectively and return a structured JSON score.

## Inputs

**Spec overview**:
{overview}

**Spec requirements**:
{requirements}

**Research findings**:
{research}

**Implementation plan**:
{plan}

## Scoring Criteria

Score each criterion from 0 to 10:

### 1. Acceptance Criteria Clarity (acceptance_criteria_clarity)
- Are the acceptance criteria specific and unambiguous?
- Can each criterion be verified mechanically (by reading code or running a command)?
- Do they describe observable end-state behaviour, not implementation steps?
- **10**: Every criterion is a concrete, testable statement with clear pass/fail conditions
- **5**: Criteria exist but some are vague or hard to verify
- **0**: No criteria, or all criteria are vague platitudes

### 2. Task Atomicity & Completeness (task_atomicity_completeness)
- Is each task self-contained with specific files, changes, and implementation details?
- Could a developer execute each task without making creative decisions?
- Are tasks small enough to be completed in one focused session?
- Do task descriptions include field names, types, validation rules, error messages?
- **10**: Every task reads like a precise work order with exact specifications
- **5**: Tasks describe what to build but leave implementation details to the builder
- **0**: Tasks are vague feature descriptions with no actionable detail

### 3. Requirements Coverage (requirements_coverage)
- Does every functional requirement have at least one corresponding task?
- Are non-functional requirements (performance, security, observability) addressed?
- Are edge cases from requirements.md covered in task descriptions or test tasks?
- **10**: Complete traceability from every requirement to tasks
- **5**: Core requirements covered, but non-functional or edge cases missing
- **0**: Many requirements have no corresponding tasks

### 4. Research Grounding (research_grounding)
- Do tasks reference actual files, functions, and interfaces found in research.md?
- Are coding patterns from research reflected in task descriptions?
- Do file paths and interface names in tasks match what exists in the codebase?
- **10**: Every task builds on verified codebase facts from research
- **5**: Some tasks reference research, others make assumptions
- **0**: Tasks ignore research findings entirely

### 5. Dependency Ordering (dependency_ordering)
- Are foundational tasks (data models, core interfaces) ordered before dependent tasks?
- Is the priority assignment (high/medium/low) logical?
- Are there circular dependencies or tasks that reference not-yet-created components?
- **10**: Clear, logical ordering with no dependency violations
- **5**: Generally correct but some tasks could be reordered
- **0**: Tasks are randomly ordered with dependency violations

### 6. Verification Completeness (verification_completeness)
- Does every implementation task have a corresponding test task?
- Do test tasks specify concrete test cases (not just "test X works")?
- Are verification approaches realistic (can actually be run)?
- **10**: Every task pair has specific, runnable verification
- **5**: Test tasks exist but are vague about what to test
- **0**: No test tasks or verification steps

## Output

Output ONLY a valid JSON block wrapped in a markdown code block. No other text before or after:

```json
{
  "scores": {
    "acceptance_criteria_clarity": {"score": 0, "max": 10, "issues": []},
    "task_atomicity_completeness": {"score": 0, "max": 10, "issues": []},
    "requirements_coverage": {"score": 0, "max": 10, "issues": []},
    "research_grounding": {"score": 0, "max": 10, "issues": []},
    "dependency_ordering": {"score": 0, "max": 10, "issues": []},
    "verification_completeness": {"score": 0, "max": 10, "issues": []}
  },
  "total_percent": 0,
  "passed": false,
  "summary": "One sentence summary of the plan's main strengths and weaknesses"
}
```

Rules:
- `total_percent` = sum of all scores / 60 * 100, rounded to nearest integer
- `issues` should be specific and actionable (e.g., "Task 3 references src/auth/handler.go but research shows the file is src/auth/handlers.go")
- `passed` is NOT for you to decide — set it to `false` always. The calling system will determine pass/fail based on tier thresholds.
- Be honest and precise. Do not inflate scores.
