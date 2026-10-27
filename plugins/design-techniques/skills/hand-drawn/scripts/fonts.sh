#!/usr/bin/env bash
# Input: 输出目录、若干 HTML/JS 文件；可选 FONT_SRC（已有字体原件的目录）、FONT_CACHE（下载缓存目录）、PY（带 fontTools+brotli 的 python）
# Output: <输出目录>/marker.woff2（霞鹜漫黑 v1.004 子集）、hand.woff2（小赖 v3.126 子集）、OFL-marker.txt、OFL-xiaolai.txt；打印字数与大小
# Pos: hand-drawn 手法的字体脚本（运行）。改了页面文字（包括 JS 字符串和 canvas fillText 的字）就重跑
#
# 用法：bash fonts.sh <输出目录> <页面.html> [更多 .html/.js ...]
#   FONT_SRC=<目录>  先在这里找 LXGWMarkerGothic-Regular.ttf、Xiaolai-Regular.ttf、OFL*.txt（递归），找不到才下载
#   FONT_CACHE=<目录> 下载缓存，默认 ./_tmp/hand-drawn-fonts
set -euo pipefail
OUT="${1:?用法：fonts.sh <输出目录> <页面.html> [更多文件]}"; shift
[ "$#" -ge 1 ] || { echo "至少给一个 HTML/JS 文件" >&2; exit 2; }
PY="${PY:-python3}"
CACHE="${FONT_CACHE:-./_tmp/hand-drawn-fonts}"
MARKER_URL="https://github.com/lxgw/LxgwMarkerGothic/releases/download/v1.004/LxgwMarkerGothic-v1.004.zip"
HAND_URL="https://github.com/lxgw/kose-font/releases/download/v3.126/Xiaolai-Regular.ttf"
MARKER_OFL="https://raw.githubusercontent.com/lxgw/LxgwMarkerGothic/main/OFL.txt"
HAND_OFL="https://raw.githubusercontent.com/lxgw/kose-font/master/OFL.txt"

"$PY" -I -c "import fontTools, brotli" 2>/dev/null || { echo "缺 fontTools 或 brotli：$PY -m pip install fonttools brotli" >&2; exit 1; }
mkdir -p "$OUT" "$CACHE"

# 找一个文件：先 FONT_SRC，再缓存
find_one() { local name="$1" d; for d in "${FONT_SRC:-}" "$CACHE"; do [ -n "$d" ] && [ -d "$d" ] || continue; find "$d" -type f -name "$name" -print -quit; done | head -n 1; }

MARKER_TTF="$(find_one LXGWMarkerGothic-Regular.ttf)"
if [ -z "$MARKER_TTF" ]; then
  echo "下载霞鹜漫黑 v1.004 …"
  mkdir -p "$CACHE/marker"; curl -fL --retry 2 -o "$CACHE/marker/marker.zip" "$MARKER_URL"
  # 本机可能没有 unzip，用 python 解压
  "$PY" -I -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$CACHE/marker/marker.zip" "$CACHE/marker/x"
  MARKER_TTF="$(find "$CACHE/marker/x" -path '*fonts/ttf/*' -name LXGWMarkerGothic-Regular.ttf -print -quit)"
fi
HAND_TTF="$(find_one Xiaolai-Regular.ttf)"
if [ -z "$HAND_TTF" ]; then
  echo "下载小赖 v3.126（约 22 MB）…"
  mkdir -p "$CACHE/xiaolai"; curl -fL --retry 2 -o "$CACHE/xiaolai/Xiaolai-Regular.ttf" "$HAND_URL"
  HAND_TTF="$CACHE/xiaolai/Xiaolai-Regular.ttf"
fi

# 许可证随子集一起发：缺了就下载
[ -f "$OUT/OFL-marker.txt" ] || { f="$(dirname "$MARKER_TTF")/../../OFL.txt"; [ -f "$f" ] && cp "$f" "$OUT/OFL-marker.txt" || curl -fsSL -o "$OUT/OFL-marker.txt" "$MARKER_OFL"; }
[ -f "$OUT/OFL-xiaolai.txt" ] || { f="$(dirname "$HAND_TTF")/OFL.txt"; [ -f "$f" ] && cp "$f" "$OUT/OFL-xiaolai.txt" || curl -fsSL -o "$OUT/OFL-xiaolai.txt" "$HAND_OFL"; }

# 取字：扫全部文件的全部字符（HTML 正文、JS 字符串、canvas 里写的字都在源码里），再补常用标点与数字
CHARS="$(mktemp)"; trap 'rm -f "$CHARS"' EXIT
"$PY" -I -c "
import sys
s=set('0123456789 ↓→←↑，。：；、？！·（）“”')
for p in sys.argv[2:]: s|=set(open(p,encoding='utf-8').read())
s={c for c in s if c.isprintable()}
open(sys.argv[1],'w',encoding='utf-8').write(''.join(sorted(s)))
print('字数', len(s))
" "$CHARS" "$@"

for pair in "marker:$MARKER_TTF" "hand:$HAND_TTF"; do
  name="${pair%%:*}"; src="${pair#*:}"
  "$PY" -I -m fontTools.subset "$src" --text-file="$CHARS" --flavor=woff2 --output-file="$OUT/$name.woff2" --layout-features='*' --no-hinting
done
ls -l "$OUT"/*.woff2 | awk '{printf "%s %d KB\n", $NF, $5/1024}'
