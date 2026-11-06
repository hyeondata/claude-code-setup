#!/usr/bin/env python3
"""Restore portable Claude settings; preview by default, never copy vault data."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile

BEGIN = '<!-- BEGIN claude-code-setup managed instructions -->'
END = '<!-- END claude-code-setup managed instructions -->'
OWNER = 'claude-code-setup'
MEMORY_PROFILES = ('full', 'none')
MANAGED_ENV = ('CLAUDE_OBSIDIAN_VAULT', 'CLAUDE_OBSIDIAN_SESSION_CONTEXT',
               'CLAUDE_OBSIDIAN_SESSION_CONTEXT_VAULT', 'EPISODIC_MEMORY_SKIP_SUMMARIES',
               'EPISODIC_MEMORY_DISABLE_AUTO_SYNC')
EVENTS = {
    'SessionStart': ('startup|resume|clear|compact|fork', 8),
    'UserPromptSubmit': (None, 15),
    'Stop': (None, 8),
    'SessionEnd': (None, 8),
}


def read_object(path: Path) -> dict:
    if path.is_symlink():
        raise ValueError(f'Refusing a symlink configuration file: {path}')
    if not path.exists():
        return {}
    if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError(f'Expected a bounded regular JSON file: {path}')
    result = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(result, dict):
        raise ValueError(f'Expected a JSON object: {path}')
    return result


def canonical(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def json_text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def select_profile_sections(content: str, memory: str) -> str:
    """Keep `<!-- memory:<profile> -->` blocks for the chosen profile and drop the others."""
    def keep(match: re.Match) -> str:
        return match.group(2) if match.group(1) == memory else ''
    content = re.sub(r'<!-- memory:(\w+) -->\n(.*?)<!-- /memory:\1 -->\n', keep, content, flags=re.S)
    if '<!-- memory:' in content or '<!-- /memory:' in content:
        raise ValueError('Malformed memory profile markers in template')
    return re.sub(r'\n{3,}', '\n\n', content)


def render(template: Path, values: dict[str, str], memory: str = 'full') -> str:
    content = select_profile_sections(template.read_text(encoding='utf-8'), memory)
    for name, value in values.items():
        content = content.replace('{{' + name + '}}', value)
    if re.search(r'\{\{[A-Z_]+\}\}', content):
        raise ValueError(f'Unresolved template placeholder: {template}')
    return content


def managed_instructions(existing: str, instructions: str) -> str:
    block = BEGIN + '\n' + instructions.rstrip() + '\n' + END
    if BEGIN in existing or END in existing:
        if existing.count(BEGIN) != 1 or existing.count(END) != 1:
            raise ValueError('CLAUDE.md has malformed or duplicate managed markers')
        start, finish = existing.index(BEGIN), existing.index(END)
        if finish < start:
            raise ValueError('CLAUDE.md managed markers are out of order')
        return existing[:start] + block + existing[finish + len(END):]
    if existing.strip() == instructions.strip():
        return block + '\n'
    separator = '\n\n' if existing.strip() else ''
    return existing.rstrip() + separator + block + '\n'


def is_owned_command(command: object, script_paths: set[str]) -> bool:
    if not isinstance(command, str):
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    return len(parts) == 2 and parts[1] in script_paths


def merge_settings(existing: dict, automation: Path, vault: Path,
                   python: Path, node: Path, previous: dict,
                   environment_path: str, memory: str = 'full') -> tuple[dict, dict]:
    """memory='none' keeps only native Auto memory: owned hooks, env and permission rules are removed, not added."""
    result = copy.deepcopy(existing)
    hooks = result.setdefault('hooks', {})
    env = result.setdefault('env', {})
    permissions = result.setdefault('permissions', {})
    allow = permissions.setdefault('allow', [])
    if not all(isinstance(x, dict) for x in (hooks, env, permissions)) or not isinstance(allow, list):
        raise ValueError('Existing hooks/env/permissions have unexpected types')
    script = str(automation / 'memory_hooks.py')
    previous = previous if previous.get('managedBy') == OWNER else {}
    owned_paths = {script}
    old_script = previous.get('hookScript')
    if isinstance(old_script, str):
        owned_paths.add(old_script)
    command = shlex.join([str(python), script])
    for event, (matcher, timeout) in EVENTS.items():
        retained = []
        groups = hooks.get(event, [])
        if not isinstance(groups, list):
            raise ValueError(f'Existing {event} hook groups must be a list')
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get('hooks'), list):
                raise ValueError(f'Existing {event} hook group is malformed')
            remaining = [hook for hook in group['hooks']
                         if not (isinstance(hook, dict) and is_owned_command(hook.get('command'), owned_paths))]
            if remaining or not group['hooks']:
                retained.append({**group, 'hooks': remaining})
        entry = {'hooks': [{'type': 'command', 'command': command, 'timeout': timeout}]}
        if matcher is not None:
            entry['matcher'] = matcher
        if memory == 'full':
            retained.append(entry)
        if retained:
            hooks[event] = retained
        else:
            hooks.pop(event, None)
    if memory == 'none':
        if previous:  # only keys this setup wrote earlier; user-set values stay
            for key in previous.get('envKeys', MANAGED_ENV):
                env.pop(key, None)
        owned_rules = set(previous.get('permissionRules', []))
        permissions['allow'] = [rule for rule in allow if rule not in owned_rules]
        if not allow and permissions == {'allow': []} and 'permissions' not in existing:
            result.pop('permissions')
        for key in ('env', 'hooks'):
            if not result[key] and key not in existing:
                result.pop(key)
        result['autoMemoryEnabled'] = True
        state = {'managedBy': OWNER, 'schemaVersion': 2, 'memory': 'none', 'hookScript': script,
                 'permissionRules': [], 'envKeys': []}
        return result, state
    env.update({
        'CLAUDE_OBSIDIAN_VAULT': str(vault),
        'CLAUDE_OBSIDIAN_SESSION_CONTEXT': '1',
        'CLAUDE_OBSIDIAN_SESSION_CONTEXT_VAULT': str(vault),
        'EPISODIC_MEMORY_SKIP_SUMMARIES': '1',
        'EPISODIC_MEMORY_DISABLE_AUTO_SYNC': '1',
    })
    old_path = env.get('PATH', environment_path)
    if not isinstance(old_path, str):
        raise ValueError('Existing env.PATH must be a string')
    prepend = [str(python.parent), str(node.parent)]
    env['PATH'] = os.pathsep.join(dict.fromkeys(prepend + old_path.split(os.pathsep)))
    adapter = str(automation / 'memory_cli.py')
    # Quote each executable/path as a shell token, including paths with spaces.
    rules = ['Bash(' + shlex.join([interpreter, adapter]) + ' *)'
             for interpreter in ('python3', str(python))]
    owned_rules = set(previous.get('permissionRules', [])) | set(rules)
    permissions['allow'] = [rule for rule in allow if rule not in owned_rules]
    permissions['allow'] += [rule for rule in rules if rule not in permissions['allow']]
    result['autoMemoryEnabled'] = True
    state = {'managedBy': OWNER, 'schemaVersion': 2, 'memory': 'full', 'hookScript': script,
             'permissionRules': rules, 'envKeys': list(MANAGED_ENV)}
    return result, state


def detect_runtimes(node_option: str | None) -> tuple[Path, Path]:
    if os.name != 'posix':
        raise ValueError('This setup supports macOS/Linux; use WSL on Windows')
    if sys.version_info < (3, 10):
        raise ValueError('Python 3.10 or newer is required')
    python = canonical(sys.executable)
    candidate = node_option or shutil.which('node')
    if not candidate:
        raise ValueError('Node.js 20+ is required; install it before running this script')
    node = canonical(candidate)
    version = subprocess.run([str(node), '--version'], check=True, capture_output=True,
                             text=True, timeout=10).stdout.strip()
    match = re.fullmatch(r'v(\d+)\.\d+\.\d+(?:[-+].*)?', version)
    if not match or int(match.group(1)) < 20:
        raise ValueError('Node.js 20+ is required')
    return python, node


def plugin_commands(repo: Path, claude_home: Path, optional: bool,
                    memory: str = 'full') -> list[list[str]]:
    manifest = read_object(repo / 'config/plugins.json')
    selected = [item for item in manifest.get('plugins', [])
                if (optional or not item.get('optional')) and (memory == 'full' or not item.get('memory'))]
    needed_markets = {item['id'].rsplit('@', 1)[1] for item in selected}
    known = read_object(claude_home / 'plugins/known_marketplaces.json')
    installed = read_object(claude_home / 'plugins/installed_plugins.json').get('plugins', {})
    commands = []
    for market in manifest.get('marketplaces', []):
        if market['name'] in needed_markets and market['name'] not in known:
            commands.append(['plugin', 'marketplace', 'add', market['source'], '--scope', 'user', '--json'])
    for plugin in selected:
        records = installed.get(plugin['id'], [])
        if not any(isinstance(record, dict) and record.get('scope') == 'user' for record in records):
            commands.append(['plugin', 'install', plugin['id'], '--scope', 'user', '--json'])
    return commands


def resolve_memory(option: str | None, claude_home: Path) -> str:
    """Explicit --memory wins; otherwise reuse this machine's last applied profile; default full."""
    if option:
        return option
    previous = read_object(claude_home / 'claude-code-setup-state.json')
    stored = previous.get('memory') if previous.get('managedBy') == OWNER else None
    return stored if stored in MEMORY_PROFILES else 'full'


