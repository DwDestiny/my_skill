#!/usr/bin/env python3
"""长任务：派活、审批状态、后台运行、进度事件。

Input:  同目录 config.json；bridge.py 调用本模块的函数；python3 tasks.py run <id>（后台单元的入口）
Output: state/tasks/<id>/ 下的 task.json（任务状态）、events.jsonl（要发回聊天的事件）、inbox.jsonl（追加指令）、
        stream.log（Claude 原始输出）；任务工作树 <tasks.root>/<服务名>/<id>，分支 bot/<id>-<月日>
Pos:    bridge.py 的任务层。bridge 管收消息、审批、往聊天里发；本文件管任务存储和后台运行。
        后台任务跑在独立的 systemd 用户单元里（macOS 用独立进程组），bridge 重启不影响任务，重启后接着看事件。
"""
import json, os, re, subprocess, sys, time, uuid, shutil, platform, signal, fcntl

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(ROOT, "config.json")
with open(CFG_PATH) as f:
    CFG = json.load(f)
X = os.path.expanduser
SLUG = CFG.get("service_name") or "fcb-" + os.path.basename(ROOT)
OWNER_NAME = CFG.get("owner_name", "主人")
T = dict({"enabled": True, "root": "~/work/.bot-tasks", "max_running": 2, "approval_hours": 24, "heartbeat_min": 30},
         **CFG.get("tasks", {}))
TASK_ROOT = os.path.join(X(T["root"]), SLUG)
STORE = os.path.join(ROOT, "state", "tasks")
WORKDIR = os.path.realpath(X(CFG.get("workdir", "~")))
RULES = os.path.join(ROOT, CFG.get("rules_file", "rules.md"))
SETTINGS = os.path.join(ROOT, "claude-settings.json")
GIT_HOOKS = os.path.join(ROOT, "hooks", "git")
ACTIVE = ("approved", "running", "waiting")
LABEL = {"pending": "待批", "approved": "排队中", "running": "进行中", "waiting": "等回复", "done": "完成",
         "failed": "失败", "lost": "中断", "cancelled": "已取消", "rejected": "没批", "expired": "过期作废"}
CH_LABEL = {"feishu": "飞书", "wecom": "企微"}
# 派活时主控按活儿挑模型和思考档；不在名单里的值忽略，走全局默认
MODELS = [m.lower() for m in T.get("models", ["haiku", "sonnet", "opus"])]
EFFORTS = ["low", "medium", "high", "xhigh", "max"]

