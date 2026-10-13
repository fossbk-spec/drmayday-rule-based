"""Load and verify immutable knowledge packages."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.version import ENGINE_VERSION


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_ROOT = ROOT / "knowledge"
PACKAGE_ID = re.compile(r"kb-[0-9]+\.[0-9]+\.[0-9]+\Z")
PACKAGE_FILES = ("classification_rules.yaml", "fields.yaml")


def normalized_bytes(path: Path) -> bytes:
    """Use the same LF bytes for package hashes on Windows and Linux."""
    return Path(path).read_bytes().replace(b"\r\n", b"\n")


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(normalized_bytes(path)).hexdigest()


@dataclass(frozen=True)
class KnowledgePackage:
    package_id: str
    package_hash: str
    rules_path: Path
    fields_path: Path
    manifest: Dict[str, Any]


def load_package(package_id: str, root: Path = KNOWLEDGE_ROOT) -> KnowledgePackage:
    if not isinstance(package_id, str) or not PACKAGE_ID.fullmatch(package_id):
        raise ValueError("invalid knowledge package id: " + str(package_id))
    package_dir = Path(root) / package_id
    manifest_path = package_dir / "manifest.yaml"
    try:
        manifest = yaml.safe_load(normalized_bytes(manifest_path).decode("utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"{manifest_path}: cannot read valid YAML ({type(exc).__name__})") from None
    if not isinstance(manifest, dict):
        raise ValueError(f"{manifest_path}: manifest must be an object")
    if manifest.get("knowledge_package_id") != package_id:
        raise ValueError(f"{manifest_path}: knowledge_package_id does not match directory")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != set(PACKAGE_FILES):
        raise ValueError(f"{manifest_path}: files must list both package YAML files")
    for name in PACKAGE_FILES:
        path = package_dir / name
        try:
            actual = sha256_file(path)
        except OSError as exc:
            raise ValueError(f"{path}: cannot read ({type(exc).__name__})") from None
        if files[name] != actual:
            raise ValueError(f"{path}: hash mismatch")
    supported = manifest.get("supported_engine_versions")
    if not isinstance(supported, list) or ENGINE_VERSION not in supported:
        raise ValueError(f"{manifest_path}: unsupported engine version {ENGINE_VERSION}")
    return KnowledgePackage(
        package_id, sha256_file(manifest_path),
        package_dir / "classification_rules.yaml", package_dir / "fields.yaml", manifest,
    )


def resolve_active(environment: str, root: Path = KNOWLEDGE_ROOT) -> Optional[str]:
    path = Path(root) / "active.yaml"
    try:
        active = yaml.safe_load(normalized_bytes(path).decode("utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"{path}: cannot read valid YAML ({type(exc).__name__})") from None
    if not isinstance(active, dict):
        raise ValueError(f"{path}: active environments must be an object")
    package_id = active.get(environment)
    if package_id is not None and (not isinstance(package_id, str) or not PACKAGE_ID.fullmatch(package_id)):
        raise ValueError(f"{path}: invalid package for {environment}")
    return package_id
