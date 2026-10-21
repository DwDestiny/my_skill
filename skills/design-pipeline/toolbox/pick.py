#!/usr/bin/env python3
"""选图页：把一个目录里的候选（PNG/JPG，或 cases.json 里的案例文字）放到一页上，用户排名、标不可用、写备注，提交写入 pick.jsonl。
用法：
  python3 toolbox/pick.py --dir <候选目录> [--title 标题] [--port 8790] [--out pick.jsonl]
  另开：cloudflared tunnel --url http://127.0.0.1:<port> --no-autoupdate   # 临时公网链接（trycloudflare），无需登录
  把 "https://<随机>.trycloudflare.com/?t=<口令>" 给用户；口令在启动时打印。只监听 127.0.0.1。
  用户提交后读 <out>，最后一行是最新一次：{"ranking":[...],"bad":[...],"notes":{...},"note":"..."}。
  收口后结束进程：fuser -k <port>/tcp（不要 pkill -f）。
约束：候选文件名就是 id；不要把私有资料放进候选目录，整个目录会被公开到隧道（带口令）。
2026-10-21 由 FDE 选板实验的临时服务器泛化而来。
"""
import json, os, sys, time, html, secrets, argparse, mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote
ap=argparse.ArgumentParser(); ap.add_argument('--dir',required=True); ap.add_argument('--title',default='候选'); ap.add_argument('--port',type=int,default=8790); ap.add_argument('--out',default=None)
A=ap.parse_args(); D=os.path.abspath(A.dir); OUT=A.out or os.path.join(D,'pick.jsonl'); TOKEN=secrets.token_urlsafe(9)
IDS=sorted(f for f in os.listdir(D) if f.lower().endswith(('.png','.jpg','.jpeg','.webp')))
PAGE='''<!doctype html><html lang=zh><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>%TITLE%</title>
<style>body{margin:0;background:#141414;color:#e8e8e8;font:15px/1.5 -apple-system,"PingFang SC","Noto Sans SC",sans-serif}
header{padding:16px 20px;border-bottom:1px solid #333}h1{font-size:18px;margin:0 0 4px}p{margin:4px 0;color:#aaa}
.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:14px;padding:16px 20px}
figure{margin:0;background:#1e1e1e;border-radius:8px;overflow:hidden;border:2px solid transparent}figure.r1{border-color:#f5b400}
img{width:100%;display:block;cursor:zoom-in}figcaption{padding:10px 12px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.id{font-weight:600}select,input[type=text],textarea{background:#111;color:#eee;border:1px solid #444;border-radius:6px;padding:6px 8px;font:inherit}
label.x{color:#f66}form.f{padding:16px 20px 40px;border-top:1px solid #333}textarea{width:min(700px,100%);height:90px}
button{background:#f5b400;color:#000;border:0;border-radius:8px;padding:10px 20px;font:600 15px/1 inherit;cursor:pointer;margin-top:10px}
dialog{max-width:96vw;background:#000;border:0;padding:0}dialog img{max-width:96vw;max-height:94vh;width:auto;cursor:zoom-out}</style>
<header><h1>%TITLE%</h1><p>点图放大。给最好的几张排名（1 最好，不必全排），不能用的勾"不可用"，备注随意。提交后对方立刻收到。</p></header>
<form class=f method=post action="/submit?t=%TOKEN%"><div class=g>%CELLS%</div>
<p>总备注（哪种感觉对、哪种不对，一两句就行）</p><textarea name=note></textarea><br><button>提交选择</button></form>
<dialog id=d onclick="this.close()"><img id=di></dialog>
<script>document.querySelectorAll('.g img').forEach(i=>i.onclick=()=>{di.src=i.src;d.showModal()});
document.querySelectorAll('select').forEach(s=>s.onchange=()=>{s.closest('figure').classList.toggle('r1',s.value=='1')});</script></html>'''
def cell(f):
    b=os.path.splitext(f)[0]; opts=''.join(f'<option value={i}>{i}</option>' for i in range(1,len(IDS)+1))
    return (f'<figure><img src="/img/{f}" loading=lazy><figcaption><span class=id>{html.escape(b)}</span>'
            f'<label>排名 <select name="rank_{b}"><option value="">—</option>{opts}</select></label>'
            f'<label class=x><input type=checkbox name="bad_{b}"> 不可用</label>'
            f'<input type=text name="note_{b}" placeholder="备注" size=22></figcaption></figure>')
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def send(self,code,ctype,body):
        self.send_response(code); self.send_header('Content-Type',ctype); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=self.path.split('?')[0]
        if path.startswith('/img/'):
            f=os.path.basename(unquote(path[5:]))
            if f in IDS: return self.send(200,mimetypes.guess_type(f)[0] or 'application/octet-stream',open(os.path.join(D,f),'rb').read())
        if path=='/' and f't={TOKEN}' in self.path:
            return self.send(200,'text/html; charset=utf-8',PAGE.replace('%TITLE%',html.escape(A.title)).replace('%TOKEN%',TOKEN).replace('%CELLS%',''.join(cell(f) for f in IDS)).encode())
        self.send_error(404)
    def do_POST(self):
        if not (self.path.startswith('/submit') and f't={TOKEN}' in self.path): return self.send_error(403)
        n=int(self.headers.get('Content-Length',0)); q=parse_qs(self.rfile.read(n).decode(),keep_blank_values=True)
        ids=[os.path.splitext(f)[0] for f in IDS]
        rec={'time':time.strftime('%Y-%m-%dT%H:%M:%S'),'ranking':sorted([b for b in ids if q.get(f'rank_{b}',[''])[0]],key=lambda b:int(q[f'rank_{b}'][0])),
             'bad':[b for b in ids if q.get(f'bad_{b}')],'notes':{b:q[f'note_{b}'][0] for b in ids if q.get(f'note_{b}',[''])[0].strip()},'note':q.get('note',[''])[0]}
        with open(OUT,'a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
        self.send(200,'text/html; charset=utf-8',f'<!doctype html><meta charset=utf-8><body style="background:#141414;color:#eee;font:16px sans-serif;padding:40px 20px">已收到：排名 {html.escape(" > ".join(rec["ranking"]) or "无")}；不可用 {html.escape(", ".join(rec["bad"]) or "无")}。可以关掉这页了。</body>'.encode())
print(f'候选 {len(IDS)} 张；本机地址 http://127.0.0.1:{A.port}/?t={TOKEN} ；结果写入 {OUT}',flush=True)
HTTPServer(('127.0.0.1',A.port),H).serve_forever()
