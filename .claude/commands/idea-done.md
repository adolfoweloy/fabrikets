Mark an open idea as done by moving it from `## Open` to `## Done` in ISSUES.md.

The argument is the 1-based index of the idea as listed by `/ideas`.

Steps:
1. Read ISSUES.md
2. Collect all numbered items under `## Open` in order
3. Identify the item at position $ARGUMENTS (1-based)
4. Remove it from `## Open` and renumber the remaining items sequentially
5. Append it to `## Done` as the next number in that section
6. Write the updated ISSUES.md
7. Confirm to the user which idea was moved
