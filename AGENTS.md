# Instructions for AI agents

Read `documentation/MAP.md` first. It indexes all project documentation and states the rules for keeping it current.

- Understand the current code from `documentation/architecture/current-state.md` and the active phase in `documentation/phases/`.
- Do not start a phase's code before its design file in `documentation/phases/` is agreed.
- Every change that alters behaviour, structure or a decision must update the matching documentation files and `documentation/MAP.md` in the same commit or pull request.
- Record significant decisions as ADRs in `documentation/decisions/` using `_template.md`.

## Implementation workflow

The project owner wants to understand every change, not just receive code.

- Work one commit at a time, following the commit plan in the active phase file.
- Before each commit: explain in plain English what you will do and why.
- After each commit: explain what changed, module by module.
- Then stop and wait for the owner's go before the next commit.
- Update the commit plan's Status column as commits land.
