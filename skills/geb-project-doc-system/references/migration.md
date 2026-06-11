# GEB Migration Playbook

## Safe Migration Order

1. Run a dry-run audit.
2. Add or trim the root L1 guide.
3. Pick one module, not the whole repo.
4. Add the module L2 guide.
5. Add L3 headers with dry-run first, then `--apply`.
6. Re-run audit and project tests.
7. Commit the module batch.

## Do Not

- Do not run bulk edits before inspecting dry-run output.
- Do not migrate generated directories.
- Do not add long narrative headers.
- Do not rewrite unrelated code while adding docs.
- Do not treat a prompt hook as the only safety gate.
