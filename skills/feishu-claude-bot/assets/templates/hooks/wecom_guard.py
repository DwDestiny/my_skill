#!/usr/bin/env python3
"""PreToolUse 钩子：按发消息的人限制 wecom-cli（企业微信 CLI）。

Input:  Claude Code 的 PreToolUse JSON（stdin）；环境变量 FCB_OWNER（1 = 主人本人发的）
Output: 违规时 exit 2，stderr 写原因（Claude 能看到）；否则 exit 0
Pos:    机器人实例的硬限制，由 claude-settings.json 引用。不论是否启用企微渠道都挂上：本机装了 wecom-cli 并授权过，飞书里的会话也能调用它
规则:
  wecom-cli 用的是“机器人代主人”的授权，能读主人的邮件、文档、日程、微盘。
  - 所有人：不能动授权（auth），不能以主人名义发 IM（message send）或发、回、转邮件（mail send/reply/forward）。
  - 主人本人发的：其余命令可用。
  - 其他人发的：只能用机器人发消息（message aibot）和查通讯录（contact）；读企微聊天记录（chat）按身份策略
    identity.others = "bot_read_im"（默认）放行，其余一律不行。
  - 跨 IM 读取（config.json 的 cross_im_read，默认关）：关闭时，飞书来的会话不能读企微聊天记录（chat）。
"""
import json, os, re, sys

data = json.load(sys.stdin)
cmd = (data.get("tool_input") or {}).get("command", "")
WECOM_CALL = r"wecom-cli|@wecom/cli|cli-(linux|darwin|win32)-(x64|arm64)|\.config/wecom"   # 只认 wecom-cli 的各种调用写法，代码里出现 wecom 字样不算
if not re.search(WECOM_CALL, cmd, re.I):
    sys.exit(0)
owner = os.environ.get("FCB_OWNER") == "1"
try:
    with open(os.environ["FCB_CONFIG"]) as f: cfg = json.load(f)
except Exception:
    cfg = {}
cross_ok = cfg.get("cross_im_read", False) or os.environ.get("FCB_CHANNEL") == "wecom"
others_read = cfg.get("identity", {}).get("others", "bot_read_im") == "bot_read_im"
ALLOWED = r"contact|message\s+aibot" + (r"|chat" if others_read else "")

def block(msg):
    sys.stderr.write("机器人规则：" + msg + "\n"); sys.exit(2)

if ".config/wecom" in cmd:
    block("企业微信凭证目录不能碰。")
# 非本人：除了“wecom-cli contact …”和“wecom-cli message aibot …”这两种直接写法，命令里出现 wecom 一律拦，
# 防止用 $(which wecom-cli)、node_modules 里的二进制、别名等绕过下面的逐段检查
if not owner and re.search(WECOM_CALL, re.sub(r"(?<![\w/.-])wecom-cli\s+(" + ALLOWED + r")\b", "", cmd), re.I):
    block("这条消息不是主人本人发的，企业微信这边只能用机器人发消息（wecom-cli message aibot）和查通讯录（wecom-cli contact）。主人的邮件、文档、日程、微盘不能读，请对方找主人。")
for seg in re.split(r"\|\||&&|[|;\n]", cmd):
    m = re.search(r"wecom-cli\s+(.*)", seg)
    if not m:
        continue
    args = [a for a in m.group(1).split() if not a.startswith("-")]
    svc, sub = (args + ["", ""])[:2]
    if svc == "chat" and not cross_ok:
        block("跨 IM 读取已关闭：飞书里的会话不能读企业微信聊天记录。")
    if svc == "auth":
        block("不能改企业微信授权。")
    if svc == "message" and sub == "send":
        block("不能以主人的名义在企业微信发消息。要发用 wecom-cli message aibot send（以机器人身份），或者请主人自己发。")
    if svc == "mail" and re.search(r"\b(send|reply|forward)", m.group(1)):
        block("不能以主人的名义发、回、转邮件。草拟好内容交给主人自己发。")
    if not owner and not (svc == "contact" or (svc == "message" and sub == "aibot") or (svc == "chat" and others_read)
                          or svc in ("", "help", "--help", "-h")):
        block("这条消息不是主人本人发的，企业微信这边只能用机器人发消息和查通讯录。主人的邮件、文档、日程、微盘不能读，请对方找主人。")
sys.exit(0)
