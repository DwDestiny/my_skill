"""preview-annotate 的文档与本地服务测试。不启动 Cloudflare 隧道，不访问外网。

Input: skills/preview-annotate/ 的 SKILL.md、agents/openai.yaml、scripts/；PATH 里的 node 与 bash
Output: unittest 结果
Pos: 仓库级测试，运行 python3 tests/test_preview_annotate.py
"""
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1] / 'skills' / 'preview-annotate'
SCRIPTS = SKILL_DIR / 'scripts'
NODE = shutil.which('node')


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class SkillDocsTest(unittest.TestCase):
    def test_frontmatter_name_matches_directory(self):
        content = (SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(content.startswith('---\nname: preview-annotate\n'))

    def test_description_is_plain_yaml_scalar(self):
        # 未加引号的值里出现“冒号+空格”，严格的 YAML 解析器（如 npx skills）会跳过整个 skill
        content = (SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8')
        line = next(l for l in content.splitlines() if l.startswith('description: '))
        self.assertNotIn(': ', line[len('description: '):])

    def test_openai_yaml_exists(self):
        self.assertTrue((SKILL_DIR / 'agents' / 'openai.yaml').exists())

    def test_scripts_listed_in_skill_exist(self):
        for name in ['preview.sh', 'server.mjs', 'annot.js', 'list.py']:
            with self.subTest(name=name):
                self.assertTrue((SCRIPTS / name).exists())


@unittest.skipUnless(NODE, '需要 node')
class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        dist = cls.tmp / 'dist'
        (dist / 'assets').mkdir(parents=True)
        (dist / 'index.html').write_text('<html><body><h1>demo</h1></body></html>', encoding='utf-8')
        (dist / 'assets' / 'app.js').write_text('console.log(1)', encoding='utf-8')
        # 与构建目录同前缀的兄弟目录，服务不得返回其中的文件
        (cls.tmp / 'dist-secret').mkdir()
        (cls.tmp / 'dist-secret' / 'x.txt').write_text('secret', encoding='utf-8')
        cls.store = cls.tmp / 'annotations.json'
        cls.port = free_port()
        cls.proc = subprocess.Popen(
            [NODE, str(SCRIPTS / 'server.mjs'), '--dir', str(dist), '--store', str(cls.store), '--port', str(cls.port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                cls.request('GET', '/')
                break
            except OSError:
                time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(5)
        shutil.rmtree(cls.tmp)

    @classmethod
    def request(cls, method, path, body=None):
        conn = http.client.HTTPConnection('127.0.0.1', cls.port, timeout=5)
        try:
            data = None if body is None else json.dumps(body)
            conn.request(method, path, body=data, headers={'content-type': 'application/json'})
            res = conn.getresponse()
            return res.status, res.read().decode('utf-8')
        finally:
            conn.close()

    def test_html_gets_overlay_script(self):
        status, body = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn('<script src="/__annot.js" defer></script></body>', body)

    def test_spa_fallback_and_missing_asset(self):
        self.assertIn('demo', self.request('GET', '/some/route')[1])
        self.assertEqual(self.request('GET', '/missing.png')[0], 404)
        self.assertEqual(self.request('GET', '/assets/app.js')[0], 200)
        self.assertEqual(self.request('GET', '/__annot.js')[0], 200)

    def test_sibling_directory_is_forbidden(self):
        status, body = self.request('GET', '/..%2fdist-secret/x.txt')
        self.assertEqual(status, 403)
        self.assertNotIn('secret', body)

    def test_malformed_path_does_not_stop_server(self):
        self.assertEqual(self.request('GET', '/%E0%A4%A')[0], 400)
        self.assertEqual(self.request('GET', '/')[0], 200)

    def test_annotation_lifecycle_and_list_script(self):
        self.assertEqual(self.request('POST', '/__annot', {'comment': '  '})[0], 400)
        status, body = self.request('POST', '/__annot', {
            'route': '/a', 'selector': 'h1', 'element': 'h1', 'text': 'demo',
            'rect': {'x': 0, 'y': 0, 'w': 10, 'h': 10}, 'viewport': '800×600', 'comment': '标题太小'})
        self.assertEqual(status, 200)
        item = json.loads(body)
        out = subprocess.run([sys.executable, str(SCRIPTS / 'list.py'), str(self.store)],
                             capture_output=True, text=True, check=True).stdout
        self.assertIn('标题太小', out)
        self.request('DELETE', '/__annot', {'id': item['id']})
        self.assertNotIn(item['id'], self.request('GET', '/__annot')[1])

    def test_concurrent_posts_keep_every_annotation(self):
        before = len(json.loads(self.request('GET', '/__annot')[1]))
        payload = {'route': '/b', 'selector': 'p', 'element': 'p', 'rect': {'x': 0, 'y': 0, 'w': 1, 'h': 1},
                   'viewport': '1×1'}
        with ThreadPoolExecutor(10) as pool:
            codes = list(pool.map(lambda i: self.request('POST', '/__annot', {**payload, 'comment': f'c{i}'})[0],
                                  range(20)))
        self.assertEqual(codes, [200] * 20)
        self.assertEqual(len(json.loads(self.request('GET', '/__annot')[1])), before + 20)


@unittest.skipUnless(NODE and shutil.which('bash'), '需要 node 与 bash')
class PreviewScriptTest(unittest.TestCase):
    def test_start_refuses_busy_port_before_tunnel(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / 'dist').mkdir()
            (tmp / 'dist' / 'index.html').write_text('<html><body></body></html>', encoding='utf-8')
            # 假 cloudflared：被调用就留下标记文件
            (tmp / 'bin').mkdir()
            fake = tmp / 'bin' / 'cloudflared'
            fake.write_text(f'#!/bin/sh\ntouch {tmp}/tunnel-called\n', encoding='utf-8')
            fake.chmod(0o755)
            env = {**os.environ, 'PATH': f"{tmp / 'bin'}{os.pathsep}{os.environ['PATH']}"}
            with socket.socket() as busy:
                busy.bind(('127.0.0.1', 0))
                busy.listen()
                port = busy.getsockname()[1]
                res = subprocess.run(['bash', str(SCRIPTS / 'preview.sh'), 'start', str(tmp / 'dist'), str(tmp / 'work'),
                                      str(port)], capture_output=True, text=True, env=env, timeout=30)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn('已被占用', res.stderr)
            self.assertFalse((tmp / 'tunnel-called').exists())
        finally:
            shutil.rmtree(tmp)

    def test_stop_really_stops_the_server(self):
        # reload 只起服务不开隧道；stop 后端口必须释放，证明 pid 文件记的是服务进程本身
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / 'dist').mkdir()
            (tmp / 'dist' / 'index.html').write_text('<html><body></body></html>', encoding='utf-8')
            work = tmp / 'work'
            work.mkdir()
            port = free_port()
            (work / 'config').write_text(f"{tmp / 'dist'}\n{port}\n", encoding='utf-8')
            (work / 'url').write_text('https://example.trycloudflare.com\n', encoding='utf-8')
            run = lambda *a: subprocess.run(['bash', str(SCRIPTS / 'preview.sh'), *a, str(work)],
                                            capture_output=True, text=True, timeout=30)
            self.assertEqual(run('reload').returncode, 0)
            self.assertIn('批注：0 条\n', run('status').stdout)
            self.assertEqual(socket.socket().connect_ex(('127.0.0.1', port)), 0)
            self.assertEqual(run('stop').returncode, 0)
            for _ in range(20):
                with socket.socket() as s:
                    if s.connect_ex(('127.0.0.1', port)) != 0:
                        break
                time.sleep(0.1)
            else:
                self.fail('stop 之后服务还在监听')
        finally:
            shutil.rmtree(tmp)


if __name__ == '__main__':
    unittest.main()
