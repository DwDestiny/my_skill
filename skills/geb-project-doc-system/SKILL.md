---
name: geb-project-doc-system
description: Use when working in medium or large code repositories that need AI-facing project documentation, first-run inventory, repository onboarding, mixed workspace triage, runtime-safe migration, CLAUDE.md, AGENTS.md, folder guides, file headers, Input/Output/Pos notes, module boundaries, structure-change documentation sync, or context/token reduction.
---

# GEB Project Doc System

## Overview

Use this skill to keep a codebase legible to AI agents through three synchronized layers:

- **L1 root guide**: project purpose, architecture, commands, rules.
- **L2 folder guide**: module boundary, owned files, dependencies, local rules.
- **L3 file header**: short `Input / Output / Pos` coordinate at the top of every source file in large projects.

The core rule: read the smallest useful map first, then open exact files.

Ownership gate comes before documentation work. Only add or update GEB layers in owned projects, owned documentation/knowledge bases, or forks/worktrees that the user explicitly intends to modify. External upstream repositories, third-party source drops, vendored code, and tools the user only uses directly are read-only reference targets: do not add L1/L2/L3 there, do not chase audit zero, and record usage notes in an owned wiki or wrapper document instead.

For multi-agent GEB work, keep judgment and final acceptance in the main Codex agent. Use Codex spark/mini only for simple, low-risk, bounded side tasks such as read-only inventory, candidate file screening, static documentation review, diff summaries, low-risk wiki maintenance, and mechanical verification.

## When To Use

Use for medium or large repositories, long-lived projects, multi-agent coding, repository onboarding, structure changes, module moves, new folders, repeated context loss, or token-heavy exploration.

Do not use for tiny throwaway prototypes unless the user explicitly wants durable project memory.

Do not use it to refactor or document an official upstream repository that the user does not own and will not second-develop. In that case, use the repository as reference only and maintain any local operating notes outside the upstream tree.

## Workflow

If this is the first time using GEB in a repository or local agent workspace, run the First-run Bootstrap before editing docs in bulk.

1. Read the project root `AGENTS.md` or `CLAUDE.md` before changing code.
2. Read the nearest folder guide before editing a module.
3. Read target file L3 headers before opening full files.
4. When changing structure, public APIs, dependencies, or module ownership, update L3 first, then L2, then L1 if the project map changed.
5. Run `scripts/audit_geb_docs.py <repo>` before closing the task.

## Write-side Contract

GEB is a read-and-write documentation system. `documentation is part of the change`; do not only read the map and then leave the map stale.

1. For a `new project`, create or update the L1 root guide before major implementation work. It should state purpose, architecture, commands, ownership, exclusions, and how agents should work in the repository.
2. For a `new or expanded module`, create or update the L2 folder guide before spreading logic across files. It should state the module boundary, owned files, inputs, outputs, dependencies, local rules, and risky paths.
3. For each `new source file`, test file, important config file, or durable script in a governed source tree, add a short L3 header with `Input`, `Output`, and `Pos`.
4. When moving, splitting, renaming, or changing public behavior, update docs in the order L3 -> L2 -> L1.
5. If a path is generated, vendored, runtime state, secret-bearing, upstream-only, or direct-use third-party code, do not add GEB docs there; record usage notes in owned wiki or wrapper docs instead.

## User Onboarding Flow

When the user is installing or rolling out GEB across their machine, guide them through three confirmed stages instead of silently configuring everything.

Use `scripts/onboard_geb_project_doc_system.py` as the productized entrypoint. It performs mechanical discovery and writes only after explicit selection: `no writes without --apply`. The script should list `standard agents only` as configurable agent targets and list `plugin runtimes separately`; semantic review of existing global prompts remains the agent's job, not the script's job.

Stage 1: Agent setup.

1. Detect local standard agent entrypoints and produce a `detected agents` list. Treat plugin or capability runtimes separately; do not count them as standard agents.
2. For each detected agent, show whether the Skill is installed, whether the managed global prompt snippet exists, and whether an existing prompt file needs agent semantic review.
3. Mark mechanical gaps as "needs install" or "needs managed snippet"; mark unreviewed prompt files as "prompt review required".
4. This stage `requires user selection`: ask which agents to configure before writing skill links or global prompts.
5. After selection, install the Skill for those agents and add only a short managed `global prompt snippet` that tells the agent to load this Skill for initialization, audit, migration, or context reduction.

Stage 2: Project selection.

1. Build a `project candidate list` from active, owned repositories and owned documentation/workflow projects.
2. Exclude official upstreams, direct-use third-party repositories, generated assets, runtime state, secrets, sessions, logs, caches, browser profiles, and databases.
3. Group candidates as P0/P1/P2, with reasons and risks.
4. This stage `requires user confirmation`: do not start bulk documentation until the user approves the candidate list.
5. After confirmation, produce a `digitalization plan` with target projects, first safe batch, L1/L2/L3 scope, commands, acceptance checks, and skipped paths.

