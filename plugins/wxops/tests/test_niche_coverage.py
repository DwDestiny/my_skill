# GEB-L3
# Input: tmp WXOPS_HOME + 非 AI / demo fixture；niche_loader + build_dataset
# Output: C4 覆盖率闸门、G2 触闸、m8/m9 降级、MD 警示块断言
# Pos: plugins/wxops/tests/test_niche_coverage.py
from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from analyze.constants import NICHE_COVERAGE_ALERT_THRESHOLD
from analyze.niche_loader import get_active, load_niche, reset_active, set_active
from build_wechat_ops_report import build_dataset, render_report

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PLUGIN_ROOT / "fixtures"
BUILTIN_AI = PLUGIN_ROOT / "niches" / "ai-tools" / "niche.json"
CN_TZ = ZoneInfo("Asia/Shanghai")

# 内置 ai-tools 包字面量钉死（review 护栏；不从代码/包文件读）
AI_TOOLS_CONTENT_TYPES = [
    "风险/账号/额度焦虑",
    "价格/额度/羊毛情报",
    "模型发布/能力解读",
    "AI 编程/Agent 工作流",
    "产品/副业/商业化",
    "泛 AI 热点/效率工具",
]
AI_TOOLS_PAIN_POINTS = [
    "账号安全与权限焦虑",
    "成本、额度与订阅压力",
    "工具选择与效率落地",
    "模型能力判断",
    "副业产品化与变现",
    "热点信息差与谈资",
]
AI_TOOLS_PERSONAS = [
    "Claude/Codex/GPT 重度用户",
    "AI 编程/Agent 实践者",
    "省钱党与套餐比较用户",
    "产品经理/独立开发者",
    "非技术效率工具用户",
    "AI 新闻观察者",
]
AI_TOOLS_TITLE_KEYS = [
    "风险损失型",
    "价格福利型",
    "模型发布型",
    "对比替代型",
    "教程清单型",
    "疑问反常识型",
    "工作流案例型",
    "普通资讯型",
]

# 母婴/生活类标题：故意避开 ai-tools 词表
_NON_AI_TITLES = [
    ("宝宝夜哭怎么办，三个安抚小妙招", "新手爸妈最常踩的坑，今晚就能用"),
    ("辅食添加时间表：6 个月后怎么吃", "循序渐进不踩雷"),
    ("产假结束后如何平衡工作与带娃", "职场妈妈真实复盘"),
    ("婴儿湿疹反复发作该怎么护理", "皮肤科医生建议的居家步骤"),
    ("二胎家庭如何分配带娃时间", "不内耗的分工清单"),
    ("月子餐七天食谱，营养又下奶", "家人也能照着做"),
    ("幼儿园入园焦虑：分离哭闹怎么办", "心理老师给的过渡方案"),
    ("母乳喂养姿势纠正，减少乳腺炎", "新手妈妈必看图解"),
    ("宝宝便秘吃什么，三款果泥食谱", "温和通便不伤胃"),
    ("产后身材恢复，居家跟练计划", "每天 20 分钟即可"),
    ("挑食宝宝餐桌引导法", "不威逼不哄骗"),
    ("儿童视力保护：电子屏怎么控", "家庭公约模板"),
    ("睡眠训练温和版，七天见效", "适合敏感气质宝宝"),
    ("亲子阅读打卡：绘本怎么选", "0-3 岁书单"),
    ("家庭收纳改造，小户型也能整洁", "周末半天搞定"),
    ("周末亲子户外路线推荐", "市区半日游不累"),
    ("学龄前社交能力怎么练", "角色扮演小游戏"),
    ("过敏宝宝饮食日记怎么记", "排查过敏源的简单方法"),
    ("换季穿衣：一层一层怎么叠", "不出汗也不着凉"),
    ("哄睡失败的夜晚，父母如何自救", "情绪先稳住"),
    ("宝宝发烧居家观察要点", "什么时候该去医院"),
    ("辅食研磨工具选购指南", "省时又好清洗"),
    ("二宝出生后大宝心理疏导", "减少争宠冲突"),
    ("孕期营养补剂怎么选", "别盲目跟风"),
    ("坐月子亲戚边界怎么设", "温和但坚定的话术"),
]


@pytest.fixture(autouse=True)
def _isolate_active_and_home(tmp_path, monkeypatch):
    """每测隔离：WXOPS_HOME=tmp，清空 active，不碰真实 ~/.wxops。"""
    monkeypatch.setenv("WXOPS_HOME", str(tmp_path))
    reset_active()
    yield
    reset_active()


