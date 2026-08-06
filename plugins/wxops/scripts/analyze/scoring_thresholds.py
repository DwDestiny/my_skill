# GEB-L3
# Input: 无运行时入参（纯阈值常量；可选由调用方构造 InteractionThresholds 覆写）
# Output: InteractionThresholds frozen dataclass + DEFAULT_INTERACTION_THRESHOLDS 平台级默认实例
# Pos: plugins/wxops/scripts/analyze/scoring_thresholds.py
"""公众号互动率打分阈值（平台级，issue #74）。

这些是**平台级**经验值：面向微信公众号，不是赛道级。
当前所有赛道共享同一组默认值；赛道包覆写由后续 PR 接入（niche 可传
InteractionThresholds 实例进 _score_types）。

标定依据：2026-08-06 对两个真实账号只读复现（health n=56、maizong n=142），
aggregate_rate ratio-of-means 口径（#59）。样本仅 2 账号 198 篇，属数量级
判断而非精确统计值——字段注释必须按此口径书写，不得写成「经统计」。
"""
from __future__ import annotations

from dataclasses import dataclass


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