Stage 3: Acceptance and result.

1. Run the planned audits, dry-runs, local tests, and syntax or build checks that fit each project.
2. Deliver an `acceptance report` listing configured agents, upgraded projects, excluded paths, commands run, failures, and residual risks.
3. Include `estimated token savings` by comparing full-source read size with GEB progressive read size for at least one representative project when practical.
4. If selected projects are Git repositories and the user confirms it, install the GEB `pre-commit hook`.
5. Tell the user that future repository work should follow GEB: read L1 -> L2 -> L3 first, update L3 -> L2 -> L1 after structural changes, and keep owned digital assets documented.

## First-run Bootstrap

Use a first-run inventory before applying GEB to a project family:

1. Classify each target as a project repository, Agent runtime, active session store, or archive/capability index.
2. Classify ownership before any write: owned project, owned documentation, explicit fork/second-development target, direct-use upstream, vendored/reference code, runtime state, or archive.
3. Stop at read-only inventory for direct-use upstream, third-party, vendored, or reference targets; do not write guides or file headers inside those trees.
4. For project repositories, inspect root guides, top folders, tech stack, dirty state, and generated/vendor/cache folders.
5. For a mixed workspace, split content workflow, product subproject, reference code, generated assets, runtime state, and active source code before writing anything.
6. For Agent runtime targets, document the governance map only; do not add L3 headers to sessions, logs, secrets, caches, SQLite databases, or browser profiles.
7. For a trading or runtime-critical repository, create or reference an issue first, freeze live/runtime paths, then start with low-risk research or tool modules.
8. Pick one small sample project or module first, then run `audit_geb_docs.py`.
9. Add or trim L1, add L2 for one module, dry-run L3 headers, review the plan, then apply only that module.

The first-run inventory should produce a short priority list and exclusion list before any bulk write.

First-run Bootstrap deliverables:

- `inventory report`: target classification, root docs, tech stack, dirty state, and audit summary.
- `priority list`: sample target, P0 projects, P0 Agent runtime maps, and P1/P2 follow-ups.
- `exclusion list`: generated, vendor, runtime, secret, cache, log, session, archive, and database paths.
- `verification log`: commands run, commands intentionally skipped, and the reason each skipped command was unsafe.
- `first safe batch`: one low-risk module or governance map that can be migrated before wider rollout.

If the target set is mixed, high-risk, or unclear, stop after inventory and ask for review before applying L2 or L3 changes.

Do not treat audit findings as a to-do list. First explain which findings are source code, generated output, vendored/reference code, product subprojects, runtime state, or intentionally deferred high-risk paths.

## Resource Guide

- Detailed rules: `references/spec.md`
- Copyable templates: `references/templates.md`
- Migration playbook: `references/migration.md`
- Audit policy: `references/audit-rules.md`
- Skill pressure tests: `references/pressure-scenarios.md`
- Deterministic scripts: `scripts/`

## Commands

```bash
python3 skills/geb-project-doc-system/scripts/onboard_geb_project_doc_system.py --json
python3 skills/geb-project-doc-system/scripts/onboard_geb_project_doc_system.py --agents codex,claude --apply
python3 skills/geb-project-doc-system/scripts/onboard_geb_project_doc_system.py --project /path/to/repo --install-hooks --apply
python3 skills/geb-project-doc-system/scripts/audit_geb_docs.py <repo>
python3 skills/geb-project-doc-system/scripts/update_file_headers.py <repo>/safe-module --json
python3 skills/geb-project-doc-system/scripts/update_file_headers.py <repo>/safe-module --apply
```

## Red Flags

- Editing code in a large repo without reading root or folder guides.
- Adding a new source file without an L3 header.
- Moving modules without updating L2 folder guides.
- Running a bulk header update without dry-run first.
- Repeated `GEB-L3` blocks in one file.
- Modifying an official upstream or third-party direct-use repository just because it is large or frequently used.
- Chasing audit zero in a mixed workspace before classifying product subprojects, generated assets, reference code, and runtime state.
- Adding L3 headers to trading, live runner, deploy, credential, gateway, or active session paths before issue-first review.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Putting the whole spec in global prompts | Keep global prompts short; load this skill on demand |
| Writing long file headers | Keep L3 to 3-5 lines |
| Trusting prompt hooks for bulk edits | Use scripts with dry-run and idempotency |
| Migrating an entire monorepo at once | Migrate one module at a time |

## Attribution and License Boundary

This skill is inspired by Zhao Chunxiang's public GEB fractal documentation idea and references the ecosystem around L1/L2/L3 project maps.

It also learned from the open-source shape of `Claudate/project-multilevel-index` and `longranger2/project-doc-bootstrap`, both published under MIT licenses. This repository's first `geb-project-doc-system` implementation is independent: its Skill text and scripts are not copied from those projects. If future changes copy or adapt third-party code, preserve the original copyright notice and license text.
