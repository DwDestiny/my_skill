"""Issue #16 回归：skill 目录只读时也能跑，所有产物落工作区。

安全红线：只读冒烟只在 mktemp 出的 skill 副本上 chmod，绝不碰真实 skill 目录。
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from build_wechat_ops_report import build_dataset, build_paths, derive_report_date, write_outputs

SKILL_DIR = Path(__file__).resolve().parents[1]
FIXTURES = SKILL_DIR / "fixtures"
SKILL_DASHBOARD_REPORT = SKILL_DIR / "dashboard" / "src" / "data" / "report.json"


def _snapshot_tree(root: Path) -> dict[str, float]:
    """path -> mtime 快照，用于断言目录未被改动。"""
    out: dict[str, float] = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p)] = p.stat().st_mtime_ns
    return out


def _seed_workspace_inputs(workspace: Path) -> None:
    """把 fixtures 原始输入复制到工作区（排除产物子目录 output/）。"""
    shutil.copytree(
        FIXTURES, workspace, dirs_exist_ok=True, ignore=shutil.ignore_patterns("output")
    )


def test_builder_writes_to_workspace_not_skill(tmp_path: Path) -> None:
    """builder 跑后 report.json 落 <ws>/output/report.json，skill dashboard 数据不被动。"""
    workspace = tmp_path / "ws"
    _seed_workspace_inputs(workspace)

    skill_dashboard_before = (
        SKILL_DASHBOARD_REPORT.stat().st_mtime_ns if SKILL_DASHBOARD_REPORT.exists() else None
    )

    report_date = derive_report_date(workspace)
    paths = build_paths(workspace, None, report_date)
    dataset = build_dataset(workspace, account_name="样例运营号")
    write_outputs(dataset, paths)

    # 主产物落工作区 output
    assert (workspace / "output" / "report.json").exists()
    assert (workspace / "output" / f"wechat-ops-report-{report_date}.json").exists()
    assert (workspace / "output" / f"wechat-ops-report-{report_date}.md").exists()

    # dashboard_data 默认落工作区，绝不指向 skill 目录
    assert paths.dashboard_data_path == workspace / "output" / "report.json"
    assert SKILL_DIR not in paths.dashboard_data_path.parents

    # skill 目录下的 dashboard 数据文件未被改动
    skill_dashboard_after = (
        SKILL_DASHBOARD_REPORT.stat().st_mtime_ns if SKILL_DASHBOARD_REPORT.exists() else None
    )
    assert skill_dashboard_before == skill_dashboard_after


def test_builder_deterministic_cross_workspace(tmp_path: Path) -> None:
    """同输入不同工作区，dataset payload byte 一致（确定性不破）。"""
    import json

    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    _seed_workspace_inputs(ws1)
    _seed_workspace_inputs(ws2)
    d1 = build_dataset(ws1, account_name="样例运营号")
    d2 = build_dataset(ws2, account_name="样例运营号")
    assert json.dumps(d1, ensure_ascii=False, sort_keys=False) == json.dumps(
        d2, ensure_ascii=False, sort_keys=False
    )


def test_demo_data_flow_fixtures_to_workspace(tmp_path: Path) -> None:
    """demo 数据流：fixtures 输入 → 工作区 → output/report.json 产出存在。"""
    workspace = tmp_path / "ws"
    _seed_workspace_inputs(workspace)
    # 工作区拿到了原始输入
    assert (workspace / "reports" / "wechat").exists()
    assert list((workspace / "reports" / "wechat").glob("publish-records-*.json"))
    # fixtures/output 产物不应被当输入拷过来
    assert not (workspace / "output").exists()

    report_date = derive_report_date(workspace)
    paths = build_paths(workspace, None, report_date)
    dataset = build_dataset(workspace, account_name="样例运营号")
    write_outputs(dataset, paths)
    assert (workspace / "output" / "report.json").exists()


def _chmod_tree_readonly(root: Path) -> None:
    for p in sorted(root.rglob("*"), reverse=True):
        try:
            os.chmod(p, stat.S_IRUSR | (stat.S_IRGRP if p.is_file() else stat.S_IRGRP | stat.S_IXUSR | stat.S_IXGRP))
        except OSError:
            pass
    os.chmod(root, stat.S_IRUSR | stat.S_IXUSR)


def _chmod_tree_writable(root: Path) -> None:
    for p in [root, *root.rglob("*")]:
        try:
            os.chmod(p, 0o755)
        except OSError:
            pass


def test_readonly_skill_copy_smoke(tmp_path: Path) -> None:
    """只读冒烟：copy skill → chmod a-w 副本 → 跑 builder，rc=0、产物落工作区、副本未被写。

    安全：只在 tmp_path 下的副本上 chmod，绝不碰真实 skill 目录。
    """
    skill_copy = tmp_path / "skill_ro"
    workspace = tmp_path / "ws"
    # 复制 skill（排除重资产 node_modules/.git 加速）
    shutil.copytree(
        SKILL_DIR,
        skill_copy,
        ignore=shutil.ignore_patterns("node_modules", ".git", "__pycache__", "dist", "*.pyc"),
    )
    _seed_workspace_inputs(workspace)

    builder = skill_copy / "scripts" / "build_wechat_ops_report.py"
    assert builder.exists()

    _chmod_tree_readonly(skill_copy)
    before = _snapshot_tree(skill_copy)
    try:
        proc = subprocess.run(
            [sys.executable, str(builder), "--workspace", str(workspace), "--account-name", "样例运营号"],
            capture_output=True,
            text=True,
        )
    finally:
        _chmod_tree_writable(skill_copy)

    assert proc.returncode == 0, f"rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
    assert (workspace / "output" / "report.json").exists()

    after = _snapshot_tree(skill_copy)
    # 只读 skill 副本内容/文件清单无变化
    assert set(before.keys()) == set(after.keys()), "只读 skill 副本出现新增/删除文件"
    changed = [k for k in before if before[k] != after.get(k)]
    assert not changed, f"只读 skill 副本被修改: {changed}"
