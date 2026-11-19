#!/usr/bin/env bash
# 查机器人和主人（当前登录用户）的 open_id，填进 config.json。
# 用法：bash ids.sh
set -euo pipefail
echo "bot_open_id:   $(lark-cli api GET /open-apis/bot/v3/info --as bot --jq .data.open_id)"
echo "bot 名字:      $(lark-cli api GET /open-apis/bot/v3/info --as bot --jq .data.app_name)"
echo "owner_open_id: $(lark-cli contact +get-user --as user --jq .data.user.open_id)"
echo "owner 名字:    $(lark-cli contact +get-user --as user --jq .data.user.name)"
