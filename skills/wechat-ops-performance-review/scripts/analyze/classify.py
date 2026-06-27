from __future__ import annotations

import re
from typing import Any

from analyze.io_utils import has_any, text_blob


def classify_content(record: dict[str, Any]) -> str:
    text = text_blob(record)
    title = str(record.get("title", "")).lower()

    risk_terms = [
        "封号",
        "废掉",
        "认证",
        "kyc",
        "验证",
        "卡",
        "收紧",
        "缩水",
        "不够用",
        "掉",
        "停用",
        "叫停",
        "限制",
        "翻车",
        "跳票",
        "失望",
        "调查",
        "风险",
        "危机",
        "白名单",
        "auth",
        "401",
    ]
    price_terms = [
        "免费",
        "额度",
        "价格",
        "低价",
        "便宜",
        "省钱",
        "羊毛",
        "优惠",
        "订阅",
        "会员",
        "pro",
        "plus",
        "美金",
        "元",
        "套餐",
        "充值",
        "开源第一",
        "彻底免费",
    ]
    agent_terms = [
        "codex",
        "claude code",
        "agent",
        "mcp",
        "skill",
        "插件",
        "工作流",
        "github",
        "开源",
        "代码",
        "编程",
        "工程师",
        "cursor",
        "opencode",
        "codegraph",
        "项目",
        "ide",
        "cli",
    ]
    model_terms = [
        "glm",
        "gpt",
        "claude",
        "deepseek",
        "kimi",
        "minimax",
        "qwen",
        "fable",
        "模型",
        "benchmark",
        "跑分",
        "性能",
        "发布",
        "能力",
        "anthropic",
        "openai",
    ]
    business_terms = [
        "产品",
        "副业",
        "商业化",
        "闲鱼",
        "变现",
        "收入",
        "增长",
        "pm",
        "独立开发",
        "创业",
    ]

    if has_any(text, risk_terms):
        return "风险/账号/额度焦虑"
    if has_any(text, price_terms):
        return "价格/额度/羊毛情报"
    if has_any(text, agent_terms):
        return "AI 编程/Agent 工作流"
    if has_any(text, model_terms):
        return "模型发布/能力解读"
    if has_any(text, business_terms):
        return "产品/副业/商业化"
    if re.search(r"ai|工具|效率|输入法|办公|ppt|浏览器|教程", title):
        return "泛 AI 热点/效率工具"
    return "泛 AI 热点/效率工具"


def classify_pain(record: dict[str, Any], content_type: str) -> str:
    text = text_blob(record)
    if content_type == "风险/账号/额度焦虑":
        return "账号安全与权限焦虑"
    if content_type == "价格/额度/羊毛情报":
        return "成本、额度与订阅压力"
    if content_type == "AI 编程/Agent 工作流":
        return "工具选择与效率落地"
    if content_type == "模型发布/能力解读":
        return "模型能力判断"
    if content_type == "产品/副业/商业化":
        return "副业产品化与变现"
    if has_any(text, ["免费", "价格", "额度", "订阅"]):
        return "成本、额度与订阅压力"
    return "热点信息差与谈资"


def classify_persona(record: dict[str, Any], content_type: str, pain: str) -> str:
    text = text_blob(record)
    if has_any(text, ["codex", "claude", "gpt", "openai", "anthropic", "kimi"]):
        if content_type == "AI 编程/Agent 工作流":
            return "AI 编程/Agent 实践者"
        return "Claude/Codex/GPT 重度用户"
    if pain == "成本、额度与订阅压力":
        return "省钱党与套餐比较用户"
    if content_type == "产品/副业/商业化":
        return "产品经理/独立开发者"
    if content_type == "泛 AI 热点/效率工具":
        return "非技术效率工具用户"
    return "AI 新闻观察者"


def title_length_bucket(title: str) -> str:
    length = len(title.strip())
    if length <= 16:
        return "16字内"
    if length <= 24:
        return "17-24字"
    if length <= 34:
        return "25-34字"
    return "35字以上"


def title_structure(title: str) -> dict[str, Any]:
    text = title.lower()
    has_number = bool(re.search(r"\d|一|二|三|四|五|六|七|八|九|十|百|千|万|亿", title))
    has_price_word = has_any(text, ["免费", "额度", "价格", "会员", "订阅", "美金", "元", "羊毛"])
    has_risk_word = has_any(text, ["封号", "废掉", "限制", "卡", "缩水", "失效", "崩", "风险", "截止", "焦虑"])
    has_model_word = has_any(text, ["glm", "kimi", "deepseek", "claude", "gpt", "minimax", "qwen", "模型"])
    has_comparison = bool(re.search(r"vs|比|对比|替代|不如|超过|打败|拿下|第一", text))
    has_question = bool(re.search(r"[?？]|为什么|怎么|能不能|是不是|到底|凭什么", title))
    has_tutorial = has_any(text, ["教程", "指南", "手把手", "完整", "附", "清单", "步骤", "一文"])
    has_workflow = has_any(text, ["codex", "claude code", "agent", "skill", "工作流", "github", "插件", "项目"])

    patterns: list[str] = []
    if has_risk_word:
        patterns.append("风险损失型")
    if has_price_word:
        patterns.append("价格福利型")
    if has_model_word and has_any(text, ["发布", "开源", "上线", "新", "更新", "拿下"]):
        patterns.append("模型发布型")
    if has_comparison:
        patterns.append("对比替代型")
    if has_tutorial or has_number:
        patterns.append("教程清单型")
    if has_question:
        patterns.append("疑问反常识型")
    if has_workflow:
        patterns.append("工作流案例型")
    if not patterns:
        patterns.append("普通资讯型")

    return {
        "length": len(title.strip()),
        "length_bucket": title_length_bucket(title),
        "primary_pattern": patterns[0],
        "patterns": patterns,
        "has_number": has_number,
        "has_price_word": has_price_word,
        "has_risk_word": has_risk_word,
        "has_model_word": has_model_word,
        "has_comparison": has_comparison,
        "has_question": has_question,
        "has_tutorial": has_tutorial,
    }


def strip_markdown_for_length(text: str) -> str:
    text = re.sub(r"(?s)^---.*?---", "", text, count=1)
    text = re.sub(r"(?s)```.*?```", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[#>*_`~\-|]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def count_article_chars(text: str) -> int:
    clean = strip_markdown_for_length(text)
    cjk = re.findall(r"[\u4e00-\u9fff]", clean)
    ascii_words = re.findall(r"[A-Za-z0-9][A-Za-z0-9+._/-]*", clean)
    return len(cjk) + sum(len(word) for word in ascii_words)


def length_bucket(length: int) -> str:
    if length <= 0:
        return "未匹配正文"
    if length < 1200:
        return "1200字内"
    if length < 2200:
        return "1200-2200字"
    if length < 3500:
        return "2200-3500字"
    return "3500字以上"
