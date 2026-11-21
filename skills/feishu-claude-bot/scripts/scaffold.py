#!/usr/bin/env python3
"""按 config.json 生成或更新一个 IM 机器人实例（飞书、企业微信，可同时启用）。

Input:  实例目录（里面要有 config.json，样例见 assets/templates/config.example.json）
Output: 在实例目录写 bridge.py、tasks.py、hooks/（含 hooks/git/ 钩子分发器）、rules.md、claude-settings.json、服务文件（Linux: systemd 用户服务；macOS: launchd plist）；
        启用企微时另写 wecom_gateway.mjs、package.json 并安装 @wecom/aibot-node-sdk
Pos:    feishu-claude-bot skill 的生成器
用法:   python3 scaffold.py <实例目录> [--rules] [--no-npm] [--confirm-cross-im]
        默认不覆盖已有 rules.md；加 --rules 才按模板重写。
        config.json 打开 cross_im_read 时，第一次生成要加 --confirm-cross-im（先把提醒给主人看、主人同意后再加）
"""
import json, os, platform, shutil, subprocess, sys, datetime

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(SKILL, "assets", "templates")
VERSION = next((l.split(":", 1)[1].strip().strip('"') for l in open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8")
                if l.strip().startswith("version:")), "unknown")
if len(sys.argv) < 2: sys.exit(__doc__)
INST = os.path.abspath(os.path.expanduser(sys.argv[1]))
CFG = json.load(open(os.path.join(INST, "config.json")))
HOME = os.path.expanduser("~")
X = lambda p: HOME + p[1:] if p.startswith("~") else p
CH = CFG.get("channels", {})
FEISHU_ON = CH.get("feishu", {}).get("enabled", True)
WECOM_ON = CH.get("wecom", {}).get("enabled", False)
need = ["name", "owner_name"] + (["owner_open_id", "bot_open_id"] if FEISHU_ON else [])
for k in need:
    if not CFG.get(k) or "（" in str(CFG[k]):
        sys.exit(f"config.json 的 {k} 还没填")
if WECOM_ON and (not CH["wecom"].get("owner_userid") or "（" in CH["wecom"]["owner_userid"]):
    sys.exit("config.json 的 channels.wecom.owner_userid 还没填（主人私聊机器人一句，在 logs/bridge.log 的 recv 行里看）")
if not (FEISHU_ON or WECOM_ON):
    sys.exit("config.json 的 channels 里至少启用一个渠道")
CROSS_WARN = """跨 IM 读取（cross_im_read）要打开：
  - 飞书里的会话能读主人的企微聊天记录，企微里的会话能用主人身份读飞书聊天记录。
  - 同事触发时也能读（identity.others = "bot_read_im" 时）。读到的内容会不会被转述到另一边，只靠守则和 Claude 自己把关，钩子不拦。
  - 不想让同事触发时跨读，把 identity.others 设为 "bot"。"""
CROSS_MARK = os.path.join(INST, "state", "cross_im_confirmed")
if CFG.get("cross_im_read") and FEISHU_ON and WECOM_ON and not os.path.exists(CROSS_MARK):
    if "--confirm-cross-im" not in sys.argv:
        sys.exit(CROSS_WARN + "\n主人确认后，加 --confirm-cross-im 重新运行。")
    os.makedirs(os.path.dirname(CROSS_MARK), exist_ok=True)
    open(CROSS_MARK, "w").write(datetime.datetime.now().isoformat(timespec="seconds") + " 主人已确认\n")
    print(CROSS_WARN + "\n已记录主人确认。")
if os.path.realpath(X(CFG.get("workdir", "~"))) == os.path.realpath(INST):
    sys.exit("workdir 不能是实例目录本身，否则会加载实例目录的 CLAUDE.md")

# 1. 代码和钩子：总是用模板覆盖，保证和 skill 同版本
for f in ("bridge.py", "tasks.py"):
    shutil.copy(os.path.join(T, f), os.path.join(INST, f))
os.makedirs(os.path.join(INST, "hooks", "git"), exist_ok=True)
for f in ("lark_identity.py", "private_guard.py", "wecom_guard.py", "git_guard.py", "task_inbox.py"):
    shutil.copy(os.path.join(T, "hooks", f), os.path.join(INST, "hooks", f))
