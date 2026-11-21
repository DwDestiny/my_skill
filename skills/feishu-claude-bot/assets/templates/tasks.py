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
T = dict({"enabled": True, "root": "~/work/.bot-tasks", "max_running": 2, "approval_hours": 24, "heartbeat_min": 30,
          # 2.0 资源和质量的硬限制：每个任务的预算、全部任务每天的预算、多久没动静算卡住、验证没过最多返工几次
          "budget_usd": 15, "daily_budget_usd": 60, "stuck_min": 40, "verify_retries": 2, "verify_timeout_min": 20,
          "cloud": {}},
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

# ---------- 花费：每轮结束记一笔，按天汇总，超了当天不再开新一轮 ----------
def spend_add(tid, usd):
    if usd <= 0: return
    os.makedirs(STORE, exist_ok=True)
    with _Lock(os.path.join(STORE, ".lock")):
        with open(os.path.join(STORE, "spend.jsonl"), "a") as f:
            f.write(json.dumps({"day": time.strftime("%Y-%m-%d"), "task": tid, "usd": round(usd, 4)}) + "\n")

def spent_today():
    day, total = time.strftime("%Y-%m-%d"), 0.0
    try:
        with open(os.path.join(STORE, "spend.jsonl")) as f:
            for l in f:
                if l.strip():
                    r = json.loads(l)
                    if r.get("day") == day: total += r.get("usd") or 0
    except FileNotFoundError: pass
    return total

def over_daily():
    cap = T.get("daily_budget_usd") or 0
    return bool(cap) and spent_today() >= cap

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
    verify = field("验证")[:300]
    if verify in ("无", "没有", "不用", "-", "—") or verify.startswith("<") or "命令，" in verify: verify = ""   # 没写或照抄了模板
    ex = field("执行")
    ex = "cloud" if ("云" in ex and "本机" not in ex) else ""
    return head, {"repo": field("仓库"), "title": field("标题")[:80] or "未命名任务", "brief": brief,
                  "model": pick(field("模型"), MODELS), "effort": pick(field("思考"), EFFORTS), "target": target,
                  "verify": verify, "exec": ex}

def model_label(t):
    """给人看的模型说明，没指定就是默认。"""
    s = " · ".join(x for x in (t.get("model"), t.get("effort") and "思考 " + t["effort"]) if x) or "默认模型"
    return s + ("，云端执行" if t.get("exec") == "cloud" else "")

# ---------- 后台运行 ----------
def unit_name(t): return f"{SLUG}-task-{t['id']}-{t['turn']}"

def launch(tid):
    """开一轮后台运行（首次开工、提问后续跑、完成后追加都算一轮）。"""
    t = load(tid)
    t = update(tid, status="running", turn=t.get("turn", 0) + 1, launched=time.time(),
               started=t.get("started") or time.time(), held_note=False)
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
    if t.get("exec") == "cloud" and t.get("cloud"): return True   # 例程已建好，结果靠 cloud_poll 查分支，超时算中断
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

def verify_line(t):
    if not t.get("verify"): return "- 派活时没定验证命令：按仓库自己的测试验，结果写进总结。"
    return (f"- 验证命令：{t['verify']}。结束前自己先跑通。你说做完后，服务会在工作树里再跑一遍，"
            f"没过会把输出退回给你返工（最多 {T['verify_retries']} 次），再不过就按失败交回。")

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
{verify_line(t)}
- 派子代理时按子活儿挑模型：查找、汇总、机械改动用 haiku，常规编码和测试用 sonnet，难的设计和排查才用 opus。

任务书：
{t['brief']}"""

def run(tid):
    """后台单元的入口：跑一轮或几轮 Claude，把进展、提问、结果写成事件。"""
    t = load(tid)
    if t.get("exec") == "cloud": return run_cloud(tid)
    o = t["origin"]
    try:
        budget = T.get("budget_usd") or 0
        if budget and (t.get("cost") or 0) >= budget:
            update(tid, status="failed")
            event(tid, "failed", f"结论：BLOCKED（预算用完：本任务已花 {t.get('cost')} 美元，上限 {budget}）。要接着干，请{OWNER_NAME}在终端里调高 tasks.budget_usd。")
            return
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
            if budget:   # 这一轮最多再花多少（CLI 按单次调用算），用完就停，不会一轮烧穿
                cmd += ["--max-budget-usd", f"{max(0.5, budget - (t.get('cost') or 0)):.2f}"]
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
            total = final.get("total_cost_usd") or 0     # 会话累计值：--resume 也接着累计，不是这一轮单算
            prev = load(tid).get("cost") or 0
            if total > prev: spend_add(tid, total - prev)
            cost = round(max(prev, total), 3)
            update(tid, cost=cost)
            over = bool(budget) and cost >= budget
            if over or "budget" in (final.get("subtype") or ""):
                update(tid, status="failed")
                event(tid, "failed", f"结论：BLOCKED（预算用完：本任务已花 {cost} 美元，上限 {budget}）。停在这里，分支和会话都留着。\n\n{text}")
                return
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
                t = load(tid)
                if t.get("verify"):   # 验证闸门：服务自己跑派活时定的命令，任务说“做完了”不算数
                    ok, out = run_verify(t)
                    rnd = t.get("verify_round", 0)
                    if not ok and rnd < T["verify_retries"]:
                        update(tid, verify_round=rnd + 1)
                        prompt, resume = (f"[验证失败] 派活时定的验证命令没通过（第 {rnd + 1} 次退回）：{t['verify']}\n"
                                          f"输出末尾：\n{out}\n\n修好再结束这一轮。修不了就写清原因，用 [提问] 交回。"), True
                        continue
                    if not ok:
                        update(tid, status="failed", verify_round=0)
                        event(tid, "failed", f"结论：BLOCKED（返工 {rnd} 次后验证仍没过）\n验证命令：{t['verify']}\n"
                                             f"输出末尾：\n{out[-800:]}\n\n任务最后的总结：\n{text}{note}")
                        return
                    text = f"结论：PASS（服务复跑验证命令通过：{t['verify']}）\n\n{text}"
                else:
                    text = "结论：没定验证命令，服务没复核\n\n" + text
                update(tid, status="done", finished=time.time(), verify_round=0); event(tid, "done", text + note)
            return
    except Exception as e:
        if (load(tid) or {}).get("status") == "cancelled": return
        update(tid, status="failed")
        event(tid, "failed", str(e)[-500:])

# ---------- 验证闸门：命令不经 Claude 的工具调用，所以先用实例的 Bash 钩子预检一遍（不花 token） ----------
def guard_check(cmd, t):
    """返回拦截原因；放行返回 None。"""
    owner = bool(t["requester"].get("owner"))
    try:
        with open(SETTINGS) as f: groups = json.load(f).get("hooks", {}).get("PreToolUse", [])
    except Exception:
        return None if owner else "读不到钩子配置，非主人任务的验证命令不跑"
    o = t["origin"]
    env = hook_env(owner, False, o.get("chat_id", ""), o.get("channel", "feishu"), t["id"])
    data = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": t["worktree"]})
    for g in groups:
        m = g.get("matcher") or "*"
        if m != "*":
            try: hit = re.fullmatch(m, "Bash")
            except re.error: hit = None
            if not hit: continue
        for h in g.get("hooks", []):
            r = subprocess.run(h["command"], shell=True, input=data, capture_output=True, text=True, env=env, cwd=t["worktree"])
            if r.returncode == 2: return (r.stderr or "被护栏拦下").strip()[-300:]
    return None

def run_verify(t):
    """在工作树里跑验证命令。返回 (通过?, 输出末尾)。"""
    why = guard_check(t["verify"], t)
    if why: return False, "验证命令被护栏拦下：" + why
    o = t["origin"]
    env = hook_env(t["requester"].get("owner"), False, o.get("chat_id", ""), o.get("channel", "feishu"), t["id"])
    try:
        r = subprocess.run(["bash", "-c", t["verify"]], cwd=t["worktree"], env=env, capture_output=True, text=True,
                           timeout=T["verify_timeout_min"] * 60)
        return r.returncode == 0, (r.stdout + r.stderr).strip()[-1500:] or f"（没有输出，退出码 {r.returncode}）"
    except subprocess.TimeoutExpired:
        return False, f"超过 {T['verify_timeout_min']} 分钟没跑完"

# ---------- 云端执行：活儿在 Claude 官方云端的一次性例程里跑，不占本机；本机只查分支头（不花 token） ----------
CLOUD = T.get("cloud") or {}
CLOUD_MODELS = dict({"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}, **CLOUD.get("models", {}))

def github_slug(repo):
    url = git(repo, "remote", "get-url", "origin").stdout.strip()
    m = re.match(r"(?:https://|git@)github\.com[/:](.+?)(?:\.git)?/?$", url)
    return m.group(1) if m else ""

def cloud_ok(repo, owner):
    """不能上云的原因；能上云返回 None。云端没有本机的护栏钩子，所以只给主人本人派的 GitHub 仓库。"""
    if not CLOUD.get("environment_id"): return "实例没配云端环境（tasks.cloud.environment_id）"
    if not owner: return f"只有{OWNER_NAME}本人派的活能上云（云端没有本机的护栏）"
    if not github_slug(repo): return "云端只能拉 GitHub 仓库"
    return None

def cloud_prompt(t, start, extra=""):
    v = t.get("verify")
    check = (f"- 验证命令（必须通过才算做完）：{v}\n" if v else "- 做完跑仓库自带的测试，命令和结果写进提交正文。\n")
    return (f"[长任务 #{t['id']}] {t['title']}（云端执行，没人盯着，做完再说话）\n"
            f"派活人：{t['requester']['name']}（{OWNER_NAME}本人）\n"
            f"开工：git fetch origin，然后 git checkout -B {t['branch']} {start}。只在这个分支上干。\n"
            "- 先列计划再做。能自己定的不要问；必须由人拍板的，写进最后一次提交的正文，按“做不下去”收尾。\n"
            "- 这台机器是新的，依赖自己装（npm ci、pip install 等）。\n" + check +
            f"\n任务书：\n{t['brief']}\n" + (f"\n{extra}\n" if extra else "") +
            "\n## 收尾（必须）\n"
            f"- 只推送 {t['branch']}。不开合并请求，不合并，不推其他分支。\n"
            "- 最后一次提交的正文写报告：做了什么、怎么验证的（命令和结果数字）、还剩什么、要人拍板的问题。\n"
            "- 最后一次提交信息末尾单独一行写 Cloud-Run: done（做不下去写 Cloud-Run: stopped，并写原因和剩余工作），然后推送。\n"
            "- 没有可提交的改动时，用 git commit --allow-empty 带上这一行推送。\n")

def cloud_launch(t, prompt):
    """一次性的 haiku 会话调 RemoteTrigger 建例程并立刻触发（约 1 美分）。返回 (例程号, 云端会话号)。"""
    body = {"name": f"{SLUG} #{t['id']} {t['title']}"[:80], "enabled": False,
            "job_config": {"ccr": {"environment_id": CLOUD["environment_id"],
                "session_context": {"model": CLOUD_MODELS.get(t.get("model") or "sonnet", CLOUD_MODELS["sonnet"]),
                                    "sources": [{"git_repository": {"url": "https://github.com/" + github_slug(t["repo"])}}],
                                    "allowed_tools": ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]},
                "events": [{"data": {"uuid": str(uuid.uuid4()), "session_id": "", "type": "user", "parent_tool_use_id": None,
                                     "message": {"role": "user", "content": prompt}}}]}}}
    path = os.path.join(tdir(t["id"]), "cloud-body.json")
    with open(path, "w") as f: json.dump(body, f, ensure_ascii=False)
    ask = (f"Read the JSON file {path}. Call the RemoteTrigger tool with action create and body equal to that JSON, unchanged. "
           "Then call RemoteTrigger with action run and the trigger_id that create returned. "
           "Reply with exactly one line: TRIGGER=<trigger_id> SESSION=<session id from the run result, or none>. "
           "If a call fails, reply ERROR=<error text>.")
    r = subprocess.run(["claude", "-p", "--model", "haiku", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                        "--allowedTools", "Read,RemoteTrigger", "--output-format", "json", "--", ask],
                       capture_output=True, text=True, timeout=300, cwd=tdir(t["id"]))
    try: res = json.loads(r.stdout).get("result") or ""
    except Exception: res = (r.stdout + r.stderr)[-300:]
    m = re.search(r"TRIGGER=(\S+)\s+SESSION=(\S+)", res)
    if not m: raise RuntimeError("云端例程没建成：" + res[-300:])
    return m.group(1), m.group(2)

def run_cloud(tid):
    t = load(tid)
    c = t.get("cloud") or {}
    if c.get("since") and not c.get("closed"):   # 上一个例程还没交结果：不重复开（续做等它交了再开）
        update(tid, status="running"); return
    try:
        repo, br = t["repo"], t["branch"]
        git(repo, "fetch", "--quiet", "origin")
        head = git(repo, "ls-remote", "origin", "refs/heads/" + br).stdout.split()
        head = head[0] if head else ""
        if not t.get("session_started") or not head:
            tg = t.get("target")
            r = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
            start = "origin/" + tg if tg else (r.stdout.strip() if r.returncode == 0 else "origin/main")
            if t["turn"] == 1: event(tid, "start", "")
            prompt = cloud_prompt(t, start, format_inbox(inbox_take(tid)))
        else:   # 续做：例程跑完不能追加消息，新开一个例程，从分支头接着干
            start = "origin/" + br
            prompt = cloud_prompt(t, start, f"这是续做：分支 {br} 上已有前面的提交（头是 {head[:10]}），在它上面接着改。\n"
                                            + format_inbox(inbox_take(tid)))
        trig, sess = cloud_launch(t, prompt)
        update(tid, session_started=True, base=t.get("base") or start,
               cloud={"trigger": trig, "session": sess, "after": head, "since": time.time()})
    except Exception as e:
        update(tid, status="failed"); event(tid, "failed", str(e)[-500:])

def cloud_poll(tid):
    """查云端任务的分支头，看到 Cloud-Run 标记就收尾：建草稿合并请求，写完成事件。返回是否有了结论。"""
    t = load(tid); c = t.get("cloud") or {}
    repo, br = t["repo"], t["branch"]
    out = git(repo, "ls-remote", "origin", "refs/heads/" + br).stdout.split()
    head = out[0] if out else ""
    if not head or head == c.get("after"):
        lim = CLOUD.get("timeout_min", 180)
        if time.time() - c.get("since", time.time()) > lim * 60:
            update(tid, status="lost", cloud=dict(c, closed=True)); event(tid, "lost", f"云端 {lim} 分钟没交结果（例程 {c.get('trigger')}）")
            return True
        return False
    git(repo, "fetch", "--quiet", "origin", f"+refs/heads/{br}:refs/remotes/origin/{br}")
    msg = git(repo, "log", "-1", "--format=%B", head).stdout
    if "Cloud-Run: done" not in msg and "Cloud-Run: stopped" not in msg:
        return False                                    # 中途推送，还没做完
    body = re.sub(r"(?m)^(Cloud-Run:.*|Co-Authored-By:.*)$", "", msg).strip()
    if "Cloud-Run: stopped" in msg:
        update(tid, status="waiting", cloud=dict(c, after=head, closed=True))
        event(tid, "question", "云端做不下去，交回来了：\n" + body[-2500:])
        return True
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "mr", "--title", t["title"], "--body", body[:6000] or t["title"],
                        "--branch", br] + (["--target", t["target"]] if t.get("target") else []),
                       cwd=repo, capture_output=True, text=True, env=dict(os.environ, FCB_OWNER="1"))
    mr = (r.stdout + r.stderr).strip()[-400:]
    update(tid, status="done", finished=time.time(), cloud=dict(c, after=head, closed=True))
    event(tid, "done", f"结论：云端做完（验证见下面的报告，本机没复跑）\n\n{body[-3000:]}\n\n合并请求：{mr}")
    return True

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
    ap.add_argument("--branch", help="源分支，默认当前分支（云端任务没有本机工作树时用）")
    a = ap.parse_args(argv)
    body = open(a.body_file).read() if a.body_file else a.body
    branch = a.branch or git(".", "branch", "--show-current").stdout.strip()
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
