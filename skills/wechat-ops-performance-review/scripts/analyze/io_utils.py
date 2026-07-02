from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze.constants import CN_TZ


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=CN_TZ)
    return dt.astimezone(CN_TZ)


def iso_dt(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def latest_publish_export(root: Path) -> Path:
    candidates = sorted((root / "reports" / "wechat").glob("publish-records-*.json"))
    candidates = [p for p in candidates if not p.name.endswith(".summary.json")]
    if not candidates:
        raise FileNotFoundError("No reports/wechat/publish-records-*.json export found")
    return candidates[-1]


def normalize_number(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).replace(",", "").strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def normalize_money(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(str(value).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def text_blob(record: dict[str, Any]) -> str:
    return f"{record.get('title', '')} {record.get('digest', '')}".lower()


def has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def compact_match_key(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[\s\W_]+", "", value.lower())


def is_nonempty_struct(v: Any) -> bool:
    """画像字段"有数据"的统一口径：仅非空 list/dict 算数,字符串/None/标量一律不算。"""
    return isinstance(v, (list, dict)) and len(v) > 0


# 与 fetch/fetch_audience.py 的 available 判定保持同一字段口径
_AUDIENCE_DATA_KEYS = (
    "cumulate_user", "new_user", "cancel_user", "netgain",
    "city", "province", "age", "gender", "user_source",
)


def load_raw_audience(root: Path) -> dict[str, Any]:
    """读取 root/raw/audience.json，不存在或异常返回 {"available": False}。

    读取层不信任文件内嵌的 available 标志（#26）：历史脏 JSON 可能 available=true
    但字段全是 None/垃圾字符串。这里用 is_nonempty_struct 重算，只降不升——
    文件显式 available=false 时保持 False。
    """
    p = root / "raw" / "audience.json"
    if not p.exists():
        return {"available": False}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"available": False}
        d = dict(data)
        has_data = any(is_nonempty_struct(d.get(k)) for k in _AUDIENCE_DATA_KEYS)
        claimed = bool(d.get("available", True))
        d["available"] = claimed and has_data
        return d
    except Exception:
        return {"available": False}


def load_raw_trend(root: Path) -> dict[str, Any]:
    """读取 root/raw/content-trend.json，不存在或异常返回 {"available": False}。"""
    p = root / "raw" / "content-trend.json"
    if not p.exists():
        return {"available": False}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"available": False}
        d = dict(data)
        if "available" not in d:
            d["available"] = True
        return d
    except Exception:
        return {"available": False}


def load_raw_account(root: Path) -> dict[str, Any]:
    """读取 root/raw/account.json（账号名/头像），不存在或异常返回 {}。"""
    p = root / "raw" / "account.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return dict(data) if isinstance(data, dict) else {}
    except Exception:
        return {}
