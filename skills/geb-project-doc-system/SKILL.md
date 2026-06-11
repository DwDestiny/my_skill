---
name: geb-project-doc-system
description: Use when working in medium or large code repositories that need AI-facing project documentation, CLAUDE.md, AGENTS.md, folder guides, file headers, Input/Output/Pos notes, module boundaries, structure-change documentation sync, or context/token reduction.
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

1. Read the project root `AGENTS.md` or `CLAUDE.md` before changing code.
2. Read the nearest folder guide before editing a module.
3. Read target file L3 headers before opening full files.
4. When changing structure, public APIs, dependencies, or module ownership, update L3 first, then L2, then L1 if the project map changed.
5. Run `scripts/audit_geb_docs.py <repo>` before closing the task.

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
python3 skills/geb-project-doc-system/scripts/update_file_headers.py <repo> --json
python3 skills/geb-project-doc-system/scripts/update_file_headers.py <repo> --apply
```

## Red Flags

- Editing code in a large repo without reading root or folder guides.
- Adding a new source file without an L3 header.
- Moving modules without updating L2 folder guides.
- Running a bulk header update without dry-run first.
- Repeated `GEB-L3` blocks in one file.

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
