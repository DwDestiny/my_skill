#!/usr/bin/env python3
# GEB-L3
# Input: wxops root Path + slug/name/niche/station 等；读写 accounts.json 与 accounts/<slug>/{account,pipeline}.json
# Output: 注册表/账号 dict|list、路径与时间格式化；原子写 json；纯逻辑零终端交互
# Pos: plugins/wxops/scripts/cli/accounts_store.py
"""多账号注册表：accounts.json 薄指针 + 各账号 account.json / pipeline.json 单一真源。"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from . import env

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")

_TOUCH_FIELDS = frozenset({"last_login_at", "last_fetch_at", "last_analyze_at"})
_PIPELINE_STATIONS = frozenset({"login", "fetch", "analyze"})

DEFAULT_REGISTRY: dict[str, Any] = {"version": 1, "current": None}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def validate_slug(slug: str) -> str:
    """合法返回原值，非法抛 ValueError（中文说明）。"""
    if not isinstance(slug, str):
        raise ValueError("slug 必须是字符串")
    if (
        not slug
        or "/" in slug
        or "\\" in slug
        or any(c.isspace() for c in slug)
        or slug in (".", "..")
        or not SLUG_RE.match(slug)
    ):
        raise ValueError(
            "slug 不合法：仅允许小写字母/数字/连字符，以字母或数字开头，长度 1–32；"
            "禁止 / \\ 空白 . .. 以及大写/中文等字符。"
            f" 收到：{slug!r}"
        )
    return slug


def get_accounts_dir(root: Path) -> Path:
    return root / "accounts"


def get_account_dir(root: Path, slug: str) -> Path:
    return get_accounts_dir(root) / validate_slug(slug)


def get_registry_path(root: Path) -> Path:
    return root / "accounts.json"


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


# 公共别名：batch 报告等复用，保留私有名不动
atomic_write_json = _atomic_write_json


def load_registry(root: Path) -> dict[str, Any]:
    path = get_registry_path(root)
    if not path.exists():
        return dict(DEFAULT_REGISTRY)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(DEFAULT_REGISTRY)
        return {
            "version": data.get("version", 1),
            "current": data.get("current"),
        }
    except Exception:
        return dict(DEFAULT_REGISTRY)


def save_registry(root: Path, reg: dict[str, Any]) -> None:
    payload = {
        "version": reg.get("version", 1),
        "current": reg.get("current"),
    }
    _atomic_write_json(get_registry_path(root), payload)


def load_account(root: Path, slug: str) -> dict[str, Any] | None:
    try:
        validate_slug(slug)
    except ValueError:
        return None
    path = get_accounts_dir(root) / slug / "account.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def save_account(root: Path, slug: str, data: dict[str, Any]) -> None:
    path = get_account_dir(root, slug) / "account.json"
    _atomic_write_json(path, data)


def list_accounts(root: Path) -> list[dict[str, Any]]:
    base = get_accounts_dir(root)
    if not base.is_dir():
        return []
    result: list[dict[str, Any]] = []
    for child in sorted(base.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        acct_path = child / "account.json"
        if not acct_path.exists():
            continue
        try:
            data = json.loads(acct_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                result.append(data)
        except Exception:
            continue
    result.sort(key=lambda a: str(a.get("slug", "")))
    return result


def get_account(root: Path, slug: str) -> dict[str, Any] | None:
    return load_account(root, slug)


def get_current_slug(root: Path) -> str | None:
    reg = load_registry(root)
    current = reg.get("current")
    if current is None or current == "":
        return None
    return str(current)


def get_current_account(root: Path) -> dict[str, Any] | None:
    slug = get_current_slug(root)
    if not slug:
        return None
    return load_account(root, slug)


def create_account(
    root: Path,
    slug: str,
    name: str,
    niche: str = "ai-tools",
) -> dict[str, Any]:
    validate_slug(slug)
    acct_dir = get_account_dir(root, slug)
    account_json = acct_dir / "account.json"
    if account_json.exists():
        raise FileExistsError(f"账号 {slug} 已存在")
    if acct_dir.exists():
        raise FileExistsError(
            f"目录已存在但不是合法账号，为避免覆盖已中止：{acct_dir.resolve()}"
        )

    env.ensure_account_dirs(acct_dir)
    account: dict[str, Any] = {
        "slug": slug,
        "name": name,
        "niche": niche or "ai-tools",
        "created_at": now_iso(),
        "last_login_at": None,
        "last_fetch_at": None,
        "last_analyze_at": None,
        "status": "active",
    }
    save_account(root, slug, account)
    save_pipeline(root, slug, default_pipeline())

    reg = load_registry(root)
    if reg.get("current") is None:
        set_current(root, slug)

    return account


def register_existing_account(
    root: Path,
    slug: str,
    name: str,
    niche: str = "ai-tools",
) -> dict[str, Any]:
    """目录已存在且无 account.json 时注册：写 account.json + pipeline，首账号自动 current。

    用于 migrate 复制完成后的收尾（create_account 会因目录已存在而拒绝）。
    """
    validate_slug(slug)
    acct_dir = get_account_dir(root, slug)
    if not acct_dir.exists():
        raise FileNotFoundError(f"账号目录不存在：{acct_dir}")
    if (acct_dir / "account.json").exists():
        raise FileExistsError(f"账号 {slug} 已存在")

    env.ensure_account_dirs(acct_dir)
    account: dict[str, Any] = {
        "slug": slug,
        "name": name,
        "niche": niche or "ai-tools",
        "created_at": now_iso(),
        "last_login_at": None,
        "last_fetch_at": None,
        "last_analyze_at": None,
        "status": "active",
    }
    save_account(root, slug, account)
    save_pipeline(root, slug, default_pipeline())

    reg = load_registry(root)
    if reg.get("current") is None:
        set_current(root, slug)

    return account


def set_current(root: Path, slug: str) -> None:
    validate_slug(slug)
    if load_account(root, slug) is None:
        raise ValueError(f"账号不存在：{slug}")
    reg = load_registry(root)
    reg["current"] = slug
    save_registry(root, reg)


def retire_account(root: Path, slug: str) -> dict[str, Any]:
    validate_slug(slug)
    account = load_account(root, slug)
    if account is None:
        raise ValueError(f"账号不存在：{slug}")
    account["status"] = "retired"
    save_account(root, slug, account)

    reg = load_registry(root)
    if reg.get("current") == slug:
        reg["current"] = None
        save_registry(root, reg)

    return account


def touch(
    root: Path,
    slug: str,
    field: str,
    when: str | None = None,
) -> None:
    if field not in _TOUCH_FIELDS:
        return
    account = load_account(root, slug)
    if account is None:
        return
    account[field] = when or now_iso()
    try:
        save_account(root, slug, account)
    except Exception:
        pass


def set_login_health(
    root: Path,
    slug: str,
    alive: bool,
    when: str | None = None,
) -> None:
    """写回 login_alive + last_check_at；账号不存在或写失败静默返回（与 touch 同风格）。"""
    account = load_account(root, slug)
    if account is None:
        return
    account["login_alive"] = bool(alive)
    account["last_check_at"] = when or now_iso()
    try:
        save_account(root, slug, account)
    except Exception:
        pass


def default_pipeline() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": now_iso(),
        "stations": {
            "login": {"at": None, "ok": False},
            "fetch": {"at": None, "ok": False},
            "analyze": {"at": None, "ok": False, "report": None},
        },
    }


def load_pipeline(root: Path, slug: str) -> dict[str, Any]:
    try:
        validate_slug(slug)
    except ValueError:
        return default_pipeline()
    path = get_accounts_dir(root) / slug / "pipeline.json"
    if not path.exists():
        return default_pipeline()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return default_pipeline()
        # 保证骨架字段齐全
        base = default_pipeline()
        stations = data.get("stations") or {}
        merged_stations = base["stations"]
        for key in ("login", "fetch", "analyze"):
            if isinstance(stations.get(key), dict):
                merged_stations[key] = {**merged_stations[key], **stations[key]}
        return {
            "version": data.get("version", 1),
            "updated_at": data.get("updated_at") or base["updated_at"],
            "stations": merged_stations,
        }
    except Exception:
        return default_pipeline()


def save_pipeline(root: Path, slug: str, data: dict[str, Any]) -> bool:
    """原子写 pipeline.json；失败返回 False，不抛致命错误。"""
    try:
        path = get_account_dir(root, slug) / "pipeline.json"
        _atomic_write_json(path, data)
        return True
    except Exception:
        return False


def touch_pipeline(
    root: Path,
    slug: str,
    station: str,
    ok: bool = True,
    report: str | None = None,
) -> bool:
    if station not in _PIPELINE_STATIONS:
        return False
    try:
        pipe = load_pipeline(root, slug)
        ts = now_iso()
        st = pipe.setdefault("stations", {}).setdefault(station, {})
        st["at"] = ts
        st["ok"] = bool(ok)
        if station == "analyze" and report is not None:
            st["report"] = report
        pipe["updated_at"] = ts
        return save_pipeline(root, slug, pipe)
    except Exception:
        return False


def humanize_ts(iso: str | None) -> str:
    """相对中文时间：今天 / 昨天 / N 天前 / 从未。"""
    if not iso:
        return "从未"
    try:
        text = str(iso).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.astimezone()
        else:
            dt = dt.astimezone()
    except Exception:
        return "从未"
    now = datetime.now().astimezone()
    delta = (now.date() - dt.date()).days
    if delta <= 0:
        return "今天"
    if delta == 1:
        return "昨天"
    return f"{delta} 天前"


def display_width(s: str) -> int:
    """东亚宽字符按 2 计宽。"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def pad_display(s: str, width: int) -> str:
    pad = width - display_width(s)
    if pad < 0:
        pad = 0
    return s + (" " * pad)


def has_legacy_layout(root: Path) -> bool:
    """是否检测到旧版单账号布局痕迹。"""
    return (
        (root / "config.json").exists()
        or (root / "raw").exists()
        or (root / "reports").exists()
    )
