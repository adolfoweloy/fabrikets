# Instructions: Plan Task Generation

You are creating an implementation plan for a software project based on spec files and codebase research findings. Each invocation processes ONE spec.

## Configuration

Your current working directory is already the project src directory.
All file paths are relative to here. Do not navigate outside this directory.

## Context

**Spec directory**: {spec_dir}
**Spec ID**: {spec_id}

## Step 1: Load Context

Read these files in order:

1. `specs/architecture.md` — global architecture decisions and patterns
2. `{spec_dir}/overview.md` — purpose, key decisions, non-goals
3. `{spec_dir}/requirements.md` — functional and non-functional requirements
4. `{spec_dir}/research.md` — codebase reality: files, patterns, interfaces, tests

Research.md is critical — it contains verified facts about the codebase. Your plan must be grounded in these findings.

## Step 2: Generate Implementation Plan

Write the plan to `{spec_dir}/implementation_plan.md` using YAML format:

```yaml
id: <spec id>
overview: <what will be implemented>
status: planning
acceptance_criteria:
  - <concrete, verifiable condition>
  - <another condition>
tasks:
  - task: <comprehensive description>
    refs: [<spec file(s) relevant to this task>]
    priority: <high|medium|low>
    status: todo
```

### Acceptance Criteria

Define 3-7 concrete, verifiable conditions that must all be true for the feature to be considered complete. Derive from `requirements.md`. Describe observable end-state behaviour, not implementation steps.

Good criteria are specific and testable:
- "GET /api/users returns a paginated list with limit/offset parameters"
- "Invalid email addresses are rejected with a 422 response and descriptive error message"
- "OAuth token refresh happens automatically before expiry without user interaction"

Bad criteria are vague or just restate tasks:
- "User management works correctly"
- "All tests pass"
- "Code is clean"

### Priority

| Priority | When to use |
|----------|-------------|
| high | Core functionality that other tasks depend on — data models, key interfaces, foundational logic. |
| medium | Important features that build on the core — API endpoints, business rules, integrations. |
| low | Polish, edge case handling, non-critical validation, documentation. |

Order tasks by priority (high first, then medium, then low).

### Task Descriptions — Be Extremely Specific

Each task MUST be detailed enough for mechanical execution. The builder should NOT need to make creative decisions. Include:

- **Exact files** to create or modify (use paths from research.md)
- **Function signatures** with parameter names and types
- **Field names, types, and validation rules** for data models
- **Error messages and status codes** for error handling
- **Specific patterns** to follow (reference patterns identified in research.md)
- **Input/output examples** where applicable

Bad: `Create User interface`
Good: `Create User interface in src/models/user.ts with fields: id (UUID, generated via crypto.randomUUID()), email (string, unique, validated with RFC 5321 regex from src/utils/validation.ts:23), role (enum: 'admin'|'member'|'viewer', default 'member'), createdAt (Date, set to new Date() on creation). Follow the existing Model pattern from src/models/project.ts:5-15.`

### Tests

For every implementation task, add a corresponding test task immediately after it. The test task must specify:
- Concrete test cases (not just "test X works")
- Happy path AND error/edge cases
- Expected inputs and outputs
- The test file path (following the convention from research.md)

Example:
```yaml
- task: >
    Create User model in src/models/user.ts with fields: id (UUID), email (string, unique, RFC 5321), ...
    Follow pattern from src/models/project.ts.
  refs: [specs/auth/user_login/requirements.md]
  priority: high
  status: todo
- task: >
    Test User model in tests/models/user.test.ts:
    1. Valid creation with all fields → returns User object with generated id
    2. Duplicate email → throws DuplicateEmailError
    3. Invalid email "not-an-email" → throws ValidationError with message "Invalid email format"
    4. Missing email field → throws ValidationError with message "Email is required"
    5. Default role is 'member' when not specified
    Use test helpers from tests/helpers.ts (setup/teardown pattern from tests/models/project.test.ts)
  refs: [specs/auth/user_login/requirements.md]
  priority: high
  status: todo
```

### refs field

Each task should list which spec files are relevant, so build mode loads only what it needs. Use full paths from src root:
- `{spec_dir}/requirements.md`
- `{spec_dir}/research.md`
- `specs/architecture.md`

### Status

**Every new task MUST have `status: todo`.** Never create tasks with `status: done`.

## Step 3: Commit

Commit your changes:

```bash
git add specs/
git commit -m "plan: {spec_id} - implementation plan generated"
```

## Step 4: Output

Output `[DONE]` on its own line when finished.

Do NOT output `[PROGRESS]` or `[STOP]` markers. This is a single-shot invocation.
