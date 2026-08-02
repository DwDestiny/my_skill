#!/usr/bin/env python3
# GEB-L3
# Input: wxops root + slug/name；盘点根下 config.json/raw/reports/data/output/browser-profile
# Output: copy-first 到 accounts/<slug>/ + 数量/大小/sha256 校验；写 runs/migrate-*.json；成功则注册账号并 set_current；源不动；exit 0/1
# Pos: plugins/wxops/scripts/cli/migrate_cmd.py
"""旧单账号工作区 → accounts/<slug>/ 的 copy-first 迁移。"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from . import accounts_store
from . import env

MIGRATE_ITEMS: list[tuple[str, str]] = [
    ("config.json", "file"),
    ("raw", "dir"),
    ("reports", "dir"),
    ("data", "dir"),
    ("output", "dir"),
    ("browser-profile", "dir"),
]

EXCLUDED_META = [
    {"name": "dashboard", "reason": "构建产物，可再生"},
    {"name": "accounts", "reason": "多账号结构本身，不迁"},
    {"name": "runs", "reason": "运行清单目录，不迁"},
    {"name": "accounts.json", "reason": "注册表，不迁"},
    {"name": ".DS_Store", "reason": "系统垃圾文件"},
]

HASH_LIMIT = 10 * 1024 * 1024  # 10MB


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _stamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _iter_files(path: Path) -> list[Path]:
    """递归列出文件，跳过 .DS_Store。"""
    if path.is_file():
        if path.name == ".DS_Store":
            return []
        return [path]
    if not path.is_dir():
        return []
    files: list[Path] = []
    for p in path.rglob("*"):
        if p.is_file() and p.name != ".DS_Store":
            files.append(p)
    return files


def inventory_item(root: Path, name: str, kind: str) -> dict[str, Any] | None:
    src = root / name
    if kind == "file":
        if not src.is_file():
            return None
        return {
            "name": name,
            "kind": "file",
            "files": 1,
            "bytes": src.stat().st_size,
        }
    if not src.is_dir():
        return None
    files = _iter_files(src)
    total = sum(f.stat().st_size for f in files)
    return {
        "name": name,
        "kind": "dir",
        "files": len(files),
        "bytes": total,
    }


def snapshot_hashes(root: Path, names: list[str]) -> dict[str, str]:
    """相对 root 的文件路径 → sha256。"""
    result: dict[str, str] = {}
    for name in names:
        src = root / name
        for f in _iter_files(src):
            rel = str(f.relative_to(root))
            result[rel] = _sha256_file(f)
    return result


def _verify_copy(
    root: Path,
    target: Path,
    inventory: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    items: list[dict[str, Any]] = []
    file_checks: list[dict[str, Any]] = []

    for inv in inventory:
        name = inv["name"]
        kind = inv["kind"]
        dst_inv = inventory_item(target, name, kind)
        if dst_inv is None:
            errors.append(f"{name}: 目标缺失")
            items.append({"name": name, "ok": False, "reason": "目标缺失"})
            continue
        ok = dst_inv["files"] == inv["files"] and dst_inv["bytes"] == inv["bytes"]
        if not ok:
            errors.append(
                f"{name}: 数量/大小不一致 "
                f"源 files={inv['files']} bytes={inv['bytes']} "
                f"目标 files={dst_inv['files']} bytes={dst_inv['bytes']}"
            )
        items.append(
            {
                "name": name,
                "ok": ok,
                "source": {"files": inv["files"], "bytes": inv["bytes"]},
                "target": {"files": dst_inv["files"], "bytes": dst_inv["bytes"]},
            }
        )

        # 逐文件哈希（≤10MB）
        src_base = root / name
        dst_base = target / name
        for src_f in _iter_files(src_base):
            if kind == "file":
                rel = Path(name)
                dst_f = dst_base
            else:
                rel = src_f.relative_to(src_base)
                dst_f = dst_base / rel
            if not dst_f.exists():
                errors.append(f"{name}/{rel}: 目标文件缺失")
                file_checks.append(
                    {"path": str(rel), "ok": False, "reason": "目标缺失"}
                )
                continue
            src_size = src_f.stat().st_size
            dst_size = dst_f.stat().st_size
            if src_size != dst_size:
                errors.append(f"{name}/{rel}: 大小不一致 {src_size} vs {dst_size}")
                file_checks.append(
                    {
                        "path": str(rel),
                        "ok": False,
                        "method": "size",
                        "reason": "size mismatch",
                    }
                )
                continue
            if src_size > HASH_LIMIT:
                file_checks.append(
                    {
                        "path": str(rel),
                        "ok": True,
                        "method": "size-only",
                        "bytes": src_size,
                    }
                )
            else:
                sh = _sha256_file(src_f)
                dh = _sha256_file(dst_f)
                match = sh == dh
                if not match:
                    errors.append(f"{name}/{rel}: sha256 不一致")
                file_checks.append(
                    {
                        "path": str(rel),
                        "ok": match,
                        "method": "sha256",
                    }
                )

    status = "ok" if not errors else "failed"
    return {"status": status, "items": items, "files": file_checks}, errors


def run(root: Path, slug: str = "default", name: str | None = None) -> int:
    started_at = _now_iso()
    root = root.resolve()

    # 1. 前置检查
    present: list[tuple[str, str]] = []
    for item_name, kind in MIGRATE_ITEMS:
        p = root / item_name
        if kind == "file" and p.is_file():
            present.append((item_name, kind))
        elif kind == "dir" and p.is_dir():
            present.append((item_name, kind))

    if not present:
        env.print_error(
            "未发现旧数据（config.json / raw / reports / data / output / browser-profile 均不存在），无需迁移。"
        )
        return 1

    try:
        accounts_store.validate_slug(slug)
    except ValueError as e:
        env.print_error(str(e))
        return 1

    target = accounts_store.get_account_dir(root, slug)
    if target.exists():
        env.print_error(
            f"目标已存在，为避免覆盖已中止；请换一个 --slug 或先处理该目录：{target.resolve()}"
        )
        return 1

    # 2. 只读盘点
    env.print_header("迁移盘点（只读）")
    inventory: list[dict[str, Any]] = []
    for item_name, kind in present:
        inv = inventory_item(root, item_name, kind)
        if inv:
            inventory.append(inv)
            env.print_info(
                f"{inv['name']:<18} {inv['kind']:<4}  files={inv['files']:<6} bytes={inv['bytes']}"
            )

    # 3. 复制
    env.print_step("复制到账号办公室", str(target))
    env.ensure_account_dirs(target)
    copied: list[str] = []
    copy_errors: list[str] = []
    for item_name, kind in present:
        src = root / item_name
        dst = target / item_name
        try:
            if kind == "file":
                shutil.copy2(src, dst)
            else:
                shutil.copytree(
                    src,
                    dst,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".DS_Store"),
                )
            copied.append(item_name)
        except Exception as e:
            copy_errors.append(f"{item_name}: 复制失败 {e}")

    # 4. 校验
    verify, verify_errors = _verify_copy(root, target, inventory)
    errors = copy_errors + verify_errors
    status = "ok" if not errors else "failed"
    finished_at = _now_iso()

    # 5. 清单落盘
    runs_dir = root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = runs_dir / f"migrate-{_stamp()}.json"
    manifest: dict[str, Any] = {
        "version": 1,
        "started_at": started_at,
        "finished_at": finished_at,
        "root": str(root),
        "slug": slug,
        "target": str(target),
        "status": status,
        "inventory": inventory,
        "copied": copied,
        "verify": verify,
        "excluded": EXCLUDED_META,
        "errors": errors,
    }
    try:
        tmp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, manifest_path)
    except Exception as e:
        env.print_warn(f"清单写入失败：{e}")

    # 6. 失败处理
    if status == "failed":
        env.print_error("迁移校验失败：")
        for err in errors:
            env.print_info(f"- {err}")
        env.print_info(f"清单：{manifest_path}")
        env.print_error(
            "已复制内容保留原地未回滚，源文件一个字节未动。"
            "请检查后手动处理目标目录，勿直接删源。"
        )
        return 1

    # 7. 成功收尾：注册已有目录
    final_name = (name or "").strip() if name else ""
    if not final_name:
        cfg = env.load_config(target)
        final_name = str(cfg.get("account_name") or "").strip()
    if not final_name:
        final_name = slug

    try:
        accounts_store.register_existing_account(
            root, slug, final_name, niche="ai-tools"
        )
    except (ValueError, FileExistsError, FileNotFoundError) as e:
        env.print_error(f"注册账号失败：{e}")
        env.print_info(f"清单：{manifest_path}")
        env.print_error("已复制内容保留原地未回滚，源文件一个字节未动。")
        return 1

    # migrate 场景总是显式 set_current
    try:
        accounts_store.set_current(root, slug)
    except ValueError as e:
        env.print_warn(f"设置当前账号失败：{e}")

    env.print_success("迁移完成")
    env.print_info(f"目标：{target.resolve()}")
    env.print_info("源文件原位保留，一个字节未动；确认无误后可自行归档。")
    env.print_info(f"清单：{manifest_path}")
    env.print_guide_next("wxops desk")
    return 0
