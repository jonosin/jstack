#!/usr/bin/env python3
"""Test connector delta materialisation without network, credentials or knowledge."""
import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

DRIVER = Path(__file__).with_name('dot_refresh.py')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL)


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source, self.target, self.output = [self.root / p for p in ('source', 'target', 'refreshed')]
        self.source.mkdir()
        git(self.source, 'init', '-q')
        git(self.source, 'config', 'user.name', 'Synthetic Test')
        git(self.source, 'config', 'user.email', 'fixture@example.invalid')
        (self.source / 'note.md').write_text('Synthetic baseline\n')
        (self.source / 'delete.md').write_text('Synthetic removable file\n')
        git(self.source, 'add', '-A')
        git(self.source, 'commit', '-qm', 'Synthetic base')
        self.base = git(self.source, 'rev-parse', 'HEAD').decode().strip()
        subprocess.run(['git', 'clone', '-q', str(self.source), str(self.target)], check=True)
        git(self.target, 'config', 'user.name', 'Synthetic Test')
        git(self.target, 'config', 'user.email', 'fixture@example.invalid')
        (self.target / 'note.md').write_text('Synthetic target\n')
        (self.target / 'delete.md').unlink()
        (self.target / 'binary.bin').write_bytes(b'\x00\xff\x01synthetic\n')
        (self.target / 'run.sh').write_text('#!/bin/sh\nexit 0\n')
        (self.target / 'run.sh').chmod(0o755)
        (self.target / 'link').symlink_to('note.md')
        git(self.target, 'add', '-A')
        git(self.target, 'commit', '-qm', 'Synthetic target')
        self.head = git(self.target, 'rev-parse', 'HEAD').decode().strip()
        self.base_tree = git(self.source, 'rev-parse', 'HEAD^{tree}').decode().strip()
        self.target_tree = git(self.target, 'rev-parse', 'HEAD^{tree}').decode().strip()
        paths = git(self.target, 'diff', '--name-only', '-z', self.base, self.head).split(b'\0')
        def entry(commit, path, content=False):
            raw = git(self.target, 'ls-tree', '-z', commit, '--', path)
            if not raw:
                return None
            mode, kind, rest = raw.decode().split(' ', 2)
            oid = rest.split('\t')[0]
            value = {'mode': mode, 'sha': oid}
            if content:
                value['content_base64'] = base64.b64encode(git(self.target, 'cat-file', 'blob', oid)).decode()
            return value
        self.plan = {'schema': 'sb.dot-refresh/v1', 'repository': 'fixture/repo',
                     'base_remote_commit': self.base, 'target_remote_commit': self.head,
                     'base_tree': self.base_tree, 'target_tree': self.target_tree,
                     'changes': [{'path': p.decode(), 'before': entry(self.base, p.decode()),
                                  'after': entry(self.head, p.decode(), content=True)} for p in paths if p]}
        self.cursor = {'repository': 'fixture/repo', 'remote_commit': self.base,
                       'tree': self.base_tree, 'local_commit': self.base}

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self):
        plan, cursor, receipt = [self.root / name for name in ('plan.json', 'cursor.json', 'next-cursor.json')]
        plan.write_text(json.dumps(self.plan))
        cursor.write_text(json.dumps(self.cursor))
        result = subprocess.run([sys.executable, str(DRIVER), '--repo', str(self.source),
                                 '--output', str(self.output), '--receipt', str(receipt),
                                 '--plan', str(plan), '--cursor', str(cursor), '--repository', 'fixture/repo'],
                                capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout)

    def test_exact_tree_add_modify_delete_binary_mode_and_symlink(self):
        code, result = self.invoke()
        self.assertEqual(code, 0, result)
        self.assertEqual(git(self.output, 'rev-parse', 'HEAD^{tree}').decode().strip(), self.target_tree)
        self.assertNotEqual(result['local_commit'], self.head)
        self.assertEqual(result['remote_commit'], self.head)
        self.assertEqual((self.output / 'binary.bin').read_bytes(), b'\x00\xff\x01synthetic\n')
        self.assertTrue((self.output / 'link').is_symlink())
        self.assertFalse((self.output / 'delete.md').exists())
        self.assertEqual(git(self.source, 'rev-parse', 'HEAD').decode().strip(), self.base)
        self.assertEqual(git(self.source, 'status', '--porcelain'), b'')
        self.assertEqual(git(self.output, 'remote'), b'')
        code, replay = self.invoke()
        self.assertEqual(code, 4)
        self.assertIn('exists', replay['error'])

    def test_omitted_change_fails_complete_target_tree(self):
        self.plan['changes'].pop()
        code, result = self.invoke()
        self.assertEqual(code, 4)
        self.assertIn('TARGET_TREE_MISMATCH', result['error'])
        self.assertEqual(git(self.source, 'status', '--porcelain'), b'')

    def test_corrupted_blob_fails_hash(self):
        change = next(item for item in self.plan['changes'] if item['after'])
        change['after']['content_base64'] = base64.b64encode(b'corrupt fixture').decode()
        code, result = self.invoke()
        self.assertEqual(code, 4)
        self.assertIn('hash mismatch', result['error'])

    def test_stale_cursor_dirty_source_and_unsafe_path_fail_before_clone(self):
        self.cursor['remote_commit'] = '0' * 40
        code, result = self.invoke()
        self.assertEqual(code, 4)
        self.assertIn('cursor', result['error'])
        self.cursor['remote_commit'] = self.base
        (self.source / 'local.md').write_text('Preserve this synthetic edit')
        code, result = self.invoke()
        self.assertEqual(code, 4)
        self.assertIn('checkpoint', result['error'])
        (self.source / 'local.md').unlink()
        self.plan['changes'][0]['path'] = '../escape'
        code, result = self.invoke()
        self.assertEqual(code, 4)
        self.assertIn('Unsafe', result['error'])
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
