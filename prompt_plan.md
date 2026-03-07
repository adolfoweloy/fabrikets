# Instructions: Planning Mode

You are creating an implementation plan for a software project. Each invocation processes ONE spec.

## Step 1: Load Current State

1. Read `specs/specs.yaml` to see all available specifications
2. Read `implementation_plan.md` (create if it doesn't exist)

## Step 2: Pick a Spec

Find the first spec from `specs/specs.yaml` that needs planning work:

1. **Not in plan yet**: Spec exists in `specs/` but has no entry in `implementation_plan.md`
2. **Incomplete coverage**: Spec is in the plan, but the spec file contains requirements that don't have corresponding tasks yet (specs evolve - new features get added)

To determine incomplete coverage:
- Read the spec file thoroughly
- Compare against existing tasks in the plan
- If any requirement in the spec lacks a task, this spec needs work

If ALL specs are fully covered (every requirement has a task), output "stop".

Print: `[SPEC] spec-filename.md`

## Step 3: Study the Spec

Read `specs/<id>/spec.md` in detail. Understand:
- What needs to be implemented
- Edge cases and error handling
- Input/output expectations

If the spec references other specs, read those too for context.

## Step 4: Check Source Code

Study the source code at `./src` to understand:
- What is already implemented for this spec
- What is missing or incomplete

## Step 5: Update Plan

Update `implementation_plan.md` with tasks for this spec. Use YAML format:

```yaml
specs:
  - id: <spec id>
    overview: <what will be implemented>
    status: <overall status>
    tasks:
      - task: <comprehensive description>
        status: <status>
```

### Task Descriptions

Each task description MUST be comprehensive and self-contained. Include:
- What to implement (function, type, endpoint, etc.)
- Key behavior and edge cases to handle
- Input/output expectations
- Any validation or error handling required

Bad: `Create User interface`
Good: `Create User interface with fields: id (UUID, generated on creation), email (string, unique, validated as RFC 5321 address), role (admin|member|viewer), createdAt (ISO 8601 timestamp, set server-side)`

### Status Values

| Status | Meaning |
|--------|---------|
| todo | Ready to be worked on |
| done | Implementation complete |
| blocked | Cannot proceed |
| cancelled | No longer needed |

### Example

```yaml
specs:
  - id: a3f2b1
    overview: Implement user authentication and session management
    status: todo
    tasks:
      - task: >
          Create User interface with fields: id (UUID, generated on creation),
          email (string, unique, validated as RFC 5321 address), passwordHash (string),
          role (admin|member|viewer), createdAt (ISO 8601 timestamp, set server-side)
        status: todo
```

## Step 6: Update Specs (if needed)

If you discover missing details that should be in the spec, update `specs/<id>/spec.md`:
- Missing edge cases
- Behavior details not covered
- API conventions we should follow

Keep specs concise but complete.

Print: `[UPDATED] <id>` if you modified a spec.

## Step 7: Commit

Commit your changes so the next iteration can see the updated state:

```bash
git add implementation_plan.md specs/
git commit -m "plan: <spec-filename> - <brief summary>"
```

Example: `plan: storage.md - added tasks for label extraction methods`

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
