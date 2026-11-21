#!/usr/bin/env python3
"""PostToolUse 钩子：长任务运行中，把聊天里补充的指令（@机器人 #N ...）塞给正在跑的 Claude。

Input:  Claude Code 的 PostToolUse JSON（stdin）；环境变量 FCB_TASK_ID（只有后台任务会话有）
Output: 有新指令时输出 additionalContext；否则什么都不输出
Pos:    机器人实例的钩子，由 claude-settings.json 引用；聊天会话里没有 FCB_TASK_ID，直接退出
"""
import json, os, sys

tid = os.environ.get("FCB_TASK_ID")
if not tid:
    sys.exit(0)
sys.stdin.read()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tasks
items = tasks.inbox_take(int(tid))
if items:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                             "additionalContext": tasks.format_inbox(items)}}, ensure_ascii=False))
