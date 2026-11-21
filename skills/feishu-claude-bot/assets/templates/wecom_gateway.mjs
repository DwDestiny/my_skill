#!/usr/bin/env node
/**
 * 企业微信智能机器人长连接网关：bridge.py 的企微收发通道。
 *
 * Input:  stdin 每行一条 JSON 指令（bridge.py 写入）：
 *           {"op":"thinking","msgid":...}            在原消息下先出“思考中”（流式消息，未结束）
 *           {"op":"reply","msgid":...,"content":...}  结束这条流式消息，换成最终回复；流已过期就主动推送到原会话
 *           {"op":"send","chatid":...,"content":...}  主动推送 Markdown 到单聊（userid）或群（chatid）
 *         凭证：环境变量 FCB_WECOM_CREDENTIALS = "wecom-cli"（读 wecom-cli auth init 存的加密凭证）或 JSON 文件路径 {"bot_id","secret"}
 * Output: stdout 每行一条 JSON 事件：{"type":"message",...} 收到的消息；{"type":"ready"} 认证成功；
 *         {"type":"sent","ref","ok","error"} send 指令的结果
 *         stderr 写日志（bridge.py 转进 bridge.log）
 * Pos:    实例目录里由 bridge.py 启动的子进程；一个机器人同时只能有一条长连接，新连接会把旧的挤掉
 * 来源:   feishu-claude-bot skill 的 assets/templates/wecom_gateway.mjs，依赖 @wecom/aibot-node-sdk（官方）
 */
import AiBot, { generateReqId } from '@wecom/aibot-node-sdk';
import { createDecipheriv } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import readline from 'node:readline';

const STREAM_EXPIRED = 846608;          // 流式消息超过 6 分钟没更新，服务端不再接受（官方 OpenClaw 插件同样处理）
const THINKING = '<think></think>';     // 企微客户端显示为“思考中”动画
const MEDIA_DIR = process.env.FCB_WECOM_MEDIA_DIR || '';
const log = (...a) => process.stderr.write(a.join(' ') + '\n');
const out = (o) => process.stdout.write(JSON.stringify(o) + '\n');

function loadCredentials(src) {
  if (!src || src === 'wecom-cli') {
    // wecom-cli 的格式：~/.config/wecom/.encryption_key（base64 的 32 字节密钥），credentials.enc = nonce(12) || 密文 || tag(16)，AES-256-GCM
    // 这是 wecom-cli 的内部格式（1.3.x），变了就在这里报错，改用 JSON 凭证文件
    const dir = process.env.WECOM_CLI_CONFIG_DIR || join(homedir(), '.config', 'wecom');
    let key, buf;
    try {
      key = Buffer.from(readFileSync(join(dir, '.encryption_key'), 'utf8').trim(), 'base64');
      buf = readFileSync(join(dir, 'credentials.enc'));
    } catch (e) {
      throw new Error('读不到 wecom-cli 凭证（先运行 wecom-cli auth init；密钥只存在系统 keyring 时也读不到，改用 JSON 凭证文件）：' + e.message);
    }
    const d = createDecipheriv('aes-256-gcm', key, buf.subarray(0, 12));
    d.setAuthTag(buf.subarray(buf.length - 16));
    const plain = Buffer.concat([d.update(buf.subarray(12, buf.length - 16)), d.final()]).toString('utf8');
    const bot = JSON.parse(plain).bot;
    if (!bot?.id || !bot?.secret) throw new Error('wecom-cli 凭证里没有 bot id/secret，格式可能变了，改用 JSON 凭证文件');
    return { botId: bot.id, secret: bot.secret };
  }
  const j = JSON.parse(readFileSync(src, 'utf8'));
  return { botId: j.bot_id, secret: j.secret };
}

const cred = loadCredentials(process.env.FCB_WECOM_CREDENTIALS);
const ws = new AiBot.WSClient({
  ...cred,
  maxReconnectAttempts: -1,            // 默认 10 次就放弃；网络抖动后要一直重连
  logger: { debug() {}, info: (m) => log('[wecom]', m), warn: (m) => log('[wecom] WARN', m), error: (m) => log('[wecom] ERROR', m) },
});

const frames = new Map();               // msgid -> { frame, streamId, target, t }
setInterval(() => {                     // 一小时前的帧不再需要
  const old = Date.now() - 3600_000;
  for (const [k, v] of frames) if (v.t < old) frames.delete(k);
}, 600_000).unref();

function textOf(body) {
  const t = body.msgtype;
  if (t === 'text') return body.text?.content || '';
  if (t === 'voice') return body.voice?.content || '';      // 语音已由企微转成文字
  if (t === 'mixed') return (body.mixed?.msg_item || []).filter((i) => i.msgtype === 'text').map((i) => i.text?.content || '').join('\n');
  return '';
}

function quoteOf(q) {
  if (!q) return null;
  return { msgtype: q.msgtype, text: q.text?.content || q.voice?.content || textOf({ msgtype: q.msgtype, ...q }) || '' };
}

