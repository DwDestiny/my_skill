#!/usr/bin/env python3
"""飞书机器人桥接：飞书消息 -> 本机 Claude Code 会话 -> 飞书回复。

Input:  同目录 config.json；lark-cli event consume im.message.receive_v1 --as bot 的 NDJSON 事件流
Output: 用机器人身份回复原消息；会话映射 state/sessions.json；日志 logs/bridge.log
Pos:    实例目录里唯一的服务进程，由 systemd 用户服务或 launchd 常驻
功能:   私聊全收；群里只收 @ 机器人的；旁听白名单群（主人在群里发 “@机器人 /旁听” 开关）不 @ 也读，由 Claude 决定插不插话
用法:   python3 bridge.py                 # 常驻服务
        python3 bridge.py --cache-check 3 # 用服务同款参数开 3 个新会话，检查缓存是否跨会话命中
来源:   feishu-claude-bot skill 的 assets/templates/bridge.py
"""
import json, os, re, subprocess, sys, threading, time, uuid, queue, logging, signal

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(ROOT, "config.json")
with open(CFG_PATH) as f:
    CFG = json.load(f)
X = os.path.expanduser
NAME = CFG.get("name", "AI 助手")
OWNER_OPEN_ID = CFG["owner_open_id"]
OWNER_NAME = CFG.get("owner_name", "主人")
BOT_OPEN_ID = CFG["bot_open_id"]
WORKDIR = X(CFG.get("workdir", "~"))          # 不要放在实例目录里，免得加载实例的 CLAUDE.md
ADD_DIRS = [X(d) for d in CFG.get("add_dirs", [])]
PERMISSION_MODE = CFG.get("permission_mode", "auto")
P2P_IDLE = CFG.get("p2p_idle_hours", 6) * 3600
GROUP_IDLE = CFG.get("group_idle_hours", 2) * 3600   # 群里（不在话题中）闲置多久开新会话
MAX_PARALLEL = CFG.get("max_parallel", 3)
CLAUDE_TIMEOUT = CFG.get("claude_timeout_min", 40) * 60
CTX = dict({"enabled": True, "max": 20, "topic_max": 50, "group_window_h": 2, "p2p_window_h": 24,
            "max_chars": 400, "read_as": "user"}, **CFG.get("context", {}))
PRIME_ON = CFG.get("prime", True)
DISABLE_MCP = CFG.get("disable_mcp", True)
EMOJI = CFG.get("processing_emoji", "OnIt")
NEW_CMDS = set(CFG.get("new_session_commands", ["/new", "/重来", "新话题"]))
RULES = os.path.join(ROOT, CFG.get("rules_file", "rules.md"))
SETTINGS = os.path.join(ROOT, "claude-settings.json")
STATE, LOGS = os.path.join(ROOT, "state"), os.path.join(ROOT, "logs")
MAX_REPLY_CHARS = 18000
STALE_SECONDS = 10 * 60           # 重启时补投的旧消息不处理
AMB = dict({"enabled": True, "poll_seconds": 40, "quiet_seconds": 25, "max_wait_seconds": 180, "max_batch": 30,
            "cooldown_min": 10, "rotate_turns": 40, "command": "/旁听"}, **CFG.get("ambient", {}))
AMBIENT_FILE = os.path.join(ROOT, "ambient.json")   # 旁听白名单：主人在群里用命令开关，默认空
AMB_SILENT = "[不回]"
PRIME = f"[会话开始] 这是{NAME}新会话的固定开场，不用做任何事，只回复“好”。"   # 改动会让缓存重写一次

