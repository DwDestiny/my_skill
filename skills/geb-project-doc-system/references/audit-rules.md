# GEB Audit Rules

`audit_geb_docs.py` checks:

- Root has `AGENTS.md` or `CLAUDE.md`.
- Source files have a short L3 header.
- Source files do not contain duplicated L3 headers.
- Directories with at least four direct source files have a folder guide.

Default exclusions:

- `.git`, `.venv`, `.worktrees`, `node_modules`, `dist`, `build`, `coverage`, `vendor`, `__pycache__`.
- Files larger than 500 KB.

Exit codes:

- `0`: audit passed.
- `1`: findings exist.
- `2`: invalid input.