async function saveMedia(body) {
  // 图片、文件、视频的下载地址 5 分钟内有效，收到就落盘，把本地路径交给 Claude
  if (!MEDIA_DIR) return [];
  const items = [];
  if (body.image?.url) items.push(body.image);
  if (body.file?.url) items.push(body.file);
  if (body.video?.url) items.push(body.video);
  for (const i of body.mixed?.msg_item || []) if (i.msgtype === 'image' && i.image?.url) items.push(i.image);
  const paths = [];
  mkdirSync(MEDIA_DIR, { recursive: true });
  for (const [n, it] of items.entries()) {
    try {
      const { buffer, filename } = await ws.downloadFile(it.url, it.aeskey);
      const ext = (filename && filename.includes('.')) ? '' : (body.msgtype === 'image' || body.msgtype === 'mixed' ? '.png' : '');
      const p = join(MEDIA_DIR, `${body.msgid}-${n}-${(filename || 'file').replace(/[^\w.\u4e00-\u9fa5-]/g, '_')}${ext}`);
      writeFileSync(p, buffer);
      paths.push(p);
    } catch (e) {
      log('[wecom] media download failed', body.msgid, e.message);
    }
  }
  return paths;
}

ws.on('authenticated', () => out({ type: 'ready' }));
ws.on('message', async (frame) => {
  const b = frame.body || {};
  if (!b.msgid) return;
  const target = b.chattype === 'group' ? b.chatid : b.from?.userid;
  frames.set(b.msgid, { frame, streamId: generateReqId('stream'), target, t: Date.now(), streamed: false });
  const files = await saveMedia(b);
  out({
    type: 'message', msgid: b.msgid, chattype: b.chattype, chatid: b.chatid || '', userid: b.from?.userid || '',
    msgtype: b.msgtype, text: textOf(b), quote: quoteOf(b.quote), files,
    create_time: b.create_time || 0,
  });
});
ws.on('event.disconnected_event', () => {
  // 同一个机器人在别处建了新长连接，服务端会断开这一条，SDK 不再重连；退出让 bridge.py 稍后重启并在日志里报出来
  log('[wecom] ERROR 被新的长连接挤下线（同一个机器人在别处也连着？）');
  setTimeout(() => process.exit(3), 500);
});
ws.on('error', (e) => log('[wecom] ERROR', e?.message || e));

async function push(target, content) {
  if (!target) throw new Error('没有可推送的会话');
  return ws.sendMessage(target, { msgtype: 'markdown', markdown: { content } });
}

async function handle(cmd) {
  const f = cmd.msgid ? frames.get(cmd.msgid) : null;
  if (cmd.op === 'thinking') {
    if (!f) return;
    try { await ws.replyStream(f.frame, f.streamId, THINKING, false); f.streamed = true; }
    catch (e) { log('[wecom] thinking failed', cmd.msgid, e?.errcode || '', e?.message || e); }
    return;
  }
  if (cmd.op === 'reply') {
    if (!f) { log('[wecom] reply: 找不到原消息（重启过？）', cmd.msgid); return; }
    try {
      await ws.replyStream(f.frame, f.streamId, cmd.content, true);
      frames.delete(cmd.msgid);
      return;
    } catch (e) {
      const msg = String(e?.message || e);
      if (/ack timeout/i.test(msg)) {   // 发出去了但没等到回执：多半已送达，不再推送，免得发两遍
        log('[wecom] WARN reply 未收到回执，不重发', cmd.msgid);
        frames.delete(cmd.msgid);
        return;
      }
      log('[wecom] replyStream failed, 改为主动推送', cmd.msgid, msg);   // 常见：846608 流式消息已过期（>6 分钟）
    }
    try { await push(f.target, cmd.content); } catch (e) { log('[wecom] ERROR push failed', cmd.msgid, e?.message || e); }
    frames.delete(cmd.msgid);
    return;
  }
  if (cmd.op === 'send') {   // 主动推送（长任务进度、审批）：把结果回给 bridge 记日志
    try { await push(cmd.chatid, cmd.content); out({ type: 'sent', ref: cmd.ref || '', ok: true }); }
    catch (e) {
      log('[wecom] ERROR send failed', e?.errcode || '', e?.message || e);
      out({ type: 'sent', ref: cmd.ref || '', ok: false, error: String(e?.errcode || e?.message || e) });
    }
  }
}

readline.createInterface({ input: process.stdin }).on('line', (line) => {
  let cmd;
  try { cmd = JSON.parse(line); } catch { return; }
  handle(cmd).catch((e) => log('[wecom] ERROR', e?.message || e));
}).on('close', () => { ws.disconnect(); process.exit(0); });   // bridge.py 退出时 stdin 关闭，跟着退出
process.on('SIGTERM', () => { ws.disconnect(); process.exit(0); });
ws.connect();