def _write_non_ai_workspace(tmp_path: Path, n: int = 24) -> Path:
    """造最小可跑 workspace：非 AI 文章进 stable，结构照抄 demo fixture。"""
    ws = tmp_path / "ws_non_ai"
    # 复制 indexes / metrics 等辅助结构（enrich 需要）
    for rel in [
        "data/social_ops/indexes",
        "data/social_ops/metrics",
        "raw",
        "reports/wechat",
    ]:
        src = FIXTURES / rel
        dst = ws / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    captured = datetime(2026, 1, 15, 18, 0, 0, tzinfo=CN_TZ)
    records = []
    for i, (title, digest) in enumerate(_NON_AI_TITLES[:n]):
        pub = captured - timedelta(days=10 + i)  # 全部 >48h → stable
        records.append(
            {
                "appmsgid": 90000 + i,
                "itemidx": 1,
                "title": title,
                "digest": digest,
                "content_url": f"https://example.com/non-ai/{i}",
                "cover": "",
                "published_at": pub.isoformat(),
                "is_deleted": False,
                "read_num": 1000 + i * 10,
                "share_num": 20 + i,
                "comment_num": 5 + (i % 3),
                "like_num": 30 + i,
                "old_like_num": 0,
                "moment_like_num": 0,
                "wow_num": 2,
                "reprint_num": 0,
                "reward_money": 0,
                "total_comment_count_contains_reply": 5 + (i % 3),
            }
        )

    export = {
        "url": "https://example.com/backend",
        "captured_at": captured.isoformat(),
        "source": "test_non_ai_fixture",
        "totals": {"record_count": len(records)},
        "groups": [],
        "record_count": len(records),
        "records": records,
        "match_stats": {},
    }
    out = ws / "reports" / "wechat" / "publish-records-non-ai.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws


def test_g2_non_ai_fixture_triggers_alert(tmp_path):
    """a. 非 AI 内容 + ai-tools → 触闸，m8/m9 degraded，MD 有警示块。"""
    ws = _write_non_ai_workspace(tmp_path, n=24)
    set_active(load_niche("ai-tools"))
    dataset = build_dataset(ws, account_name="母婴样例号")
    cov = dataset["niche_coverage"]

    assert cov["total"] > 0
    assert cov["hit_rate"] < NICHE_COVERAGE_ALERT_THRESHOLD
    assert cov["alert"] is True
    assert cov["niche_id"] == "ai-tools"

    fl = dataset["forward_looking"]
    assert fl.get("degraded") is True
    assert "题材信号不可用" in (fl.get("degraded_reason") or "")
    # 题材依赖信号应被剔除
    sig_keys = {s["key"] for s in fl.get("signals", [])}
    assert "topic_distribution" not in sig_keys
    assert "viral_type" not in sig_keys
    assert "interaction" in sig_keys

    at = dataset["account_type"]
    assert at.get("degraded") is True
    assert at["primary"]["key"] == "general"
    assert at.get("fallback_to_general") is True

    md = render_report(dataset, "dataset.json")
    assert "赛道包覆盖率警示" in md
    assert "换包" in md
    assert "建包" in md
    assert "templates/niche.template.json" in md
    assert "references/niche-contract.md" in md


def test_generic_always_alerts(tmp_path):
    """b. 同一 fixture 用 _generic → term_hits==0、hit_rate==0、alert True。"""
    ws = _write_non_ai_workspace(tmp_path, n=20)
    set_active(load_niche("_generic"))
    dataset = build_dataset(ws, account_name="通用样例号")
    cov = dataset["niche_coverage"]
    assert cov["niche_id"] == "_generic"
    assert cov["term_hits"] == 0
    assert cov["hit_rate"] == 0.0
    assert cov["alert"] is True
    assert dataset["forward_looking"].get("degraded") is True
    assert dataset["account_type"].get("degraded") is True


