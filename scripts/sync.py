#!/usr/bin/env python3
"""Commit/push shared settings, or pull them and restore this machine's setup."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys

ALLOWED_FILES = frozenset({
    '.gitignore', 'README.md', 'claude-sync',
    'automation/AUTOMATION.md.tmpl', 'automation/episodic_search.mjs',
    'automation/memory_cli.py', 'automation/memory_hooks.py',
    'config/CLAUDE.md.tmpl', 'config/plugins.json',
    'docs/00-index.md', 'docs/01-development.md', 'docs/02-memory-knowledge.md',
    'docs/03-integrations.md', 'docs/04-recommended-stack.md',
    'docs/05-memory-automation.md', 'docs/06-installation-operations.md',
    'docs/07-claude-policy.md', 'docs/08-built-in-features.md',
    'docs/09-memory-research.md', 'docs/10-development-research.md',
    'docs/11-integration-research.md', 'docs/12-priorities.md',
    'docs/13-installed-memory.md', 'docs/14-skill-routing.md',
    'scripts/bootstrap.py', 'scripts/sync.py',
    'tests/test_bootstrap.py', 'tests/test_sync.py',
})


class SyncError(Exception):
    """An unsafe state or failed command that must not be automatically repaired."""


def git(repo: Path, *arguments: str, echo: bool = False) -> bytes:
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GIT_OPTIONAL_LOCKS': '0'}
    result = subprocess.run(['git', *arguments], cwd=repo, env=env,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if result.returncode:
        detail = result.stderr.decode('utf-8', 'replace').strip()
        raise SyncError(f'git {arguments[0]} failed: {detail or "see Git configuration/authentication"}')
    if echo:
        for output in (result.stdout, result.stderr):
            if output:
                print(output.decode('utf-8', 'replace').rstrip())
    return result.stdout


def incoming_allowed(name: str) -> bool:
    """Permit source additions during self-update, while excluding local data."""
    if name in {'.gitignore', 'README.md', 'claude-sync'}:
        return True
    parts = PurePosixPath(name).parts
    if len(parts) != 2 or any(part.startswith('.') for part in parts):
        return False
    directory, filename = parts
    if directory == 'config':
        return filename == 'plugins.json' or filename.endswith('.tmpl')
    if directory == 'automation':
        return filename.endswith(('.py', '.mjs', '.tmpl'))
    if directory == 'scripts':
        return filename.endswith('.py')
    if directory == 'tests':
        return filename.startswith('test_') and filename.endswith('.py')
    return directory == 'docs' and filename.endswith('.md')


def validate_entry(name: str, mode: str, *, incoming: bool = False) -> None:
    permitted = incoming_allowed(name) if incoming else name in ALLOWED_FILES
    if not permitted:
        raise SyncError(f'Unapproved tracked/staged/history path: {name!r}. Local data must stay out of Git.')
    if mode not in {'100644', '100755'}:
        raise SyncError(f'Symlinks, submodules, and non-regular files are not shared: {name!r}')


def audit_tree(repo: Path, revision: str, *, incoming: bool = False) -> None:
    for entry in git(repo, 'ls-tree', '-r', '-z', '--full-tree', revision).split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        mode, kind, _ = metadata.decode('ascii').split()
        name = raw_name.decode('utf-8', 'surrogateescape')
        validate_entry(name, mode, incoming=incoming)
        if kind != 'blob':
            raise SyncError(f'Non-file Git object cannot be shared: {name!r}')


def audit_history(repo: Path, revisions: str, *, incoming: bool = False) -> None:
    for revision in git(repo, 'rev-list', revisions).decode('ascii').splitlines():
        audit_tree(repo, revision, incoming=incoming)


def audit_index(repo: Path) -> None:
    for entry in git(repo, 'ls-files', '--stage', '-z').split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        mode, _, stage = metadata.decode('ascii').split()
        name = raw_name.decode('utf-8', 'surrogateescape')
        validate_entry(name, mode)
        if stage != '0':
            raise SyncError('Resolve the existing Git conflict before syncing.')


def audit_shared_worktree(repo: Path, names=ALLOWED_FILES) -> None:
    for name in names:
        path = repo / name
        current = path
        while current != repo:
            if current.is_symlink():
                raise SyncError(f'Shared file or its parent is a symlink: {name!r}')
            current = current.parent
        if path.exists() and not stat.S_ISREG(path.stat().st_mode):
            raise SyncError(f'Shared path is not a regular file: {name!r}')


def check_repository(repo: Path) -> None:
    root = git(repo, 'rev-parse', '--show-toplevel').decode().strip()
    if Path(root).resolve() != repo.resolve():
        raise SyncError('Run the launcher from its own settings repository.')
    branch = git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD').decode().strip()
    if branch != 'main':
        raise SyncError('Switch to main before syncing; branches are not changed automatically.')
    git(repo, 'remote', 'get-url', 'origin')
    git(repo, 'show-ref', '--verify', 'refs/remotes/origin/main')
    for operation in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
        raw_path = git(repo, 'rev-parse', '--git-path', operation).decode().strip()
        path = Path(raw_path)
        if (path if path.is_absolute() else repo / path).exists():
            raise SyncError('Finish the existing Git merge/rebase/cherry-pick/revert before syncing.')
    audit_tree(repo, 'HEAD')
    audit_index(repo)
    audit_shared_worktree(repo)


def fetch_main(repo: Path) -> tuple[int, int, str]:
    git(repo, 'fetch', '--no-tags', 'origin', 'refs/heads/main:refs/remotes/origin/main', echo=True)
    behind, ahead = map(int, git(repo, 'rev-list', '--left-right', '--count',
                                 'origin/main...HEAD').decode().split())
    revision = git(repo, 'rev-parse', 'refs/remotes/origin/main').decode().strip()
    return behind, ahead, revision


def push(repo: Path, message: str) -> None:
    if not message.strip():
        raise SyncError('The commit message must not be empty.')
    check_repository(repo)
    behind, ahead, _ = fetch_main(repo)
    if behind:
        state = 'diverged from' if ahead else 'behind'
        raise SyncError(f'Local main is {state} origin/main. Reconcile your changes before pushing; no force push is used.')
    audit_tree(repo, 'origin/main')
    audit_history(repo, 'origin/main..HEAD')
    tracked = set(git(repo, 'ls-files', '-z').decode('utf-8', 'surrogateescape').split('\0'))
    paths = [name for name in sorted(ALLOWED_FILES) if name in tracked or (repo / name).exists()]
    if paths:
        git(repo, 'add', '--all', '--', *(':(literal)' + name for name in paths))
    audit_index(repo)
    if git(repo, 'diff', '--cached', '--name-only', '-z'):
        git(repo, 'commit', '-m', message, echo=True)
    else:
        print('No shared-file changes to commit; retrying any existing local commits.')
    # Audit every outgoing snapshot, including files added and removed in older commits.
    audit_history(repo, 'origin/main..HEAD')
    try:
        git(repo, '-c', 'push.followTags=false', '-c', 'remote.origin.mirror=false',
            'push', 'origin', 'refs/heads/main:refs/heads/main', echo=True)
    except SyncError as exc:
        raise SyncError(f'{exc}\nLocal commits were kept. Fix authentication/network issues and rerun claude-sync push.') from exc
    print('Shared Claude Code settings pushed to origin/main. Local memory data was not staged.')


def absolute_setting(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or not Path(value).is_absolute() or '..' in Path(value).parts:
        raise SyncError(f'Local {label} must be an absolute path without traversal.')
    return value


def preserve_paths(repo: Path, args: argparse.Namespace) -> list[str]:
    config_path = repo / 'automation/config.json'
    config = {}
    if config_path.is_symlink():
        raise SyncError('Local automation/config.json must not be a symlink.')
    if config_path.exists():
        if not config_path.is_file() or config_path.stat().st_size > 65536:
            raise SyncError('Expected a small local automation/config.json file.')
        try:
            config = json.loads(config_path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError) as exc:
            raise SyncError('Local automation/config.json is invalid; repair it before applying settings.') from exc
        if not isinstance(config, dict):
            raise SyncError('Local automation/config.json must be an object.')
    saved_home = None
    if config.get('registryPath') is not None:
        registry = Path(absolute_setting(config['registryPath'], 'registryPath'))
        if registry.parts[-2:] != ('plugins', 'installed_plugins.json') or registry.parent.parent == Path('/'):
            raise SyncError('Local registryPath must be <claude-home>/plugins/installed_plugins.json.')
        saved_home = str(registry.parent.parent)
    saved_vault = absolute_setting(config['vaultPath'], 'vaultPath') if config.get('vaultPath') is not None else None
    saved_node = absolute_setting(config['nodePath'], 'nodePath') if config.get('nodePath') is not None else None
    vault = args.vault or saved_vault or str(repo / 'obsidian')
    home = args.claude_home or saved_home or os.environ.get('CLAUDE_CONFIG_DIR') or str(Path.home() / '.claude')
    node = args.node or saved_node
    flags = ['--setup-dir', str(repo), '--vault', str(Path(vault).expanduser().absolute()),
             '--claude-home', str(Path(home).expanduser().absolute())]
    if node:
        flags += ['--node', str(Path(node).expanduser().absolute())]
    if args.with_optional:
        flags.append('--with-optional')
    return flags


def pull(repo: Path, args: argparse.Namespace) -> None:
    check_repository(repo)
    if git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all'):
        raise SyncError('Shared working tree is dirty. Commit/push or resolve your changes before pulling; ignored local memory is allowed.')
    flags = ['--install-plugins', *preserve_paths(repo, args)]
    if args.dry_run:
        print('Dry run: no fetch or pull; previewing the currently checked-out installer only.')
    else:
        behind, ahead, revision = fetch_main(repo)
        if ahead:
            state = 'diverged' if behind else 'has unpushed local commits'
            raise SyncError(f'Local main {state}. Push or reconcile it before pulling; no automatic reset/rebase is used.')
        audit_tree(repo, revision, incoming=True)
        audit_history(repo, 'HEAD..origin/main', incoming=True)
        # Pull the audited snapshot, so a concurrently advanced remote cannot add unchecked paths.
        git(repo, '-c', 'rebase.autoStash=false', '-c', 'merge.autoStash=false',
            'pull', '--ff-only', '--no-autostash', 'origin', revision, echo=True)
        audit_tree(repo, 'HEAD', incoming=True)
        names = [name for name in git(repo, 'ls-files', '-z').decode('utf-8', 'surrogateescape').split('\0') if name]
        audit_shared_worktree(repo, names)
        flags = ['--apply', *flags]
    command = [sys.executable, str(repo / 'scripts/bootstrap.py'), *flags]
    result = subprocess.run(command, cwd=repo)
    if result.returncode:
        action = 'preview' if args.dry_run else 'apply'
        raise SyncError(f'Bootstrap {action} failed (exit {result.returncode}). Git commits were kept; fix the prerequisite and rerun claude-sync pull.')
    if not args.dry_run:
        print('Settings updated and applied. Start a new Claude Code session; vault and conversations were not transferred.')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest='action', required=True)
    push_parser = subcommands.add_parser('push', help='Commit allowed shared files and push main normally')
    push_parser.add_argument('-m', '--message', default='Update shared Claude Code settings')
    pull_parser = subcommands.add_parser('pull', help='Fast-forward main and apply this machine\'s configuration')
    pull_parser.add_argument('--vault')
    pull_parser.add_argument('--claude-home')
    pull_parser.add_argument('--node')
    pull_parser.add_argument('--with-optional', action='store_true')
    pull_parser.add_argument('--dry-run', action='store_true', help='Offline installer preview; no fetch/pull or writes by bootstrap')
    args = parser.parse_args(argv)
    try:
        if sys.version_info < (3, 10):
            raise SyncError('Python 3.10+ is required; use the claude-sync launcher to find it.')
        repo = Path(__file__).absolute().parents[1]
        if args.action == 'push':
            push(repo, args.message)
        else:
            pull(repo, args)
        return 0
    except (SyncError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
