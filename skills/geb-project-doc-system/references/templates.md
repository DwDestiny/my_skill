# GEB Templates

## Root L1

```md
# Project Agent Guide

## Purpose
- ...

## Architecture Map
- `src/` — ...
- `tests/` — ...

## Commands
- Test: `...`
- Build: `...`

## GEB Documentation Rules
- Read this file before structural work.
- Read the nearest folder guide before editing a module.
- Every source file keeps a short GEB-L3 header.
- Structure changes update L3 -> L2 -> L1.
```

## Folder L2

```md
# Folder Agent Guide

## Purpose
- ...

## Files
- `service.py` — ...

## Boundaries
- Owns ...
- Must not ...

## Local Verification
- `...`
```

## File L3

```py
# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by src/example.py
# Pos: src/example.py
```
