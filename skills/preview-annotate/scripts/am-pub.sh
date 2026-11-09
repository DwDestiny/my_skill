#!/usr/bin/env bash
# answer-me-with-html 页面的匿名链接：am serve 加 Cloudflare 快速隧道
# 用法：
#   am-pub.sh ensure [端口]      没在运行或链接打不开时重启，打印公开链接的地址。已在运行就直接打印
#   am-pub.sh status             查看进程、地址、页面数与回复数
#   am-pub.sh replies [页面文件名] 打印页面上保存的回复和标注（新的在前）
#   am-pub.sh stop               停止 am serve 和隧道。已发出的链接立即失效
# ensure 之后，`am render`（输出到默认的 pages/ 目录）会多打印一行 `link: https://…`，那就是给用户的链接。
# Input: PATH 里的 node、cloudflared、curl；answer-me-with-html skill 的 scripts/am.mjs（或环境变量 AM_MJS）
# Output: 后台的 am serve 与 cloudflared 进程；~/.answer-me-with-html/pub/ 里的 pid、日志、url
# Pos: preview-annotate skill 里发布 answer-me-with-html 页面的入口脚本，智能体按 SKILL.md 第 6 节调用
set -euo pipefail

AM_HOME="${AM_HOME:-$HOME/.answer-me-with-html}"
work="$AM_HOME/pub"
secret="$AM_HOME/serve-secret"

node_bin() {
  if command -v node >/dev/null 2>&1; then command -v node; return; fi
  local n; n="$(ls -d "$HOME"/.nvm/versions/node/*/bin/node 2>/dev/null | sort -V | tail -1)"
  [ -n "$n" ] || { echo "找不到 node" >&2; exit 1; }
  echo "$n"
}

am_mjs() {
  local c
  for c in "${AM_MJS:-}" "$HOME/.claude/skills/answer-me-with-html/scripts/am.mjs" "$HOME/.agents/skills/answer-me-with-html/scripts/am.mjs"; do
    [ -n "$c" ] && [ -f "$c" ] && { echo "$c"; return; }
  done
  echo "找不到 answer-me-with-html 的 am.mjs，先安装该 skill，或设置 AM_MJS" >&2; exit 1
}

alive() { [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }
port_busy() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

# am serve 对根路径回 "Not found"。隧道断了时 Cloudflare 回的是错误页，所以用这句判断整条链路是通的
healthy() { [ "$(curl -s -m 8 "$1/" 2>/dev/null || true)" = "Not found" ]; }

if command -v setsid >/dev/null 2>&1; then detach=(setsid nohup); else detach=(nohup); fi

stop_all() {
  local p
  for p in serve tunnel; do
    if alive "$work/$p.pid"; then kill "$(cat "$work/$p.pid")" 2>/dev/null || true; fi
    rm -f "$work/$p.pid"
  done
}

cmd="${1:-}"; shift || true
case "$cmd" in
  ensure)
    port="${1:-8765}"
    mkdir -p "$work"
    if alive "$work/serve.pid" && alive "$work/tunnel.pid" && [ -f "$work/url" ] && healthy "$(cat "$work/url")"; then
      cat "$work/url"; exit 0
    fi
    stop_all; sleep 0.5
    command -v cloudflared >/dev/null || { echo "缺少 cloudflared" >&2; exit 1; }
    if port_busy "$port"; then echo "端口 $port 已被别的程序占用，换一个端口：am-pub.sh ensure <端口>" >&2; exit 1; fi
    am="$(am_mjs)"
    # 先开隧道拿到地址，再用这个地址启动 am serve：am render 打印的 link 以它开头
    "${detach[@]}" cloudflared tunnel --no-autoupdate --url "http://127.0.0.1:$port" >"$work/tunnel.log" 2>&1 < /dev/null &
    echo $! >"$work/tunnel.pid"
    url=""
    for _ in $(seq 60); do
      url="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$work/tunnel.log" | head -1 || true)"
      [ -n "$url" ] && break; sleep 0.5
    done
    [ -n "$url" ] || { echo "隧道没有给出地址，见 $work/tunnel.log" >&2; stop_all; exit 1; }
    echo "$url" >"$work/url"
    # 密钥存在文件里：重启后旧链接的路径仍然有效，只是域名换成新的
    "${detach[@]}" "$(node_bin)" "$am" serve --port "$port" --public-url "$url" --secret-file "$secret" \
      >"$work/serve.log" 2>&1 < /dev/null &
    echo $! >"$work/serve.pid"
    for _ in $(seq 20); do port_busy "$port" && break; sleep 0.5; done
    alive "$work/serve.pid" || { echo "am serve 没有启动，见 $work/serve.log" >&2; stop_all; exit 1; }
    # 等隧道注册连接，再等几秒让 DNS 生效；过早查询会让本机缓存 NXDOMAIN
    for _ in $(seq 60); do grep -q 'Registered tunnel connection' "$work/tunnel.log" && break; sleep 0.5; done
    sleep 5
    ok=""
    for _ in $(seq 20); do healthy "$url" && { ok=1; break; }; sleep 3; done
    [ -n "$ok" ] || echo "警告：本机还打不开 $url，稍后再试；见 $work/tunnel.log" >&2
    echo "$url"
    ;;
  status)
    alive "$work/serve.pid" 2>/dev/null && echo "am serve：运行中" || echo "am serve：未运行"
    alive "$work/tunnel.pid" 2>/dev/null && echo "隧道：运行中" || echo "隧道：未运行"
    [ -f "$work/url" ] && echo "地址：$(cat "$work/url")"
    echo "页面：$(ls "$AM_HOME/pages" 2>/dev/null | grep -c '\.html$' || true) 个"
    echo "有回复或标注的页面：$(ls "$AM_HOME/serve-state" 2>/dev/null | grep -c '\.json$' || true) 个"
    ;;
  replies)
    "$(node_bin)" - "$AM_HOME/serve-state" "${1:-}" <<'JS'
const fs = require('fs'), path = require('path');
const [dir, only] = process.argv.slice(2);
let files = [];
try { files = fs.readdirSync(dir).filter((f) => f.endsWith('.json')).map((f) => path.join(dir, f)); } catch {}
const rows = files.map((f) => {
  try { return { mtime: fs.statSync(f).mtime, ...JSON.parse(fs.readFileSync(f, 'utf8')) }; } catch { return null; }
}).filter((r) => r && (!only || r.file === only)).sort((a, b) => b.mtime - a.mtime);
if (!rows.length) { console.log('没有保存的回复或标注'); process.exit(0); }
for (const r of rows) {
  console.log(`## ${r.file}（${r.mtime.toISOString()}）`);
  for (const k of ['reply', 'remark']) if (r[k] !== undefined) console.log(`${k}: ${JSON.stringify(r[k], null, 2)}`);
}
JS
    ;;
  stop)
    stop_all
    echo "已停止。页面仍在 $AM_HOME/pages"
    ;;
  *) sed -n '2,8p' "$0"; exit 1 ;;
esac
