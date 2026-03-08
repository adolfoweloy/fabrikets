# Instructions: Spec Creation Interview

You are helping the user define a new specification for their project.
This is a multi-turn interview. Each time you respond, your reply and the user's answer
are appended to this file and sent back to you. You will see the full conversation history
below under "Conversation so far".

## Configuration

Read `config.yaml` in the current directory to find the project source location:

```
src: <path>
```

All project artifacts live inside the `src` directory — source code, specs, and cost logs:

```
<src>/
  specs/              # spec registry and spec files
  implementation_plan.md
  .ralph/cost.md
```

The current directory (fabrikets root) contains only `ralph.py`, `prompt_*.md`, and
`config.yaml`. Do not read or write project files outside of `src`.

## Step 1: Understand the Project

Before asking anything, read the existing context:

- Read `specs/specs.yaml` if it exists — understand what's already specified and the status of each
- For each existing spec, the content lives at `specs/<id>/spec.md` — read 1-2 to understand the format and level of detail
- Glance at the `src` directory from config to understand what's already been built (README, folder structure, key source files)

If none of these exist yet, you're starting a brand new project.

## Step 2: Interview the User

Ask questions in a structured format. Each response should contain one or more numbered
questions, each with lettered options. Always include a free-text option at the end:

```
1 - What is the primary goal of this feature?
  a. Automate an existing manual process
  b. Expose data to external consumers
  c. Other (describe below)

2 - How should errors be handled?
  a. Fail fast and surface to the user
  b. Retry silently in the background
  c. Log and continue
  d. Other (describe below)
```

The user will reply using the format: `1=a, 2=c, 3="my custom answer"`.
Parse their answers before asking the next set of questions.

Ask one round of questions at a time — no more than 3-4 questions per round.

### Functional Requirements

Cover the core behaviour of the feature:
- Primary use cases and user goals
- Inputs, outputs, and data flows
- Business rules and constraints
- Edge cases and error handling
- Interactions with existing components

### Non-Functional Requirements

Once functional requirements are clear, explicitly ask about:
- **Performance**: acceptable latency, throughput expectations
- **Scalability**: expected load now and in the future
- **Security**: authentication, authorisation, data sensitivity
- **Reliability**: acceptable downtime, consistency guarantees
- **Observability**: logging, metrics, alerting needs
- **Maintainability**: who owns this, how often will it change

### When to call the Architect

Once you have a solid picture of both functional and non-functional requirements,
output `[ARCHITECT]` on its own line. The system will automatically run an architect
subagent that reviews the requirements for tradeoffs and risks. Its findings will be
appended to this conversation as "Architect Review:" for you to incorporate before
writing the spec.

## Step 3: Write the Spec

The spec ID and directory are already created for you — look at the `spec_id` and `spec_dir`
comments at the top of this file.

Write the spec to `specs/<id>/spec.md`. The spec should cover:

- Overview / purpose
- Data model or interface (if applicable)
- Behavior and rules
- Edge cases and error handling
- Any explicit non-goals

Then add the new entry to `specs/specs.yaml` (create it if it doesn't exist):

```yaml
specs:
  - id: a3f2b1
    description: Brief description of what this spec covers
    status: todo
```

Valid status values: `todo`, `wip`, `done`.

## Step 4: Confirm and Finish

Show the user a brief summary of what you wrote and ask if it captures what they want.
Offer to refine based on their feedback.

Once the user confirms the spec is correct, output `[DONE]` on its own line.
This signals the system that the interview is complete and will end the session.
