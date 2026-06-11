# GEB Project Documentation Spec

## L1 Root Guide

Create `AGENTS.md` and/or `CLAUDE.md` at the repository root. It should answer:

- What the project does.
- Where the main modules live.
- Which commands build, test, lint, and run the project.
- Which files, APIs, or workflows must not be changed casually.
- How L2 and L3 docs are maintained.

Keep L1 short enough to read every session. Put deep references in `docs/`.

## L2 Folder Guide

Create a folder guide when a directory is a core module, a high-frequency entry point, or has at least four source files. Use `AGENTS.md` or `CLAUDE.md`.

Each L2 guide should include:

- Module purpose.
- Important files.
- Dependencies in and out.
- Local rules and test commands.
- When this guide must be updated.

## L3 File Header

In large projects, every source file should start with a short header:

```text
GEB-L3
Input: what this file receives or depends on
Output: what this file provides
Pos: where this file sits in the system
```

Keep it short. Do not paste history, architecture essays, or implementation details into L3.

## Update Rule

When code structure changes, update from the leaf upward:

1. L3 file headers for changed files.
2. L2 folder guides for changed module boundaries.
3. L1 root guide if architecture, commands, or project map changed.
