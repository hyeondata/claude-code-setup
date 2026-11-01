#!/usr/bin/env python3
"""Narrow Claude memory commands; configuration is pinned beside this file."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile

PLUGIN_KEY = "claude-obsidian@agricidaniel-claude-obsidian"
LEDGERS = {"wiki/meta/ledgers/source-ledger.json", "wiki/meta/ledgers/claim-ledger.json"}


def no_symlinks(path: Path, *, must_exist: bool = True) -> Path:
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("An absolute, non-traversing path is required")
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise ValueError(f"Symlink paths are not allowed: {part}")
    if must_exist and not path.exists():
        raise ValueError(f"Required path does not exist: {path}")
    return path


def read_json(path: Path, limit: int = 8 * 1024 * 1024) -> dict:
    no_symlinks(path)
    if not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > limit:
        raise ValueError("Expected a bounded regular JSON file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def load_config() -> dict:
    config_path = Path(__file__).absolute().parent / "config.json"
    config = read_json(config_path, 65536)
    for key in ("registryPath", "vaultPath", "pythonPath", "nodePath"):
        if not isinstance(config.get(key), str) or not Path(config[key]).is_absolute():
            raise ValueError(f"Missing absolute config value: {key}")
    no_symlinks(Path(config["registryPath"]))
    vault = no_symlinks(Path(config["vaultPath"]))
    if not vault.is_dir():
        raise ValueError("Configured vault is not a directory")
    # Interpreter symlinks are normal in Homebrew; resolve the configured paths.
    for key in ("pythonPath", "nodePath"):
        binary = Path(config[key]).resolve(strict=True)
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise ValueError(f"Configured interpreter is not executable: {key}")
        config[key] = str(binary)
    config["configPath"] = str(config_path)
    return config


def plugin_root(config: dict) -> Path:
    registry = read_json(Path(config["registryPath"]))
    entries = registry.get("plugins", {}).get(PLUGIN_KEY, [])
    entries = [entry for entry in entries if isinstance(entry, dict) and entry.get("scope") == "user"]
    if not entries:
        raise ValueError("The user-scoped claude-obsidian plugin is not installed")
    latest = max(entries, key=lambda item: (item.get("lastUpdated", ""), item.get("installedAt", "")))
    root = no_symlinks(Path(latest["installPath"]))
    if not root.is_dir():
        raise ValueError("Plugin install path is not a directory")
    manifest = read_json(root / ".claude-plugin" / "plugin.json")
    if manifest.get("name") != "claude-obsidian":
        raise ValueError("Unexpected plugin manifest")
    return root


def allowed_target(raw: object, vault: Path) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw:
        raise ValueError("Write target must be a canonical relative path")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or ".." in relative.parts or str(relative) != raw:
        raise ValueError("Write target is not canonical or escapes the vault")
    if not ((raw.startswith("wiki/") and raw.endswith(".md")) or raw in LEDGERS):
        raise ValueError(f"Save target is outside the allowed wiki paths: {raw}")
    target = no_symlinks(vault / raw, must_exist=False)
    if target.exists() and not stat.S_ISREG(target.stat().st_mode):
        raise ValueError("Existing write target is not a regular file")
    return raw


def validate_bundle(bundle_path: Path, vault: Path) -> dict:
    bundle = read_json(bundle_path)
    if bundle.get("operation_type") != "save":
        raise ValueError("Only save workflow bundles are allowed")
    if "deletes" in bundle and bundle["deletes"] != []:
        raise ValueError("Delete operations are not allowed")
    writes = bundle.get("writes")
    if not isinstance(writes, list) or not writes:
        raise ValueError("The save bundle must contain writes")
    seen = set()
    for write in writes:
        if not isinstance(write, dict) or write.get("mode") not in {"create", "replace"}:
            raise ValueError("Only create and replace writes are allowed")
        target = allowed_target(write.get("path"), vault)
        if target in seen:
            raise ValueError("Duplicate write target")
        seen.add(target)
        if "content_file" in write:
            raw = write["content_file"]
            if not isinstance(raw, str) or not raw or "\\" in raw:
                raise ValueError("Invalid content_file")
            draft = Path(raw)
            if not draft.is_absolute():
                draft = bundle_path.parent / draft
            no_symlinks(draft)
            if not draft.is_relative_to(bundle_path.parent) or not stat.S_ISREG(draft.stat().st_mode):
                raise ValueError("content_file must be a regular file within the bundle directory")
    expected = bundle.get("expected_hashes")
    if not isinstance(expected, dict):
        raise ValueError("expected_hashes must be an explicit object")
    for target in seen:
        if target not in expected:
            raise ValueError(f"Missing explicit expected_hashes precondition: {target}")
    for target, digest in expected.items():
        allowed_target(target, vault)
        if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest)):
            raise ValueError(f"Invalid expected hash: {target}")
    return bundle


def read_bounded_bytes(path: Path, limit: int = 4 * 1024 * 1024) -> bytes:
    no_symlinks(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError("Expected a bounded regular content file")
        data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Content file exceeds the read limit")
        return data


def snapshot(vault: Path, paths: list[str]) -> dict:
    paths = paths or ["wiki/index.md", "wiki/log.md", "wiki/hot.md"]
    if len(paths) > 64:
        raise ValueError("Snapshot accepts at most 64 paths")
    files = []
    total = 0
    for relative in dict.fromkeys(paths):
        allowed_target(relative, vault)
        target = vault / relative
        if not target.exists():
            files.append({"path": relative, "content": None, "sha256": None})
            continue
        data = read_bounded_bytes(target)
        total += len(data)
        if total > 8 * 1024 * 1024:
            raise ValueError("Snapshot exceeds the total read limit")
        files.append({"path": relative, "content": data.decode("utf-8"),
            "sha256": hashlib.sha256(data).hexdigest()})
    return {"files": files}


def prepare(draft_path: Path, output: str, vault: Path) -> dict:
    bundle = validate_bundle(draft_path, vault)
    for write in bundle["writes"]:
        if ("content" in write) == ("content_file" in write):
            raise ValueError("Each write requires exactly one of content or content_file")
        if "content_file" in write:
            source = Path(write["content_file"])
            if not source.is_absolute():
                source = draft_path.parent / source
            data = read_bounded_bytes(source)
            content = data.decode("utf-8")
        else:
            content = write["content"]
            if not isinstance(content, str):
                raise ValueError("Write content must be UTF-8 text")
            data = content.encode("utf-8")
            if len(data) > 4 * 1024 * 1024:
                raise ValueError("Write content exceeds the size limit")
        digest = hashlib.sha256(data).hexdigest()
        if "sha256" in write and write["sha256"] != digest:
            raise ValueError(f"Provided content SHA-256 does not match: {write['path']}")
        write["content"] = content
        write.pop("content_file", None)
        write["sha256"] = digest

    drafts_dir = no_symlinks(Path(__file__).absolute().parent / "drafts", must_exist=False)
    target = Path(output)
    if not target.is_absolute():
        target = drafts_dir / target
    no_symlinks(target, must_exist=False)
    if not target.is_relative_to(drafts_dir) or target.is_relative_to(vault) or target.suffix != ".json":
        raise ValueError("Output must be a JSON file under this script's drafts directory, outside the vault")
    encoded = (json.dumps(bundle, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(encoded) > 8 * 1024 * 1024:
        raise ValueError("Prepared bundle exceeds the size limit")
    if target.exists():
        if read_bounded_bytes(target, 8 * 1024 * 1024) != encoded:
            raise ValueError("Output already exists with different content; choose a new bundle path")
        return {"bundle": str(target), "status": "unchanged", "writes": len(bundle["writes"])}
    target.parent.mkdir(parents=True, exist_ok=True)
    no_symlinks(target.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(target, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return {"bundle": str(target), "status": "created", "writes": len(bundle["writes"])}


def run_script(config: dict, root: Path, filename: str, args: list[str]) -> int:
    script = no_symlinks(root / "scripts" / filename)
    if not script.is_file():
        raise ValueError("Plugin entry point is not a regular file")
    command = [config["pythonPath"], str(script), *args]
    return subprocess.run(command, shell=False, cwd=str(root)).returncode


def reindex(config: dict, root: Path) -> int:
    vault = config["vaultPath"]
    code = run_script(config, root, "contextual-prefix.py", ["--vault", vault, "--all", "--no-llm"])
    if code:
        return code
    return run_script(config, root, "bm25-index.py", ["--vault", vault, "build"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("paths", "reindex", "lint", "doctor"):
        commands.add_parser(command)
    for command in ("inspect", "apply"):
        sub = commands.add_parser(command)
        sub.add_argument("bundle")
        if command == "apply":
            sub.add_argument("--approved-plan-sha256", required=True)
    commands.add_parser("search").add_argument("query")
    commands.add_parser("snapshot").add_argument("wiki_paths", nargs="*")
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("draft")
    prepare_parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        config = load_config()
        root = plugin_root(config)
        vault = Path(config["vaultPath"])
        if args.command == "paths":
            print(json.dumps({key: config[key] for key in ("configPath", "registryPath", "vaultPath", "pythonPath", "nodePath")} | {"pluginRoot": str(root)}, ensure_ascii=False))
            return 0
        if args.command == "snapshot":
            print(json.dumps(snapshot(vault, args.wiki_paths), ensure_ascii=False))
            return 0
        if args.command == "prepare":
            print(json.dumps(prepare(Path(os.path.abspath(args.draft)), args.output, vault), ensure_ascii=False))
            return 0
        if args.command == "reindex":
            return reindex(config, root)
        if args.command in {"doctor", "lint"}:
            return run_script(config, root, "claude-obsidian.py", [args.command, "--vault", str(vault)])
        if args.command == "search":
            if not args.query.strip():
                raise ValueError("Search query is empty")
            return run_script(config, root, "retrieve.py", ["--vault", str(vault),
                "--top", "3", "--bm25-top", "8", "--no-rerank", "--explain", "--", args.query])

        bundle_path = Path(os.path.abspath(args.bundle))
        bundle = validate_bundle(bundle_path, vault)
        if args.command == "apply" and not re.fullmatch(r"[0-9a-fA-F]{64}", args.approved_plan_sha256):
            raise ValueError("Approval hash must contain exactly 64 hexadecimal characters")
        # Snapshot the validated JSON beside the draft to preserve relative content_file
        # references and prevent a concurrent bundle edit from changing allowed targets.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json",
                prefix=".memory-validated-", dir=bundle_path.parent, delete=False) as frozen:
            json.dump(bundle, frozen, ensure_ascii=False)
            frozen_path = Path(frozen.name)
        try:
            command = ["workflow", args.command, str(frozen_path), "--vault", str(vault)]
            if args.command == "apply":
                command += ["--approved-plan-sha256", args.approved_plan_sha256.lower()]
            code = run_script(config, root, "claude-obsidian.py", command)
        finally:
            frozen_path.unlink(missing_ok=True)
        if code or args.command == "inspect":
            return code
        try:
            index_code = reindex(config, root)
        except (OSError, ValueError) as error:
            print(f"memory_cli: save applied; reindex could not run: {error}", file=sys.stderr)
            index_code = 2
        if index_code:
            print(json.dumps({"save": "applied", "reindex": "failed", "reindexExitCode": index_code,
                "retry": "memory_cli.py reindex"}), file=sys.stderr)
            return 3  # The workflow receipt on stdout remains the successful save result.
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"memory_cli: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