def plan_files(repo: Path, setup: Path, claude_home: Path, vault: Path,
               python: Path, node: Path, memory: str = 'full') -> dict[Path, str]:
    automation = setup / 'automation'
    for name in ('memory_hooks.py', 'memory_cli.py', 'episodic_search.mjs'):
        if not (automation / name).is_file():
            raise ValueError(f'Missing automation script: {automation / name}; use the cloned repository as --setup-dir')
    values = {'VAULT_PATH': str(vault), 'AUTOMATION_DIR': str(automation),
              'PYTHON_PATH': str(python), 'NODE_PATH': str(node)}
    state_path = claude_home / 'claude-code-setup-state.json'
    settings, state = merge_settings(read_object(claude_home / 'settings.json'), automation,
                                     vault, python, node, read_object(state_path), os.environ.get('PATH', ''),
                                     memory)
    policy_path = claude_home / 'CLAUDE.md'
    if policy_path.is_symlink():
        raise ValueError(f'Refusing a symlink instruction file: {policy_path}')
    existing = policy_path.read_text(encoding='utf-8') if policy_path.exists() else ''
    policy = managed_instructions(existing, render(repo / 'config/CLAUDE.md.tmpl', values, memory))
    plan = {
        claude_home / 'settings.json': json_text(settings),
        policy_path: policy,
        state_path: json_text(state),
    }
    if memory == 'none':
        return plan
    return {
        **plan,
        automation / 'config.json': json_text({'vaultPath': str(vault),
            'registryPath': str(claude_home / 'plugins/installed_plugins.json'),
            'pythonPath': str(python), 'nodePath': str(node)}),
        automation / 'AUTOMATION.md': render(repo / 'automation/AUTOMATION.md.tmpl', values),
    }


