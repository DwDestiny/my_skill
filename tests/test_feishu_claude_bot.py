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
        for f in ['bridge.py', 'rules.md', 'claude-settings.json', 'hooks/lark_identity.py', 'hooks/private_guard.py']:
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
        self.assertIn(f'Edit({self.inst}/**)', st['permissions']['deny'])

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
        (inst / 'bridge.py').write_text((TEMPLATES / 'bridge.py').read_text(encoding='utf-8'), encoding='utf-8')
        spec = importlib.util.spec_from_file_location('fcb_bridge_test', inst / 'bridge.py')
        b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b)
        cls.b, cls.types = b, types
        cls.sent = []
        b.reply = lambda ev, text, in_thread: cls.sent.append((ev['message_id'], text)) or 'om_out'

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


if __name__ == '__main__':
    unittest.main()
