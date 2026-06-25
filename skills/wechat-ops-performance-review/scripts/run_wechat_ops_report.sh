#!/usr/bin/env bash
set -euo pipefail

root="${1:-/Users/dw/Desktop/claude}"
wiki_root="${2:-/Users/dw/wiki}"

python3 "${root}/scripts/social_ops/build_wechat_ops_report.py" --root "${root}" --wiki-root "${wiki_root}"
python3 "${root}/scripts/social_ops/build_wechat_ops_report.py" --root "${root}" --wiki-root "${wiki_root}" --check
python3 -m pytest "${root}/tests/test_wechat_ops_report.py" -q
pnpm -C "${root}/reports/wechat-ops-dashboard" build
