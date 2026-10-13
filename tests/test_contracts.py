import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

from src.classify import ClinicalRuleEngine
from src.classifiers import Classifier, RuleBasedClassifier, make_envelope
from src.version import ENGINE_VERSION, RESULT_SCHEMA_VERSION
from tools.build_fields import rule_field_usage


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules" / "classification_rules.yaml"
CASES = json.loads((ROOT / "data" / "synthetic" / "rule_logic_cases.json").read_text(encoding="utf-8"))["cases"]
ENVELOPE_KEYS = {
    "result_schema_version", "classifier_id", "classifier_version", "knowledge_package_id",
    "knowledge_package_hash", "run_id", "record_id", "status", "predicted_label",
    "missing_fields", "explanation", "issues", "details",
}
DETAIL_KEYS = {
    "matched_rule_id", "matched_rule_ids", "blocking_rule_ids", "priority", "rule_results", "trace",
}


class DummyClassifier(Classifier):
    classifier_id = "dummy"
    classifier_version = "0.1.0"

    def classify(self, snapshot, *, record_id=None, run_id=None):
        return make_envelope(
            classifier_id=self.classifier_id, classifier_version=self.classifier_version,
            status="UNRESOLVED", summary="No decision", record_id=record_id, run_id=run_id,
        )


class EnvelopeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = RuleBasedClassifier(RULES)
        cls.engine = ClinicalRuleEngine(str(RULES))

    def test_all_cases_preserve_engine_output(self):
        self.assertEqual(len(CASES), 138)
        for case in CASES:
            with self.subTest(case=case["id"]):
                snapshot = copy.deepcopy(case["du_lieu"])
                before = copy.deepcopy(snapshot)
                engine_result = self.engine.classify_patient(copy.deepcopy(snapshot))
                result = self.adapter.classify(snapshot, record_id=case["id"], run_id="test-run")
                self.assertEqual(snapshot, before)
                self.assertEqual(set(result), ENVELOPE_KEYS)
                self.assertEqual(set(result["details"]), DETAIL_KEYS)
                self.assertEqual(result["result_schema_version"], RESULT_SCHEMA_VERSION)
                self.assertEqual(result["classifier_id"], "rule-based")
                self.assertEqual(result["classifier_version"], ENGINE_VERSION)
                self.assertEqual(result["knowledge_package_id"], "kb-" + engine_result["rules_version"])
                self.assertEqual(result["knowledge_package_hash"], "sha256:" + engine_result["rules_sha256"])
                self.assertEqual(result["record_id"], case["id"])
                self.assertEqual(result["run_id"], "test-run")
                self.assertIn(result["status"], ClinicalRuleEngine.STATUSES)
                for key in ("status", "predicted_label", "missing_fields"):
                    self.assertEqual(result[key], engine_result[key], key)
                self.assertEqual(result["explanation"], {"summary": engine_result["decision_trace"]})
                self.assertEqual(result["issues"], [])
                for key in DETAIL_KEYS:
                    self.assertEqual(result["details"][key], engine_result[key], key)
                self.assertNotIn("patient_token_id", result)

    def test_dummy_uses_only_common_contract(self):
        result = DummyClassifier().classify({}, record_id="r", run_id="run")
        self.assertEqual(set(result), ENVELOPE_KEYS)
        self.assertEqual(result["knowledge_package_id"], None)
        self.assertEqual(result["knowledge_package_hash"], None)
        self.assertEqual(result["details"], {})
        self.assertEqual(result["record_id"], "r")
        self.assertEqual(result["run_id"], "run")
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["explanation"], {"summary": "No decision"})


class FieldsContractTest(unittest.TestCase):
    def test_coverage_types_and_used_by(self):
        rules = yaml.safe_load(RULES.read_text(encoding="utf-8"))
        fields = yaml.safe_load((ROOT / "rules" / "fields.yaml").read_text(encoding="utf-8"))
        usage = rule_field_usage(rules)
        self.assertEqual(fields["version"], "0.1.0")
        self.assertEqual(fields["missing_conventions"], {
            "missing": None, "unknown": ["unknown", -1], "not_applicable": "N/A",
        })
        self.assertFalse(set(usage) - set(fields["fields"]))
        for path, rule_ids in usage.items():
            with self.subTest(path=path):
                entry = fields["fields"][path]
                self.assertIn(entry["type"], {"number", "string", "boolean", "list", "object"})
                self.assertEqual(entry["used_by"], rule_ids)
                self.assertIsInstance(entry["values"], list)
                self.assertIn("todo", entry)

    def test_build_fields_check(self):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "tools/build_fields.py", "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
