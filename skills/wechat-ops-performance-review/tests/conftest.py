"""Pytest configuration for wechat ops report tests.

Ensures scripts/ is importable so tests can import the decoupled builder directly.
"""
from pathlib import Path
import sys

# Add scripts dir to path so `import build_wechat_ops_report` works without package install.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
