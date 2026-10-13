"""Create a new immutable knowledge package from the draft rules."""

import argparse
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.classify import ClinicalRuleEngine  # noqa: E402
from src.knowledge import PACKAGE_ID, sha256_file  # noqa: E402
from src.version import ENGINE_VERSION  # noqa: E402


def release(version, summary=None, previous=None, root=ROOT):
    root = Path(root)
    package_id = "kb-" + version
    if not PACKAGE_ID.fullmatch(package_id):
        raise ValueError("version must be X.Y.Z")
    if previous is not None and not PACKAGE_ID.fullmatch(previous):
        raise ValueError("invalid previous package id")
    source = root / "rules"
    destination = root / "knowledge" / package_id
    if destination.exists():
        raise ValueError(f"{destination}: package already exists")
    rules_path = source / "classification_rules.yaml"
    fields_path = source / "fields.yaml"
    rules = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    fields = yaml.safe_load(fields_path.read_text(encoding="utf-8"))
    if not isinstance(rules, dict) or rules.get("version") != version:
        raise ValueError("rule version does not match requested version")
    if not isinstance(fields, dict) or not isinstance(fields.get("version"), str):
        raise ValueError("fields.yaml has no valid version")
    if previous and not (root / "knowledge" / previous).is_dir():
        raise ValueError(f"previous package does not exist: {previous}")
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_fields.py"), "--check"],
        cwd=root, capture_output=True, text=True,
    ) if root == ROOT else _check_fields_in_root(root)
    if result.returncode:
        raise ValueError("build_fields --check failed: " + result.stdout + result.stderr)
    ClinicalRuleEngine(str(rules_path))
    destination.mkdir(parents=True)
    try:
        for name in ("classification_rules.yaml", "fields.yaml"):
            shutil.copyfile(source / name, destination / name)
        manifest = {
            "knowledge_package_id": package_id,
            "package_version": version,
            "fields_version": fields["version"],
            "supported_engine_versions": [ENGINE_VERSION],
            "previous_package_id": previous,
            "released_at": datetime.date.today().isoformat(),
            "change_summary": summary or "Đóng gói YAML hiện có; chưa qua duyệt chuyên môn.",
            "files": {name: sha256_file(destination / name) for name in ("classification_rules.yaml", "fields.yaml")},
        }
        with (destination / "manifest.yaml").open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))
    except Exception:
        shutil.rmtree(destination)
        raise
    return destination


def _check_fields_in_root(root):
    """Run the same field coverage logic against a temporary checkout."""
    from tools.build_fields import rule_field_usage
    rules = yaml.safe_load((root / "rules" / "classification_rules.yaml").read_text(encoding="utf-8"))
    fields = yaml.safe_load((root / "rules" / "fields.yaml").read_text(encoding="utf-8"))
    usage = rule_field_usage(rules)
    entries = fields["fields"]
    valid = not (set(usage) - set(entries)) and all(entries[path].get("used_by") == used_by for path, used_by in usage.items())
    return subprocess.CompletedProcess([], 0 if valid else 1, "", "")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--summary")
    parser.add_argument("--previous")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        print(release(args.version, args.summary, args.previous, args.root))
    except (ValueError, OSError, yaml.YAMLError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
