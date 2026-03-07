# Instructions: Spec Creation Interview

You are helping the user define a new specification for their project.
This is a multi-turn interview. Each time you respond, your reply and the user's answer
are appended to this file and sent back to you. You will see the full conversation history
below under "Conversation so far".

## Step 1: Understand the Project

Before asking anything, read the existing context:

- Read `specs/specs.yaml` if it exists — understand what's already specified and the status of each
- For each existing spec, the content lives at `specs/<id>/spec.md` — read 1-2 to understand the format and level of detail
- Glance at `src/` to understand what's already been built

If none of these exist yet, you're starting a brand new project.

## Step 2: Interview the User

Ask the user what they want to add or build. Keep it conversational — one or two focused
questions at a time. Explore:

- What is the goal of this feature or component?
- What are the inputs and outputs?
- What edge cases or constraints matter?
- How does it relate to what already exists?

Dig deeper where needed. Stop asking when you have enough to write a solid spec.

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