def test_total_zero_no_alert():
    """c. 空 stable → hit_rate 0.0、alert False。"""
    from analyze.m8_forward import build_forward_looking
    from analyze.m9_account_type import build_account_type

    set_active(load_niche("ai-tools"))
    # 最小空 dataset：只挂 coverage 所需字段
    dataset = {
        "articles": {"stable": [], "all_period": []},
        "meta": {},
        "account_profile": {},
        "account": {},
        "modules": {},
        "analysis": {"by_content_type": []},
        "viral_genes": {"viral_formula": {}},
    }
    total = 0
    term_hits = 0
    hit_rate = round(term_hits / total, 3) if total else 0.0
    dataset["niche_coverage"] = {
        "niche_id": "ai-tools",
        "niche_name": "AI 工具与编程",
        "requested_id": "ai-tools",
        "total": total,
        "term_hits": term_hits,
        "fallback_count": 0,
        "hit_rate": hit_rate,
        "threshold": NICHE_COVERAGE_ALERT_THRESHOLD,
        "alert": total > 0 and hit_rate < NICHE_COVERAGE_ALERT_THRESHOLD,
    }
    assert dataset["niche_coverage"]["hit_rate"] == 0.0
    assert dataset["niche_coverage"]["alert"] is False

    fl = build_forward_looking(dataset)
    assert "degraded" not in fl
    at = build_account_type(dataset)
    assert "degraded" not in at


def test_ai_tools_demo_no_alert():
    """d. demo fixture + ai-tools → 不触闸，m8/m9 无 degraded，MD 无警示。"""
    set_active(load_niche("ai-tools"))
    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    cov = dataset["niche_coverage"]
    assert cov["alert"] is False
    assert cov["hit_rate"] >= NICHE_COVERAGE_ALERT_THRESHOLD
    assert "degraded" not in dataset["forward_looking"]
    assert "degraded" not in dataset["account_type"]
    md = render_report(dataset, "dataset.json")
    assert "赛道包覆盖率警示" not in md
    body = md.split("---", 2)[-1].lstrip()
    assert body.startswith("## 本周先做这 5 件事")


def test_user_override_package_end_to_end(tmp_path):
    """e. 用户覆盖包端到端：改 name 与题材名后出现在输出。"""
    data = json.loads(BUILTIN_AI.read_text(encoding="utf-8"))
    data["name"] = "用户覆盖 AI 工具 P3b"
    # 改第一个题材名，并同步 rules/by_content_type 引用
    old = data["content_types"]["names"][0]
    new = "用户自定义风险题材"
    data["content_types"]["names"][0] = new
    for rule in data["content_types"]["rules"]:
        if rule["type"] == old:
            rule["type"] = new
    if old in data["pain_points"]["by_content_type"]:
        data["pain_points"]["by_content_type"][new] = data["pain_points"]["by_content_type"].pop(old)
    for rule in data["personas"]["rules"]:
        if_obj = rule.get("if") or {}
        if if_obj.get("content_type") == old:
            if_obj["content_type"] = new

    niche_path = tmp_path / "niches" / "ai-tools" / "niche.json"
    niche_path.parent.mkdir(parents=True, exist_ok=True)
    niche_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    spec = load_niche("ai-tools")
    assert spec.name == "用户覆盖 AI 工具 P3b"
    assert new in spec.content_type_names
    set_active(spec)

    dataset = build_dataset(FIXTURES, account_name="样例运营号")
    assert dataset["niche_coverage"]["niche_name"] == "用户覆盖 AI 工具 P3b"
    keys = [row["key"] for row in dataset["analysis"]["by_content_type"]]
    assert new in keys
    assert old not in keys


def test_builtin_ai_tools_literals_pinned(tmp_path):
    """f. 内置 ai-tools 包字面量钉死（WXOPS_HOME 空 tmp，封闭性）。"""
    # tmp_path 已是空 home，无用户覆盖
    spec = load_niche("ai-tools")
    assert spec.id == "ai-tools"
    assert spec.content_type_names == AI_TOOLS_CONTENT_TYPES
    assert spec.pain_point_names == AI_TOOLS_PAIN_POINTS
    assert spec.persona_names == AI_TOOLS_PERSONAS
    assert spec.title_pattern_keys == AI_TOOLS_TITLE_KEYS


def test_unknown_fields_warn_and_load(tmp_path, capsys):
    """g. 含未知顶层键与组内键 → 加载成功 + stderr 警告。"""
    data = json.loads(BUILTIN_AI.read_text(encoding="utf-8"))
    data["id"] = "with-unknown"
    data["future_top_field"] = "ignore-me"
    data["content_types"]["extra_ct_key"] = 123
    data["pain_points"]["legacy_flag"] = True
    path = tmp_path / "niches" / "with-unknown" / "niche.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    spec = load_niche("with-unknown")
    assert spec.id == "with-unknown"
    err = capsys.readouterr().err
    assert "含未知字段" in err
    assert "future_top_field" in err
    assert "extra_ct_key" in err or "content_types.extra_ct_key" in err
