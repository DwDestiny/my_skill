#!/usr/bin/env python3
"""GEB-L3
Input: the nine maintained skills inside plugins/ui-delivery and its plugin recipe.
Output: a portable, deterministic plugin directory and ZIP with file hashes.
Pos: UI delivery distribution builder; never installs or changes global settings.
"""
import argparse
import hashlib
import json
import posixpath
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import zipfile

SKILLS = (
    "ui-delivery", "ui-product-planning", "ui-ux-architecture",
    "ui-visual-direction", "ui-design-system", "ui-high-fidelity",
    "ui-motion-design", "ui-frontend-implementation", "ui-visual-qa",
)
SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".txt", ".svg",
            ".png", ".jpg", ".webp", ".html", ".css", ".js", ".ts", ".tsx"}
SKIP_DIRS = {"__pycache__", ".pytest_cache"}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def check_source_path(path, boundary):
    cursor = boundary
    for part in path.relative_to(boundary).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"symlink is not distributable: {cursor}")


def checked_file(path, boundary=None):
    if boundary is not None:
        check_source_path(path, boundary)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"not a regular source file: {path}")
    return path.read_bytes()


def check_links(files):
    """Check local Markdown destinations against the packaged files, not checkout."""
    for name, data in files.items():
        if not name.endswith(".md"):
            continue
        for raw in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", data.decode("utf-8")):
            link = raw.strip().strip("<>")
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parsed.path)))
            if target.startswith(("/", "../")) or target == "..":
                raise ValueError(f"link escapes plugin: {name} -> {link}")
            if target not in files and not any(path.startswith(target.rstrip("/") + "/") for path in files):
                raise ValueError(f"missing packaged link: {name} -> {link}")


def build(source, output):
    """Validate all inputs first. Refuse to reuse output rather than deleting it."""
    source, output = Path(source).resolve(), Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"output already exists; choose a new directory: {output}")
    recipe = source / "plugins/ui-delivery"
    manifest = json.loads(checked_file(recipe / ".codex-plugin/plugin.json", source))
    version = manifest.get("version", "")
    if manifest.get("name") != "ui-delivery" or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("recipe must identify ui-delivery and a release version")
    if manifest.get("skills") != "./skills/":
        raise ValueError("recipe skills path must be ./skills/")
    files = {".codex-plugin/plugin.json": encoded(manifest),
             "LICENSE": checked_file(recipe / "LICENSE", source),
             "README.md": checked_file(recipe / "README.md", source)}
    for optional in ("plugin.json", ".claude-plugin/plugin.json"):
        if (recipe / optional).exists():
            data = checked_file(recipe / optional, source)
            identity = json.loads(data)
            if any(identity.get(key) != manifest[key] for key in ("name", "version")):
                raise ValueError(f"manifest identity mismatch: {optional}")
            files[optional] = data
    for name in SKILLS:
        folder = recipe / "skills" / name
        check_source_path(folder, source)
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError(f"missing regular skill folder: {name}")
        for required in ("SKILL.md", "agents/openai.yaml"):
            if not (folder / required).is_file():
                raise ValueError(f"missing skill resource: {name}/{required}")
        for path in sorted(folder.rglob("*")):
            rel = path.relative_to(folder)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if path.is_symlink():
                raise ValueError(f"symlink is not distributable: {path}")
            if path.is_dir():
                continue
            if path.name.startswith(".") or path.suffix.lower() not in SUFFIXES:
                raise ValueError(f"unexpected source file; inspect before packaging: {path}")
            files[f"skills/{name}/{rel.as_posix()}"] = checked_file(path, source)
    check_links(files)
    files["package-lock.json"] = encoded({
        "name": "ui-delivery", "version": version, "skills": list(SKILLS),
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
        "scope": "Distribution integrity only; not a UI quality verdict.",
    })
    output.mkdir(parents=True, exist_ok=False)
    plugin = output / "ui-delivery"
    for name, data in files.items():
        target = plugin / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    archive_path = output / f"ui-delivery-{version}.zip"
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(f"ui-delivery/{name}", date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            entry.create_system = 3
            archive.writestr(entry, data)
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    (output / "SHA256SUMS").write_text(f"{digest}  {archive_path.name}\n")
    return archive_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True, help="new output directory; never overwritten")
    args = parser.parse_args()
    try:
        result = build(args.source, args.output)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"package error: {exc}\n")
    print(result)


if __name__ == "__main__":
    main()