os.makedirs(STATE, exist_ok=True); os.makedirs(LOGS, exist_ok=True)
logging.basicConfig(filename=os.path.join(LOGS, "bridge.log"), level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bridge")
lock = threading.Lock()
SESS_FILE, SEEN_FILE = os.path.join(STATE, "sessions.json"), os.path.join(STATE, "seen.json")

def load(path, default):
    try:
        with open(path) as f: return json.load(f)
    except Exception: return default

def save(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f: json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)

sessions = load(SESS_FILE, {})
seen = load(SEEN_FILE, [])
names = {OWNER_OPEN_ID: OWNER_NAME}
sem = threading.Semaphore(MAX_PARALLEL)
workers = {}

def lark(args, stdin=None, timeout=60):
    r = subprocess.run(["lark-cli", *args], input=stdin, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        log.warning("lark-cli %s failed: %s", args[:3], (r.stdout + r.stderr)[-500:])
    return r

def sender_name(open_id):
    if open_id in names: return names[open_id]
    name = open_id
    try:   # 机器人身份通常没有通讯录权限，用主人的用户身份只读查名字
        r = lark(["contact", "+get-user", "--user-id", open_id, "--as", "user", "--jq", ".data.user.name // .data.name"])
        v = r.stdout.strip().strip('"')
        if r.returncode == 0 and v and v != "null": name = v
    except Exception as e:
        log.warning("name lookup failed: %s", e)
    names[open_id] = name
    return name

def react(message_id):
    r = lark(["im", "reactions", "create", "--as", "bot", "--message-id", message_id,
              "--data", json.dumps({"reaction_type": {"emoji_type": EMOJI}})])
    try: return json.loads(r.stdout)["data"]["reaction_id"]
    except Exception: return None

def unreact(message_id, reaction_id):
    if reaction_id:
        lark(["api", "DELETE", f"/open-apis/im/v1/messages/{message_id}/reactions/{reaction_id}", "--as", "bot"])

def no_at_all(text):
    """不许 @所有人：把 <at user_id="all"> 之类换成普通文字。"""
    return re.sub(r'<at\s+(user_)?ids?\s*=\s*"?all"?\s*>.*?</at>', "@所有人", text)

def reply(ev, text, in_thread):
    text = text.strip() or "（空回复，再问一次？）"
    text = no_at_all(text)
    if len(text) > MAX_REPLY_CHARS:
        text = text[:MAX_REPLY_CHARS] + "\n\n……太长了，后面截掉了。"
    args = ["im", "+messages-reply", "--as", "bot", "--message-id", ev["message_id"], "--markdown", "-",
            "--idempotency-key", ("fcb-" + ev["message_id"])[:50]]
    if in_thread: args.append("--reply-in-thread")
    r = lark(args, stdin=text)
    if r.returncode != 0:   # markdown 失败时退回纯文本
        args[args.index("--markdown")] = "--text"
        r = lark(args, stdin=text)
    try: return json.loads(r.stdout)["data"]["message_id"]
    except Exception: return None

def session_key(ev):
    if ev.get("chat_type") == "p2p":
        return "p2p:" + ev["chat_id"]
    if in_topic(ev):                 # 话题里的消息：一个话题一个会话
        return "grp:" + ev["chat_id"] + ":" + ev["thread_id"]
    return "grp:" + ev["chat_id"]    # 群里直接发的：整个群一个会话，闲置 group_idle_hours 后换新

def in_topic(ev):
    return bool(ev.get("thread_id") and ev.get("root_id"))

def _ts(m):
    try: return time.mktime(time.strptime(m.get("create_time", ""), "%Y-%m-%d %H:%M"))
    except Exception: return 0

def fetch_context(ev, s):
    """取这条消息之前、本会话还没见过的前文。只补新增的，前文放在消息原文前、缓存前缀之后。"""
    if not CTX["enabled"]: return [], None
    seen_ids = set(s.get("ctx_ids", []))
    cur = ev["message_id"]
    as_id = CTX["read_as"]
    in_topic = bool(ev.get("thread_id") and ev.get("root_id"))
    if in_topic:
        args = ["im", "+threads-messages-list", "--thread", ev["thread_id"], "--order", "desc", "--page-size", "50"]
        limit, window = CTX["topic_max"], None
    else:
        args = ["im", "+chat-messages-list", "--chat-id", ev["chat_id"], "--order", "desc", "--page-size", "30"]
        limit = CTX["max"]
        window = 3600 * CTX["p2p_window_h" if ev.get("chat_type") == "p2p" else "group_window_h"]
    try:
        r = lark(args + ["--as", as_id, "--no-reactions"], timeout=30)
        msgs = json.loads(r.stdout)["data"].get("messages") or []
    except Exception as e:
        log.warning("context fetch failed: %s", e); return [], None
    cur_t = int(ev.get("create_time", "0")) / 1000 or time.time()
    floor = s.get("ctx_ts")          # 上次处理到的时间：后面的轮次只补这之后的新消息
    picked = []
    for m in msgs:   # 新到旧
        mid = m.get("message_id")
        if not mid or mid == cur or mid in seen_ids or m.get("deleted"): continue
        t = _ts(m)
        if t > cur_t + 60: continue
        if window and t and cur_t - t > window: break
        if floor and t and t < floor - 60: break
        picked.append(m)
        if len(picked) >= limit: break
    picked.reverse()
    have = seen_ids | {m.get("message_id") for m in picked} | {cur}
    root = ev.get("root_id") if in_topic else None          # 话题列表不含话题第一条
    rt = ev.get("reply_to") or ev.get("parent_id")           # 被引用的消息
    want = [i for i in dict.fromkeys([root, rt]) if i and i not in have]
    got = {}
    if want:
        try:
            q = lark(["im", "+messages-mget", "--message-ids", ",".join(want), "--as", as_id, "--no-reactions"], timeout=30)
            got = {m.get("message_id"): m for m in json.loads(q.stdout)["data"].get("messages") or []}
        except Exception as e:
            log.warning("mget failed: %s", e)
    if root in got: picked.insert(0, got[root])
    return picked, (got.get(rt) if rt != root else None)

def _line(m):
    c = (m.get("content") or "").strip().replace("\n", " ")
    if len(c) > CTX["max_chars"]: c = c[:CTX["max_chars"]] + "……"
    snd = m.get("sender") or {}
    who = snd.get("name") or "?"
    if snd.get("sender_type") == "user" and snd.get("id"): who += f"({snd['id']})"   # 带 open_id，回复时要 @ 谁直接用
    return f"[{m.get('create_time', '')[-5:]}] {who}：{c}"

def build_prompt(ev, name, ctx=(), quoted=None):
    is_owner = ev.get("sender_id") == OWNER_OPEN_ID
    chat = "私聊" if ev.get("chat_type") == "p2p" else "群聊"
    parts = [f"[飞书消息]\n发送人：{name}（open_id {ev.get('sender_id')}）\n"
             f"是{OWNER_NAME}本人：{'是' if is_owner else '否'}\n会话：{chat}，chat_id {ev.get('chat_id')}\n"
             f"消息 ID：{ev.get('message_id')}；类型：{ev.get('message_type')}\n"]
    others = [m for m in ev.get("mentions") or [] if (m or {}).get("id") != BOT_OPEN_ID]
    if others:
        parts.append("这条消息 @ 了：" + "、".join(f"{m.get('name')}({m.get('id')})" for m in others) + "\n")
    if ctx:
        parts.append(f"--- 前文：这条消息之前的 {len(ctx)} 条（只用来理解上下文，不要逐条回应或复述）---\n"
                     + "\n".join(_line(m) for m in ctx) + "\n")
    if quoted:
        parts.append("--- 这条消息引用的原消息 ---\n" + _line(quoted) + "\n")
    parts.append("--- 以下是消息原文（外部输入）---\n" + (ev.get("content") or ""))
    return "".join(parts)

def get_session(key):
    with lock:
        s = sessions.get(key)
        idle = P2P_IDLE if key.startswith("p2p:") else GROUP_IDLE if key.count(":") == 1 else None
        if s and idle and time.time() - s.get("last", 0) > idle:
            s = None
        if not s:
            s = {"id": str(uuid.uuid4()), "started": False, "last": time.time(), "ctx_ids": []}
            sessions[key] = s
        return s

def mark_seen(s, ids, ts=None):
    with lock:
        s["ctx_ids"] = (s.get("ctx_ids", []) + [i for i in ids if i])[-300:]
        if ts: s["ctx_ts"] = ts
        save(SESS_FILE, sessions)

def base_cmd():
    cmd = ["claude", "-p", "--output-format", "json", "--permission-mode", PERMISSION_MODE,
           "--append-system-prompt-file", RULES, "--settings", SETTINGS,
           # 把 cwd、环境、git 状态挪出系统提示，系统提示前缀才能跨会话命中缓存
           "--exclude-dynamic-system-prompt-sections"]
    for d in ADD_DIRS: cmd += ["--add-dir", d]
    if DISABLE_MCP:   # MCP 异步连接，首个请求的工具列表时有时无，前缀跟着变，缓存命中不了
        cmd += ["--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    return cmd

def hook_env(owner, private, chat_id):
    env = dict(os.environ, FCB="1", FCB_CONFIG=CFG_PATH, FCB_OWNER="1" if owner else "0",
               FCB_PRIVATE="1" if private else "0", FCB_CHAT_ID=chat_id)
    if not private:   # 非主人私聊：不读不写自动记忆
        env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    return env

def prime(sid):
    """新会话先发固定开场白：会话开头的上下文（CLAUDE.md、skill 清单等）跟着固定内容进缓存，下一个新会话直接命中。"""
    return subprocess.run(base_cmd() + ["--session-id", sid], input=PRIME, capture_output=True, text=True,
                          timeout=300, cwd=WORKDIR, env=hook_env(False, False, ""))

def run_claude(key, s, prompt, owner, private, chat_id, quiet=False):
    with lock: sid, started = s["id"], s["started"]
    if not started and PRIME_ON:
        pr = prime(sid)
        if pr.returncode == 0: started = True
        else: log.warning("prime failed: %s", (pr.stdout + pr.stderr)[-500:])
    cmd = base_cmd() + (["--resume", sid] if started else ["--session-id", sid])
    t0 = time.time()
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=CLAUDE_TIMEOUT,
                       cwd=WORKDIR, env=hook_env(owner, private, chat_id))
    log.info("claude %s rc=%s %.0fs", key, r.returncode, time.time() - t0)
    try: out = json.loads(r.stdout)
    except Exception: out = None
    if not out or (out.get("is_error") and not out.get("result")):
        log.error("claude failed: %s", (r.stdout + r.stderr)[-1500:])
        with lock:   # 丢掉会话映射，下一条消息开新会话；同一个 --session-id 不能重用
            sessions.pop(key, None); save(SESS_FILE, sessions)
        return None if quiet else "我这边卡壳了，再发一次我会开个新会话接着来。"
    u = out.get("usage") or {}
    log.info("cost %s session_total=$%.3f in=%s cache_read=%s cache_write=%s out=%s", key, out.get("total_cost_usd") or 0,
             u.get("input_tokens"), u.get("cache_read_input_tokens"), u.get("cache_creation_input_tokens"), u.get("output_tokens"))
    with lock:
        s["started"] = True; s["last"] = time.time(); s["id"] = out.get("session_id", sid)
        save(SESS_FILE, sessions)
    return out.get("result") or ""

def handle(ev):
    key = session_key(ev)
    name = sender_name(ev.get("sender_id", ""))
    text = (ev.get("content") or "").strip()
    in_thread = in_topic(ev)          # 默认引用原消息直接回在群里；原消息在话题里才回在话题里
    if ev.get("chat_type") == "p2p" and text in NEW_CMDS:
        with lock: sessions.pop(key, None); save(SESS_FILE, sessions)
        reply(ev, "好，翻篇了，新话题请讲。", False); return
    if AMB["enabled"] and ev.get("chat_type") != "p2p" and ev.get("sender_id") == OWNER_OPEN_ID:
        cmd = re.sub(r"@\S+\s*", "", text).strip()
        c = AMB["command"]
        if cmd in (c, c + " 开", c + " 关", c + " 状态"):
            reply(ev, ambient_cmd(ev["chat_id"], cmd), in_thread); return
    rid = react(ev["message_id"])
    try:
        with sem:
            owner = ev.get("sender_id") == OWNER_OPEN_ID
            s = get_session(key)
            ctx, quoted = fetch_context(ev, s)
            mark_seen(s, [m.get("message_id") for m in ctx] + [ev["message_id"], (quoted or {}).get("message_id")],
                      int(ev.get("create_time", "0")) / 1000 or time.time())
            log.info("context %s: %d msgs%s", key, len(ctx), " +quoted" if quoted else "")
            result = run_claude(key, s, build_prompt(ev, name, ctx, quoted), owner,
                                owner and ev.get("chat_type") == "p2p", ev.get("chat_id", ""))
    except subprocess.TimeoutExpired:
        with lock: sessions.pop(key, None); save(SESS_FILE, sessions)
        result = "这活儿超时了，我先停了。太大的活儿请回终端开个会话来做。"
    except Exception as e:
        log.exception("handle failed")
        result = f"出岔子了：{type(e).__name__}，请看日志。"
    out_id = reply(ev, result, in_thread)
    with lock: cur_s = sessions.get(key)
    if cur_s is not None: mark_seen(cur_s, [out_id])
    unreact(ev["message_id"], rid)

def worker(key, q):
    while True:
        ev = q.get()
        try: handle(ev)
        except Exception: log.exception("worker error")
        finally: q.task_done()

def should_handle(ev):
    """私聊全收；群聊只收明确 @ 了机器人的（@所有人 不算）。其他机器人的消息不收。"""
    if ev.get("sender_type") != "user": return False
    if ev.get("chat_type") == "p2p": return True
    return any((m or {}).get("id") == BOT_OPEN_ID for m in (ev.get("mentions") or []))

def dispatch(ev):
    if not should_handle(ev): return
    mid = ev.get("message_id")
    if not mid: return
    with lock:
        if mid in seen: return
        seen.append(mid); del seen[:-500]; save(SEEN_FILE, seen)
    try:
        if time.time() - int(ev.get("create_time", "0")) / 1000 > STALE_SECONDS:
            log.info("skip stale %s", mid); return
    except ValueError: pass
    key = session_key(ev)
    log.info("recv %s from %s in %s", mid, ev.get("sender_id"), key)
    with lock:
        q = workers.get(key)
        if q is None:
            q = queue.Queue(); workers[key] = q
            threading.Thread(target=worker, args=(key, q), daemon=True).start()
    q.put(ev)

# ---------- 旁听：白名单群不 @ 也读，攒一批交给 Claude 决定插不插话 ----------
# 用主人的用户身份定时拉消息，不开“读取群内所有消息”权限，非白名单群照旧收不到。
AMB_STATE = os.path.join(STATE, "ambient_state.json")
amb = load(AMB_STATE, {})         # chat_id -> {"seen": [...], "init": bool, "cool_until": ts, "turns": n}
amb_buf = {}                      # chat_id -> {"msgs": [...], "first": ts, "last": ts}
amb_lock = threading.Lock()       # 旁听同一时间只跑一个 Claude，不跟 @ 消息抢并发

def ambient_chats():
    return load(AMBIENT_FILE, {}).get("chats", {})

def ambient_init(chat_id):
    """开旁听时马上记下群里已有的消息（不处理），之后到的才算新消息。
    不能留到下一轮拉取再记：开启到下一轮之间发的消息会被当成旧消息吞掉。"""
    seen = []
    try:
        r = lark(["im", "+chat-messages-list", "--chat-id", chat_id, "--order", "desc", "--page-size", "30",
                  "--as", "user", "--no-reactions"], timeout=30)
        seen = [m.get("message_id") for m in _flatten(json.loads(r.stdout)["data"].get("messages") or []) if m.get("message_id")]
        ok = True
    except Exception as e:
        log.warning("ambient init %s failed: %s", chat_id, e); ok = False
    with lock:
        amb[chat_id] = {"seen": seen, "init": ok}

def ambient_cmd(chat_id, cmd):
    c = AMB["command"]
    data = load(AMBIENT_FILE, {"chats": {}})
    chats = data.setdefault("chats", {})
    if cmd == c + " 状态":
        return "这个群我在旁听，没 @ 我也会看，觉得该接话才接。" if chat_id in chats else "这个群没开旁听，只有 @ 我才说话。"
    turn_on = cmd != c + " 关" and not (cmd == c and chat_id in chats)
    if turn_on:
        chats[chat_id] = {"since": time.strftime("%Y-%m-%d %H:%M")}
        ambient_init(chat_id)
        msg = f"收到，这个群我开始旁听了。不 @ 我也看，有梗接梗，跟{OWNER_NAME}或者我有关的会搭话，其余时候不出声。关掉：@我 {c} 关"
    else:
        chats.pop(chat_id, None)
        msg = "好，这个群我不旁听了，@ 我才说话。"
    save(AMBIENT_FILE, data)
    log.info("ambient %s -> %s", chat_id, turn_on)
    return msg

def _flatten(msgs):
    for m in msgs:
        yield m
        for r in m.get("thread_replies") or []:
            yield r

def ambient_poll_once():
    now = time.time()
    chats = ambient_chats()
    for chat_id in chats:
        st = amb.setdefault(chat_id, {"seen": [], "init": False})
        try:
            r = lark(["im", "+chat-messages-list", "--chat-id", chat_id, "--order", "desc", "--page-size", "30",
                      "--as", "user", "--no-reactions"], timeout=30)
            msgs = list(_flatten(json.loads(r.stdout)["data"].get("messages") or []))
        except Exception as e:
            log.warning("ambient poll %s failed: %s", chat_id, e); continue
        seen_set = set(st["seen"])
        fresh = []
        for m in msgs:
            mid = m.get("message_id")
            if not mid or mid in seen_set: continue
            seen_set.add(mid); st["seen"].append(mid)
            if not st["init"]: continue                                   # 刚开旁听：之前的消息只记下，不处理
            snd = m.get("sender") or {}
            if m.get("deleted") or snd.get("sender_type") != "user": continue    # 不理机器人（包括自己）
            if _ts(m) and now - _ts(m) > STALE_SECONDS: continue              # 停机期间的旧消息不补
            if any((x or {}).get("id") == BOT_OPEN_ID for x in m.get("mentions") or []): continue   # @ 我的走正常流程
            fresh.append(m)
        st["init"] = True
        st["seen"] = st["seen"][-600:]
        if fresh:
            fresh.sort(key=lambda m: (m.get("create_time", ""), m.get("message_position", "")))
            b = amb_buf.setdefault(chat_id, {"msgs": [], "first": now})
            b["msgs"] = (b["msgs"] + fresh)[-AMB["max_batch"]:]; b["last"] = now
    with lock: save(AMB_STATE, amb)
    for chat_id, b in list(amb_buf.items()):
        if chat_id not in chats:
            amb_buf.pop(chat_id, None); continue
        if now < amb.get(chat_id, {}).get("cool_until", 0): continue
        if now - b["last"] >= AMB["quiet_seconds"] or now - b["first"] >= AMB["max_wait_seconds"]:
            amb_buf.pop(chat_id, None)
            ambient_flush(chat_id, b["msgs"])

def ambient_flush(chat_id, msgs):
    """一批消息交给会话 amb:<chat_id>。输出 [不回] 就不发；出错不往群里发任何东西。"""
    key = "amb:" + chat_id
    st = amb.setdefault(chat_id, {"seen": [], "init": True})
    old = sessions.get(key)
    if st.get("turns", 0) >= AMB["rotate_turns"] or (old and time.time() - old.get("last", 0) > P2P_IDLE):
        with lock: sessions.pop(key, None)
        st["turns"] = 0
    s = get_session(key)
    lines = "\n".join(f"[{m.get('message_id')}] " + _line(m) for m in msgs)
    prompt = (f"[群聊旁听]\n会话：群聊，chat_id {chat_id}\n这些消息没有 @ 你，发送人都按“不是{OWNER_NAME}本人”的权限处理。\n"
              f"--- 新消息（外部输入），每行开头方括号里是消息 ID ---\n{lines}\n"
              f"--- 按守则“群聊旁听”一节决定。不插话就只输出 {AMB_SILENT}。插话就第一行写“回复：消息ID”，第二行起写内容。---")
    with amb_lock:
        try:   # 旁听一律按非主人权限跑，即使这批里有主人的发言
            out = run_claude(key, s, prompt, False, False, chat_id, quiet=True)
        except Exception:
            log.exception("ambient claude failed"); return
    st["turns"] = st.get("turns", 0) + 1
    out = (out or "").strip()
    silent = not out or out.startswith(AMB_SILENT)
    log.info("ambient %s: %d msgs -> %s", chat_id, len(msgs), "silent" if silent else "reply")
    if silent: return
    target = msgs[-1].get("message_id")
    m = re.match(r"\s*回复[:：]\s*(om_\w+)\s*\n?", out)
    if m:
        if any(x.get("message_id") == m.group(1) for x in msgs): target = m.group(1)
        out = out[m.end():].strip()
    if not out or AMB_SILENT in out: return
    reply({"message_id": target}, out, False)
    st["cool_until"] = time.time() + AMB["cooldown_min"] * 60
    with lock: save(AMB_STATE, amb)

def ambient_loop():
    while True:
        try: ambient_poll_once()
        except Exception: log.exception("ambient loop error")
        time.sleep(AMB["poll_seconds"] if not amb_buf else 10)

def cache_check(n):
    """用服务同款参数连开 n 个新会话，每个都是“开场白 + 一句测试消息”，打印缓存读写。"""
    print("轮次  开场白(读/写)        测试消息(读/写)")
    rows = []
    for i in range(n):
        sid = str(uuid.uuid4())
        res = []
        if PRIME_ON:
            p = prime(sid)
            res.append(json.loads(p.stdout)["usage"])
        r = subprocess.run(base_cmd() + (["--resume", sid] if PRIME_ON else ["--session-id", sid]),
                           input=f"[缓存检查] 第 {i + 1} 轮，只回复“好”。", capture_output=True, text=True,
                           timeout=300, cwd=WORKDIR, env=hook_env(False, False, ""))
        res.append(json.loads(r.stdout)["usage"])
        rows.append(res)
        fmt = lambda u: f"{u.get('cache_read_input_tokens')}/{u.get('cache_creation_input_tokens')}"
        print(f"{i + 1:>3}   " + "    ".join(f"{fmt(u):<18}" for u in res), flush=True)
        time.sleep(5)
    first_w = rows[-1][0].get("cache_creation_input_tokens", 0)
    ok = all(r[0].get("cache_creation_input_tokens", 0) < 2000 for r in rows[1:])
    print("结论：" + ("正常。第 2 轮起开场白几乎不写缓存。" if ok else
                     f"异常。第 2 轮起开场白仍写 {first_w} token，按 references/cache.md 排查。"))
    return 0 if ok else 1

def main():
    # stdin 用管道保持打开：lark-cli 在不限时运行时把 stdin EOF 当退出信号
    p = subprocess.Popen(["lark-cli", "event", "consume", "im.message.receive_v1", "--as", "bot"],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    def pump_err():
        for line in p.stderr: log.info("[lark] %s", line.rstrip())
    threading.Thread(target=pump_err, daemon=True).start()
    def stop(*_): p.terminate()   # SIGTERM，让 lark-cli 正常收尾；不要 kill -9
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    if AMB["enabled"]:
        threading.Thread(target=ambient_loop, daemon=True).start()
    log.info("bridge started: %s", NAME)
    for line in p.stdout:
        line = line.strip()
        if not line: continue
        try: dispatch(json.loads(line))
        except Exception: log.exception("bad event: %s", line[:300])
    rc = p.wait()
    log.info("lark-cli exited rc=%s", rc)
    sys.exit(rc or 1)   # 交给 systemd / launchd 重启

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--cache-check":
        sys.exit(cache_check(int(sys.argv[2]) if len(sys.argv) > 2 else 3))
    main()
