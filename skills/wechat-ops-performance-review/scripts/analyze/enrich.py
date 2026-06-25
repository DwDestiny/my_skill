from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze.classify import (
    classify_content,
    classify_pain,
    classify_persona,
    count_article_chars,
    length_bucket,
    title_structure,
)
from analyze.constants import WEEKDAY_LABELS
from analyze.io_utils import (
    compact_match_key,
    iso_dt,
    normalize_money,
    normalize_number,
    parse_dt,
    read_json,
)
from analyze.stats import rate


def build_article_lookup(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    index = read_json(root / "data/social_ops/indexes/articles.json", {"items": []})
    by_url: dict[str, dict[str, Any]] = {}
    by_title: dict[str, dict[str, Any]] = {}
    for item in index.get("items", []):
        title_key = compact_match_key(item.get("title"))
        if title_key and title_key not in by_title:
            by_title[title_key] = item
        wechat = item.get("platforms", {}).get("wechat", {})
        for value in [
            item.get("url"),
            item.get("public_url"),
            item.get("content_url"),
            wechat.get("public_url"),
        ]:
            if value:
                by_url[str(value).strip()] = item
    return by_url, by_title


def select_article_source(root: Path, article_dir: str) -> Path | None:
    if not article_dir:
        return None
    base = root / article_dir
    if not base.exists():
        return None
    for name in ["article.wechat.source.md", "article.wechat.md", "article.md"]:
        candidate = base / name
        if candidate.exists():
            return candidate
    candidates = [
        p
        for p in sorted(base.glob("*.md"))
        if not re.search(r"(twitter|toutiao|zhihu|digest|metadata|raw|before)", p.name, re.I)
    ]
    return candidates[0] if candidates else None


def enrich_article(article: dict[str, Any], root: Path, by_url: dict[str, dict[str, Any]], by_title: dict[str, dict[str, Any]]) -> None:
    item = by_url.get(article.get("url", "")) or by_title.get(compact_match_key(article.get("title")))
    if item:
        article["article_dir"] = article.get("article_dir") or item.get("article_dir") or ""
        article["article_slug"] = article.get("article_slug") or item.get("article_slug") or ""
        article["content_id"] = article.get("content_id") or item.get("content_id") or article.get("id")

    source = select_article_source(root, article.get("article_dir", ""))
    length = count_article_chars(source.read_text(encoding="utf-8")) if source else 0
    article["title_structure"] = title_structure(article.get("title", ""))
    article["title_primary_pattern"] = article["title_structure"]["primary_pattern"]
    article["title_length_bucket"] = article["title_structure"]["length_bucket"]
    article["article_length_chars"] = length
    article["article_length_source"] = str(source) if source else ""
    article["length_bucket"] = length_bucket(length)
    article["length_status"] = "matched_local_article" if source else "missing_local_article"


def build_article(record: dict[str, Any], captured_at: datetime) -> dict[str, Any]:
    published_at = parse_dt(record.get("published_at"))
    content_type = classify_content(record)
    pain = classify_pain(record, content_type)
    persona = classify_persona(record, content_type, pain)
    reads = normalize_number(record.get("read_num"))
    shares = normalize_number(record.get("share_num"))
    comments = normalize_number(record.get("comment_num"))
    comments_with_replies = normalize_number(record.get("total_comment_count_contains_reply"))
    likes = normalize_number(record.get("like_num"))
    old_likes = normalize_number(record.get("old_like_num"))
    moment_likes = normalize_number(record.get("moment_like_num"))
    is_deleted = bool(record.get("is_deleted"))
    hours_since_publish = None
    is_immature = False
    if published_at:
        hours_since_publish = round((captured_at - published_at).total_seconds() / 3600, 2)
        is_immature = hours_since_publish < 48
    article_key = (
        record.get("content_id")
        or f"wechat_backend/{record.get('appmsgid', '')}-{record.get('itemidx', '')}"
    )
    return {
        "id": article_key,
        "content_id": record.get("content_id") or article_key,
        "article_dir": record.get("article_dir") or "",
        "article_slug": record.get("article_slug") or "",
        "title": record.get("title") or "",
        "digest": record.get("digest") or "",
        "url": record.get("content_url") or "",
        "cover": record.get("cover") or record.get("pic_cdn_url_235_1") or "",
        "published_at": iso_dt(published_at),
        "date": published_at.date().isoformat() if published_at else "",
        "hour": published_at.hour if published_at else None,
        "weekday": published_at.weekday() + 1 if published_at else None,
        "weekday_label": WEEKDAY_LABELS[published_at.weekday()] if published_at else "",
        "iso_week": f"{published_at.isocalendar().year}-W{published_at.isocalendar().week:02d}"
        if published_at
        else "",
        "month": published_at.strftime("%Y-%m") if published_at else "",
        "status": "deleted" if is_deleted else "published",
        "is_deleted": is_deleted,
        "is_immature": is_immature,
        "hours_since_publish": hours_since_publish,
        "reads": reads,
        "likes": likes,
        "old_likes": old_likes,
        "moment_likes": moment_likes,
        "comments": comments,
        "comments_with_replies": comments_with_replies,
        "shares": shares,
        "reprints": normalize_number(record.get("reprint_num")),
        "reward_money": normalize_money(record.get("reward_money")),
        "share_rate": rate(shares, reads),
        "comment_rate": rate(comments, reads),
        "like_rate": rate(likes + old_likes + moment_likes, reads),
        "content_type": content_type,
        "pain_point": pain,
        "persona": persona,
    }
