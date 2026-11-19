#!/usr/bin/env python3
"""PreToolUse 钩子：除了“主人私聊”，挡住私密资料的读取，并让知识库全库搜索自动跳过私密目录。

Input:  Claude Code 的 PreToolUse JSON（stdin）；环境变量 FCB_PRIVATE（1 = 主人本人私聊）、FCB_CONFIG
Output: 命中时 exit 2，stderr 写原因；改写搜索命令时输出 updatedInput；否则 exit 0
Pos:    飞书机器人实例的硬限制，由 claude-settings.json 引用
配置（config.json 的 private）:
  paths:        正则列表，工具参数里出现就拦（路径里的 ~ 和 $HOME 会先展开）
  search_roots: [{"root": "~/wiki/wiki", "exclude": ["**/people/**", "**/entities/People*"]}]
                对这些目录的全库 rg/grep 自动加排除规则；Grep/Glob 工具和 find 等不能对整个目录用
"""
import json, os, re, sys

if os.environ.get("FCB_PRIVATE") == "1":
    sys.exit(0)
try:
    with open(os.environ["FCB_CONFIG"]) as f: cfg = json.load(f).get("private", {})
except Exception:
    cfg = {}
HOME = os.path.expanduser("~")
X = lambda p: HOME + p[1:] if p.startswith("~") else p
data = json.load(sys.stdin)
tool = data.get("tool_name", "")
ti = data.get("tool_input") or {}
text = " ".join(str(v) for v in ti.values() if isinstance(v, (str, int)))
text = text.replace("${HOME}", HOME).replace("$HOME", HOME)
text = re.sub(r"(?<![\w/])~(?=/|\s|$)", HOME, text)

def block(msg):
    sys.stderr.write("机器人红线：" + msg + " 私密资料只在主人私聊里能碰，被拦了不要绕路。\n"); sys.exit(2)

for pat in cfg.get("paths", []):
    p = X(pat)
    if p in text or re.search(p, text):
        block("这个路径在当前场景不能读。")

def grep_ex(globs):
    out = []
    for g in globs:
        if g.endswith("/**"): out.append("--exclude-dir=" + g[:-3].split("/")[-1])
        else: out.append("--exclude='" + g.split("/")[-1] + "'")
    return " ".join(out)

if tool == "Bash":
    cmd = ti.get("command", "")
    new = cmd
    for sr in cfg.get("search_roots", []):
        root = X(sr["root"]).rstrip("/")
        whole = r"(" + re.escape(root) + r"|" + re.escape(sr["root"].rstrip("/")) + r")/?(?=[\s'\";&|)]|$)"
        cd_root = re.search(r"\bcd\s+(" + re.escape(root) + r"|" + re.escape(sr["root"].rstrip("/")) + r")/?(\s|&|;|$)", cmd)
        if not (re.search(whole, text) or cd_root):
            continue
        if re.search(r"\b(ag|ack|find|fd|tree|ls\s+-\w*R|cat\s+\*|xargs)\b", cmd):
            block(f"对 {sr['root']} 整个目录只能用 rg 或 grep 搜索（会自动跳过私密目录），或者指定子目录。")
        rg_ex = " ".join("--glob '!" + g + "'" for g in sr.get("exclude", []))
        new = re.sub(r"\brg(\s)", lambda m: "rg " + rg_ex + m.group(1), new)
        new = re.sub(r"\b(e?grep)(\s)", lambda m: m.group(1) + " " + grep_ex(sr.get("exclude", [])) + m.group(2), new)
    if new != cmd:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                          "permissionDecisionReason": "搜索已自动跳过私密目录",
                          "updatedInput": dict(ti, command=new)}}, ensure_ascii=False))
        sys.exit(0)
elif tool in ("Grep", "Glob"):
    path = X(str(ti.get("path", "")).rstrip("/"))
    for sr in cfg.get("search_roots", []):
        if path and path == X(sr["root"]).rstrip("/"):
            block(f"不能用 {tool} 对 {sr['root']} 整个目录搜索。改用 Bash 的 rg（会自动跳过私密目录），或者指定子目录。")
sys.exit(0)
