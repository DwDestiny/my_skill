#!/usr/bin/env python3
"""按 config.json 生成或更新一个飞书机器人实例。

Input:  实例目录（里面要有 config.json，样例见 assets/templates/config.example.json）
Output: 在实例目录写 bridge.py、hooks/、rules.md、claude-settings.json、服务文件（Linux: systemd 用户服务；macOS: launchd plist）
Pos:    feishu-claude-bot skill 的生成器
用法:   python3 scaffold.py <实例目录> [--rules]   # 默认不覆盖已有 rules.md；加 --rules 才按模板重写
"""
import json, os, platform, shutil, sys, datetime

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(SKILL, "assets", "templates")
VERSION = next((l.split(":", 1)[1].strip().strip('"') for l in open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8")
                if l.strip().startswith("version:")), "unknown")
if len(sys.argv) < 2: sys.exit(__doc__)
INST = os.path.abspath(os.path.expanduser(sys.argv[1]))
CFG = json.load(open(os.path.join(INST, "config.json")))
HOME = os.path.expanduser("~")
X = lambda p: HOME + p[1:] if p.startswith("~") else p
for k in ("name", "owner_name", "owner_open_id", "bot_open_id"):
    if not CFG.get(k) or "（" in str(CFG[k]):
        sys.exit(f"config.json 的 {k} 还没填")
if os.path.realpath(X(CFG.get("workdir", "~"))) == os.path.realpath(INST):
    sys.exit("workdir 不能是实例目录本身，否则会加载实例目录的 CLAUDE.md")

# 1. 代码和钩子：总是用模板覆盖，保证和 skill 同版本
shutil.copy(os.path.join(T, "bridge.py"), os.path.join(INST, "bridge.py"))
os.makedirs(os.path.join(INST, "hooks"), exist_ok=True)
for f in ("lark_identity.py", "private_guard.py"):
    shutil.copy(os.path.join(T, "hooks", f), os.path.join(INST, "hooks", f))

# 2. 守则：已有就不动（实例的守则会按使用反馈改），--rules 才重写
rules = os.path.join(INST, CFG.get("rules_file", "rules.md"))
if not os.path.exists(rules) or "--rules" in sys.argv:
    persona = open(os.path.join(T, "rules", f"persona-{CFG.get('persona', 'work')}.md")).read()
    style_raw = open(os.path.join(T, "rules", f"style-{CFG.get('style', 'veteran')}.md")).read()
    label = style_raw.split("label:", 1)[1].split("-->", 1)[0].strip()
    style = style_raw.split("-->", 1)[1].strip()
    body = open(os.path.join(T, "rules", "base.md")).read()
    body = body.replace("{{PERSONA}}", persona.strip()).replace("{{STYLE}}", style)
    body = body.replace("{{PERSONA_LABEL}}", {"work": "工作分身", "personal": "私人助理"}[CFG.get("persona", "work")])
    body = body.replace("{{STYLE_LABEL}}", label).replace("{{DATE}}", datetime.date.today().isoformat()).replace("{{VERSION}}", VERSION)
    body = body.replace("{{NAME}}", CFG["name"]).replace("{{OWNER}}", CFG["owner_name"]).replace("{{OWNER_OPEN_ID}}", CFG["owner_open_id"])
    open(rules, "w").write(body)
    print("写了", rules)
else:
    print("保留已有", rules, "（加 --rules 按模板重写）")

# 3. Claude 设置：权限拒绝表 + 两个钩子
deny = [f"Read({X(p)}/**)" for p in CFG.get("private", {}).get("paths", []) if p.startswith(("~", "/")) and "(" not in p and "\\" not in p]
deny += [f"Edit({X(p)}/**)" for p in CFG.get("private", {}).get("paths", []) if p.startswith(("~", "/")) and "(" not in p and "\\" not in p]
deny += ["Read(**/.private/**)", "Edit(**/.private/**)", f"Read({HOME}/.lark-cli/**)", "Read(**/.env)", "Read(**/.env.*)",
         "Bash(lark-cli config:*)", "Bash(lark-cli auth:*)", "Bash(lark-cli profile:*)", "Bash(lark-cli event:*)",
         f"Edit({INST}/**)", f"Write({INST}/**)", f"Read({INST}/state/**)", f"Read({INST}/logs/**)", f"Read({INST}/config.json)"]
deny += [f"Bash(systemctl --user stop fcb-{os.path.basename(INST)}:*)", f"Bash(launchctl unload:*)"]
deny += CFG.get("deny_extra", [])
hook = lambda f: {"type": "command", "command": f"python3 {os.path.join(INST, 'hooks', f)}"}
settings = {"permissions": {"deny": list(dict.fromkeys(deny))},
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [hook("lark_identity.py")]},
                                     {"matcher": "Read|Grep|Glob|Bash|Edit|Write|NotebookEdit", "hooks": [hook("private_guard.py")]}]}}
json.dump(settings, open(os.path.join(INST, "claude-settings.json"), "w"), ensure_ascii=False, indent=2)

# 4. 服务文件
os.makedirs(os.path.join(INST, "logs"), exist_ok=True)
slug = "fcb-" + os.path.basename(INST)
path_env = ":".join(dict.fromkeys([os.path.dirname(shutil.which("lark-cli") or "/usr/local/bin/lark-cli"),
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

[Install]
WantedBy=default.target
""")
    print(f"服务文件：{svc}\n安装：ln -sf {svc} ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now {slug}"
          f"\n服务器上还要：sudo loginctl enable-linger $USER")
open(os.path.join(INST, ".gitignore"), "w").write("state/\nlogs/\n__pycache__/\n")
print(f"完成（feishu-claude-bot v{VERSION}）。下一步：python3 bridge.py --cache-check 3")
