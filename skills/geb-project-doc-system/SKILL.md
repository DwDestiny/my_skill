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

## When To Use

Use for medium or large repositories, long-lived projects, multi-agent coding, repository onboarding, structure changes, module moves, new folders, repeated context loss, or token-heavy exploration.

Do not use for tiny throwaway prototypes unless the user explicitly wants durable project memory.

## Workflow

If this is the first time using GEB in a repository or local agent workspace, run the First-run Bootstrap before editing docs in bulk.

1. Read the project root `AGENTS.md` or `CLAUDE.md` before changing code.
2. Read the nearest folder guide before editing a module.
3. Read target file L3 headers before opening full files.
4. When changing structure, public APIs, dependencies, or module ownership, update L3 first, then L2, then L1 if the project map changed.
5. Run `scripts/audit_geb_docs.py <repo>` before closing the task.

## First-run Bootstrap

Use a first-run inventory before applying GEB to a project family:

1. Classify each target as a project repository, Agent runtime, active session store, or archive/capability index.
2. For project repositories, inspect root guides, top folders, tech stack, dirty state, and generated/vendor/cache folders.
3. For a mixed workspace, split content workflow, product subproject, reference code, generated assets, runtime state, and active source code before writing anything.
4. For Agent runtime targets, document the governance map only; do not add L3 headers to sessions, logs, secrets, caches, SQLite databases, or browser profiles.
5. For a trading or runtime-critical repository, create or reference an issue first, freeze live/runtime paths, then start with low-risk research or tool modules.
6. Pick one small sample project or module first, then run `audit_geb_docs.py`.
7. Add or trim L1, add L2 for one module, dry-run L3 headers, review the plan, then apply only that module.

The first-run inventory should produce a short priority list and exclusion list before any bulk write.

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
