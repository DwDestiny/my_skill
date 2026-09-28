# plugins/ui-delivery

This directory is the complete, independently browsable UI Delivery plugin source. The nine maintained Skills live under this directory's `skills/` folder; root `skills/ui-*` paths are relative compatibility symlinks.

- `plugin.json`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json` identify the same release and must agree on the package name and version.
- `README.md` is copied into the archive. Keep its internal links relative to the packaged plugin root, beginning at `./skills/ui-delivery/`.
- `scripts/build_ui_delivery_plugin.py` is the package builder. It packages this directory's Skills and LICENSE without editing global settings and refuses an existing output directory.
- Update this L2 when plugin contents or packaging responsibilities change. Do not duplicate maintained Skill content elsewhere in the repository.
