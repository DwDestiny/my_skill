// 预览服务：静态托管构建目录（SPA 回退），向 HTML 注入批注层，批注存本地 JSON
// 用法：node server.mjs --dir <构建目录> --store <annotations.json> [--port 4192]
// Input: 构建目录、批注文件路径、端口；同目录的 annot.js
// Output: 127.0.0.1:<端口> 上的 HTTP 服务；/__annot 接口读写批注文件
// Pos: preview.sh 启动的服务进程，Cloudflare 隧道把公开链接转发到这里
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const argv = process.argv.slice(2), args = {};
for (let i = 0; i < argv.length; i += 2) args[argv[i].replace(/^--/, '')] = argv[i + 1];
const here = path.dirname(fileURLToPath(import.meta.url));
const dist = path.resolve(args.dir || 'dist');
const store = path.resolve(args.store || 'annotations.json');
const port = Number(args.port || 4192);
if (!fs.existsSync(path.join(dist, 'index.html'))) { console.error(`缺少 ${dist}/index.html，先构建`); process.exit(1); }

const types = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.gif': 'image/gif', '.webp': 'image/webp', '.avif': 'image/avif', '.woff': 'font/woff', '.woff2': 'font/woff2',
  '.ico': 'image/x-icon', '.txt': 'text/plain', '.mp4': 'video/mp4', '.webm': 'video/webm', '.wasm': 'application/wasm',
};

const load = () => { try { return JSON.parse(fs.readFileSync(store, 'utf8')); } catch { return []; } };
const save = (list) => fs.writeFileSync(store, JSON.stringify(list, null, 2));
const send = (res, code, body, type = 'application/json') => {
  res.writeHead(code, { 'content-type': type, 'cache-control': 'no-store' });
  res.end(typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body));
};

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on('data', (c) => { size += c.length; if (size > 64 * 1024) { reject(new Error('too large')); req.destroy(); } else chunks.push(c); });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
  });
}

async function handle(req, res) {
  const url = new URL(req.url, 'http://x');
  // 每次请求重新读取批注层，改脚本后刷新页面即生效
  if (url.pathname === '/__annot.js') return send(res, 200, fs.readFileSync(path.join(here, 'annot.js')), 'text/javascript');
  if (url.pathname === '/__annot') {
    if (req.method === 'GET') return send(res, 200, load());
    try {
      const body = JSON.parse(await readBody(req));
      // 读完请求体再读文件，并发保存时不会用旧列表覆盖别人的批注
      const list = load();
      if (req.method === 'POST') {
        if (list.length >= 2000 || !String(body.comment || '').trim()) return send(res, 400, { error: 'bad' });
        const item = { ...body, id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), ts: new Date().toISOString() };
        list.push(item); save(list); return send(res, 200, item);
      }
      if (req.method === 'DELETE') { save(list.filter((a) => a.id !== body.id)); return send(res, 200, { ok: true }); }
    } catch { return send(res, 400, { error: 'bad' }); }
    return send(res, 405, { error: 'method' });
  }
  let rel;
  try { rel = decodeURIComponent(url.pathname); } catch { return send(res, 400, 'bad request', 'text/plain'); }
  let file = path.join(dist, rel);
  // 只允许构建目录内的文件；同前缀的兄弟目录（dist-x）也拒绝
  if (file !== dist && !file.startsWith(dist + path.sep)) return send(res, 403, 'forbidden', 'text/plain');
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!fs.existsSync(file)) {
    if (path.extname(url.pathname)) return send(res, 404, 'not found', 'text/plain');
    file = path.join(dist, 'index.html');
  }
  if (file.endsWith('.html')) {
    const html = fs.readFileSync(file, 'utf8');
    const tag = '<script src="/__annot.js" defer></script>';
    return send(res, 200, html.includes('</body>') ? html.replace('</body>', `${tag}</body>`) : html + tag, types['.html']);
  }
  const cache = file.includes(`${path.sep}assets${path.sep}`) ? 'public, max-age=31536000, immutable' : 'no-cache';
  res.writeHead(200, { 'content-type': types[path.extname(file).toLowerCase()] || 'application/octet-stream', 'cache-control': cache });
  fs.createReadStream(file).on('error', () => res.destroy()).pipe(res);
}

// 单个请求出错只返回 500，不让公开链接上的异常请求打垮服务
http.createServer((req, res) => handle(req, res).catch(() => {
  if (res.headersSent) res.destroy(); else send(res, 500, { error: 'server' });
})).on('error', (e) => { console.error(`服务启动失败：${e.message}`); process.exit(1); })
  .listen(port, '127.0.0.1', () => console.log(`preview on http://127.0.0.1:${port}  dist=${dist}  store=${store}`));
