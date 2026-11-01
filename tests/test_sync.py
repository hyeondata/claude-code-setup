"""Black-box sync tests: real local Git remotes, synthetic data, fake bootstrap.

Run this module with Python 3.10+; launcher fallback tests provide a separate old-Python fixture.
No test changes HOME, contacts GitHub, or runs the real settings installer.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]
FAKE_BOOTSTRAP = '''import json, os, sys
from pathlib import Path
log = Path(os.environ["TEST_BOOTSTRAP_LOG"])
with log.open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(sys.argv[1:]) + "\\n")
raise SystemExit(int(os.environ.get("TEST_BOOTSTRAP_FAIL", "0")))
'''


class SyncIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='claude-sync-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.env = os.environ.copy()
        for name in list(self.env):
            if name in {'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR', 'GIT_CONFIG'} or name.startswith('GIT_CONFIG_'):
                self.env.pop(name)
        global_config = self.root / 'empty-gitconfig'
        global_config.write_text('')
        self.log = self.root / 'bootstrap-calls.jsonl'
        self.env.update({
            'GIT_CONFIG_GLOBAL': str(global_config),
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_TERMINAL_PROMPT': '0',
            'GIT_AUTHOR_NAME': 'Sync Test',
            'GIT_AUTHOR_EMAIL': 'sync-test@example.invalid',
            'GIT_COMMITTER_NAME': 'Sync Test',
            'GIT_COMMITTER_EMAIL': 'sync-test@example.invalid',
            'TEST_BOOTSTRAP_LOG': str(self.log),
            'PYTHONDONTWRITEBYTECODE': '1',
        })
        self.env.pop('TEST_BOOTSTRAP_FAIL', None)
        self.env.pop('CLAUDE_SYNC_PYTHON', None)
        self.origin = self.root / 'origin.git'
        self.seed = self.root / 'seed'
        self.first = self.root / 'first clone'
        self.second = self.root / 'second clone'
        self.seed.mkdir()
        tracked = self.run_command(['git', '-C', str(SOURCE), 'ls-files', '-z']).stdout.split('\0')
        names = set(filter(None, tracked)) | {'claude-sync', 'scripts/sync.py', 'tests/test_sync.py'}
        for name in names:
            source = SOURCE / name
            self.assertTrue(source.is_file(), f'Implementation file is not ready: {name}')
            target = self.seed / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        (self.seed / 'scripts/bootstrap.py').write_text(FAKE_BOOTSTRAP)
        self.run_command(['git', 'init', '--bare', '--initial-branch=main', str(self.origin)])
        self.run_command(['git', 'init', '--initial-branch=main', str(self.seed)])
        self.configure_identity(self.seed)
        self.git(self.seed, 'add', '--', *sorted(names))
        self.git(self.seed, 'commit', '-m', 'Synthetic sync fixture')
        self.git(self.seed, 'remote', 'add', 'origin', str(self.origin))
        self.git(self.seed, 'push', '-u', 'origin', 'main')
        for path in (self.first, self.second):
            self.run_command(['git', 'clone', str(self.origin), str(path)])
            self.configure_identity(path)
        self.initial_head = self.head(self.first)

    def run_command(self, argv, *, cwd=None, env=None, check=True):
        result = subprocess.run(argv, cwd=cwd, env=env or self.env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=40)
        if check and result.returncode:
            self.fail(f'Command failed: {argv}\nstdout: {result.stdout}\nstderr: {result.stderr}')
        return result

    def git(self, root, *args, check=True):
        return self.run_command(['git', '-C', str(root), *args], check=check)

    def configure_identity(self, repo):
        self.git(repo, 'config', 'user.name', 'Sync Test')
        self.git(repo, 'config', 'user.email', 'sync-test@example.invalid')
        self.git(repo, 'config', 'commit.gpgsign', 'false')
        self.git(repo, 'config', 'tag.gpgsign', 'false')

    def head(self, repo):
        return self.git(repo, 'rev-parse', 'HEAD').stdout.strip()

    def remote_head(self):
        return self.git(self.origin, 'rev-parse', 'refs/heads/main').stdout.strip()

    def sync(self, repo, *args, env=None):
        return self.run_command([str(repo / 'claude-sync'), *args], cwd=repo,
                                env=env, check=False)

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def change(self, repo, path='README.md', content='\nSynthetic settings update.\n'):
        target = repo / path
        target.write_text(target.read_text() + content)

    def publish_from_second(self, path='docs/01-development.md'):
        self.change(self.second, path)
        self.git(self.second, 'add', '--', path)
        self.git(self.second, 'commit', '-m', 'Update from another machine')
        self.git(self.second, 'push', 'origin', 'main')
        return self.head(self.second)

    def bootstrap_calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def local_runtime(self, repo):
        vault = self.root / 'separate vault with spaces'
        home = self.root / 'local Claude home'
        node = self.root / 'node bin/node'
        vault.mkdir()
        (vault / 'personal-note.md').write_text('Synthetic private note; never publish.\n')
        node.parent.mkdir()
        node.write_text('#!/bin/sh\nprintf "v22.0.0\\n"\n')
        node.chmod(0o755)
        config = {'vaultPath': str(vault),
                  'registryPath': str(home / 'plugins/installed_plugins.json'),
                  'pythonPath': sys.executable, 'nodePath': str(node)}
        (repo / 'automation/config.json').write_text(json.dumps(config))
        return vault, home, node

    def test_push_commits_configuration_without_memory_or_runtime_files(self):
        self.change(self.first)
        vault = self.first / 'obsidian'
        vault.mkdir()
        (vault / 'personal-note.md').write_text('Synthetic excluded knowledge.\n')
        drafts = self.first / 'automation/drafts'
        drafts.mkdir()
        (drafts / 'save.json').write_text('{"content":"Synthetic excluded draft"}')
        runtime = self.first / 'automation/config.json'
        runtime.write_text('{"vaultPath":"/synthetic/private/path"}')
        before = {p: p.read_bytes() for p in (vault / 'personal-note.md', drafts / 'save.json', runtime)}
        result = self.sync(self.first, 'push', '-m', 'Share settings only')
        self.assert_success(result)
        self.assertEqual(self.head(self.first), self.remote_head())
        self.assertNotEqual(self.head(self.first), self.initial_head)
        self.assertEqual(self.git(self.origin, 'show', 'main:README.md').stdout,
                         (self.first / 'README.md').read_text())
        remote_paths = self.git(self.origin, 'ls-tree', '-r', '--name-only', 'main').stdout.splitlines()
        self.assertEqual(len(remote_paths), 28)
        self.assertFalse(any(p.startswith(('obsidian/', 'automation/drafts/')) or p == 'automation/config.json' for p in remote_paths))
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_staged_unlisted_file_blocks_push_without_committing_it(self):
        secret = self.first / '.env'
        secret.write_text('SYNTHETIC_TEST_VALUE=private\n')
        self.git(self.first, 'add', '-f', '--', '.env')
        self.change(self.first)
        result = self.sync(self.first, 'push', '-m', 'Must not include staged private file')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.head(self.first), self.initial_head)
        self.assertEqual(self.remote_head(), self.initial_head)
        self.assertIn('.env', self.git(self.first, 'diff', '--cached', '--name-only').stdout.splitlines())

    def test_deleted_private_file_in_outgoing_history_still_blocks_push(self):
        (self.first / '.env').write_text('SYNTHETIC_TEST_VALUE=private\n')
        self.git(self.first, 'add', '-f', '--', '.env')
        self.git(self.first, 'commit', '-m', 'Synthetic accidental private commit')
        self.git(self.first, 'rm', '--', '.env')
        self.git(self.first, 'commit', '-m', 'Delete private file from tip')
        before = self.head(self.first)
        result = self.sync(self.first, 'push')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.head(self.first), before)
        self.assertEqual(self.remote_head(), self.initial_head)

    def test_diverged_push_rejects_without_merging_or_rewriting(self):
        remote = self.publish_from_second()
        self.change(self.first)
        self.git(self.first, 'add', '--', 'README.md')
        self.git(self.first, 'commit', '-m', 'Independent local change')
        local = self.head(self.first)
        result = self.sync(self.first, 'push')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.head(self.first), local)
        self.assertEqual(self.remote_head(), remote)
        self.assertFalse((self.first / '.git/MERGE_HEAD').exists())

    def test_diverged_pull_rejects_without_merging_or_applying(self):
        self.publish_from_second()
        self.change(self.first)
        self.git(self.first, 'add', '--', 'README.md')
        self.git(self.first, 'commit', '-m', 'Independent local change')
        before = self.head(self.first)
        result = self.sync(self.first, 'pull')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.head(self.first), before)
        self.assertFalse((self.first / '.git/MERGE_HEAD').exists())
        self.assertEqual(self.bootstrap_calls(), [])

    def test_dirty_pull_does_not_update_or_apply(self):
        self.publish_from_second()
        self.change(self.first)
        before = (self.first / 'README.md').read_bytes()
        result = self.sync(self.first, 'pull')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.head(self.first), self.initial_head)
        self.assertEqual((self.first / 'README.md').read_bytes(), before)
        self.assertEqual(self.bootstrap_calls(), [])

    def test_pull_fast_forwards_and_applies_saved_machine_paths(self):
        vault, home, node = self.local_runtime(self.first)
        config_before = (self.first / 'automation/config.json').read_bytes()
        note_before = (vault / 'personal-note.md').read_bytes()
        remote = self.publish_from_second()
        result = self.sync(self.first, 'pull', '--with-optional')
        self.assert_success(result)
        self.assertEqual(self.head(self.first), remote)
        calls = self.bootstrap_calls()
        self.assertEqual(len(calls), 1)
        args = calls[0]
        self.assertIn('--apply', args)
        self.assertIn('--install-plugins', args)
        self.assertIn('--with-optional', args)
        for flag, expected in (('--vault', vault), ('--claude-home', home), ('--node', node)):
            self.assertIn(flag, args)
            self.assertEqual(args[args.index(flag) + 1], str(expected))
        self.assertEqual((self.first / 'automation/config.json').read_bytes(), config_before)
        self.assertEqual((vault / 'personal-note.md').read_bytes(), note_before)

    def test_pull_explicit_machine_paths_override_saved_paths(self):
        self.local_runtime(self.first)
        vault = self.root / 'explicit vault'
        home = self.root / 'explicit home'
        node = self.root / 'explicit node'
        node.write_text('#!/bin/sh\nprintf "v22.0.0\\n"\n')
        node.chmod(0o755)
        result = self.sync(self.first, 'pull', '--vault', str(vault),
                           '--claude-home', str(home), '--node', str(node))
        self.assert_success(result)
        args = self.bootstrap_calls()[-1]
        for flag, expected in (('--vault', vault), ('--claude-home', home), ('--node', node)):
            self.assertEqual(args[args.index(flag) + 1], str(expected))

    def test_dry_run_works_offline_and_only_previews_local_bootstrap(self):
        self.local_runtime(self.first)
        self.git(self.first, 'remote', 'set-url', 'origin', str(self.root / 'offline-origin.git'))
        config_before = (self.first / 'automation/config.json').read_bytes()
        result = self.sync(self.first, 'pull', '--dry-run')
        self.assert_success(result)
        self.assertEqual(self.head(self.first), self.initial_head)
        calls = self.bootstrap_calls()
        self.assertEqual(len(calls), 1)
        self.assertNotIn('--apply', calls[0])
        self.assertIn('--install-plugins', calls[0])
        self.assertEqual((self.first / 'automation/config.json').read_bytes(), config_before)

    def test_noop_push_does_not_create_an_empty_commit(self):
        result = self.sync(self.first, 'push')
        self.assert_success(result)
        self.assertEqual(self.head(self.first), self.initial_head)
        self.assertEqual(self.remote_head(), self.initial_head)
        self.assertEqual(self.git(self.first, 'status', '--porcelain').stdout, '')

    def test_failed_push_retry_reuses_the_existing_local_commit(self):
        hook = self.origin / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\necho "Synthetic temporary rejection" >&2\nexit 1\n')
        hook.chmod(0o755)
        self.change(self.first)
        first = self.sync(self.first, 'push', '-m', 'Keep this commit for retry')
        self.assertNotEqual(first.returncode, 0)
        committed = self.head(self.first)
        self.assertNotEqual(committed, self.initial_head)
        self.assertEqual(self.remote_head(), self.initial_head)
        hook.unlink()
        second = self.sync(self.first, 'push', '-m', 'Do not create a duplicate')
        self.assert_success(second)
        self.assertEqual(self.head(self.first), committed)
        self.assertEqual(self.remote_head(), committed)
        self.assertEqual(self.git(self.first, 'rev-list', '--count', self.initial_head + '..HEAD').stdout.strip(), '1')

    def test_failed_apply_can_retry_after_git_is_already_up_to_date(self):
        remote = self.publish_from_second()
        failed_env = {**self.env, 'TEST_BOOTSTRAP_FAIL': '23'}
        first = self.sync(self.first, 'pull', env=failed_env)
        self.assertNotEqual(first.returncode, 0)
        self.assertEqual(self.head(self.first), remote)
        second = self.sync(self.first, 'pull')
        self.assert_success(second)
        self.assertEqual(self.head(self.first), remote)
        self.assertEqual(len(self.bootstrap_calls()), 2)
        self.assertTrue(all('--apply' in args for args in self.bootstrap_calls()))


    def test_pull_accepts_a_new_shared_document_from_another_machine(self):
        target = self.second / 'docs/new-topic.md'
        target.write_text('# New shared setup guidance\n\nSynthetic documentation.\n')
        self.git(self.second, 'add', '--', 'docs/new-topic.md')
        self.git(self.second, 'commit', '-m', 'Add shared setup documentation')
        self.git(self.second, 'push', 'origin', 'main')
        result = self.sync(self.first, 'pull')
        self.assert_success(result)
        self.assertEqual((self.first / 'docs/new-topic.md').read_bytes(), target.read_bytes())
        self.assertEqual(self.head(self.first), self.head(self.second))
        self.assertEqual(len(self.bootstrap_calls()), 1)

    def test_pull_rejects_incoming_vault_files_before_checkout_or_apply(self):
        remote_vault = self.second / 'obsidian'
        remote_vault.mkdir()
        (remote_vault / 'incoming-note.md').write_text('Synthetic excluded remote knowledge.\n')
        self.git(self.second, 'add', '-f', '--', 'obsidian/incoming-note.md')
        self.git(self.second, 'commit', '-m', 'Synthetic forbidden incoming vault file')
        self.git(self.second, 'push', 'origin', 'main')
        result = self.sync(self.first, 'pull')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.head(self.first), self.initial_head)
        self.assertFalse((self.first / 'obsidian/incoming-note.md').exists())
        self.assertEqual(self.bootstrap_calls(), [])

    def test_pull_rejects_incoming_symlink_in_shared_document_area(self):
        (self.second / 'docs/reference.md').symlink_to('../../outside-private-note.md')
        self.git(self.second, 'add', '--', 'docs/reference.md')
        self.git(self.second, 'commit', '-m', 'Synthetic forbidden shared symlink')
        self.git(self.second, 'push', 'origin', 'main')
        result = self.sync(self.first, 'pull')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.head(self.first), self.initial_head)
        self.assertFalse((self.first / 'docs/reference.md').is_symlink())
        self.assertEqual(self.bootstrap_calls(), [])

    def test_push_rejects_an_allowlisted_file_replaced_with_a_symlink(self):
        outside = self.root / 'outside-private-note.md'
        outside.write_text('Synthetic private content.\n')
        target = self.first / 'README.md'
        target.unlink()
        target.symlink_to(outside)
        result = self.sync(self.first, 'push')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.head(self.first), self.initial_head)
        self.assertEqual(self.remote_head(), self.initial_head)
        self.assertTrue(target.is_symlink())
        self.assertEqual(outside.read_text(), 'Synthetic private content.\n')

    def test_launcher_falls_back_when_default_python_is_too_old(self):
        bins = self.root / 'launcher bins'
        bins.mkdir()
        old = bins / 'python3'
        old.write_text('#!/bin/sh\nexit 1\n')
        old.chmod(0o755)
        (bins / 'python3.11').symlink_to(sys.executable)
        env = {**self.env, 'PATH': str(bins) + os.pathsep + '/usr/bin:/bin'}
        result = self.sync(self.first, 'push', env=env)
        self.assert_success(result)
        self.assertEqual(self.head(self.first), self.initial_head)

    def test_launcher_explicit_python_path_with_spaces_is_one_argument(self):
        selected = self.root / 'selected Python executable'
        selected.symlink_to(sys.executable)
        result = self.sync(self.first, 'push', env={**self.env, 'CLAUDE_SYNC_PYTHON': str(selected)})
        self.assert_success(result)
        self.assertEqual(self.head(self.first), self.initial_head)

    def test_launcher_rejects_invalid_explicit_python_without_fallback(self):
        old = self.root / 'old Python executable'
        old.write_text('#!/bin/sh\nexit 1\n')
        old.chmod(0o755)
        result = self.sync(self.first, 'push', env={**self.env, 'CLAUDE_SYNC_PYTHON': str(old)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.head(self.first), self.initial_head)
        self.assertEqual(self.remote_head(), self.initial_head)


if __name__ == '__main__':
    unittest.main()
