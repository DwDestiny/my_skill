# GEB-L3
# Input: 无运行时入参（analyze 包入口）
# Output: 空包标记；运营报告分析子模块容器（classify/enrich/m1–m9 等），对外符号经 build_wechat_ops_report 再导出
# Pos: plugins/wxops/scripts/analyze/__init__.py
"""analyze package: pure mechanical split of build_wechat_ops_report internals.

All logic unchanged. Public names re-exported via build_wechat_ops_report.
"""
