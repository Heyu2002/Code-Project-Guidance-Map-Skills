#!/usr/bin/env python3
"""Sync the development skill into the distributable plugin skill copy."""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SOURCE = Path(".agents/skills/code-project-guidance-map")
DEFAULT_TARGET = Path("plugins/code-project-guidance-map/skills/code-project-guidance-map")
EXCLUDED_NAMES = {"__pycache__", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


@dataclass(frozen=True)
class Drift:
    missing: tuple[str, ...]
    changed: tuple[str, ...]
    extra: tuple[str, ...]

    @property
    def has_drift(self) -> bool:
        return bool(self.missing or self.changed or self.extra)


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_NAMES for part in path.parts) or path.suffix in EXCLUDED_SUFFIXES


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_under(repo: Path, path: Path, label: str) -> Path:
    resolved = (repo / path).resolve() if not path.is_absolute() else path.resolve()
    repo_resolved = repo.resolve()
    if resolved != repo_resolved and repo_resolved not in resolved.parents:
        raise ValueError(f"{label} path is outside repository: {resolved}")
    return resolved


def relative_files(root: Path) -> set[str]:
    if not root.exists():
        return set()
    files: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if is_excluded(relative):
            continue
        files.add(relative.as_posix())
    return files


def compare_trees(source: Path, target: Path) -> Drift:
    source_files = relative_files(source)
    target_files = relative_files(target)
    missing = sorted(source_files - target_files)
    extra = sorted(target_files - source_files)
    changed = sorted(
        rel
        for rel in source_files & target_files
        if not filecmp.cmp(source / rel, target / rel, shallow=False)
    )
    return Drift(tuple(missing), tuple(changed), tuple(extra))


def remove_empty_dirs(root: Path) -> None:
    if not root.exists():
        return
    for path in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        if is_excluded(path.relative_to(root)):
            continue
        try:
            path.rmdir()
        except OSError:
            pass


def sync_trees(source: Path, target: Path) -> Drift:
    if not source.exists():
        raise FileNotFoundError(f"Source skill does not exist: {source}")
    if not (source / "SKILL.md").is_file():
        raise FileNotFoundError(f"Source skill is missing SKILL.md: {source}")

    before = compare_trees(source, target)
    target.mkdir(parents=True, exist_ok=True)

    for rel in before.extra:
        path = (target / rel).resolve()
        target_resolved = target.resolve()
        if path != target_resolved and target_resolved not in path.parents:
            raise ValueError(f"Refusing to remove outside target: {path}")
        path.unlink()

    for rel in sorted(relative_files(source)):
        src = source / rel
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    remove_empty_dirs(target)
    return before


def print_drift(drift: Drift) -> None:
    if not drift.has_drift:
        print("Skill copies are in sync.")
        return
    for label, values in (("Missing from plugin copy", drift.missing), ("Changed", drift.changed), ("Extra in plugin copy", drift.extra)):
        if not values:
            continue
        print(f"{label}:")
        for value in values:
            print(f"  {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync the repo skill into the plugin skill copy.")
    parser.add_argument("--repo", type=Path, default=repo_root_from_script(), help="Repository root.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Source skill path.")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET, help="Plugin skill target path.")
    parser.add_argument("--check", action="store_true", help="Only check for drift; do not modify files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = args.repo.resolve()
    try:
        source = resolve_under(repo, args.source, "source")
        target = resolve_under(repo, args.target, "target")
        if args.check:
            drift = compare_trees(source, target)
            print_drift(drift)
            return 1 if drift.has_drift else 0

        drift = sync_trees(source, target)
        if drift.has_drift:
            print("Synchronized plugin skill copy.")
            print_drift(drift)
        else:
            print("Plugin skill copy was already in sync.")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
