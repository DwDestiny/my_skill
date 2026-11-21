#!/usr/bin/env python3
"""PreToolUse 钩子：按发消息的人限制 lark-cli 的身份。

Input:  Claude Code 的 PreToolUse JSON（stdin）；环境变量 FCB_OWNER（1 = 主人本人发的）、FCB_CONFIG
Output: 违规时 exit 2，stderr 写原因（Claude 能看到）；否则 exit 0
Pos:    飞书机器人实例的硬限制，由 claude-settings.json 引用
策略（config.json 的 identity）:
  owner:  "user_no_speak"（默认）可用主人的用户身份办事，但不能以主人名义发、改、撤消息
          "user"          完全可用主人的用户身份
          "bot"           只能用机器人身份
  others: "bot_read_im"（默认）读聊天记录可用主人身份，其余只能用机器人身份
          "bot"           只能用机器人身份
"""
import json, os, re, sys

data = json.load(sys.stdin)
cmd = (data.get("tool_input") or {}).get("command", "")
if "lark-cli" not in cmd:
    sys.exit(0)
try:
    with open(os.environ["FCB_CONFIG"]) as f: cfg = json.load(f)
except Exception:
    cfg = {}
pol = cfg.get("identity", {})
# 跨 IM 读取（config.json 的 cross_im_read）：关闭时，企微来的会话不能用主人身份读飞书聊天记录
cross_ok = cfg.get("cross_im_read", False) or os.environ.get("FCB_CHANNEL", "feishu") == "feishu"
owner = os.environ.get("FCB_OWNER") == "1"
mode = pol.get("owner", "user_no_speak") if owner else pol.get("others", "bot_read_im")

IM_SPEAK = re.compile(r"\bim\s+(\+messages-(send|reply|edit|forward)|messages\s+(delete|patch|forward|merge_forward|urgent_\w+))\b"
                      r"|\bapi\s+(POST|PUT|PATCH|DELETE)\s+/open-apis/im/v1/messages", re.I)
IM_READ = re.compile(r"\bim\s+\+(chat-messages-list|threads-messages-list|messages-mget|messages-search|chat-list"
                     r"|chat-search|chat-members-list|messages-resources-download)\b")

def block(msg):
    sys.stderr.write("机器人规则：" + msg + "\n"); sys.exit(2)

for seg in re.split(r"\|\||&&|[|;\n]", cmd):
    if "lark-cli" not in seg:
        continue
    if re.search(r"--as[ =]bot\b", seg):
        continue
    if not cross_ok and IM_READ.search(seg):
        block("跨 IM 读取已关闭：企业微信里的会话不能用主人身份读飞书聊天记录。")
    if mode == "user":
        continue
    if mode == "user_no_speak":
        if IM_SPEAK.search(seg):
            block("不能以主人的名义在飞书发、改、撤消息。要发消息用 --as bot，或者请主人自己发。")
        continue
    if mode == "bot_read_im" and IM_READ.search(seg):
        continue
    block("这个场景只能用机器人身份。lark-cli 命令要显式加 --as bot，做不到的事请对方找主人。")
sys.exit(0)
