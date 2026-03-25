# Instructions: Planning Mode

You are creating an implementation plan for a software project. Each invocation processes ONE spec.

## Configuration

Your current working directory is already the project src directory.
All file paths are relative to here. Do not navigate outside this directory.

## Step 1: Load Current State

1. Read `specs/specs.yaml` to see all available specifications
2. Read `specs/architecture.md` — understand global architecture decisions and patterns that apply across all specs

## Step 2: Pick a Spec

Find the first spec from `specs/specs.yaml` that needs planning work:

1. **Not planned yet**: `specs/<domain>/<feature>/implementation_plan.md` does not exist
2. **Incomplete coverage**: The plan exists but the spec files contain requirements that don't have corresponding tasks yet (specs evolve - new features get added)

To determine incomplete coverage:
- Read `specs/<domain>/<feature>/implementation_plan.md`
- Read the spec files thoroughly
- Compare against existing tasks in the plan
- If any requirement in the spec lacks a task, this spec needs work

If ALL specs are fully covered (every requirement has a task), output `[STOP]`.

When in doubt about whether a requirement is already covered by an existing task, assume it is — prefer `[STOP]` over adding potentially redundant tasks.

Print: `[SPEC] <domain>/<feature>`

## Step 3: Study the Spec

For the chosen spec, derive the directory path from its `domain` and `feature` fields in specs.yaml:
`specs/<domain>/<feature>/`

Read the spec files that exist:
- `specs/<domain>/<feature>/overview.md` — start here for purpose and key decisions
- `specs/<domain>/<feature>/requirements.md` — full functional and non-functional requirements
- `specs/<domain>/<feature>/design.md` — data model, interfaces, component design (may not exist yet for bug specs — you will create it in Step 6)

If the spec references other specs, read their `overview.md` for context.

## Step 4: Check Source Code

Study the source code to understand:
- What is already implemented for this spec
- What is missing or incomplete

## Step 5: Update Plan

Write tasks to `specs/<domain>/<feature>/implementation_plan.md` (create if it doesn't exist). Use YAML format:

```yaml
id: <spec id>
overview: <what will be implemented>
status: <overall status>
tasks:
  - task: <comprehensive description>
    refs: [<spec file(s) relevant to this task>]
    priority: <high|medium|low>
    status: <status>
```

### Priority

Assign a priority to each task based on how critical it is to the solution:

| Priority | When to use |
|----------|-------------|
| high | Core functionality that other tasks depend on — data models, key interfaces, foundational logic. Without these, nothing else works. |
| medium | Important features that build on the core — API endpoints, business rules, integrations. |
| low | Nice-to-haves, polish, edge case handling, non-critical validation, documentation. |

Order tasks within the plan by priority (high first, then medium, then low).
Test tasks inherit the priority of the implementation task they correspond to.

### Task Descriptions

Each task description MUST be comprehensive and self-contained. Include:
- What to implement (function, type, endpoint, etc.)
- Key behavior and edge cases to handle
- Input/output expectations
- Any validation or error handling required

Bad: `Create User interface`
Good: `Create User interface with fields: id (UUID, generated on creation), email (string, unique, validated as RFC 5321 address), role (admin|member|viewer), createdAt (ISO 8601 timestamp, set server-side)`

### Tests

For every implementation task, add a corresponding test task immediately after it. The test task should cover:
- Happy path for the main behaviour
- Key edge cases and error conditions from `requirements.md`
- Any boundary conditions or invariants from `design.md`

Example:
```yaml
- task: >
    Create User model with fields: id (UUID), email (string, unique, RFC 5321), ...
  refs: [specs/auth/user_login/design.md]
  priority: high
  status: todo
- task: >
    Test User model: valid creation, duplicate email rejection, invalid email format,
    missing required fields, id uniqueness across multiple creations
  refs: [specs/auth/user_login/requirements.md]
  priority: high
  status: todo
```

### refs field

Each task should list which spec files are relevant to it, so build mode loads only what it needs:
- `specs/<domain>/<feature>/requirements.md` — for tasks implementing a specific requirement
- `specs/<domain>/<feature>/design.md` — for tasks implementing data models, interfaces, or component structure
- `specs/architecture.md` — for tasks that must follow a global architectural pattern

Example:
```yaml
tasks:
  - task: >
      Create User model with fields: id (UUID), email (string, unique, RFC 5321), ...
    refs:
      - specs/auth/user_login/design.md
      - specs/architecture.md
    priority: high
    status: todo
```

Since the plan file lives next to the spec files, you can use relative paths in `refs` (e.g. `design.md`) or full paths from src root (e.g. `specs/auth/user_login/design.md`). Full paths are preferred for clarity.

### Status Values

| Status | Meaning |
|--------|---------|
| todo | Ready to be worked on |
| done | Implementation complete |
| blocked | Cannot proceed |
| cancelled | No longer needed |

## Step 6: Update or Create design.md

Update `specs/<domain>/<feature>/design.md` with any decisions or discoveries made while planning:
- Implementation approach and component ordering
- Patterns or conventions adopted from the existing codebase
- Design decisions that were implicit in the spec but now made explicit
- Missing edge cases or error flows discovered while thinking through tasks

For **bug specs** (`domain: bugs`), `design.md` will not exist yet. Create it with:
- **Root Cause** — what is causing the bug, based on your source code analysis
- **Proposed Fix** — which files, functions, or logic to change and how
- **Test Strategy** — how to verify the fix and prevent regression

Also update other spec files if needed:
- New constraints or edge cases → `requirements.md`
- Updated summary → `overview.md`

Keep specs concise but complete.

Print: `[UPDATED] <domain>/<feature>` if you modified or created a spec file.

## Step 7: Commit

Commit your changes so the next iteration can see the updated state:

```bash
git add specs/
git commit -m "plan: <domain>/<feature> - <brief summary>"
```

## Step 8: Output Status

You MUST output exactly one of these status markers at the end of your response:

**`[PROGRESS]`** - You completed work on a spec. The outer loop will continue.

**`[STOP]`** - ALL specs are fully planned (every requirement has a task). The loop will end.

## Status Rules

- Output `[PROGRESS]` after completing Steps 3-7 for one spec
- Output `[STOP]` only when Step 2 finds no specs needing work
- If you cannot do any work (unclear requirements, need input), output `[STOP]` and explain why

**Important**: A spec being in the plan does NOT mean it's complete. Specs evolve. Always compare the current spec content against existing tasks to find gaps.

This keeps each invocation focused on a single spec.
