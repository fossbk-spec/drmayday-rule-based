import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from src.classifiers import RuleBasedClassifier
from src.knowledge import load_package, resolve_active, sha256_file


ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "data" / "synthetic" / "rule_logic_cases.json").read_text(encoding="utf-8"))["cases"]


class KnowledgeTest(unittest.TestCase):
    def test_package_and_envelope_match_draft_on_all_cases(self):
        package = load_package("kb-1.2.1")
        self.assertEqual(package.package_id, "kb-1.2.1")
        self.assertEqual(package.package_hash, sha256_file(ROOT / "knowledge" / "kb-1.2.1" / "manifest.yaml"))
        packaged = RuleBasedClassifier.from_package("kb-1.2.1")
        draft = RuleBasedClassifier(ROOT / "rules" / "classification_rules.yaml")
        self.assertEqual(len(CASES), 138)
        for case in CASES:
            with self.subTest(case=case["id"]):
                result = packaged.classify(copy.deepcopy(case["du_lieu"]))
                expected = draft.classify(copy.deepcopy(case["du_lieu"]))
                self.assertEqual(result["knowledge_package_id"], package.package_id)
                self.assertEqual(result["knowledge_package_hash"], package.package_hash)
                for key in ("status", "predicted_label", "missing_fields", "details"):
                    self.assertEqual(result[key], expected[key])

    def test_tampering_and_engine_compatibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "knowledge" / "kb-1.2.1", root / "kb-1.2.1")
            rules = root / "kb-1.2.1" / "classification_rules.yaml"
            rules.write_bytes(rules.read_bytes() + b"\n# tampered\n")
            with self.assertRaisesRegex(ValueError, "classification_rules.yaml.*hash mismatch"):
                load_package("kb-1.2.1", root)
            shutil.copyfile(ROOT / "knowledge" / "kb-1.2.1" / "classification_rules.yaml", rules)
            manifest = root / "kb-1.2.1" / "manifest.yaml"
            data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            data["supported_engine_versions"] = ["0.0.0"]
            manifest.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported engine"):
                load_package("kb-1.2.1", root)

    def test_hash_is_independent_of_crlf(self):
        with tempfile.TemporaryDirectory() as temporary:
            left = Path(temporary) / "left.yaml"
            right = Path(temporary) / "right.yaml"
            left.write_bytes(b"version: 1\nfield: value\n")
            right.write_bytes(b"version: 1\r\nfield: value\r\n")
            self.assertEqual(sha256_file(left), sha256_file(right))

    def test_active(self):
        self.assertEqual(resolve_active("demo"), "kb-1.2.1")
        self.assertIsNone(resolve_active("real"))
        with self.assertRaisesRegex(ValueError, "no active knowledge package"):
            RuleBasedClassifier.from_active("real")

    def test_release_only_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "rules", root / "rules")
            command = [sys.executable, "-X", "utf8", str(ROOT / "tools" / "release_package.py"),
                       "--version", "1.2.1", "--root", str(root)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            package = load_package("kb-1.2.1", root / "knowledge")
            self.assertEqual(package.manifest["package_version"], "1.2.1")
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)

    def test_impact_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base, head = root / "base", root / "head"
            for checkout in (base, head):
                shutil.copytree(ROOT / "rules", checkout / "rules")
                shutil.copytree(ROOT / "src", checkout / "src")
            command = [sys.executable, "-X", "utf8", str(ROOT / "tools" / "impact_report.py"),
                       "--base-root", str(base), "--head-root", str(head),
                       "--cases", str(ROOT / "data" / "synthetic" / "rule_logic_cases.json")]
            same = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(same.returncode, 0, same.stderr)
            self.assertIn("Không có thay đổi kết quả", same.stdout)
            path = head / "rules" / "classification_rules.yaml"
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            for rule in document["rules"]:
                if "target_label" in rule:
                    rule["target_label"] = "Nhãn kiểm thử"
            path.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
            changed = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(changed.returncode, 0, changed.stderr)
            self.assertIn("Các ca thay đổi", changed.stdout)
            self.assertIn("Nhãn kiểm thử", changed.stdout)

    def test_check_packages(self):
        result = subprocess.run([sys.executable, "-X", "utf8", "tools/check_packages.py"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
