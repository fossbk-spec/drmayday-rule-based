import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from src.classifiers import RuleBasedClassifier
from src.evaluate import evaluate
from src.ingest import Record, load_records
from src.pipeline import run_batch
from src.validate import validate_canonical


ROOT = Path(__file__).resolve().parents[1]
FIELDS = yaml.safe_load((ROOT / "rules" / "fields.yaml").read_text(encoding="utf-8"))


class PipelineTest(unittest.TestCase):
    def test_ingest_fixture_counts_and_isolation(self):
        paths = sorted((ROOT / "data" / "synthetic").glob("*.json"))
        paths = [path for path in paths if path.name != "rule_logic_results.json"]
        records = load_records(paths)
        self.assertEqual(len(records), 191)
        self.assertEqual(len({record.record_id for record in records}), 191)
        self.assertEqual(sum(record.ground_truth is not None for record in records), 53)
        for record in records:
            self.assertTrue({"nhan", "expected_engine", "workflow_gap", "mo_ta", "id"}.isdisjoint(record.snapshot))

    def test_ingest_duplicates_malformed_and_nested_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cases.json"
            path.write_text(json.dumps([
                {"id": "x", "du_lieu": {"nhan": "secret", "tuoi": 20}},
                {"id": "x#2", "du_lieu": {}},
                {"id": "x", "du_lieu": {}},
                {"id": "bad", "du_lieu": []},
            ]), encoding="utf-8")
            records = load_records([path])
            self.assertEqual(len({record.record_id for record in records}), 4)
            self.assertNotIn("nhan", records[0].snapshot)
            self.assertEqual(records[-1].error, "InvalidSnapshot")
            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(load_records([path])[0].error, "JSONDecodeError")

    def test_validation(self):
        self.assertEqual(validate_canonical({"tuoi": True}, FIELDS)[0]["code"], "INVALID_TYPE")
        self.assertEqual(validate_canonical({"anh_san_phu": "Sai"}, FIELDS)[0]["code"], "INVALID_VALUE")
        issue = validate_canonical({"so_ngay_theo_doi": "bad"}, FIELDS)[0]
        self.assertEqual(issue["severity"], "warning")
        self.assertEqual(validate_canonical({"tuoi": -1, "anh_san_phu": "unknown"}, FIELDS), [])

    def test_fixture_batch_matches_direct_classifier(self):
        records = load_records([ROOT / "data" / "synthetic" / "rule_logic_cases.json"])
        classifier = RuleBasedClassifier.from_active("demo")
        fields = yaml.safe_load((ROOT / "knowledge" / "kb-1.2.1" / "fields.yaml").read_text(encoding="utf-8"))
        manifest, results = run_batch(records, classifier, fields=fields, run_id="test")
        self.assertEqual(manifest["knowledge_package_id"], "kb-1.2.1")
        self.assertTrue(manifest["knowledge_package_hash"].startswith("sha256:"))
        self.assertEqual(manifest["counts"]["received"], 138)
        self.assertEqual(138, sum(manifest["counts"]["classified_by_status"].values()) + manifest["counts"]["errors"])
        for record, result in zip(records, results):
            if result.get("status") == "INVALID_DATA":
                self.assertTrue(any(issue["severity"] == "error" for issue in result["issues"]))
            else:
                expected = classifier.classify(record.snapshot, record_id=record.record_id, run_id="test")
                expected["issues"] = result["issues"]
                self.assertEqual(result, expected)

    def test_exception_does_not_drop_record(self):
        class Throwing:
            classifier_id = "fake"
            classifier_version = "1"
            def classify(self, snapshot, **kwargs):
                if snapshot.get("fail"):
                    raise RuntimeError("boom")
                return {"status": "CLASSIFIED", "record_id": kwargs["record_id"], "predicted_label": "A", "issues": []}
        records = [Record("a", {"fail": True}, None, {}), Record("b", {}, None, {})]
        manifest, results = run_batch(records, Throwing(), fields={"version": "1", "fields": {}})
        self.assertEqual(results[0], {"record_id": "a", "error": "RuntimeError"})
        self.assertEqual(manifest["counts"]["errors"], 1)
        self.assertEqual(sum(manifest["counts"]["classified_by_status"].values()) + 1, 2)

    def test_evaluation_includes_abstention(self):
        records = [Record(str(i), {}, "A", {}) for i in range(3)]
        results = [{"status": "CLASSIFIED", "predicted_label": "A"},
                   {"status": "CLASSIFIED", "predicted_label": "B"},
                   {"status": "INSUFFICIENT_DATA"}]
        report = evaluate(results, records, {"A": "A"})
        self.assertEqual(report["denominator"], 3)
        self.assertEqual(report["confusion_matrix"]["A"]["(INSUFFICIENT_DATA)"], 1)
        self.assertAlmostEqual(report["per_class"]["A"]["recall"], 1 / 3)
        self.assertAlmostEqual(report["accuracy"], 1 / 3)
        self.assertAlmostEqual(report["coverage"], 2 / 3)

    def test_cli_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            input_path = Path(temporary) / "cases.json"
            input_path.write_text(json.dumps([{"id": "one", "nhan": "A", "du_lieu": {}}]), encoding="utf-8")
            labels = Path(temporary) / "labels.yaml"
            labels.write_text("A: A\n", encoding="utf-8")
            out = Path(temporary) / "out"
            command = [sys.executable, "-X", "utf8", "-m", "src.pipeline", "--input", str(input_path),
                       "--env", "demo", "--out", str(out), "--label-map", str(labels)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ("run_manifest.json", "results.jsonl", "evaluation.json", "summary.md"):
                self.assertTrue((out / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
