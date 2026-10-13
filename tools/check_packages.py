"""Validate package manifests, active pointers, and released-file immutability."""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.knowledge import load_package, normalized_bytes  # noqa: E402


def check(root=ROOT, base_ref=None):
    root = Path(root)
    knowledge = root / "knowledge"
    packages = {path.name for path in knowledge.iterdir() if path.is_dir()}
    for package_id in sorted(packages):
        package = load_package(package_id, knowledge)
        manifest = package.manifest
        rules = yaml.safe_load(normalized_bytes(package.rules_path).decode("utf-8"))
        fields = yaml.safe_load(normalized_bytes(package.fields_path).decode("utf-8"))
        if not isinstance(rules, dict) or manifest.get("package_version") != rules.get("version"):
            raise ValueError(f"{package_id}: package_version differs from rules YAML")
        if not isinstance(fields, dict) or manifest.get("fields_version") != fields.get("version"):
            raise ValueError(f"{package_id}: fields_version differs from fields YAML")
        previous = manifest.get("previous_package_id")
        if previous is not None and previous not in packages:
            raise ValueError(f"{package_id}: previous_package_id does not exist: {previous}")
    active_path = knowledge / "active.yaml"
    active = yaml.safe_load(normalized_bytes(active_path).decode("utf-8"))
    if not isinstance(active, dict):
        raise ValueError(f"{active_path}: expected environment mapping")
    for environment, package_id in active.items():
        if package_id is not None and package_id not in packages:
            raise ValueError(f"{active_path}: {environment} references missing package {package_id}")
    if base_ref:
        _check_immutable(root, base_ref)


def _check_immutable(root, base_ref):
    base = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", base_ref, "--", "knowledge/"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    old_packages = {parts[1] for line in base.stdout.splitlines()
                    if (parts := line.split("/"))[:1] == ["knowledge"] and len(parts) >= 3}
    diff = subprocess.run(
        ["git", "diff", "--name-status", f"{base_ref}...HEAD", "--", "knowledge/"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    for line in diff.stdout.splitlines():
        status, *paths = line.split("\t")
        for path in paths:
            parts = path.split("/")
            if len(parts) >= 3 and parts[1] in old_packages:
                raise ValueError(f"released package file changed: {path} ({status})")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref")
    args = parser.parse_args()
    try:
        check(base_ref=args.base_ref)
    except (ValueError, OSError, yaml.YAMLError, subprocess.CalledProcessError) as exc:
        parser.exit(1, str(exc) + "\n")
    print("Knowledge packages OK")


if __name__ == "__main__":
    main()
