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

    def test_no_real_ids_in_skill(self):
        pat = re.compile(r'\b(ou|oc|cli)_[0-9a-f]{12,}\b')
        for f in SKILL_DIR.rglob('*'):
            if f.is_file():
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


if __name__ == '__main__':
    unittest.main()
