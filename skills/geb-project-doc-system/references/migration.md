# GEB Migration Playbook

## First-run Inventory

Before the first migration, do a read-only inventory. The goal is to decide what should be initialized, what should only be indexed, and what must be excluded.

Classify each target:

- Project repository: source code, tests, docs, and normal project rules.
- Agent runtime: global rules, skills, plugins, automations, memory, and bridge configuration.
- Active session store: Codex/Claude/Hermes conversations, gateway sessions, browser profiles, and state files.
- Archive or capability index: old sessions, skill libraries, historical workspaces, and inactive agent folders.

Required inventory output:

- Priority: sample project, P0 projects, P0 Agent runtime, P1/P2 follow-ups.
- Existing L1 docs: root `AGENTS.md` / `CLAUDE.md` status.
- Candidate L2 folders: core modules, scripts, tests, runtime folders, product folders.
- Exclusion list: `secrets`, `.env`, `sessions`, `archived_sessions`, `logs`, `cache`, `.cache`, `.pytest_cache`, `.serena`, `.claude/worktrees`, `node_modules`, `venv`, `.venv`, `dist`, `build`, generated site output, browser profiles, SQLite databases, credentials, tokens.
- Dirty-state summary for git repositories.

Do not write anything until this inventory is reviewed.

## Safe Migration Order

1. Choose a small sample project or module.
2. Run a dry-run audit.
3. Add or trim the root L1 guide.
4. Pick one module, not the whole repo.
5. Add the module L2 guide.
6. Add L3 headers with dry-run first, then `--apply`.
7. Re-run audit and project tests.
8. Commit the module batch.

## Agent Runtime Rule

Agent runtime folders are not normal source repositories. Use GEB there to create a governance map, not to annotate every file.

For runtime targets, document:

- Rule entrypoints.
- Installed skills and plugins.
- Automation memory locations.
- Active session stores and archive stores.
- Known secrets/config boundaries.
- Safe maintenance commands.

Never run bulk L3 updates on runtime session stores, credentials, logs, caches, browser profiles, or databases.

## Do Not

- Do not run bulk edits before inspecting dry-run output.
- Do not migrate generated directories.
- Do not migrate Agent runtime directories as if they were normal code repositories.
- Do not add long narrative headers.
- Do not rewrite unrelated code while adding docs.
- Do not treat a prompt hook as the only safety gate.
