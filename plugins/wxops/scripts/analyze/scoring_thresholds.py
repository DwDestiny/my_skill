# GEB-L3
# Input: 无运行时入参（纯阈值常量；可选由调用方构造 InteractionThresholds 覆写）
# Output: InteractionThresholds frozen dataclass + DEFAULT_INTERACTION_THRESHOLDS 平台级默认实例
# Pos: plugins/wxops/scripts/analyze/scoring_thresholds.py
"""公众号互动率打分阈值（平台级，issue #74）。

这些是**平台级**经验值：面向微信公众号，不是赛道级。
平台级缺省值在本文件；赛道包可经 niche_loader 校验后二阶覆写部分字段，
由编排层 merge 后以 InteractionThresholds 实例注入 _score_types / m9。

标定依据：2026-08-06 对两个真实账号只读复现（health n=56、maizong n=142），
aggregate_rate ratio-of-means 口径（#59）。样本仅 2 账号 198 篇，属数量级
判断而非精确统计值——字段注释必须按此口径书写，不得写成「经统计」。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace
from typing import Any


@dataclass(frozen=True)
class InteractionThresholds:
    """m9 互动率类判据阈值集合。改数值只动这里，不在打分函数里散落字面量。"""

    # 点赞率高线。旧值 0.04 照搬点赞驱动型平台（小红书/抖音）量级，
    # 在公众号上从未被触发过：2026-08-06 实测两个真实账号 like_rate
    # 分别为 0.0045 / 0.0068（198 篇）。公众号传播主要发生在转发进群与
    # 朋友圈，点赞与在看天然低一到两个数量级。
    # 0.008 取略高于观测上界，语义是"点赞率显著高于同平台常态"。
    # 样本仅 2 账号，属数量级判断而非精确统计值。
    like_high: float = 0.008

    # 评论率高线。旧值 0.008 同样来自点赞/评论驱动平台量级；
    # 实测 health 0.0006、maizong 0.0014，旧阈值从未命中，personal_ip
    # 的 +0.15 评论分支在真实数据上等于死代码。
    # 0.002 取略高于观测上界，语义是"评论率显著高于同平台常态"。
    # 样本仅 2 账号，属数量级判断而非精确统计值。
    comment_high: float = 0.002

    # personal_ip 转发高线。旧值 0.025；实测 maizong 0.0463 可命中、
    # health 0.0079 不命中，量级与公众号转发驱动特性一致，本轮保留。
    # 语义："个人号内容被主动转发传播"的高线。
    # 样本仅 2 账号，属数量级判断而非精确统计值。
    share_high_ip: float = 0.025

    # knowledge_service 转发高线。旧值 0.02；实测两账号可区分
    # （health 0.0079 不达、maizong 0.0463 达），本轮保留。
    # 语义："方法/教程类被转发沉淀"的高线。
    # 样本仅 2 账号，属数量级判断而非精确统计值。
    share_high_ks: float = 0.02

    # 机构号「互动冷清」转发上界。旧值 0.01 宽于真实常态下界，
    # 导致 health（share 0.0079）自动领 brand_org +0.15，冷清被当成机构调性。
    # 0.005 取低于 health 观测（0.0079），使「真实偏低但仍正常」的个人号
    # 不再误领冷清分；只有转发更冷的号才触发。
    # 样本仅 2 账号，属数量级判断而非精确统计值。
    brand_quiet_share: float = 0.005

    # 机构号「互动冷清」评论上界。旧值 0.005 远高于实测（0.0006 / 0.0014），
    # 几乎所有公众号评论率都落在其下，与 share 条件联立后冷清分过宽。
    # 0.0005 取贴近 health 观测下界，语义收紧为"评论近乎静默"。
    # 样本仅 2 账号，属数量级判断而非精确统计值。
    brand_quiet_comment: float = 0.0005

    # 转发主导倍数。旧判据 share >= max(comment, like) 在公众号恒为 True
    # （转发天然压过点赞评论），media_news 白送 +0.10、零区分度。
    # 乘 2.0 后实测 health False（0.0079 < 2×0.0045）、maizong True
    # （0.0463 >= 2×0.0068），恢复区分度。
    # 样本仅 2 账号，属数量级判断而非精确统计值。
    share_dominance_ratio: float = 2.0


DEFAULT_INTERACTION_THRESHOLDS = InteractionThresholds()

# 六个"率"字段：语义是 互动数/阅读数，取值必须落在 (0, 1)
_RATE_FIELDS = frozenset({
    "like_high", "comment_high", "share_high_ip", "share_high_ks",
    "brand_quiet_share", "brand_quiet_comment",
})
# 倍数字段：语义是 share 相对 max(comment, like) 的倍数，必须 >= 1
_RATIO_FIELDS = frozenset({"share_dominance_ratio"})

INTERACTION_THRESHOLD_FIELDS = _RATE_FIELDS | _RATIO_FIELDS

# 模块 import 时守卫：dataclass 字段必须全部归入 rate/ratio，防止加字段忘归类
_dataclass_field_names = frozenset(f.name for f in fields(InteractionThresholds))
if _dataclass_field_names != INTERACTION_THRESHOLD_FIELDS:
    missing = _dataclass_field_names - INTERACTION_THRESHOLD_FIELDS
    extra = INTERACTION_THRESHOLD_FIELDS - _dataclass_field_names
    raise RuntimeError(
        "INTERACTION_THRESHOLD_FIELDS 与 InteractionThresholds 字段不一致："
        f"dataclass 多出 {sorted(missing)!r}，集合多出 {sorted(extra)!r}"
    )
del _dataclass_field_names


def validate_threshold_overrides(raw: Any) -> dict[str, float]:
    """校验赛道包 interaction_thresholds 覆写值；只处理已知键，未知键忽略。

    不合法抛 ValueError（含字段名、实际值、原因）。不依赖 niche_loader。
    """
    if not isinstance(raw, dict):
        raise ValueError(f"interaction_thresholds 必须为对象，得到 {type(raw).__name__}")

    out: dict[str, float] = {}
    for key, value in raw.items():
        if key not in INTERACTION_THRESHOLD_FIELDS:
            continue
        # bool 必须显式挡在数值检查之前：isinstance(True, int) is True
        if isinstance(value, bool):
            raise ValueError(
                f"{key}={value!r} 不合法：布尔值不能作为阈值"
                f"（isinstance(True, int) 陷阱）"
            )
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"{key}={value!r} 不合法：必须为数值，得到 {type(value).__name__}"
            )
        if not math.isfinite(float(value)):
            raise ValueError(f"{key}={value!r} 不合法：不得为 NaN 或 inf")
        v = float(value)
        if key in _RATE_FIELDS:
            if not (0.0 < v < 1.0):
                raise ValueError(
                    f"{key}={value!r} 不合法：率字段必须满足 0 < v < 1"
                )
        elif key in _RATIO_FIELDS:
            # 小于 1 语义荒谬（等于说"转发数少于点赞数也算转发主导"）
            if v < 1.0:
                raise ValueError(
                    f"{key}={value!r} 不合法：倍数字段必须 >= 1"
                )
        out[key] = v
    return out


def merge_thresholds(
    base: InteractionThresholds,
    overrides: dict[str, float],
) -> InteractionThresholds:
    """二阶覆写：未提供的字段保持 base 值，不是整体替换。

    overrides 为空 dict 时，返回实例与 base 相等（frozen dataclass __eq__）。
    """
    if not overrides:
        return replace(base)
    return replace(base, **overrides)