# git 钩子分发器：非主人触发的会话把 core.hooksPath 指到 hooks/git，pre-push 只放行 bot/ 分支
gh = os.path.join(INST, "hooks", "git")
shutil.copy(os.path.join(T, "hooks", "git", "fcb-githook"), os.path.join(gh, "fcb-githook"))
os.chmod(os.path.join(gh, "fcb-githook"), 0o755)
for name in ("pre-commit", "prepare-commit-msg", "commit-msg", "post-commit", "pre-push", "pre-rebase",
             "post-checkout", "post-merge", "post-rewrite", "pre-merge-commit"):
    p = os.path.join(gh, name)
    if os.path.lexists(p): os.remove(p)
    os.symlink("fcb-githook", p)
if WECOM_ON:
    shutil.copy(os.path.join(T, "wecom_gateway.mjs"), os.path.join(INST, "wecom_gateway.mjs"))
    pkg = os.path.join(INST, "package.json")
    if not os.path.exists(pkg):
        json.dump({"private": True, "type": "module", "dependencies": {"@wecom/aibot-node-sdk": "1.0.7"}},
                  open(pkg, "w"), indent=2)
    if "--no-npm" not in sys.argv:
        r = subprocess.run(["npm", "install", "--omit=dev", "--no-audit", "--no-fund"], cwd=INST, capture_output=True, text=True)
        print("npm install:", "成功" if r.returncode == 0 else "失败\n" + r.stdout[-800:] + r.stderr[-800:])

# 2. 守则：已有就不动（实例的守则会按使用反馈改），--rules 才重写
rules = os.path.join(INST, CFG.get("rules_file", "rules.md"))
if not os.path.exists(rules) or "--rules" in sys.argv:
    persona = open(os.path.join(T, "rules", f"persona-{CFG.get('persona', 'work')}.md")).read()
    style_raw = open(os.path.join(T, "rules", f"style-{CFG.get('style', 'veteran')}.md")).read()
    label = style_raw.split("label:", 1)[1].split("-->", 1)[0].strip()
    style = style_raw.split("-->", 1)[1].strip()
    body = open(os.path.join(T, "rules", "base.md")).read()
    body = body.replace("{{PERSONA}}", persona.strip()).replace("{{STYLE}}", style)
    names = [n for n, on in (("飞书", FEISHU_ON), ("企业微信", WECOM_ON)) if on]
    heads = [h for h, on in (("`[飞书消息]`", FEISHU_ON), ("`[企微消息]`", WECOM_ON)) if on]
    wecom_sec = open(os.path.join(T, "rules", "channel-wecom.md")).read() if WECOM_ON else ""
    if FEISHU_ON:
        dm = f"`lark-cli im +messages-send --as bot --user-id {CFG['owner_open_id']} --text ...`"
    else:
        dm = "先用 `wecom-cli message aibot sessions list` 找到和主人的单聊，再 `wecom-cli message aibot send`"
    body = (body.replace("{{CHANNELS}}", "和".join(names)).replace("{{HEADS}}", "、".join(heads))
                .replace("{{WECOM_SECTION}}", wecom_sec).replace("{{OWNER_DM}}", dm.replace("主人", CFG["owner_name"]))
                )
    body = "\n".join(l.replace("{{FEISHU_ONLY}}", "") for l in body.split("\n") if FEISHU_ON or "{{FEISHU_ONLY}}" not in l)
    body = body.replace("{{PERSONA_LABEL}}", {"work": "工作分身", "personal": "私人助理"}[CFG.get("persona", "work")])
    body = body.replace("{{STYLE_LABEL}}", label).replace("{{DATE}}", datetime.date.today().isoformat()).replace("{{VERSION}}", VERSION)
    body = body.replace("{{NAME}}", CFG["name"]).replace("{{OWNER}}", CFG["owner_name"]).replace("{{OWNER_OPEN_ID}}", CFG.get("owner_open_id", ""))
    open(rules, "w").write(body)
    print("写了", rules)
else:
    print("保留已有", rules, "（加 --rules 按模板重写）")

