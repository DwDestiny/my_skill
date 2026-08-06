# GEB-L3
# Input: by_content_type 题材统计行列表 + account_share_rate（账号级 ratio-of-means 分享率）
# Output: 运营角色列表 [{role, key, stats, reason}, ...]；判据不成立的角色缺席（不返回空 key）
# Pos: plugins/wxops/scripts/analyze/topic_roles.py
"""题材运营角色判定（issue #60）。

从数据特征判定每个题材扮演的运营角色，题材名是变量，不做赛道硬编码断言。
角色判据与认领优先级由真实账号手算验证，禁止擅自改判据/权重/顺序。
"""
from __future__ import annotations

from typing import Any

# 与 analysis_sections 里 by_hour 的 count>=3 口径一致
MIN_TOPIC_SAMPLES = 3

ROLE_ORDER = ("workhorse", "volatile", "reach_entry", "loyalty_base")


def _ratio(avg: float, median: float) -> float:
    if median <= 0:
        return 0.0
    return float(avg) / float(median)


def assign_topic_roles(
    by_content_type: list[dict[str, Any]],
    account_share_rate: float,
) -> list[dict[str, Any]]:
    """从题材统计中判定每个题材扮演的运营角色。

    by_content_type: dataset["analysis"]["by_content_type"]，每行含
        key / count / avg / median / p75 / max / trimmed_mean /
        total_reads / share_rate_avg / comment_rate_avg / top_sample
    account_share_rate: 账号级分享率（ratio-of-means）

    返回 [{"role": str, "key": str, "stats": dict, "reason": str}, ...]
    角色判据不成立时该角色**不出现在返回值里**（不是返回空 key）。
    """
    pool: list[dict[str, Any]] = [
        row
        for row in by_content_type
        if int(row.get("count", 0) or 0) >= MIN_TOPIC_SAMPLES
    ]
    claimed: list[dict[str, Any]] = []

    def _remove(row: dict[str, Any]) -> None:
        nonlocal pool
        pool = [r for r in pool if r is not row and r.get("key") != row.get("key")]

    # 1. workhorse：候选池非空 → count 最大者
    if pool:
        winner = max(pool, key=lambda r: int(r.get("count", 0) or 0))
        cnt = int(winner.get("count", 0) or 0)
        claimed.append(
            {
                "role": "workhorse",
                "key": str(winner.get("key", "")),
                "stats": winner,
                "reason": f"count={cnt} 为候选池最高",
            }
        )
        _remove(winner)

    # 2. volatile：median > 0 且 avg/median >= 2.0 且 max >= 5 * median → ratio 最大者
    volatile_cands: list[tuple[float, dict[str, Any]]] = []
    for row in pool:
        med = float(row.get("median", 0) or 0)
        avg = float(row.get("avg", 0) or 0)
        mx = float(row.get("max", 0) or 0)
        if med > 0 and _ratio(avg, med) >= 2.0 and mx >= 5.0 * med:
            volatile_cands.append((_ratio(avg, med), row))
    if volatile_cands:
        ratio, winner = max(volatile_cands, key=lambda t: t[0])
        mx = int(winner.get("max", 0) or 0)
        claimed.append(
            {
                "role": "volatile",
                "key": str(winner.get("key", "")),
                "stats": winner,
                "reason": f"avg/median = {ratio:.1f}，max {mx} 由单篇爆款拉高",
            }
        )
        _remove(winner)

    # 3. reach_entry：share_rate_avg < account_share_rate → median 最大者
    reach_cands = [
        row
        for row in pool
        if float(row.get("share_rate_avg", 0) or 0) < float(account_share_rate)
    ]
    if reach_cands:
        winner = max(reach_cands, key=lambda r: float(r.get("median", 0) or 0))
        med = float(winner.get("median", 0) or 0)
        share = float(winner.get("share_rate_avg", 0) or 0)
        claimed.append(
            {
                "role": "reach_entry",
                "key": str(winner.get("key", "")),
                "stats": winner,
                "reason": (
                    f"share_rate_avg={share:.4f} < account={float(account_share_rate):.4f}，"
                    f"题材内 median={med} 最高"
                ),
            }
        )
        _remove(winner)

    # 4. loyalty_base：share_rate_avg > account_share_rate → share_rate_avg 最大者
    loyalty_cands = [
        row
        for row in pool
        if float(row.get("share_rate_avg", 0) or 0) > float(account_share_rate)
    ]
    if loyalty_cands:
        winner = max(
            loyalty_cands, key=lambda r: float(r.get("share_rate_avg", 0) or 0)
        )
        share = float(winner.get("share_rate_avg", 0) or 0)
        claimed.append(
            {
                "role": "loyalty_base",
                "key": str(winner.get("key", "")),
                "stats": winner,
                "reason": (
                    f"share_rate_avg={share:.4f} > account={float(account_share_rate):.4f}，"
                    f"分享率题材内最高"
                ),
            }
        )
        _remove(winner)

    return claimed