def optional_tool_notes() -> list[str]:
    """Machine-local tools this repository documents but does not install (see README)."""
    notes = []
    if not shutil.which('graphify'):
        notes.append('Optional tool not found: graphify (README "graphify"; uv tool install graphifyy, then graphify install --platform claude).')
    return notes


def changed_files(plan: dict[Path, str]) -> dict[Path, str]:
    result = {}
    for path, content in plan.items():
        if path.is_symlink():
            raise ValueError(f'Refusing a symlink output file: {path}')
        if not path.exists() or path.read_text(encoding='utf-8') != content:
            result[path] = content
    return result


def backup_files(paths: list[Path], claude_home: Path) -> Path:
    directory = claude_home / 'setup-backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f-portable')
    directory.mkdir(parents=True, mode=0o700)
    manifest = []
    for index, path in enumerate(dict.fromkeys(paths)):
        if path.is_symlink():
            raise ValueError(f'Refusing to back up a symlink output: {path}')
        record = {'path': str(path), 'existed': path.exists()}
        if path.exists():
            name = f'{index:02d}-{path.name}'
            shutil.copy2(path, directory / name)
            os.chmod(directory / name, 0o600)
            record['backup'] = name
        manifest.append(record)
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return directory


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Write settings; otherwise only preview')
    parser.add_argument('--install-plugins', action='store_true', help='Install missing selected plugins, only with --apply')
    parser.add_argument('--with-optional', action='store_true', help='Include optional plugins such as Dart/Flutter')
    parser.add_argument('--vault', default='~/claude/obsidian', help='Separate local vault; never initialized or copied here')
    parser.add_argument('--claude-home', default='~/.claude')
    parser.add_argument('--setup-dir', help='Cloned repository containing automation scripts')
    parser.add_argument('--node', help='Node.js 20+ executable if absent from PATH')
    parser.add_argument('--memory', choices=MEMORY_PROFILES,
                        help='full: episodic-memory, claude-obsidian and lifecycle hooks; none: native Auto memory only '
                             '(for machines with their own memory system). Default: last applied profile, else full')
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[1]
    setup = canonical(args.setup_dir or repo)
    claude_home = canonical(args.claude_home)
    vault = canonical(args.vault)
    python, node = detect_runtimes(args.node)
    memory = resolve_memory(args.memory, claude_home)
    plan = plan_files(repo, setup, claude_home, vault, python, node, memory)
    changed = changed_files(plan)
    commands = plugin_commands(repo, claude_home, args.with_optional, memory) if args.install_plugins else []
    print('Mode:', 'APPLY' if args.apply else 'DRY RUN (no writes or installations)')
    print('Claude configuration:', claude_home)
    print('Memory profile:', memory)
    if memory == 'full':
        print('Local vault (contents excluded from this setup):', vault)
    for path in changed:
        print('Write:', path)
    for command in commands:
        print('Run:', shlex.join(['claude', *command]))
    for note in optional_tool_notes():
        print(note)
    if memory == 'full' and not vault.is_dir():
        print('Prerequisite: restore or initialize the vault separately. Configuration can be installed first.')
    if not args.install_plugins:
        print('Plugins are not installed by this invocation; use --apply --install-plugins to install missing plugins.')
    if not args.apply:
        return 0
    claude = shutil.which('claude') if commands else None
    if commands and not claude:
        raise ValueError('Claude Code CLI is required before --install-plugins')
    if not changed and not commands:
        print('Already configured; nothing changed.')
        return 0
    backup_targets = list(plan)
    if commands:
        backup_targets += [claude_home / 'plugins/installed_plugins.json',
                           claude_home / 'plugins/known_marketplaces.json']
    backup = backup_files(backup_targets, claude_home)
    print('Backup:', backup)
    print('Rollback: restore existing files from manifest.json; remove only generated files marked existed=false.')
    if commands:
        env = os.environ.copy()
        # The default home must not be passed explicitly: with CLAUDE_CONFIG_DIR set, the CLI reads
        # <dir>/.claude.json instead of ~/.claude.json and creates a fresh, empty global config there.
        if claude_home != canonical('~/.claude'):
            env['CLAUDE_CONFIG_DIR'] = str(claude_home)
        else:
            env.pop('CLAUDE_CONFIG_DIR', None)
        for command in commands:
            subprocess.run([claude, *command], check=True, env=env)
        # Native installation edits settings; merge again rather than overwrite its updates.
        plan = plan_files(repo, setup, claude_home, vault, python, node, memory)
        changed = changed_files(plan)
    for path, content in changed.items():
        atomic_write(path, content)
    print('Applied. Start a new Claude Code session. Authenticate external services separately on this machine.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        raise SystemExit(1)
