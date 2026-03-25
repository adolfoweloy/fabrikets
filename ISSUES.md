# Issues / Ideas

## Open

1. The specs could later be maintained in a local database (e.g. SQLite) instead of files, with a tool to query/manage the specs repository.
2. At some point this should be migrated to or at least support a web UI.
3. There should be an option to list current specs for a project.
4. During the build phase, show progress as "step X of N" so the user knows where they are relative to --max-iterations.
5. Specs should have a priority field (low/medium/high). During the interview phase, the LLM should collect this via a selectable input tool (e.g. AskUserQuestion with predefined options), so the user can pick from low, medium, or high.
6. config.yaml should probably be stored in a ~/.ralph directory.
7. Task dependency tracking in implementation plans: add a `depends_on` field so plan mode can express which tasks must complete before others. This enables parallel build execution in the future — tasks with no unfinished dependencies can run concurrently. Currently priority covers most ordering needs, but explicit dependencies would be needed for spawning multiple Claude processes in parallel.
8. Code-reviewer subagent during build phase: after committing a task, ralph calls a reviewer subagent for a thorough code review. The review output creates a temporary `review.md` file alongside `implementation_plan.md` with high-priority fix tasks. On the next iteration, if `review.md` exists, the LLM works on review tasks first before picking up the next backlog task. After applying review suggestions, it tests, commits, removes `review.md`, and continues to the next task.

## Done

1. Spec phase should dive deeper into functional and non-functional requirements. Also explore a subagent acting as an architect that analyses tradeoffs and risks and feeds findings back to the interviewer.
2. Config management needs rework: currently only supports one project at a time. Need a way to manage and switch between multiple projects.