# ---------- Claude 参数和钩子环境：聊天会话和任务会话共用，缓存前缀才一致 ----------
def claude_args():
    cmd = ["claude", "-p", "--permission-mode", CFG.get("permission_mode", "auto"),
           "--append-system-prompt-file", RULES, "--settings", SETTINGS,
           # 把 cwd、环境、git 状态挪出系统提示，系统提示前缀才能跨会话命中缓存
           "--exclude-dynamic-system-prompt-sections"]
    for d in CFG.get("add_dirs", []): cmd += ["--add-dir", X(d)]
    if CFG.get("disable_mcp", True):   # MCP 异步连接，首个请求的工具列表时有时无，前缀跟着变，缓存命中不了
        cmd += ["--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    return cmd

def hook_env(owner, private, chat_id, channel="feishu", task_id=None):
    env = dict(os.environ, FCB="1", FCB_CONFIG=CFG_PATH, FCB_OWNER="1" if owner else "0",
               FCB_PRIVATE="1" if private else "0", FCB_CHAT_ID=chat_id, FCB_CHANNEL=channel)
    if not private:   # 非主人私聊：不读不写自动记忆
        env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    if not owner and os.path.isdir(GIT_HOOKS):
        # 非主人触发的会话：git 钩子换成实例的 hooks/git（pre-push 只放行 bot/ 分支，其余转给仓库原来的钩子）
        env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.hooksPath", GIT_CONFIG_VALUE_0=GIT_HOOKS)
    if task_id is not None:
        env["FCB_TASK_ID"] = str(task_id)
    return env

# ---------- 存储 ----------
class _Lock:
    def __init__(self, path): self.path = path
    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.f = open(self.path, "a+"); fcntl.flock(self.f, fcntl.LOCK_EX); return self
    def __exit__(self, *a): fcntl.flock(self.f, fcntl.LOCK_UN); self.f.close()

def tdir(tid): return os.path.join(STORE, str(tid))

def load(tid):
    try:
        with open(os.path.join(tdir(tid), "task.json")) as f: return json.load(f)
    except Exception: return None

def update(tid, **kv):
    with _Lock(os.path.join(tdir(tid), ".lock")):
        t = load(tid) or {}
        t.update(kv); t["updated"] = time.time()
        tmp = os.path.join(tdir(tid), "task.json.tmp")
        with open(tmp, "w") as f: json.dump(t, f, ensure_ascii=False, indent=1)
        os.replace(tmp, os.path.join(tdir(tid), "task.json"))
        return t

def create(**fields):
    os.makedirs(STORE, exist_ok=True)
    with _Lock(os.path.join(STORE, ".lock")):
        n = 1 + max([int(d) for d in os.listdir(STORE) if d.isdigit()] or [0])
        os.makedirs(tdir(n))
    fields.update(id=n, created=time.time(), posted=0, turn=0, session_id=str(uuid.uuid4()),
                  branch=f"bot/{n}-{time.strftime('%m%d')}", worktree=os.path.join(TASK_ROOT, str(n)))
    return update(n, **fields)

def all_tasks():
    if not os.path.isdir(STORE): return []
    return [t for t in (load(int(d)) for d in sorted((d for d in os.listdir(STORE) if d.isdigit()), key=int)) if t]

def _append(tid, name, obj):
    with _Lock(os.path.join(tdir(tid), ".lock")):
        with open(os.path.join(tdir(tid), name), "a") as f: f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def _read(tid, name):
    try:
        with open(os.path.join(tdir(tid), name)) as f: return [json.loads(l) for l in f if l.strip()]
    except FileNotFoundError: return []

def event(tid, kind, text=""):
    """kind: start / progress / question / done / failed / lost。bridge 按顺序发回原聊天。"""
    _append(tid, "events.jsonl", {"kind": kind, "text": text, "ts": time.time()})

def events(tid, start=0): return _read(tid, "events.jsonl")[start:]

def inbox_add(tid, who, owner, text):
    _append(tid, "inbox.jsonl", {"who": who, "owner": owner, "text": text, "ts": time.time()})

def inbox_take(tid):
    """取出还没交给 Claude 的追加指令（每条只交一次）。"""
    with _Lock(os.path.join(tdir(tid), ".lock")):
        p = os.path.join(tdir(tid), "inbox.off")
        try:
            with open(p) as f: off = int(f.read() or 0)
        except Exception: off = 0
        try:
            with open(os.path.join(tdir(tid), "inbox.jsonl")) as f: items = [json.loads(l) for l in f if l.strip()]
        except FileNotFoundError: items = []
        with open(p, "w") as f: f.write(str(len(items)))
        return items[off:]

def format_inbox(items):
    return "\n".join(f"[追加指令] {i['who']}{'（' + OWNER_NAME + '本人）' if i.get('owner') else ''}：{i['text']}" for i in items)

# ---------- 派活前的检查 ----------
def check_repo(path):
    """返回 (仓库根目录, 错误)。只接受工作目录里的 git 仓库；实例目录、私密路径不行。"""
    p = os.path.realpath(X(path.strip().strip(chr(96))))
    if not (p == WORKDIR or p.startswith(WORKDIR + os.sep)):
        return None, f"仓库要在工作目录 {WORKDIR} 里"
    if p == ROOT or p.startswith(ROOT + os.sep) or p.startswith(os.path.realpath(X(T["root"]))):
        return None, "不能在机器人自己的目录里干活"
    for pat in CFG.get("private", {}).get("paths", []):
        if pat.startswith("~") or pat.startswith("/") and not re.search(r"[\\(|]", pat):
            pp = os.path.realpath(X(pat))
            if p == pp or p.startswith(pp + os.sep): return None, "这个目录是私密的"
        else:
            try:
                if re.search(pat, p): return None, "这个目录是私密的"
            except re.error: pass
    r = subprocess.run(["git", "-C", p, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode != 0:
        return None, "不是 git 仓库（长任务要在独立分支上干）"
    return os.path.realpath(r.stdout.strip()), None

def parse_directive(text):
    """从回复里拆出 [派活] 块。返回 (去掉块的回复, {"repo","title","brief"} 或 None)。"""
    m = re.search(r"^\s*\[派活\]\s*$", text, re.M)
    if not m: return text, None
    head, block = text[:m.start()].rstrip(), text[m.end():]
    fence = re.compile(r"^\s*(`{3,}|~{3,})\w*\s*$")   # 守则里的格式写在代码块里，Claude 常把围栏一起抄出来
    hl = head.splitlines()
    while hl and fence.match(hl[-1]): hl.pop()
    head = "\n".join(hl).rstrip()
    block = "\n".join(l for l in block.splitlines() if not fence.match(l))
    bm = re.search(r"^\s*任务书\s*[:：]\s*", block, re.M)
    fields = block[:bm.start()] if bm else block   # 字段只认任务书之前的，任务书正文里的“模型:”不算
    def field(name):
        mm = re.search(r"^\s*" + name + r"\s*[:：]\s*(.*)$", fields, re.M)
        return mm.group(1).strip() if mm else ""
    brief = block[bm.end():].strip() if bm else ""
    def pick(v, ok):   # 正好写了一个合法值才算；照抄“haiku / sonnet / opus”这种就当没写
        hit = {w for w in re.split(r"[\s,，/（()）]+", v.lower()) if w in ok}
        return hit.pop() if len(hit) == 1 else ""
    target = field("目标分支").split()[0] if field("目标分支") else ""
    if not re.fullmatch(r"[\w./-]{1,100}", target) or ".." in target: target = ""
    return head, {"repo": field("仓库"), "title": field("标题")[:80] or "未命名任务", "brief": brief,
                  "model": pick(field("模型"), MODELS), "effort": pick(field("思考"), EFFORTS), "target": target}

def model_label(t):
    """给人看的模型说明，没指定就是默认。"""
    return " · ".join(x for x in (t.get("model"), t.get("effort") and "思考 " + t["effort"]) if x) or "默认模型"

# ---------- 后台运行 ----------
def unit_name(t): return f"{SLUG}-task-{t['id']}-{t['turn']}"

def launch(tid):
    """开一轮后台运行（首次开工、提问后续跑、完成后追加都算一轮）。"""
    t = load(tid)
    t = update(tid, status="running", turn=t.get("turn", 0) + 1, launched=time.time(),
               started=t.get("started") or time.time())
    if platform.system() == "Linux" and shutil.which("systemd-run") and os.environ.get("FCB_TASK_LAUNCH") != "popen":
        env = [f"--setenv={k}={os.environ[k]}" for k in ("PATH", "HOME", "LANG", "USER") if k in os.environ]
        r = subprocess.run(["systemd-run", "--user", "--quiet", "--collect", "--unit", unit_name(t),
                            f"--working-directory={ROOT}", *env, sys.executable, os.path.abspath(__file__), "run", str(tid)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            update(tid, status="failed"); event(tid, "failed", "后台单元没起来：" + (r.stderr or r.stdout)[-300:])
            return False
        update(tid, unit=unit_name(t), pid=None)
    else:   # macOS 或没有 systemd：独立进程组，bridge 重启不受影响（机器重启会断，标成“中断”）
        log = open(os.path.join(tdir(tid), "runner.log"), "a")
        p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "run", str(tid)], cwd=ROOT,
                             stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)
        update(tid, unit=None, pid=p.pid)
    return True

def alive(t):
    if t.get("unit"):
        r = subprocess.run(["systemctl", "--user", "is-active", t["unit"]], capture_output=True, text=True)
        return r.stdout.strip() in ("active", "activating", "reloading")
    pid = t.get("pid")
    if not pid: return False
    try:   # 自己启动的子进程先回收，免得僵尸进程被当成活的
        if os.waitpid(pid, os.WNOHANG) != (0, 0): return False
    except ChildProcessError: pass
    try: os.kill(pid, 0); return True
    except OSError: return False

def stop(t):
    if t.get("unit"):
        subprocess.run(["systemctl", "--user", "stop", t["unit"]], capture_output=True)
    elif t.get("pid"):
        try: os.killpg(t["pid"], signal.SIGTERM)
        except OSError: pass

def git(repo, *a): return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)

def make_worktree(t):
    """从远端默认分支的最新代码切出任务分支；没有远端就从当前 HEAD 切。"""
    wt, repo = t["worktree"], t["repo"]
    if os.path.isdir(wt): return t.get("base", "")
    os.makedirs(os.path.dirname(wt), exist_ok=True)
    base = "HEAD"
    if git(repo, "remote").stdout.strip():
        git(repo, "fetch", "--quiet", "origin")
        r = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
        tg = t.get("target")
        if tg and git(repo, "rev-parse", "--verify", "--quiet", "origin/" + tg).returncode == 0: base = "origin/" + tg
        elif r.returncode == 0: base = r.stdout.strip()
        elif git(repo, "rev-parse", "--verify", "--quiet", "origin/main").returncode == 0: base = "origin/main"
    r = git(repo, "worktree", "add", "--quiet", "-b", t["branch"], wt, base)
    if r.returncode != 0: raise RuntimeError("建工作树失败：" + r.stderr.strip()[-300:])
    return base

def first_prompt(t, base):
    who = t["requester"]
    src = ("私聊" if t["origin"]["chat_type"] == "p2p" else "群聊") + "（" + CH_LABEL.get(t["origin"]["channel"], "") + "）"
    ok = f"，{OWNER_NAME}已批准" if not who.get("owner") else ""
    return f"""[长任务 #{t['id']}] {t['title']}
派活人：{who['name']}（{'是' if who.get('owner') else '不是'}{OWNER_NAME}本人）{ok}；来自{src}
仓库：{t['repo']}。你在它的独立工作树 {t['worktree']} 里，分支 {t['branch']}（基于 {base}）。只改这个工作树。

这是后台任务，没人盯着，做完再说话：
- 先用待办工具列计划。
- 进展汇报：单独起一行写“[进展] 一句话”，会转发给派活人。什么时候报，按守则“长任务”一节的汇报规矩。
- 必须由人拍板的事（方案二选一、需求说不清、要授权），把问题和你的建议写清楚，单独起一行“[提问] 一句话问题”，然后结束这一轮等回复。能自己定的不要问。
- 做完：提交到 {t['branch']}；仓库有远端就推送这个分支，再建草稿合并请求：在工作树里跑 `{mr_cmd(t, base)}`（GitHub、Codeup 都走它，凭据它自己读；不要直接读令牌或调平台接口）。不合并、不推主干、不发版。
- 最后一条回复是给派活人看的总结：做了什么、怎么验证的、分支和合并请求链接、还剩什么。按守则的说话风格，简短。
- 运行中可能收到“[追加指令]”，按它调整。
- 派子代理时按子活儿挑模型：查找、汇总、机械改动用 haiku，常规编码和测试用 sonnet，难的设计和排查才用 opus。

任务书：
{t['brief']}"""

def run(tid):
    """后台单元的入口：跑一轮或几轮 Claude，把进展、提问、结果写成事件。"""
    t = load(tid)
    o = t["origin"]
    try:
        if not t.get("session_started"):
            base = make_worktree(t)
            update(tid, base=base)
            if t["turn"] == 1: event(tid, "start", "")
            prompt, resume = first_prompt(load(tid), base), False
            early = inbox_take(tid)   # 批之前、开工之前就补充的话
            if early: prompt += "\n\n" + format_inbox(early)
        else:
            items = inbox_take(tid)
            prompt, resume = (format_inbox(items) if items else "[追加指令] 继续，把没做完的做完。"), True
        while True:
            t = load(tid)
            cmd = claude_args() + ["--output-format", "stream-json", "--verbose"]
            # 模型和思考档整个任务固定，续跑也一样，换了缓存就白写
            if t.get("model"): cmd += ["--model", t["model"]]
            if t.get("effort"): cmd += ["--effort", t["effort"]]
            cmd += ["--resume", t["session_id"]] if resume else ["--session-id", t["session_id"]]
            env = hook_env(t["requester"].get("owner"), False, o.get("chat_id", ""), o.get("channel", "feishu"), tid)
            final, tools_n = None, t.get("tools", 0)
            with open(os.path.join(tdir(tid), "stream.log"), "a") as raw:
                p = subprocess.Popen(cmd, cwd=t["worktree"], env=env, text=True,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=raw)
                update(tid, session_started=True)
                p.stdin.write(prompt); p.stdin.close()
                for line in p.stdout:
                    raw.write(line)
                    try: obj = json.loads(line)
                    except Exception: continue
                    if obj.get("type") == "assistant":
                        for b in (obj.get("message") or {}).get("content") or []:
                            if b.get("type") == "text" and obj.get("parent_tool_use_id") is None:
                                for l in b.get("text", "").splitlines():
                                    m = re.match(r"\s*\[进展\]\s*(.+)", l)
                                    if m: event(tid, "progress", m.group(1).strip())
                            elif b.get("type") == "tool_use":
                                tools_n += 1
                                kv = {"tools": tools_n, "last_tool": b.get("name"), "last_tool_at": time.time()}
                                if b.get("name") == "TodoWrite":
                                    kv["todos"] = (b.get("input") or {}).get("todos") or []
                                update(tid, **kv)
                    elif obj.get("type") == "result":
                        final = obj
                p.wait(); p.stdout.close()
            if final is None:
                raise RuntimeError(f"Claude 异常退出（rc={p.returncode}），详情看 state/tasks/{tid}/stream.log")
            text = final.get("result") or ""
            text = "\n".join(l for l in text.splitlines() if not re.match(r"\s*\[进展\]", l)).strip()
            denied = sorted({d.get("tool_name", "") for d in final.get("permission_denials") or []} - {""})
            update(tid, cost=round((load(tid).get("cost") or 0) + (final.get("total_cost_usd") or 0), 3))
            pending = inbox_take(tid)
            if pending:   # 这一轮结束前又来了追加指令：接着跑，不停下来
                prompt, resume = format_inbox(pending), True
                continue
            note = ("\n\n（有些操作被权限拦下了：" + "、".join(denied) + "）") if denied else ""
            if (load(tid) or {}).get("status") == "cancelled": return   # 跑完这一轮之前被取消了
            if re.search(r"^\s*\[提问\]", text, re.M):
                update(tid, status="waiting")
                event(tid, "question", re.sub(r"^\s*\[提问\]\s*", "", text, flags=re.M).strip() + note)
            elif final.get("is_error"):
                update(tid, status="failed"); event(tid, "failed", (text or final.get("subtype", "")) + note)
            else:
                update(tid, status="done", finished=time.time()); event(tid, "done", text + note)
            return
    except Exception as e:
        if (load(tid) or {}).get("status") == "cancelled": return
        update(tid, status="failed")
        event(tid, "failed", str(e)[-500:])

def remove_worktree(t):
    r = git(t["repo"], "worktree", "remove", t["worktree"])
    return r.returncode == 0, r.stderr.strip()[-200:]

# ---------- 建草稿合并请求：GitHub 走 gh，Codeup 走 OpenAPI。凭据只在本进程里读，不打印；只建草稿，不合并 ----------
CODEUP_TOKEN = T.get("codeup_token", "~/.config/codeup/token")
CODEUP_API = "https://openapi-rdc.aliyuncs.com/oapi/v1/codeup/organizations"

def mr_cmd(t, base=""):
    tg = t.get("target") or (base.split("/", 1)[1] if base.startswith("origin/") else "")
    return f"python3 {os.path.abspath(__file__)} mr --title '<标题>' --body-file <说明文件>" + (f" --target {tg}" if tg else "")

def _api(method, url, body=None):
    import urllib.request
    tok = open(X(CODEUP_TOKEN)).read().strip()
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"x-yunxiao-token": tok, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Codeup 接口 {e.code}：{e.read().decode(errors='replace')[:300]}")

def create_mr(argv):
    import argparse, urllib.parse
    ap = argparse.ArgumentParser(prog="tasks.py mr", description="在当前 git 工作树里，为当前分支建草稿合并请求")
    ap.add_argument("--title", required=True); ap.add_argument("--body-file"); ap.add_argument("--body", default="")
    ap.add_argument("--target", help="目标分支，默认仓库的默认分支")
    a = ap.parse_args(argv)
    body = open(a.body_file).read() if a.body_file else a.body
    branch = git(".", "branch", "--show-current").stdout.strip()
    if not branch: sys.exit("当前不在分支上")
    if os.environ.get("FCB_OWNER") != "1" and not branch.startswith("bot/"):
        sys.exit(f"不是{OWNER_NAME}本人触发的会话，只能从 bot/ 开头的分支建合并请求（当前 {branch}）")
    if git(".", "ls-remote", "--exit-code", "--heads", "origin", branch).returncode != 0:
        sys.exit(f"远端还没有 {branch}，先 git push -u origin {branch}")
    url = git(".", "remote", "get-url", "origin").stdout.strip()
    m = re.match(r"(?:https://|git@)([^/:]+)[/:](.+?)(?:\.git)?/?$", url)
    if not m: sys.exit("认不出远端地址")
    host, path = m.group(1).split("@")[-1], m.group(2)
    if host == "github.com":
        cmd = ["gh", "pr", "create", "--draft", "--head", branch, "--title", a.title, "--body", body or a.title]
        if a.target: cmd += ["--base", a.target]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print((r.stdout + r.stderr).strip()); sys.exit(r.returncode)
    if host != "codeup.aliyun.com": sys.exit(f"{host} 还不支持自动建合并请求，把分支名告诉派活人")
    org = path.split("/")[0]
    repo = _api("GET", f"{CODEUP_API}/{org}/repositories/{urllib.parse.quote(path, safe='')}")
    rid = repo.get("id")
    if not rid: sys.exit("查不到仓库")
    target = a.target or repo.get("defaultBranch") or "main"
    if target == branch: sys.exit("源分支和目标分支一样")
    r = _api("POST", f"{CODEUP_API}/{org}/repositories/{rid}/changeRequests",
             {"title": a.title, "description": body or a.title, "sourceBranch": branch, "targetBranch": target,
              "sourceProjectId": rid, "targetProjectId": rid, "workInProgress": True})
    print(f"草稿合并请求 !{r.get('localId')}：{branch} → {target}\n{r.get('detailUrl') or ''}")

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "run":
        run(int(sys.argv[2]))
    elif len(sys.argv) >= 2 and sys.argv[1] == "mr":
        create_mr(sys.argv[2:])
    else:
        sys.exit("用法：python3 tasks.py run <id>（由 bridge 启动）；python3 tasks.py mr --title T [--body-file F] [--target 分支]")
