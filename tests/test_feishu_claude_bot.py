import uuid
import shutil
"""feishu-claude-bot 的文档、生成器和钩子测试。不连飞书，不调 Claude。

Input: skills/feishu-claude-bot/ 的 SKILL.md、agents/openai.yaml、scripts/scaffold.py、assets/templates/
Output: unittest 结果
Pos: 仓库级测试，运行 python3 tests/test_feishu_claude_bot.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1] / 'skills' / 'feishu-claude-bot'
TEMPLATES = SKILL_DIR / 'assets' / 'templates'
OWNER = 'ou_' + '0' * 32
BOT = 'ou_' + '1' * 32


class SkillDocsTest(unittest.TestCase):
    def test_frontmatter_name_matches_directory(self):
        content = (SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(content.startswith('---\nname: feishu-claude-bot\n'))

    def test_description_is_plain_yaml_scalar(self):
        content = (SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8')
        line = next(l for l in content.splitlines() if l.startswith('description: '))
        self.assertNotIn(': ', line[len('description: '):])

    def test_linked_files_exist(self):
        for doc in [SKILL_DIR / 'SKILL.md', SKILL_DIR / 'README.md']:
            text = doc.read_text(encoding='utf-8')
            for rel in re.findall(r'\]\(([^)#:]+)\)', text):
                self.assertTrue((SKILL_DIR / rel).exists(), f'{doc.name} 链接失效：{rel}')

    def test_every_style_has_label(self):
        styles = sorted(TEMPLATES.glob('rules/style-*.md'))
        self.assertGreaterEqual(len(styles), 4)
        for s in styles:
            self.assertTrue(s.read_text(encoding='utf-8').startswith('<!-- label: '), s.name)

    def test_version_consistent(self):
        skill = (SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8')
        m = re.search(r'^  version: "(\d+\.\d+\.\d+)"$', skill, re.M)
        self.assertIsNotNone(m, 'SKILL.md frontmatter 缺 metadata.version')
        v = m.group(1)
        self.assertIn(f'> v{v} ·', skill)
        self.assertIn(f'- {v}（', skill, '变更记录缺当前版本')
        self.assertIn(f'版本 {v}', (SKILL_DIR / 'README.md').read_text(encoding='utf-8'))
        root = (SKILL_DIR.parents[1] / 'README.md').read_text(encoding='utf-8')
        row = '| feishu-claude-bot | [`skills/feishu-claude-bot/`](skills/feishu-claude-bot/README.md) | v' + v + ' ·'
        self.assertEqual(root.count(row), 2, '仓库 README 中英目录表的版本号要和 SKILL.md 一致')

    def test_no_real_ids_in_skill(self):
        pat = re.compile(r'\b(ou|oc|cli)_[0-9a-f]{12,}\b')
        for f in SKILL_DIR.rglob('*'):
            if f.is_file() and f.suffix in ('.md', '.py', '.sh', '.json', '.yaml', '.yml'):
                self.assertIsNone(pat.search(f.read_text(encoding='utf-8')), f'{f} 含疑似真实 ID')


class ScaffoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.home = Path(cls.tmp.name) / 'home'
        cls.inst = cls.home / 'bots' / 'demo'
        cls.inst.mkdir(parents=True)
        cfg = json.loads((TEMPLATES / 'config.example.json').read_text(encoding='utf-8'))
        cfg.update(name='测试助理', owner_name='小王', owner_open_id=OWNER, bot_open_id=BOT, workdir='~/work')
        (cls.inst / 'config.json').write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
        cls.env = dict(os.environ, HOME=str(cls.home))
        cls.out = subprocess.run([sys.executable, str(SKILL_DIR / 'scripts' / 'scaffold.py'), str(cls.inst)],
                                 capture_output=True, text=True, env=cls.env)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_scaffold_succeeds(self):
        self.assertEqual(self.out.returncode, 0, self.out.stderr)
        for f in ['bridge.py', 'rules.md', 'claude-settings.json', 'hooks/lark_identity.py', 'hooks/private_guard.py',
                  'hooks/wecom_guard.py']:
            self.assertTrue((self.inst / f).exists(), f)

    def test_rules_rendered(self):
        rules = (self.inst / 'rules.md').read_text(encoding='utf-8')
        self.assertNotIn('{{', rules)
        self.assertIn('测试助理', rules)
        self.assertIn(OWNER, rules)
        self.assertIn('群聊旁听', rules)
        v = re.search(r'version: "([\d.]+)"', (SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8')).group(1)
        self.assertIn(f'skill v{v} 生成', rules)

    def test_rules_kept_on_rerun(self):
        p = self.inst / 'rules.md'
        orig = p.read_text(encoding='utf-8')
        try:
            p.write_text('自定义守则', encoding='utf-8')
            subprocess.run([sys.executable, str(SKILL_DIR / 'scripts' / 'scaffold.py'), str(self.inst)],
                           capture_output=True, text=True, env=self.env, check=True)
            self.assertEqual(p.read_text(encoding='utf-8'), '自定义守则')
        finally:
            p.write_text(orig, encoding='utf-8')

    def test_settings_wire_hooks_and_deny_instance(self):
        st = json.loads((self.inst / 'claude-settings.json').read_text(encoding='utf-8'))
        cmds = [h['command'] for m in st['hooks']['PreToolUse'] for h in m['hooks']]
        self.assertTrue(any('lark_identity.py' in c for c in cmds))
        self.assertTrue(any('private_guard.py' in c for c in cmds))
        self.assertTrue(any('wecom_guard.py' in c for c in cmds), '没启用企微也要挂：本机装了 wecom-cli，飞书会话也能调用')
        self.assertIn(f'Read(/{self.home}/.config/wecom/**)', st['permissions']['deny'])
        self.assertIn(f'Edit(/{self.inst}/**)', st['permissions']['deny'])
        # 绝对路径必须写成 //，单个 / 在 Claude Code 里是相对项目根，规则形同虚设
        for r in st['permissions']['deny']:
            m = re.match(r'(Read|Edit|Write)\((.*)\)$', r)
            if m and m.group(2).startswith('/'):
                self.assertTrue(m.group(2).startswith('//'), r)

    def test_rules_feishu_only_has_no_wecom_section(self):
        rules = (self.inst / 'rules.md').read_text(encoding='utf-8')
        self.assertNotIn('## 企业微信', rules)
        self.assertIn('lark-cli im +messages-send --as bot --user-id ' + OWNER, rules)

    def test_wecom_guard(self):
        o, m = {'FCB_OWNER': '0'}, {'FCB_OWNER': '1'}
        g = lambda env, c: self.bash('wecom_guard.py', env, c).returncode
        self.assertEqual(g(o, 'wecom-cli mail list'), 2)
        self.assertEqual(g(o, '$(which wecom-cli) doc get'), 2, '绕路调用也要拦')
        self.assertEqual(g(o, 'wecom-cli contact search x'), 0)
        self.assertEqual(g(o, "wecom-cli message aibot send --json '{}'"), 0)
        self.assertEqual(g(m, 'wecom-cli mail list'), 0)
        self.assertEqual(g(m, 'wecom-cli mail send --json x'), 2)
        self.assertEqual(g(m, 'wecom-cli message send --chat-id x'), 2, '不以主人名义发企微消息')
        self.assertEqual(g(m, 'cat ~/.config/wecom/credentials.enc'), 2)
        self.assertEqual(g(m, 'wecom-cli auth show'), 2)
        self.assertEqual(g(o, 'echo hi'), 0)
        self.assertEqual(g(o, 'rg -n wecom ~/work/app'), 0, '代码里出现 wecom 字样不拦')
        self.assertEqual(g(o, 'cat node_modules/@wecom/cli-linux-x64/bin/wecom mail'), 2)

    def test_cross_im_read_switch(self):
        cfgp = self.inst / 'config.json'
        orig = cfgp.read_text(encoding='utf-8')
        g = lambda tool, env, c: self.bash(tool, env, c).returncode
        fs = {'FCB_OWNER': '1', 'FCB_CHANNEL': 'feishu'}
        wx = {'FCB_OWNER': '1', 'FCB_CHANNEL': 'wecom'}
        read_fs = 'lark-cli im +chat-messages-list --chat-id oc_x --as user'
        read_wx = "wecom-cli chat messages list --json '{}'"
        try:
            self.assertEqual(g('wecom_guard.py', wx, read_wx), 0, '同渠道读自己的记录')
            self.assertEqual(g('lark_identity.py', fs, read_fs), 0)
            self.assertEqual(g('wecom_guard.py', fs, read_wx), 2, '默认关：飞书会话不能读企微记录')
            self.assertEqual(g('lark_identity.py', wx, read_fs), 2, '默认关：企微会话不能读飞书记录')
            self.assertEqual(g('lark_identity.py', wx, 'lark-cli im +messages-send --as bot --text hi'), 0, '机器人身份发消息不算跨读')
            cfg = json.loads(orig); cfg['cross_im_read'] = True
            cfgp.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
            self.assertEqual(g('wecom_guard.py', fs, read_wx), 0)
            self.assertEqual(g('lark_identity.py', wx, read_fs), 0)
            self.assertEqual(g('wecom_guard.py', dict(fs, FCB_OWNER='0'), read_wx), 0, 'others=bot_read_im 时同事触发也能读')
            self.assertEqual(g('wecom_guard.py', dict(fs, FCB_OWNER='0'), 'wecom-cli mail list'), 2)
        finally:
            cfgp.write_text(orig, encoding='utf-8')

    def test_rejects_unfilled_config(self):
        bad = self.home / 'bots' / 'bad'
        bad.mkdir(parents=True, exist_ok=True)
        (bad / 'config.json').write_text((TEMPLATES / 'config.example.json').read_text(encoding='utf-8'), encoding='utf-8')
        r = subprocess.run([sys.executable, str(SKILL_DIR / 'scripts' / 'scaffold.py'), str(bad)],
                           capture_output=True, text=True, env=self.env)
        self.assertNotEqual(r.returncode, 0)

    def test_bridge_compiles(self):
        r = subprocess.run([sys.executable, '-m', 'py_compile', str(self.inst / 'bridge.py')], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    # 钩子
    def hook(self, name, env, tool, ti):
        e = dict(self.env, FCB_CONFIG=str(self.inst / 'config.json'), **env)
        return subprocess.run([sys.executable, str(self.inst / 'hooks' / name)],
                              input=json.dumps({'tool_name': tool, 'tool_input': ti}),
                              capture_output=True, text=True, env=e)

    def bash(self, name, env, cmd):
        return self.hook(name, env, 'Bash', {'command': cmd})

    def test_identity_others(self):
        o = {'FCB_OWNER': '0'}
        self.assertEqual(self.bash('lark_identity.py', o, 'lark-cli im +messages-send --text hi').returncode, 2)
        self.assertEqual(self.bash('lark_identity.py', o, 'lark-cli calendar +agenda').returncode, 2)
        self.assertEqual(self.bash('lark_identity.py', o, 'lark-cli calendar +agenda --as bot').returncode, 0)
        self.assertEqual(self.bash('lark_identity.py', o, 'lark-cli im +chat-messages-list --chat-id x --as user').returncode, 0)

    def test_identity_owner(self):
        o = {'FCB_OWNER': '1'}
        self.assertEqual(self.bash('lark_identity.py', o, 'lark-cli calendar +agenda').returncode, 0)
        self.assertEqual(self.bash('lark_identity.py', o, 'lark-cli api POST /open-apis/im/v1/messages --as user').returncode, 2)
        self.assertEqual(self.bash('lark_identity.py', o, 'echo x && lark-cli im +messages-reply --message-id m').returncode, 2)
        self.assertEqual(self.bash('lark_identity.py', o, 'lark-cli im +messages-send --as bot --text hi').returncode, 0)

    def test_private_paths(self):
        p = {'FCB_PRIVATE': '0'}
        self.assertEqual(self.hook('private_guard.py', p, 'Read', {'file_path': f'{self.home}/personal/a.md'}).returncode, 2)
        self.assertEqual(self.bash('private_guard.py', p, 'cat ~/personal/a.md').returncode, 2)
        self.assertEqual(self.bash('private_guard.py', p, 'cat $HOME/personal/a.md').returncode, 2)
        self.assertEqual(self.hook('private_guard.py', {'FCB_PRIVATE': '1'}, 'Read', {'file_path': f'{self.home}/personal/a.md'}).returncode, 0)
        self.assertEqual(self.hook('private_guard.py', p, 'Read', {'file_path': f'{self.home}/work/a.py'}).returncode, 0)
        self.assertEqual(self.hook('private_guard.py', p, 'Read', {'file_path': f'{self.inst}/inbox/private/x.png'}).returncode, 2)
        self.assertEqual(self.hook('private_guard.py', p, 'Read', {'file_path': f'{self.inst}/inbox/x.png'}).returncode, 0)
        self.assertEqual(self.bash('private_guard.py', p, f'tail {self.inst}/logs/bridge.log').returncode, 2)

    def test_wiki_search_rewritten(self):
        p = {'FCB_PRIVATE': '0'}
        r = self.bash('private_guard.py', p, 'rg -l foo ~/wiki/wiki')
        self.assertEqual(r.returncode, 0)
        cmd = json.loads(r.stdout)['hookSpecificOutput']['updatedInput']['command']
        self.assertIn("--glob '!**/people/**'", cmd)
        r = self.bash('private_guard.py', p, f'grep -rl foo {self.home}/wiki/wiki/')
        self.assertIn('--exclude-dir=people', json.loads(r.stdout)['hookSpecificOutput']['updatedInput']['command'])
        self.assertEqual(self.bash('private_guard.py', p, 'find ~/wiki/wiki -name x').returncode, 2)
        self.assertEqual(self.hook('private_guard.py', p, 'Grep', {'pattern': 'x', 'path': f'{self.home}/wiki/wiki'}).returncode, 2)
        self.assertEqual(self.hook('private_guard.py', p, 'Grep', {'pattern': 'x', 'path': f'{self.home}/wiki/wiki/concepts'}).returncode, 0)


class AmbientTest(unittest.TestCase):
    """旁听：用假 lark 和假 Claude 跑 bridge 的旁听逻辑，不连飞书、不调 Claude。"""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        import types
        cls.tmp = tempfile.TemporaryDirectory()
        inst = Path(cls.tmp.name)
        cfg = json.loads((TEMPLATES / 'config.example.json').read_text(encoding='utf-8'))
        cfg.update(name='测试助理', owner_name='小王', owner_open_id=OWNER, bot_open_id=BOT)
        (inst / 'config.json').write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
        for f in ('bridge.py', 'tasks.py'):
            (inst / f).write_text((TEMPLATES / f).read_text(encoding='utf-8'), encoding='utf-8')
        spec = importlib.util.spec_from_file_location('fcb_bridge_test', inst / 'bridge.py')
        b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b)
        cls.b, cls.types = b, types
        cls.sent = []
        b.reply = lambda ev, text, in_thread, key=None: cls.sent.append((ev['message_id'], text)) or 'om_out'

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.sent.clear()
        self.b.amb.clear()
        self.b.amb_buf.clear()

    def msg(self, i, typ='user', at=False, old=False):
        now = time.strftime('%Y-%m-%d %H:%M')
        return {'message_id': f'om_p{i}', 'create_time': '2020-01-01 00:00' if old else now, 'content': f'msg{i}',
                'sender': {'name': 'x', 'sender_type': typ}, 'mentions': [{'id': BOT}] if at else []}

    def test_default_off_and_command_toggles(self):
        b = self.b
        b.lark = lambda args, **k: self.types.SimpleNamespace(stdout=json.dumps({'data': {'messages': []}}), returncode=0)
        self.assertEqual(b.ambient_chats(), {})
        self.assertIn('开始旁听', b.ambient_cmd('oc_a', '/旁听'))
        self.assertIn('oc_a', b.ambient_chats())
        self.assertIn('在旁听', b.ambient_cmd('oc_a', '/旁听 状态'))
        self.assertIn('不旁听', b.ambient_cmd('oc_a', '/旁听'))
        self.assertEqual(b.ambient_chats(), {})

    def test_poll_filters_and_cooldown(self):
        b = self.b
        batches = [[self.msg(1), self.msg(2)],
                   [self.msg(3), self.msg(4, typ='app'), self.msg(5, at=True), self.msg(6, old=True)]]
        batches[1][0]['thread_replies'] = [self.msg(7)]
        cur = {'i': 0}
        b.lark = lambda args, **k: self.types.SimpleNamespace(
            stdout=json.dumps({'data': {'messages': batches[cur['i']]}}), returncode=0)
        b.ambient_cmd('oc_p', '/旁听')                 # 开启时群里已有 om_p1、om_p2
        batches[0].append(self.msg(9))                 # 开启后、第一轮拉取前到的消息不能被吞
        flushed = []
        orig_flush, orig_quiet = b.ambient_flush, b.AMB['quiet_seconds']
        b.ambient_flush = lambda c, msgs: flushed.append([m['message_id'] for m in msgs])
        b.AMB['quiet_seconds'] = 0
        try:
            b.ambient_poll_once()
            self.assertEqual(flushed, [['om_p9']], '开启前已有的不处理，开启后到的要处理')
            flushed.clear()
            cur['i'] = 1
            b.ambient_poll_once()
            self.assertEqual(flushed, [['om_p3', 'om_p7']], '跳过机器人、@ 机器人、过期消息，收话题回复')
            b.amb['oc_p']['cool_until'] = time.time() + 999
            batches[1].append(self.msg(8))
            b.ambient_poll_once()
            self.assertEqual(len(flushed), 1, '冷却期内不处理')
            self.assertEqual([m['message_id'] for m in b.amb_buf['oc_p']['msgs']], ['om_p8'])
        finally:
            b.ambient_flush, b.AMB['quiet_seconds'] = orig_flush, orig_quiet
            b.ambient_cmd('oc_p', '/旁听 关')

    def flush_with(self, output):
        b = self.b
        seen = {}
        def fake(key, s, prompt, owner, private, chat_id, quiet=False):
            seen.update(owner=owner, private=private, quiet=quiet)
            return output
        orig = b.run_claude
        b.run_claude = fake
        try:
            b.ambient_flush('oc_f', [self.msg(1), self.msg(2)])
        finally:
            b.run_claude = orig
        return seen

    def test_reply_mode_and_session_key(self):
        b = self.b
        plain = {'chat_type': 'group', 'chat_id': 'oc_g', 'message_id': 'om_1'}
        reply_quote = dict(plain, root_id='om_0')                      # 引用回复但不在话题里
        topic = dict(plain, root_id='om_0', thread_id='omt_1')
        self.assertEqual(b.session_key(plain), 'grp:oc_g')
        self.assertEqual(b.session_key(reply_quote), 'grp:oc_g')
        self.assertEqual(b.session_key(topic), 'grp:oc_g:omt_1')
        self.assertFalse(b.in_topic(plain))
        self.assertTrue(b.in_topic(topic))
        self.assertEqual(b.session_key({'chat_type': 'p2p', 'chat_id': 'oc_p'}), 'p2p:oc_p')

    def test_group_session_rotates_when_idle(self):
        b = self.b
        s = b.get_session('grp:oc_idle')
        s['last'] = time.time() - b.GROUP_IDLE - 10
        self.assertNotEqual(b.get_session('grp:oc_idle')['id'], s['id'])
        t = b.get_session('grp:oc_idle:omt_1')
        t['last'] = time.time() - b.GROUP_IDLE - 10
        self.assertEqual(b.get_session('grp:oc_idle:omt_1')['id'], t['id'], '话题会话不按闲置轮换')

    def test_no_at_all_and_open_id_in_context(self):
        b = self.b
        self.assertEqual(b.no_at_all('<at user_id="all"></at> 开会'), '@所有人 开会')
        self.assertEqual(b.no_at_all('<at user_id="ou_x">小李</at> 看下'), '<at user_id="ou_x">小李</at> 看下')
        line = b._line({'create_time': '2026-11-20 10:00', 'content': 'hi', 'sender': {'name': '小李', 'id': 'ou_x', 'sender_type': 'user'}})
        self.assertIn('小李(ou_x)', line)

    def test_silent_sends_nothing(self):
        self.flush_with('[不回]')
        self.assertEqual(self.sent, [])

    def test_failure_sends_nothing(self):
        seen = self.flush_with(None)
        self.assertEqual(self.sent, [])
        self.assertTrue(seen['quiet'])

    def test_reply_targets_chosen_message_without_owner_rights(self):
        seen = self.flush_with('回复：om_p1\n接个梗')
        self.assertEqual(self.sent, [('om_p1', '接个梗')])
        self.assertFalse(seen['owner'])
        self.assertFalse(seen['private'])
        self.assertGreater(self.b.amb['oc_f']['cool_until'], time.time())


class WecomTest(unittest.TestCase):
    """企微渠道：只启用企微的实例能生成；事件归一、会话 key、主人识别、守则渲染。不连企微、不调 Claude。"""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        cls.tmp = tempfile.TemporaryDirectory()
        cls.home = Path(cls.tmp.name) / 'home'
        cls.inst = cls.home / 'bots' / 'wx'
        cls.inst.mkdir(parents=True)
        cfg = json.loads((TEMPLATES / 'config.example.json').read_text(encoding='utf-8'))
        cfg.update(name='测试助理', owner_name='小王', workdir='~/work')
        cfg.pop('owner_open_id'); cfg.pop('bot_open_id')
        cfg['channels'] = {'feishu': {'enabled': False}, 'wecom': {'enabled': True, 'owner_userid': 'wangxiao'}}
        (cls.inst / 'config.json').write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
        cls.out = subprocess.run([sys.executable, str(SKILL_DIR / 'scripts' / 'scaffold.py'), str(cls.inst), '--no-npm'],
                                 capture_output=True, text=True, env=dict(os.environ, HOME=str(cls.home)))
        spec = importlib.util.spec_from_file_location('fcb_bridge_wx', cls.inst / 'bridge.py')
        cls.b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.b)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_scaffold_wecom_only(self):
        self.assertEqual(self.out.returncode, 0, self.out.stderr)
        self.assertTrue((self.inst / 'wecom_gateway.mjs').exists())
        self.assertIn('@wecom/aibot-node-sdk', (self.inst / 'package.json').read_text(encoding='utf-8'))
        rules = (self.inst / 'rules.md').read_text(encoding='utf-8')
        self.assertNotIn('{{', rules)
        self.assertIn('## 企业微信', rules)
        self.assertIn('[企微消息]', rules)
        self.assertNotIn('lark-cli im +chat-messages-list', rules, '没启用飞书就不教它翻飞书记录')

    def test_cross_im_needs_confirmation(self):
        d = self.home / 'bots' / 'both'
        d.mkdir(parents=True, exist_ok=True)
        cfg = json.loads((TEMPLATES / 'config.example.json').read_text(encoding='utf-8'))
        cfg.update(name='测试助理', owner_name='小王', owner_open_id='ou_test', bot_open_id='ou_bot', workdir='~/work',
                   cross_im_read=True)
        cfg['channels'] = {'feishu': {'enabled': True}, 'wecom': {'enabled': True, 'owner_userid': 'wangxiao'}}
        (d / 'config.json').write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
        run = lambda *a: subprocess.run([sys.executable, str(SKILL_DIR / 'scripts' / 'scaffold.py'), str(d), '--no-npm', *a],
                                        capture_output=True, text=True, env=dict(os.environ, HOME=str(self.home)))
        r = run()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('--confirm-cross-im', r.stderr)
        self.assertEqual(run('--confirm-cross-im').returncode, 0)
        self.assertEqual(run().returncode, 0, '确认过一次，之后重新生成不用再确认')

    def test_requires_owner_userid(self):
        bad = self.home / 'bots' / 'wxbad'
        bad.mkdir(parents=True, exist_ok=True)
        cfg = json.loads((self.inst / 'config.json').read_text(encoding='utf-8'))
        cfg['channels']['wecom']['owner_userid'] = ''
        (bad / 'config.json').write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
        r = subprocess.run([sys.executable, str(SKILL_DIR / 'scripts' / 'scaffold.py'), str(bad), '--no-npm'],
                           capture_output=True, text=True, env=dict(os.environ, HOME=str(self.home)))
        self.assertNotEqual(r.returncode, 0)

    def test_event_normalized(self):
        b = self.b
        ev = b.wecom_event({'msgid': 'm1', 'chattype': 'group', 'chatid': 'g1', 'userid': 'wangxiao',
                            'msgtype': 'text', 'text': '@测试助理 看下这个', 'create_time': 1763600000,
                            'quote': {'msgtype': 'text', 'text': '原话'}})
        self.assertEqual((ev['channel'], ev['chat_type'], ev['chat_id']), ('wecom', 'group', 'g1'))
        self.assertEqual(ev['content'], '看下这个', '去掉开头的 @机器人')
        self.assertEqual(ev['create_time'], '1763600000000', '秒转毫秒')
        self.assertTrue(b.is_owner(ev))
        self.assertEqual(b.session_key(ev), 'wx:grp:g1')
        p2p = b.wecom_event({'msgid': 'm2', 'chattype': 'single', 'userid': 'lisi', 'msgtype': 'text', 'text': 'hi'})
        self.assertEqual((p2p['chat_type'], p2p['chat_id'], b.session_key(p2p)), ('p2p', 'lisi', 'wx:p2p:lisi'))
        self.assertFalse(b.is_owner(p2p))
        prompt = b.build_prompt(ev, '小王', *b.fetch_context(ev, {}))
        self.assertTrue(prompt.startswith('[企微消息]'))
        self.assertIn('原话', prompt)

    def test_idle_rotation_with_channel_prefix(self):
        b = self.b
        self.assertEqual(b.idle_limit('wx:p2p:lisi'), b.P2P_IDLE)
        self.assertEqual(b.idle_limit('wx:grp:g1'), b.GROUP_IDLE)
        self.assertEqual(b.idle_limit('grp:oc:omt'), None)
        s = b.get_session('wx:grp:g9')
        s['last'] = time.time() - b.GROUP_IDLE - 10
        self.assertNotEqual(b.get_session('wx:grp:g9')['id'], s['id'])

    def test_wecom_reply_trims_bytes_and_blocks_at_all(self):
        b = self.b
        sent = []
        orig = b.wecom_send
        b.wecom_send = sent.append
        try:
            b.wecom_reply({'channel': 'wecom', 'message_id': 'm1'}, '中' * 9000 + ' <@all>')
        finally:
            b.wecom_send = orig
        c = sent[0]['content']
        self.assertLessEqual(len(c.encode('utf-8')), 20480)
        self.assertNotIn('<@all>', c)



class TaskTest(unittest.TestCase):
    """长任务：派活、审批、补充指令、事件回报、后台运行（假 Claude）、git 护栏。不连 IM、不调真 Claude。"""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        cls.inst, cls.work = base / 'inst', base / 'work'
        cls.inst.mkdir(); cls.work.mkdir(); (cls.work / 'secret').mkdir()
        cfg = json.loads((TEMPLATES / 'config.example.json').read_text(encoding='utf-8'))
        cfg.update(name='测试助理', owner_name='小王', owner_open_id=OWNER, bot_open_id=BOT, workdir=str(cls.work),
                   tasks={'enabled': True, 'root': str(base / 'tasks'), 'max_running': 1, 'approval_hours': 24, 'heartbeat_min': 30},
                   private={'paths': [str(cls.work / 'secret')]})
        cfg['channels']['wecom'].update(enabled=True, owner_userid='boss')
        cfg['ambient']['enabled'] = False
        (cls.inst / 'config.json').write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
        for f in ('bridge.py', 'tasks.py'):
            (cls.inst / f).write_text((TEMPLATES / f).read_text(encoding='utf-8'), encoding='utf-8')
        gh = cls.inst / 'hooks' / 'git'; gh.mkdir(parents=True)
        shutil.copy(TEMPLATES / 'hooks' / 'git' / 'fcb-githook', gh / 'fcb-githook')
        os.chmod(gh / 'fcb-githook', 0o755)
        os.symlink('fcb-githook', gh / 'pre-push')
        spec = importlib.util.spec_from_file_location('fcb_bridge_task_test', cls.inst / 'bridge.py')
        b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
        cls.b, cls.t = b, b.tasks
        cls.sent, cls.wx = [], []
        b.reply = lambda ev, text, in_thread, key=None: cls.sent.append((ev.get('message_id'), text, key)) or 'om_out'
        b.wecom_send = lambda cmd: cls.wx.append(cmd)
        b.lark = lambda args, stdin=None, timeout=60: cls.sent.append(('lark', stdin, None))
        b.sender_name = lambda i: {OWNER: '小王'}.get(i, '同事甲')
        cls.repo = cls.work / 'proj'
        cls.git_repo(cls.repo, base / 'proj.git')

    @staticmethod
    def git_repo(path, bare):
        run = lambda *a, cwd=None: subprocess.run(['git', *a], cwd=cwd, check=True, capture_output=True)
        run('init', '-q', '--bare', '-b', 'main', str(bare))
        run('init', '-q', '-b', 'main', str(path))
        for k, v in (('user.email', 't@t'), ('user.name', 't')): run('config', k, v, cwd=path)
        (path / 'a.txt').write_text('x')
        run('add', '.', cwd=path); run('commit', '-qm', 'init', cwd=path)
        run('remote', 'add', 'origin', str(bare), cwd=path); run('push', '-q', 'origin', 'main', cwd=path)
        run('remote', 'set-head', 'origin', 'main', cwd=path)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.sent.clear(); self.wx.clear()

    def ev(self, text, sender=OWNER, chat='oc_g', chat_type='group', channel='feishu', mid=None):
        return {'channel': channel, 'sender_id': sender, 'chat_id': chat, 'chat_type': chat_type, 'content': text,
                'message_id': mid or 'om_' + uuid.uuid4().hex[:8], 'create_time': '0'}

    def directive(self, title='加个功能', repo=None):
        return f"我准备这么干。\n\n[派活]\n仓库: {repo or self.repo}\n标题: {title}\n任务书:\n目标：加个功能\n验收：测试通过"

    def test_parse_directive(self):
        head, d = self.t.parse_directive(self.directive())
        self.assertEqual(head, '我准备这么干。')
        self.assertEqual((d['title'], d['repo']), ('加个功能', str(self.repo)))
        self.assertIn('验收：测试通过', d['brief'])
        self.assertEqual(self.t.parse_directive('普通回复')[1], None)
        fenced = "我准备这么干。\n\n```\n[派活]\n仓库: ~/work/x\n标题: 修\n任务书:\n改 bug\n```"
        head, d = self.t.parse_directive(fenced)                # Claude 照抄守则里的代码块围栏
        self.assertEqual(head, '我准备这么干。')
        self.assertEqual(d['brief'], '改 bug')

    def test_check_repo(self):
        self.assertIsNone(self.t.check_repo(str(self.repo))[1])
        self.assertIn('工作目录', self.t.check_repo('/etc')[1])
        self.assertIn('私密', self.t.check_repo(str(self.work / 'secret'))[1])
        (self.work / 'plain').mkdir(exist_ok=True)
        self.assertIn('git', self.t.check_repo(str(self.work / 'plain'))[1])
        self.assertIn('派活没成', self.b.task_directive(self.ev('x'), self.directive(repo='/etc')))

    def test_owner_directive_queues(self):
        out = self.b.task_directive(self.ev('x'), self.directive())
        n = int(re.search(r'任务 #(\d+)', out).group(1))
        self.assertNotIn('[派活]', out)
        t = self.t.load(n)
        self.assertEqual(t['status'], 'approved')
        self.assertTrue(t['requester']['owner'])
        self.assertTrue(t['branch'].startswith('bot/'))

    def test_group_colleague_needs_approval_in_group(self):
        ev = self.ev('x', sender='ou_mate')
        out = self.b.task_directive(ev, self.directive())
        n = int(re.search(r'批 (\d+)', out).group(1))
        self.assertIn(f'<at user_id="{OWNER}">', out)      # 在原群里 @ 主人
        self.assertEqual(self.t.load(n)['status'], 'pending')
        self.assertIn('只有小王能批', self.b.task_command(self.ev(f'@_user_1 批 {n}', sender='ou_mate')))
        self.assertEqual(self.t.load(n)['status'], 'pending')
        self.assertIn('排上了', self.b.task_command(self.ev(f'@_user_1 批 {n}')))
        self.assertEqual(self.t.load(n)['status'], 'approved')

    def test_p2p_colleague_asks_owner_by_dm(self):
        ev = self.ev('x', sender='mate', chat='mate', chat_type='p2p', channel='wecom')
        out = self.b.task_directive(ev, self.directive())
        n = int(re.search(r'任务 #(\d+)', out).group(1))
        self.assertEqual(self.wx[-1]['chatid'], 'boss')    # 私聊主人
        self.assertIn(f'批 {n}', self.wx[-1]['content'])
        self.wx.clear()
        self.assertIn('排上了', self.b.task_command(self.ev(f'批 {n}', sender='boss', chat='boss', chat_type='p2p', channel='wecom')))
        self.assertEqual(self.wx[-1]['chatid'], 'mate')    # 回原会话说一声

    def test_wecom_group_mention_stripped(self):
        n = self.t.create(title='x', repo=str(self.repo), brief='b', status='pending',
                          requester={'channel': 'wecom', 'id': 'mate', 'name': '同事甲', 'owner': False},
                          origin={'channel': 'wecom', 'chat_id': 'wrg', 'chat_type': 'group', 'message_id': 'm'})['id']
        out = self.b.task_command(self.ev(f'@测试助理 批 {n}', sender='boss', chat='wrg', channel='wecom'))
        self.assertIn('排上了', out)

    def test_follow_up_authorization(self):
        n = self.t.create(title='x', repo=str(self.repo), brief='b', status='running',
                          requester={'channel': 'feishu', 'id': 'ou_mate', 'name': '同事甲', 'owner': False},
                          origin={'channel': 'feishu', 'chat_id': 'oc_g', 'chat_type': 'group', 'message_id': 'm'})['id']
        self.assertIn('不是你派的', self.b.task_command(self.ev(f'#{n} 改成红色', sender='ou_other')))
        self.assertIn('转给', self.b.task_command(self.ev(f'#{n} 改成红色', sender='ou_mate')))
        self.assertIn('转给', self.b.task_command(self.ev(f'#{n} 再加个测试')))
        items = self.t.inbox_take(n)
        self.assertEqual([i['text'] for i in items], ['改成红色', '再加个测试'])
        self.assertEqual(self.t.inbox_take(n), [])          # 每条只交一次
        self.assertIn('没有这个任务', self.b.task_command(self.ev(f'/任务 {n}', sender='ou_x', chat='oc_other')))
        self.assertIn('不是你派的', self.b.task_command(self.ev(f'/任务 取消 {n}', sender='ou_other')))

    def test_tick_posts_once_and_expires(self):
        launched = []
        orig = self.t.launch
        self.b.tasks.launch = lambda tid: launched.append(tid)
        try:
            n = self.t.create(title='x', repo=str(self.repo), brief='b', status='done',
                              requester={'channel': 'feishu', 'id': OWNER, 'name': '小王', 'owner': True},
                              origin={'channel': 'feishu', 'chat_id': 'oc_g', 'chat_type': 'group', 'message_id': 'om_src'})['id']
            self.t.event(n, 'progress', '计划定了'); self.t.event(n, 'done', '做完了')
            p = self.t.create(title='y', repo=str(self.repo), brief='b', status='pending',
                              requester={'channel': 'feishu', 'id': 'ou_mate', 'name': '同事甲', 'owner': False},
                              origin={'channel': 'feishu', 'chat_id': 'oc_g', 'chat_type': 'group', 'message_id': 'om_p'})['id']
            self.t.update(p, created=time.time() - 25 * 3600)
            self.b.task_tick(); self.b.task_tick()
            mine = [s for s in self.sent if s[0] == 'om_src']
            self.assertEqual(len(mine), 2)                    # 两个事件各发一次，第二次 tick 不重发
            self.assertEqual(len({s[2] for s in mine}), 2)    # 幂等键不同，飞书不会去重吞掉
            self.assertEqual(self.t.load(p)['status'], 'expired')
            q = self.t.create(title='z', repo=str(self.repo), brief='b', status='waiting',
                              requester={'channel': 'feishu', 'id': OWNER, 'name': '小王', 'owner': True},
                              origin={'channel': 'feishu', 'chat_id': 'oc_g', 'chat_type': 'p2p', 'message_id': 'om_q'})['id']
            self.t.event(q, 'question', '选 A 还是 B？')
            ok_reply = self.b.reply
            self.b.reply = lambda ev, text, in_thread, key=None: None     # 发送失败
            self.b.task_tick()
            self.assertEqual(self.t.load(q)['posted'], 0)               # 没发出去不记，下一轮重试
            self.b.reply = ok_reply
            self.b.task_tick()
            self.assertEqual(self.t.load(q)['posted'], 1)
        finally:
            self.b.tasks.launch = orig

    def test_runner_with_fake_claude(self):
        bindir = Path(self.tmp.name) / 'bin'; bindir.mkdir(exist_ok=True)
        fake = bindir / 'claude'
        fake.write_text('#!/usr/bin/env python3\n'
                        'import json, sys, os\n'
                        'sys.stdin.read()\n'
                        'open("done.txt", "w").write(os.environ.get("FCB_TASK_ID", ""))\n'
                        'p = lambda o: print(json.dumps(o, ensure_ascii=False), flush=True)\n'
                        'p({"type": "system", "subtype": "init"})\n'
                        'p({"type": "assistant", "parent_tool_use_id": None, "message": {"content": ['
                        '{"type": "text", "text": "[进展] 计划定了"},'
                        '{"type": "tool_use", "name": "TodoWrite", "input": {"todos": [{"content": "写代码", "status": "in_progress"}]}}]}})\n'
                        'p({"type": "result", "result": "[进展] 收尾\\n做完了，分支已推送", "is_error": False, "total_cost_usd": 0.5})\n')
        fake.chmod(0o755)
        n = self.t.create(title='x', repo=str(self.repo), brief='b', status='running', turn=1,
                          requester={'channel': 'feishu', 'id': OWNER, 'name': '小王', 'owner': True},
                          origin={'channel': 'feishu', 'chat_id': 'oc_g', 'chat_type': 'p2p', 'message_id': 'om_s'})['id']
        self.t.update(n, turn=1)
        old = os.environ['PATH']; os.environ['PATH'] = f'{bindir}:{old}'
        try: self.t.run(n)
        finally: os.environ['PATH'] = old
        t = self.t.load(n)
        self.assertEqual(t['status'], 'done', self.t.events(n))
        self.assertEqual([e['kind'] for e in self.t.events(n)], ['start', 'progress', 'done'])
        self.assertEqual(self.t.events(n)[-1]['text'], '做完了，分支已推送')
        self.assertEqual(t['todos'][0]['content'], '写代码')
        self.assertEqual(t['cost'], 0.5)
        wt = Path(t['worktree'])
        self.assertEqual((wt / 'done.txt').read_text(), str(n))   # 在工作树里跑，带着任务号
        br = subprocess.run(['git', '-C', str(wt), 'branch', '--show-current'], capture_output=True, text=True).stdout.strip()
        self.assertEqual(br, t['branch'])
        self.assertIn('claude --resume', self.b.task_event_text(t, self.t.events(n)[-1]))   # 主人私聊给接手命令

    def guard(self, cmd, owner=False):
        r = subprocess.run([sys.executable, str(TEMPLATES / 'hooks' / 'git_guard.py')],
                           input=json.dumps({'tool_input': {'command': cmd}}), capture_output=True, text=True,
                           env=dict(os.environ, FCB_OWNER='1' if owner else '0'))
        return r.returncode

    def test_git_guard(self):
        blocked = ['git push --no-verify origin bot/1', 'git -c core.hooksPath=/dev/null push', 'GIT_CONFIG_COUNT=0 git push',
                   'git push -f origin bot/1', 'git push origin +bot/1', 'git push origin :main', 'git push --tags',
                   'gh pr merge 3', 'gh pr create --title x', 'gh release create v1', 'gh api -X DELETE repos/a/b',
                   'gh auth token', 'cat ~/.config/gh/hosts.yml', 'cd x && gh repo delete a/b --yes',
                   'env -i PATH="$PATH" HOME="$HOME" git push origin bot/1', 'unset GIT_CONFIG_COUNT; git push',
                   'git push origin HEAD:main', 'git push origin bot/1:refs/heads/release']
        allowed = ['git push origin bot/1-1121', 'git push -u origin HEAD', 'git push origin HEAD:bot/1-1121',
                   'git push git@github.com:a/b.git bot/1', 'git push https://github.com/a/b.git HEAD:refs/heads/bot/2', 'gh pr create --draft --title x --body y',
                   'gh pr view 3', 'gh api repos/a/b/pulls', 'git status', 'ls']
        for c in blocked: self.assertEqual(self.guard(c), 2, c)
        for c in allowed: self.assertEqual(self.guard(c), 0, c)
        self.assertEqual(self.guard('gh pr merge 3', owner=True), 0)
        self.assertEqual(self.guard('git push -f origin main', owner=True), 2)
        self.assertEqual(self.guard('git push --no-verify', owner=True), 2)

    def test_pre_push_only_bot_branches(self):
        repo = Path(self.tmp.name) / 'pp'
        self.git_repo(repo, Path(self.tmp.name) / 'pp.git')
        (repo / 'b.txt').write_text('y')   # 有新提交，推送才有 ref 交给 pre-push
        subprocess.run(['git', 'add', '.'], cwd=repo, check=True); subprocess.run(['git', 'commit', '-qm', 'b'], cwd=repo, capture_output=True)
        env = self.t.hook_env(False, False, 'oc_g', 'feishu', 1)
        push = lambda ref, e: subprocess.run(['git', 'push', '-q', 'origin', ref], cwd=repo, env=e, capture_output=True, text=True)
        r = push('HEAD:main', env)
        self.assertNotEqual(r.returncode, 0); self.assertIn('bot/', r.stderr)
        self.assertNotEqual(push('HEAD:refs/heads/feature', env).returncode, 0)
        self.assertEqual(push('HEAD:bot/9-1121', env).returncode, 0)
        self.assertEqual(push('HEAD:main', self.t.hook_env(True, True, '', 'feishu')).returncode, 0)   # 主人本人不受限

if __name__ == '__main__':
    unittest.main()