# 3. Claude 设置：权限拒绝表 + 钩子
deny = [f"Read({X(p)}/**)" for p in CFG.get("private", {}).get("paths", []) if p.startswith(("~", "/")) and "(" not in p and "\\" not in p]
deny += [f"Edit({X(p)}/**)" for p in CFG.get("private", {}).get("paths", []) if p.startswith(("~", "/")) and "(" not in p and "\\" not in p]
deny += ["Read(**/.private/**)", "Edit(**/.private/**)", f"Read({HOME}/.lark-cli/**)", "Read(**/.env)", "Read(**/.env.*)",
         "Bash(lark-cli config:*)", "Bash(lark-cli auth:*)", "Bash(lark-cli profile:*)", "Bash(lark-cli event:*)",
         f"Read({HOME}/.config/wecom/**)", f"Edit({HOME}/.config/wecom/**)", "Bash(wecom-cli auth:*)",
         f"Read({HOME}/.config/gh/**)", "Bash(gh auth:*)",
         f"Edit({INST}/**)", f"Write({INST}/**)", f"Read({INST}/state/**)", f"Read({INST}/logs/**)", f"Read({INST}/config.json)"]
SLUG = CFG.get("service_name") or "fcb-" + os.path.basename(INST)
deny += [f"Bash(systemctl --user stop {SLUG}:*)", f"Bash(launchctl unload:*)"]
deny += CFG.get("deny_extra", [])
hook = lambda f: {"type": "command", "command": f"python3 {os.path.join(INST, 'hooks', f)}"}
settings = {"permissions": {"deny": list(dict.fromkeys(deny))},
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [hook("lark_identity.py"), hook("wecom_guard.py"),
                                                                  hook("git_guard.py")]},
                                     {"matcher": "Read|Grep|Glob|Bash|Edit|Write|NotebookEdit", "hooks": [hook("private_guard.py")]}],
                      # 长任务运行中把聊天里的补充指令塞进去；聊天会话里这个钩子直接退出
                      "PostToolUse": [{"matcher": "*", "hooks": [hook("task_inbox.py")]}]}}
json.dump(settings, open(os.path.join(INST, "claude-settings.json"), "w"), ensure_ascii=False, indent=2)

# 4. 服务文件
os.makedirs(os.path.join(INST, "logs"), exist_ok=True)
slug = SLUG
path_env = ":".join(dict.fromkeys([os.path.dirname(shutil.which("lark-cli") or "/usr/local/bin/lark-cli"),
                                   os.path.dirname(shutil.which("node") or "/usr/local/bin/node"),
                                   os.path.dirname(shutil.which("claude") or "/usr/local/bin/claude"),
                                   "/usr/local/bin", "/usr/bin", "/bin"]))
if platform.system() == "Darwin":
    svc = os.path.join(INST, f"com.{slug}.plist")
    open(svc, "w").write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.{slug}</string>
  <key>ProgramArguments</key><array><string>/usr/bin/python3</string><string>{INST}/bridge.py</string></array>
  <key>WorkingDirectory</key><string>{INST}</string>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>{path_env}</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardErrorPath</key><string>{INST}/logs/launchd.err</string>
</dict></plist>
""")
    print(f"服务文件：{svc}\n安装：ln -sf {svc} ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.{slug}.plist")
else:
    svc = os.path.join(INST, f"{slug}.service")
    open(svc, "w").write(f"""[Unit]
Description=Feishu Claude bot {CFG['name']}
After=network-online.target

[Service]
WorkingDirectory={INST}
ExecStart=/usr/bin/python3 {INST}/bridge.py
Environment=PATH={path_env}
Restart=always
RestartSec=5
KillSignal=SIGTERM
TimeoutStopSec=20

[Install]
WantedBy=default.target
""")
    print(f"服务文件：{svc}\n安装：ln -sf {svc} ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now {slug}"
          f"\n服务器上还要：sudo loginctl enable-linger $USER")
open(os.path.join(INST, ".gitignore"), "w").write("state/\nlogs/\ninbox/\nnode_modules/\n_tmp/\n__pycache__/\n")
print(f"完成（feishu-claude-bot v{VERSION}）。下一步：python3 bridge.py --cache-check 3")
