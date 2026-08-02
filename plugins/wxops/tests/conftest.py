# GEB-L3
# Input: pytest 自动加载本 conftest；无额外 fixture / 假数据
# Output: 将 plugins/wxops/scripts 插入 sys.path，供全套测试 import build_wechat_ops_report
# Pos: plugins/wxops/tests/conftest.py
"""Pytest configuration for wechat ops report tests.

Ensures scripts/ is importable so tests can import the decoupled builder directly.
"""
from pathlib import Path
import sys

# Add scripts dir to path so `import build_wechat_ops_report` works without package install.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
