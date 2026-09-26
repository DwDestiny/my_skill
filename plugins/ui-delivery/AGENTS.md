# plugins/ui-delivery

This directory is the portable UI Delivery plugin recipe, not the maintained Skill source tree. Maintained Skills live under the repository's skills directory.

- `plugin.json`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json` identify the same release and must agree on the package name and version.
- `README.md` is copied into the archive. Keep its internal links relative to the packaged plugin root, beginning at `./skills/ui-delivery/`.
- `scripts/build_ui_delivery_plugin.py` is the package builder. It packages the Skills without editing global settings and refuses an existing output directory.
- Update this L2 when recipe contents or packaging responsibilities change. Do not duplicate maintained Skill content here.
