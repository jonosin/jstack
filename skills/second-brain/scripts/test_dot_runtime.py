#!/usr/bin/env python3
"""Exercise supplied-text capture/replay/compile against code-only temp fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

BRAIN_CODE = None
DRIVER = Path(__file__).with_name('dot_runtime.py')


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'brain'
        self.repo.mkdir()
        for directory in ('tools', 'schemas'):
            (self.repo / directory).mkdir()
            for source in (BRAIN_CODE / directory).iterdir():
                if source.is_file() and not source.is_symlink():
                    (self.repo / directory / source.name).write_bytes(source.read_bytes())
        for directory in ('raw', 'wiki/personal', 'wiki/concepts', 'wiki/system', 'state'):
            (self.repo / directory).mkdir(parents=True, exist_ok=True)
        (self.repo / 'AGENTS.md').write_text('# Synthetic fixture contract\n')
        (self.repo / 'CONTEXT.md').write_text('# Synthetic fixture context\n')
        (self.repo / 'state/migration-manifest.jsonl').write_text('')
        self.git('init', '-q')
        self.git('config', 'user.name', 'Synthetic Test')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.checkpoint()
        self.state = self.root / 'receipts'
        self.request = {'schema': 'sb.remote-capture-request/v1', 'route': 'x',
                        'title': 'Synthetic notebook fixture',
                        'source': 'https://x.com/fixture/status/1234567890123456789',
                        'role': 'concepts', 'target': 'raw/2026-01-01-fixture.md',
                        'body': '## Provenance\nSynthetic supplied text, no network.\n\n## Source\nThe fictional notebook uses numbered pages.'}

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, stderr=subprocess.DEVNULL, text=True)

    def checkpoint(self):
        self.git('add', '-A')
        self.git('commit', '-qm', 'Synthetic fixture checkpoint')

    def invoke(self, operation, value=None, operation_id='capture-001'):
        command = [sys.executable, str(DRIVER), '--repo', str(self.repo), '--state', str(self.state), operation]
        if operation != 'doctor':
            request = self.root / ('input-' + operation_id + '.json')
            request.write_text(json.dumps(value or self.request))
            command.extend(['--id', operation_id, '--request', str(request)])
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_doctor_reports_actual_processing_dependencies(self):
        code, report = self.invoke('doctor')
        self.assertEqual(code, 0)
        self.assertTrue(report['pyyaml'])
        self.assertFalse(report['credentials_required_for_local_processing'])

    def test_capture_preserves_body_role_and_reports_failed_global_verify(self):
        code, report = self.invoke('capture')
        self.assertEqual(code, 3)  # Synthetic fixture lacks historical global proofs.
        self.assertTrue(report['captured'])
        self.assertFalse(report['verified'])
        text = (self.repo / self.request['target']).read_text()
        self.assertIn('role: "concepts"', text)
        self.assertTrue(text.endswith(self.request['body'] + '\n'))
        self.assertEqual(len(list((self.repo / 'raw').glob('*.md'))), 1)
        self.assertFalse((self.repo / 'state/remote-capture-requests').exists())
        receipt = json.loads((self.state / 'capture-001.json').read_text())
        self.assertEqual(receipt['steps'][-1]['command'], 'sb verify --json')

    def test_identical_replay_does_not_finalize_again(self):
        self.invoke('capture')
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in (self.repo / 'state').rglob('*') if path.is_file()}
        code, report = self.invoke('capture')
        self.assertEqual(code, 0)
        self.assertTrue(report['result']['already_present'])
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in (self.repo / 'state').rglob('*') if path.is_file()}
        self.assertEqual(before, after)

    def test_x_tracking_url_is_same_source(self):
        self.invoke('capture')
        alternate = dict(self.request, source=self.request['source'] + '?s=20')
        code, report = self.invoke('capture', alternate, 'capture-tracking')
        self.assertEqual(code, 0)
        self.assertTrue(report['result']['already_present'])
        self.assertEqual(len(list((self.repo / 'raw').glob('*.md'))), 1)

    def test_changed_body_and_reused_id_are_blocked(self):
        self.invoke('capture')
        changed = dict(self.request, body='Different synthetic source version')
        code, report = self.invoke('capture', changed)
        self.assertEqual(code, 3)
        self.assertIn('different request', report['error'])
        code, report = self.invoke('capture', changed, 'capture-different-body')
        self.assertEqual(code, 3)
        self.assertIn('different bytes', report['error'])

    def test_unsafe_target_and_fetch_sentinel_are_blocked(self):
        for index, request in enumerate((dict(self.request, target='../escape.md'),
                                         dict(self.request, body='@fetch-source'))):
            code, report = self.invoke('capture', request, 'invalid-' + str(index))
            self.assertEqual(code, 3)
            self.assertEqual(report['phase'], 'blocked')
        self.assertFalse((self.root / 'escape.md').exists())
        self.assertEqual(list((self.repo / 'raw').glob('*')), [])

    def test_partial_unregistered_raw_is_preserved(self):
        target = self.repo / self.request['target']
        target.write_text('Partial synthetic source')
        code, report = self.invoke('capture')
        self.assertEqual(code, 3)
        self.assertIn('Partial/uncertain', report['error'])
        self.assertEqual(target.read_text(), 'Partial synthetic source')

    def compile_request(self):
        record = json.loads((self.repo / 'state/compile-manifest.jsonl').read_text().splitlines()[0])
        raw_id = record['raw_id']
        return {'schema': 'sb.remote-compile-request/v1', 'raw_ids': [raw_id],
                'extractions': [{'raw_id': raw_id, 'source_digest': 'Synthetic notebook fixture, no durable canonical change warranted.',
                                 'key_claims': ['The fictional notebook uses numbered pages.'],
                                 'nodes': [], 'edges': [], 'hyperedges': [],
                                 'canonical_impact': []}],
                'operations': [{'action': 'no-change', 'raw_ids': [raw_id], 'path': None,
                                'before_blob_sha': None, 'content': None}]}

    def test_compile_requires_clean_checkpoint(self):
        self.invoke('capture')
        code, report = self.invoke('compile', self.compile_request(), 'compile-dirty')
        self.assertEqual(code, 3)
        self.assertIn('clean isolated checkpoint', report['error'])
        self.assertFalse((self.state / 'compile-dirty.json').exists())

    def test_compile_no_change_indexes_and_blocks_blind_replay(self):
        self.invoke('capture')
        request = self.compile_request()
        self.checkpoint()
        code, report = self.invoke('compile', request, 'compile-001')
        self.assertEqual(code, 3, report)  # Keep global verify failure visible.
        self.assertTrue(report['compiled'], report)
        self.assertTrue(report['indexed'], report)
        self.assertFalse(report['verified'])
        self.assertEqual(report['steps'][-1]['command'], 'sb verify --json', report)
        narrow = [step for step in report['steps'] if isinstance(step['command'], list)
                  and step['command'][0] == 'tools/remote_compile_verify.py'][0]
        self.assertEqual(narrow['exit_code'], 0, narrow)
        record = json.loads((self.repo / 'state/compile-manifest.jsonl').read_text().splitlines()[0])
        self.assertEqual(record['state'], 'verified')
        code, replay = self.invoke('compile', request, 'compile-001')
        self.assertEqual(code, 3)
        self.assertIn('already attempted', replay['error'])

    def test_create_canonical_page_and_query_its_source(self):
        self.invoke('capture')
        request = self.compile_request()
        raw_id = request['raw_ids'][0]
        content = ('---\nschema: sb.canonical/v2\nid: AUTO\nrole: concepts\n'
                   'title: Synthetic notebooks\nsummary: Numbered pages in a fictional notebook.\n'
                   'status: active\ncreated: 2026-01-01\nupdated: 2026-01-01\n'
                   'raw:\n  - ' + raw_id + '\n---\n\n# Synthetic notebooks\n\n'
                   'The fictional notebook uses numbered pages.\n')
        # Quote dates so YAML returns strings, as canonical-v2 requires.
        content = content.replace('created: 2026-01-01', 'created: "2026-01-01"').replace('updated: 2026-01-01', 'updated: "2026-01-01"')
        request['operations'] = [{'action': 'create', 'raw_ids': [raw_id],
                                  'path': 'wiki/concepts/synthetic-notebooks.md',
                                  'before_blob_sha': None, 'content': content}]
        self.checkpoint()
        code, report = self.invoke('compile', request, 'compile-create')
        self.assertEqual(code, 3, report)
        self.assertTrue(report['compiled'], report)
        self.assertTrue(report['indexed'], report)
        page = self.repo / 'wiki/concepts/synthetic-notebooks.md'
        self.assertIn(raw_id, page.read_text())
        query = subprocess.run([sys.executable, 'tools/sb.py', 'node', 'get',
                                'wiki/concepts/synthetic-notebooks.md', '--budget', '1200', '--json'],
                               cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(query.returncode, 0, query.stderr + query.stdout)
        result = json.loads(query.stdout)
        self.assertTrue(result['ok'])
        self.assertIn('wiki/concepts/synthetic-notebooks.md', query.stdout)
        search = subprocess.run([sys.executable, 'tools/sb.py', 'query',
                                 'Synthetic notebooks', '--depth', 'evidence',
                                 '--budget', '1200', '--json'],
                                cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(search.returncode, 0, search.stderr + search.stdout)
        self.assertTrue(json.loads(search.stdout)['ok'])
        self.assertIn('wiki/concepts/synthetic-notebooks.md', search.stdout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--brain-code', type=Path, required=True)
    options, remaining = parser.parse_known_args()
    BRAIN_CODE = options.brain_code.resolve()
    unittest.main(argv=[sys.argv[0], *remaining])
