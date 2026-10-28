#!/usr/bin/env bash
# 匿名预览 + 批注：静态服务与 Cloudflare 快速隧道
# 用法：
#   preview.sh start  <构建目录> <工作目录> [端口]   启动服务和隧道，打印公开链接
#   preview.sh reload <工作目录>                     只重启服务（链接不变，用于重新构建后）
#   preview.sh status <工作目录>                     查看进程与链接
#   preview.sh stop   <工作目录>                     停止服务和隧道
# 工作目录放在项目已被 Git 忽略的临时目录下。批注存为 <工作目录>/annotations.json
# Input: 构建目录（含 index.html）、工作目录、端口；PATH 里的 node、cloudflared、curl
# Output: 后台的 server.mjs 与 cloudflared 进程；工作目录里的 pid、日志、url、config、annotations.json
# Pos: 本 skill 的入口脚本，智能体按 SKILL.md 调用
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"

node_bin() {
  if command -v node >/dev/null 2>&1; then command -v node; return; fi
  local n; n="$(ls -d "$HOME"/.nvm/versions/node/*/bin/node 2>/dev/null | sort -V | tail -1)"
  [ -n "$n" ] || { echo "找不到 node" >&2; exit 1; }
  echo "$n"
}

alive() { [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }

# 端口上已有服务在监听时返回成功
port_busy() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

# 后台启动时脱离当前会话；macOS 没有 setsid，只用 nohup。
# 用数组直接启动，不包成函数：后台运行函数会多一层子 shell，pid 文件记下的就不是服务本身
if command -v setsid >/dev/null 2>&1; then detach=(setsid nohup); else detach=(nohup); fi

start_server() {
  local work="$1" dist="$2" port="$3"
  "${detach[@]}" "$(node_bin)" "$here/server.mjs" --dir "$dist" --store "$work/annotations.json" --port "$port" \
    >"$work/server.log" 2>&1 < /dev/null &
  echo $! >"$work/server.pid"
  # 本实例的进程必须还活着，避免把别的服务当成本实例
  for _ in $(seq 20); do
    alive "$work/server.pid" && curl -fs -o /dev/null "http://127.0.0.1:$port/" && return 0
    sleep 0.5
  done
  echo "服务没有启动，见 $work/server.log" >&2; exit 1
}

cmd="${1:-}"; shift || true
case "$cmd" in
  start)
    dist="$(cd "$1" && pwd)"; mkdir -p "$2"; work="$(cd "$2" && pwd)"; port="${3:-4192}"
    command -v cloudflared >/dev/null || { echo "缺少 cloudflared" >&2; exit 1; }
    if alive "$work/server.pid" || alive "$work/tunnel.pid"; then echo "已在运行，先 stop 或用 reload" >&2; exit 1; fi
    if port_busy "$port"; then echo "端口 $port 已被占用，换一个端口" >&2; exit 1; fi
    printf '%s\n%s\n' "$dist" "$port" >"$work/config"
    [ -f "$work/annotations.json" ] || echo '[]' >"$work/annotations.json"
    start_server "$work" "$dist" "$port"
    "${detach[@]}" cloudflared tunnel --no-autoupdate --url "http://127.0.0.1:$port" >"$work/tunnel.log" 2>&1 < /dev/null &
    echo $! >"$work/tunnel.pid"
    url=""
    for _ in $(seq 60); do
      url="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$work/tunnel.log" | head -1 || true)"
      [ -n "$url" ] && break; sleep 0.5
    done
    [ -n "$url" ] || { echo "隧道没有给出链接，见 $work/tunnel.log" >&2; exit 1; }
    echo "$url" >"$work/url"
    # 等隧道注册连接，再等几秒让 DNS 生效；过早查询会让本机缓存 NXDOMAIN
    for _ in $(seq 60); do grep -q 'Registered tunnel connection' "$work/tunnel.log" && break; sleep 0.5; done
    sleep 5
    ok=""
    for _ in $(seq 20); do curl -fs -m 8 -o /dev/null "$url/" && { ok=1; break; }; sleep 3; done
    [ -n "$ok" ] || echo "警告：本机还打不开链接，稍后再试；见 $work/tunnel.log" >&2
    echo "$url"
    ;;
  reload)
    work="$(cd "$1" && pwd)"; dist="$(sed -n 1p "$work/config")"; port="$(sed -n 2p "$work/config")"
    alive "$work/server.pid" && kill "$(cat "$work/server.pid")" && sleep 0.5
    start_server "$work" "$dist" "$port"
    cat "$work/url"
    ;;
  status)
    work="$(cd "$1" && pwd)"
    alive "$work/server.pid" && echo "服务：运行中" || echo "服务：未运行"
    alive "$work/tunnel.pid" && echo "隧道：运行中" || echo "隧道：未运行"
    [ -f "$work/url" ] && echo "链接：$(cat "$work/url")"
    echo "批注：$(grep -c '"comment"' "$work/annotations.json" 2>/dev/null || echo 0) 条"
    ;;
  stop)
    work="$(cd "$1" && pwd)"
    for p in server tunnel; do alive "$work/$p.pid" && kill "$(cat "$work/$p.pid")"; rm -f "$work/$p.pid"; done
    echo "已停止。批注仍在 $work/annotations.json"
    ;;
  *) sed -n '2,8p' "$0"; exit 1 ;;
esac
