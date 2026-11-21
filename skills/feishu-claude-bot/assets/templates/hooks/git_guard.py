#!/usr/bin/env python3
"""PreToolUse 钩子：限制 git 和 gh 能做什么。

Input:  Claude Code 的 PreToolUse JSON（stdin）；环境变量 FCB_OWNER（1 = 主人本人触发的会话或任务）
Output: 违规时 exit 2，stderr 写原因（Claude 能看到）；否则 exit 0
Pos:    机器人实例的硬限制，由 claude-settings.json 引用。推送的分支由 hooks/git/pre-push 在 ref 层面再拦一遍
规则:
  - 所有人：不能绕过 git 钩子（--no-verify、改 core.hooksPath、GIT_CONFIG_*）；不能读 gh 的登录凭证；
    不能直接碰代码平台凭据（config.json 的 credential_paths、git 凭据助手、带令牌的接口请求头）。
    建合并请求走 python3 tasks.py mr，它在自己进程里读凭据、只建草稿。
  - 主人本人：不能强推或删除 main/master。
  - 其他人（含主人批准过的同事任务）：git push 不能强推、删分支、推标签、--mirror/--all；
    gh 只能建草稿合并请求、看合并请求/issue/CI、提 issue 和评论、只读的 gh api。合并、发版、改仓库设置一律不行。
"""
import json, os, re, sys

data = json.load(sys.stdin)
cmd = (data.get("tool_input") or {}).get("command", "")
owner = os.environ.get("FCB_OWNER") == "1"

def block(msg):
    sys.stderr.write("机器人规则：" + msg + "\n"); sys.exit(2)

# 代码平台凭据：谁触发的会话都不能直接读或拿去调接口（主人的令牌能合并、能删仓，同事任务拿到就越过了“只建草稿”）
HOME = os.path.expanduser("~")
try:
    with open(os.environ["FCB_CONFIG"]) as f: cred = json.load(f).get("credential_paths", [])
except Exception:
    cred = []
norm = re.sub(r"(?<![\w/])~(?=/)", HOME, cmd.replace("${HOME}", HOME).replace("$HOME", HOME))
for p in cred:
    p = os.path.expanduser(p).rstrip("/")
    if p and p in norm:
        block("不能直接读代码平台凭据。建合并请求用 python3 tasks.py mr（在任务工作树里跑）。")
if re.search(r"git-credential-\S+\s+(get|fill)|\bgit\s+credential\b|credential\.helper\s*=|x-yunxiao-token|PRIVATE-TOKEN", cmd, re.I):
    block("不能直接取用代码平台凭据。建合并请求用 python3 tasks.py mr（在任务工作树里跑）。")

if not re.search(r"\b(git|gh)\b", cmd):
    sys.exit(0)

if re.search(r"--no-verify|hookspath|GIT_CONFIG_|--config-env", cmd, re.I):
    block("不能绕过或改写 git 钩子。")
if not owner and re.search(r"\benv\s+(-\S*[iu]|--ignore-environment|--unset)|\bunset\s+\S*(GIT|FCB)|\bsetsid\b|systemd-run|\bsudo\b", cmd):
    block("这个会话不是主人本人触发的：不能清掉或改写运行环境。")
if re.search(r"\bgh\s+auth\s+(token|status\s+.*--show-token)|\.config/gh|git\s+credential", cmd):
    block("不能读 GitHub 登录凭证。")

segs = re.split(r"\|\||&&|[|;\n]|\$\(|\x60", cmd)
for seg in segs:
    s = seg.strip()
    m = re.search(r"(?:^|[\s/])git\s+(?:-C\s+\S+\s+)?push\b(.*)", s)
    if m:
        args = m.group(1)
        force = re.search(r"(^|\s)(-f|--force\S*|--mirror|--delete|-d|--prune)(\s|$)|(^|\s)\+\S+|(^|\s):\S+", args)
        if owner:
            if force and re.search(r"\b(main|master)\b", args):
                block("不能强推或删除 main/master。")
        else:
            if force or re.search(r"(^|\s)(--tags|--all|--follow-tags)(\s|$)", args):
                block("这个会话不是主人本人触发的：只能普通推送 bot/ 开头的分支，不能强推、删分支、推标签。")
            for ref in re.findall(r"(?:^|\s)(?!-)(\S*:\S+)", args):   # 写明了推到哪：目标必须是 bot/ 分支
                if "@" in ref.split(":", 1)[0] or "://" in ref: continue   # 远端地址，不是 refspec
                dst = ref.split(":", 1)[1].replace("refs/heads/", "")
                if not dst.startswith("bot/"):
                    block(f"这个会话不是主人本人触发的：只能推 bot/ 开头的分支，{dst} 不行。")
    if owner:
        continue
    for g in re.finditer(r"(?:^|[\s/])gh\s+(\S+)\s*(\S*)(.*)", s):
        sub, act, rest = g.group(1), g.group(2), g.group(3)
        ok = (sub == "pr" and act in ("view", "list", "diff", "checks", "status")) \
            or (sub == "pr" and act == "create" and "--draft" in rest + " " + act) \
            or (sub == "issue" and act in ("create", "view", "list", "comment", "status")) \
            or (sub in ("repo",) and act == "view") \
            or (sub == "run" and act in ("view", "list", "watch")) \
            or (sub == "search") \
            or (sub == "api" and not re.search(r"(-X|--method)\s*(?!GET\b)\S+|(^|\s)(-f|-F|--field|--raw-field|--input)(\s|=)", act + " " + rest))
        if not ok:
            block("这个会话不是主人本人触发的：gh 只能建草稿合并请求（gh pr create --draft）、看合并请求/issue/CI、提 issue 和评论。合并、发版、改设置请主人来。")
sys.exit(0)
