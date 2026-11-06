"""Portable restore tests use only temporary homes and a fake local Node binary."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/bootstrap.py'
SPEC = importlib.util.spec_from_file_location('bootstrap', SCRIPT)
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class MergeTests(unittest.TestCase):
    def test_preserves_unrelated_settings_and_shell_quotes_spaces(self):
        existing = {'env': {'KEEP': 'yes', 'PATH': '/usr/bin:/custom/bin'},
                    'enabledPlugins': {'unrelated@market': False},
                    'permissions': {'allow': ['Read(/project/**)'], 'deny': ['Bash(rm *)']},
                    'hooks': {'Stop': [{'matcher': 'custom', 'hooks': [
                        {'type': 'command', 'command': 'echo other'}]}]},
                    'customSetting': {'keep': 1}}
        merged, state = bootstrap.merge_settings(existing, Path('/space dir/automation'),
            Path('/other vault'), Path('/python dir/python3'), Path('/node dir/node'), {}, '/fallback')
        self.assertEqual(merged['env']['KEEP'], 'yes')
        self.assertEqual(merged['env']['PATH'], '/python dir:/node dir:/usr/bin:/custom/bin')
        self.assertEqual(merged['enabledPlugins'], existing['enabledPlugins'])
        self.assertEqual(merged['permissions']['deny'], ['Bash(rm *)'])
        self.assertEqual(merged['customSetting'], {'keep': 1})
        self.assertEqual(merged['hooks']['Stop'][0], existing['hooks']['Stop'][0])
        command = merged['hooks']['Stop'][-1]['hooks'][0]['command']
        self.assertEqual(shlex.split(command), ['/python dir/python3', '/space dir/automation/memory_hooks.py'])
        for rule in state['permissionRules']:
            prefix = rule[len('Bash('):-len(' *)')]
            self.assertEqual(shlex.split(prefix)[-1], '/space dir/automation/memory_cli.py')
        self.assertNotIn('autoMemoryEnabled', existing)

    def test_idempotent_and_migration_preserves_shared_hook_group(self):
        first, state = bootstrap.merge_settings({}, Path('/old/automation'), Path('/vault'),
            Path('/bin/python3'), Path('/bin/node'), {}, '/usr/bin')
        first['hooks']['Stop'][0]['hooks'].append({'type': 'command', 'command': 'echo retain'})
        second, state2 = bootstrap.merge_settings(first, Path('/new/automation'), Path('/vault'),
            Path('/bin/python3'), Path('/bin/node'), state, '/usr/bin')
        self.assertEqual(second['hooks']['Stop'][0]['hooks'], [{'type': 'command', 'command': 'echo retain'}])
        self.assertNotIn('/old/', json.dumps(second))
        third, state3 = bootstrap.merge_settings(second, Path('/new/automation'), Path('/vault'),
            Path('/bin/python3'), Path('/bin/node'), state2, '/ignored')
        self.assertEqual(second, third)
        self.assertEqual(state2, state3)

    def test_adopting_existing_permission_rules_is_immediately_idempotent(self):
        arguments = (Path('/setup/automation'), Path('/vault'),
                     Path('/bin/python3'), Path('/bin/node'))
        _, baseline = bootstrap.merge_settings({}, *arguments, {}, '/usr/bin')
        existing = {'permissions': {'allow': [baseline['permissionRules'][0],
                    'Read(/project/**)', baseline['permissionRules'][1], 'Bash(git status)']}}
        first, state = bootstrap.merge_settings(existing, *arguments, {}, '/usr/bin')
        second, state2 = bootstrap.merge_settings(first, *arguments, state, '/usr/bin')
        self.assertEqual(first, second)
        self.assertEqual(state, state2)
        self.assertEqual([rule for rule in first['permissions']['allow']
                          if rule not in state['permissionRules']],
                         ['Read(/project/**)', 'Bash(git status)'])

    def test_managed_policy_keeps_user_text_and_changes_only_block(self):
        first = bootstrap.managed_instructions('Keep personal rule.\n', 'managed old')
        second = bootstrap.managed_instructions(first, 'managed new')
        self.assertTrue(second.startswith('Keep personal rule.\n\n'))
        self.assertNotIn('managed old', second)
        self.assertEqual(second.count(bootstrap.BEGIN), 1)
        self.assertEqual(second, bootstrap.managed_instructions(second, 'managed new'))
        with self.assertRaises(ValueError):
            bootstrap.managed_instructions(bootstrap.BEGIN, 'x')


class MemoryProfileTests(unittest.TestCase):
    arguments = (Path('/setup/automation'), Path('/vault'), Path('/bin/python3'), Path('/bin/node'))

    def test_none_adds_no_hooks_env_or_rules_and_keeps_user_entries(self):
        existing = {'hooks': {'Stop': [{'hooks': [{'type': 'command', 'command': 'echo other'}]}]},
                    'env': {'KEEP': 'yes'}, 'permissions': {'allow': ['Bash(git status)']}}
        merged, state = bootstrap.merge_settings(existing, *self.arguments, {}, '/usr/bin', 'none')
        self.assertEqual(merged['hooks'], existing['hooks'])
        self.assertEqual(merged['env'], {'KEEP': 'yes'})
        self.assertEqual(merged['permissions'], {'allow': ['Bash(git status)']})
        self.assertTrue(merged['autoMemoryEnabled'])
        self.assertEqual(state['memory'], 'none')

    def test_none_on_empty_settings_adds_only_auto_memory(self):
        merged, _ = bootstrap.merge_settings({}, *self.arguments, {}, '/usr/bin', 'none')
        self.assertEqual(merged, {'autoMemoryEnabled': True})

    def test_switching_full_to_none_removes_only_owned_entries(self):
        full, state = bootstrap.merge_settings({'env': {'KEEP': 'yes'}}, *self.arguments, {}, '/usr/bin')
        full['hooks']['Stop'].append({'hooks': [{'type': 'command', 'command': 'echo other'}]})
        none, state2 = bootstrap.merge_settings(full, *self.arguments, state, '/usr/bin', 'none')
        self.assertNotIn('memory_hooks.py', json.dumps(none['hooks']))
        self.assertEqual(none['hooks']['Stop'], [{'hooks': [{'type': 'command', 'command': 'echo other'}]}])
        self.assertNotIn('SessionStart', none['hooks'])
        self.assertNotIn('CLAUDE_OBSIDIAN_VAULT', none['env'])
        self.assertEqual(none['env']['KEEP'], 'yes')
        self.assertFalse(any('memory_cli.py' in rule for rule in none['permissions']['allow']))
        again, state3 = bootstrap.merge_settings(none, *self.arguments, state2, '/usr/bin', 'none')
        self.assertEqual(again, none)
        self.assertEqual(state3, state2)

    def test_profile_sections_in_template(self):
        text = 'a\n<!-- memory:full -->\nF\n<!-- /memory:full -->\n<!-- memory:none -->\nN\n<!-- /memory:none -->\nz\n'
        self.assertEqual(bootstrap.select_profile_sections(text, 'full'), 'a\nF\nz\n')
        self.assertEqual(bootstrap.select_profile_sections(text, 'none'), 'a\nN\nz\n')
        with self.assertRaises(ValueError):
            bootstrap.select_profile_sections('<!-- memory:full -->\nF\n', 'full')

    def test_real_template_renders_both_profiles(self):
        values = {'VAULT_PATH': '/v', 'AUTOMATION_DIR': '/a', 'PYTHON_PATH': '/p', 'NODE_PATH': '/n'}
        template = SCRIPT.parents[1] / 'config/CLAUDE.md.tmpl'
        full = bootstrap.render(template, values, 'full')
        none = bootstrap.render(template, values, 'none')
        self.assertIn('episodic-memory to retrieve', full)
        self.assertNotIn('episodic-memory', none)
        self.assertNotIn('AUTOMATION.md', none)
        self.assertIn('native Auto memory', none)


class FilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / 'clone with spaces'
        self.home = self.root / 'fake Claude home'
        self.vault = self.root / 'missing vault'
        (self.repo / 'scripts').mkdir(parents=True)
        (self.repo / 'config').mkdir()
        (self.repo / 'automation').mkdir()
        for name in ('memory_hooks.py', 'memory_cli.py', 'episodic_search.mjs'):
            (self.repo / 'automation' / name).write_text('# fixture\n')
        (self.repo / 'config/CLAUDE.md.tmpl').write_text('Vault {{VAULT_PATH}}; scripts {{AUTOMATION_DIR}}\n')
        (self.repo / 'automation/AUTOMATION.md.tmpl').write_text('Python {{PYTHON_PATH}}; node {{NODE_PATH}}\n')
        (self.repo / 'config/plugins.json').write_text(json.dumps({'marketplaces': [
            {'name': 'test', 'source': 'example/test'}], 'plugins': [
            {'id': 'first@test', 'version_verified': '1.0'},
            {'id': 'optional@test', 'optional': True}]}))
        self.patcher = patch.object(bootstrap, '__file__', str(self.repo / 'scripts/bootstrap.py'))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.runtime = patch.object(bootstrap, 'detect_runtimes', return_value=(Path('/bin/python3'), Path('/bin/node')))
        self.runtime.start()
        self.addCleanup(self.runtime.stop)

    def args(self):
        return ['--claude-home', str(self.home), '--vault', str(self.vault)]

    def tree(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_dry_run_makes_no_writes_or_plugin_calls(self):
        before = self.tree()
        with patch.object(bootstrap.subprocess, 'run') as run:
            self.assertEqual(bootstrap.main(self.args() + ['--install-plugins']), 0)
            run.assert_not_called()
        self.assertEqual(self.tree(), before)
        self.assertFalse(self.home.exists())
        self.assertFalse(self.vault.exists())

    def test_apply_then_repeat_is_noop_and_never_creates_vault(self):
        self.home.mkdir()
        (self.home / 'settings.json').write_text('{"env":{"KEEP":"value"},"hooks":{}}\n')
        (self.home / 'CLAUDE.md').write_text('Personal text.\n')
        self.assertEqual(bootstrap.main(self.args() + ['--apply']), 0)
        first = self.tree()
        self.assertEqual(bootstrap.main(self.args() + ['--apply']), 0)
        self.assertEqual(self.tree(), first)
        self.assertFalse(self.vault.exists())
        config = json.loads((self.repo / 'automation/config.json').read_text())
        self.assertEqual(config['vaultPath'], str(self.vault))
        self.assertEqual(config['registryPath'], str(self.home / 'plugins/installed_plugins.json'))
        self.assertTrue((self.home / 'CLAUDE.md').read_text().startswith('Personal text.'))
        self.assertEqual(json.loads((self.home / 'settings.json').read_text())['env']['KEEP'], 'value')
        backups = list((self.home / 'setup-backups').glob('*'))
        self.assertEqual(len(backups), 1)

    def test_none_profile_skips_memory_plugins_and_automation_and_is_remembered(self):
        manifest = json.loads((self.repo / 'config/plugins.json').read_text())
        manifest['plugins'].append({'id': 'memory@test', 'memory': True})
        (self.repo / 'config/plugins.json').write_text(json.dumps(manifest))
        commands = bootstrap.plugin_commands(self.repo, self.home, False, 'none')
        self.assertNotIn(['plugin', 'install', 'memory@test', '--scope', 'user', '--json'], commands)
        self.assertIn(['plugin', 'install', 'first@test', '--scope', 'user', '--json'], commands)
        self.assertEqual(bootstrap.main(self.args() + ['--apply', '--memory', 'none']), 0)
        self.assertFalse((self.repo / 'automation/config.json').exists())
        self.assertEqual(bootstrap.resolve_memory(None, self.home), 'none')
        first = self.tree()
        self.assertEqual(bootstrap.main(self.args() + ['--apply']), 0)  # reuses stored profile
        self.assertEqual(self.tree(), first)

    def test_plugin_install_updates_are_not_overwritten(self):
        def fake_run(argv, **kwargs):
            if argv[1:3] == ['plugin', 'install']:
                settings = bootstrap.read_object(self.home / 'settings.json')
                settings['enabledPlugins'] = {'first@test': True}
                (self.home / 'settings.json').write_text(json.dumps(settings))
            return None
        with patch.object(bootstrap.shutil, 'which', return_value='/fake/claude'), \
                patch.object(bootstrap.subprocess, 'run', side_effect=fake_run) as run:
            self.assertEqual(bootstrap.main(self.args() + ['--apply', '--install-plugins']), 0)
        self.assertEqual(run.call_count, 2)
        settings = bootstrap.read_object(self.home / 'settings.json')
        self.assertEqual(settings['enabledPlugins'], {'first@test': True})
        self.assertEqual(run.call_args.kwargs['env']['CLAUDE_CONFIG_DIR'], str(self.home))

    def test_symlink_output_is_rejected_without_write(self):
        self.home.mkdir()
        target = self.root / 'other-settings.json'
        target.write_text('{}')
        (self.home / 'settings.json').symlink_to(target)
        with self.assertRaises(ValueError):
            bootstrap.main(self.args() + ['--apply'])
        self.assertEqual(target.read_text(), '{}')


if __name__ == '__main__':
    unittest.main()
