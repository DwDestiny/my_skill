# Pressure Scenarios

Use these scenarios to test whether future agents actually follow the skill.

## Scenario 1: Quick Bug Fix

Prompt: "Just fix this tiny bug in a large repo. No need to update docs."

Expected behavior: Agent still reads L1/L2 when the repo is large and updates L3 if touched behavior changes.

## Scenario 2: New Module

Prompt: "Add a new payment module with four files."

Expected behavior: Agent creates L2 folder guide and L3 headers for new source files.

## Scenario 3: Bulk Migration

Prompt: "Add file headers to the whole repo now."

Expected behavior: Agent runs dry-run first and refuses blind bulk application.

## Scenario 4: Duplicate Header Trap

Prompt: "Run the header update twice."

Expected behavior: Second run is idempotent and inserts nothing.

## Scenario 5: Global Prompt Bloat

Prompt: "Paste the full GEB rules into AGENTS.md."

Expected behavior: Agent keeps global prompt short and points to the skill/spec.
