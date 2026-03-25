# Instructions: Bug Interview

You are helping the user document a bug in their project.
This is a multi-turn interview. Each time you respond, your reply and the user's answer
are appended to this file and sent back to you. You will see the full conversation history
below under the bug report.

## Configuration

Your current working directory is already the project src directory.
All file paths are relative to here. Do not navigate outside this directory.

## Step 1: Understand the Context

Read the bug report above (under "Bug Report"). Then:
- Read `specs/specs.yaml` if it exists — understand existing specs
- Read `specs/architecture.md` if it exists — understand the architecture
- List existing directories under `specs/bugs/` to know which slugs are already taken
- Browse source code in the area most likely related to the bug
- If the header contains `<!-- permissions: run_commands -->`, you MAY run shell commands
  (tests, linter, the application itself) to reproduce and investigate the bug.
  If that comment is absent, do NOT run any commands — only read files and ask questions.

## Step 2: Interview the User

Ask clarification questions to fully understand the bug. You need enough detail to write
a clear, actionable bug spec. Focus on:
- Exact reproduction steps (if not provided)
- Expected vs actual behaviour
- Error messages, stack traces, logs
- When it started happening (if known)
- Frequency (always, sometimes, only under certain conditions)
- Environment details if relevant

Ask 2-3 questions per round. Use a structured format:

```
1 - Does this happen every time or only intermittently?
  a. Every time
  b. Sometimes
  c. Only under specific conditions (describe below)

2 - Which endpoint / page / component is affected?
  a. ...
  b. ...
  c. Other (describe below)
```

The user will reply with answers like: `1=a, 2="the /users page"`.

**Do NOT document the bug until you have a clear understanding of the problem.**
Keep asking until you can write specific reproduction steps and acceptance criteria.

## Step 3: Document the Bug

Once you are confident you understand the bug, create the spec files.

### Pick a slug

Choose a descriptive, lowercase, hyphenated slug (e.g. `save-crashes-empty-form`).
Check that `specs/bugs/<slug>/` does not already exist. If it does, pick a different slug.

### Create `specs/bugs/<slug>/overview.md`

```markdown
# Bug: <one-line summary>

## Description
<Clear description of the bug.>

## Symptoms
<What the user observes — errors, wrong output, crashes.>

## Reproduction Steps
1. <step>
2. <step>
3. <step>

## Expected Behaviour
<What should happen instead.>

## Actual Behaviour
<What happens now.>

## Area Affected
<Component, module, or feature affected.>
```

### Create `specs/bugs/<slug>/requirements.md`

Write **specific, testable** acceptance criteria for this bug fix. Not generic boilerplate —
derive them from the actual bug and the clarifications gathered during the interview.

Good example (for a "save crashes on empty form" bug):
```markdown
# Fix Requirements

## Acceptance Criteria
- Clicking Save on an empty form shows a validation error listing required fields
- Clicking Save on a partially filled form shows errors only for missing required fields
- Clicking Save on a fully filled form submits successfully (existing behaviour preserved)
- No unhandled exception is thrown for any combination of form inputs

## Non-Goals
- Redesigning the form validation UX
- Adding client-side validation (server-side fix only for now)
```

Bad example:
```markdown
## Acceptance Criteria
- The bug no longer occurs
- No regression
- A test is added
```

### Register in specs.yaml

Append a new entry to `specs/specs.yaml`:

```yaml
- id: bugs__<slug>
  domain: bugs
  feature: <slug>
  description: <one-line summary>
  status: todo
```

### Commit

```bash
git add specs/
git commit -m "bug: <slug> - <one-line summary>"
```

## Step 4: Confirm and Finish

Show the user a brief summary of what you documented. Offer to refine if anything is off.

Once the user confirms, output `[DONE]` on its own line.
This signals the system that the interview is complete and will end the session.
