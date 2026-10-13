import copy
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from src.classify import ClinicalRuleEngine

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules" / "classification_rules.yaml"
CASES = json.loads((ROOT / "data" / "synthetic" / "rule_logic_cases.json").read_text(encoding="utf-8"))["cases"]
CASES_BY_ID = {case["id"]: case for case in CASES}


class FixtureReplayTest(unittest.TestCase):
    """Engine khớp expected_engine của 138 ca giả (hành vi đã mô tả, không phải ground truth lâm sàng)."""

    @classmethod
    def setUpClass(cls):
        cls.engine = ClinicalRuleEngine(str(RULES))

    def test_all_cases_match_expected_engine(self):
        for case in CASES:
            with self.subTest(case=case["id"]):
                data = copy.deepcopy(case["du_lieu"])
                expected = case["expected_engine"]
                self.assertNotIn("exception", expected)
                result = self.engine.classify_patient(data)
                for key in ("status", "matched_rule_id", "predicted_label"):
                    if key in expected:
                        self.assertEqual(result[key], expected[key], key)
                for rule_id, value in expected.get("rule_results", {}).items():
                    self.assertIs(result["rule_results"][rule_id], value, rule_id)
                self.assertEqual(data, case["du_lieu"], "input must not be mutated")


class FormulaOperandTest(unittest.TestCase):
    """TECH-01 / TECH-03: công thức HATT kiểm tra cả hai vế và báo đúng trường."""

    @classmethod
    def setUpClass(cls):
        cls.engine = ClinicalRuleEngine(str(RULES))
        cls.base = CASES_BY_ID["SOC-NEN-MISSING"]["du_lieu"]

    def classify(self, **overrides):
        data = copy.deepcopy(self.base)
        data.update(overrides)
        return self.engine.classify_patient(data)

    def assert_review_not_shock(self, result):
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertIsNone(result["predicted_label"])
        self.assertIsNone(result["rule_results"]["R-SOC"])

    def test_bool_measurement_is_not_a_blood_pressure(self):
        for value in (True, False):
            with self.subTest(value=value):
                self.assert_review_not_shock(self.classify(huyet_ap_tam_thu_thap_nhat=value, huyet_ap_tam_thu_nen=120))

    def test_malformed_measurement_does_not_crash(self):
        for value in ([], [85, 90], {}, {"gia_tri": 85}, "80"):
            with self.subTest(value=value):
                self.assert_review_not_shock(self.classify(huyet_ap_tam_thu_thap_nhat=value, huyet_ap_tam_thu_nen=120))

    def test_bool_baseline_is_rejected(self):
        self.assert_review_not_shock(self.classify(huyet_ap_tam_thu_thap_nhat=100, huyet_ap_tam_thu_nen=True))

    def test_missing_baseline_reports_baseline_field(self):
        result = self.classify(huyet_ap_tam_thu_thap_nhat=95, huyet_ap_tam_thu_nen=None)
        self.assertEqual(result["status"], "INSUFFICIENT_DATA")
        self.assertIn("huyet_ap_tam_thu_nen", result["missing_fields"])
        self.assertNotIn("huyet_ap_tam_thu_thap_nhat", result["missing_fields"])

    def test_missing_measurement_reports_measurement_field(self):
        result = self.classify(huyet_ap_tam_thu_thap_nhat=None, huyet_ap_tam_thu_nen=120)
        self.assertEqual(result["status"], "INSUFFICIENT_DATA")
        self.assertIn("huyet_ap_tam_thu_thap_nhat", result["missing_fields"])

    def test_valid_numbers_still_evaluate(self):
        self.assertIs(self.classify(huyet_ap_tam_thu_thap_nhat=60, huyet_ap_tam_thu_nen=120)["rule_results"]["R-SOC"], True)


class ListSentinelTest(unittest.TestCase):
    """Sentinel bên trong danh sách là UNKNOWN, không phải giá trị không khớp."""

    def test_unknown_item_in_symptom_list(self):
        engine = ClinicalRuleEngine(str(RULES))
        data = copy.deepcopy(CASES_BY_ID["SOC-NEN-MISSING"]["du_lieu"])
        for item in ("unknown", "N/A", "", None):
            with self.subTest(item=item):
                data["trieu_chung_da_hien_tai_pv"] = {"danh_sach_chon": [item]}
                events = [event for event in engine.classify_patient(data)["trace"]
                          if event["field_path"] == "trieu_chung_da_hien_tai_pv.danh_sach_chon"]
                self.assertTrue(events)
                for event in events:
                    self.assertIsNone(event["result"])
                    self.assertIn(event["reason"], {"UNKNOWN_SENTINEL", "MISSING_VALUE"})


class TokenEchoTest(unittest.TestCase):
    """Chỉ trả lại token đúng định dạng anonymizer; văn bản tự do có thể chứa PII."""

    def test_free_text_token_not_echoed(self):
        engine = ClinicalRuleEngine(str(RULES))
        self.assertEqual(engine.classify_patient({"patient_token_id": "Nguyen Van A 0912345678"})["patient_token_id"], "UNKNOWN")
        self.assertEqual(engine.classify_patient({})["patient_token_id"], "UNKNOWN")
        token = "PT_0123456789ABCDEF"
        self.assertEqual(engine.classify_patient({"patient_token_id": token})["patient_token_id"], token)


GOLDEN = ROOT / "tests" / "golden" / "engine_outputs.json"
CONTRACT_KEYS = {
    "patient_token_id", "predicted_label", "matched_rule_id", "priority", "decision_trace", "status",
    "rule_results", "matched_rule_ids", "blocking_rule_ids", "missing_fields", "trace",
    "rules_version", "rules_sha256",
}


def contract_view(result):
    """Các trường dễ sai khi chọn kết luận/UNKNOWN; trace được khóa bằng hash."""
    view = {key: result[key] for key in (
        "status", "predicted_label", "matched_rule_id", "matched_rule_ids", "priority",
        "blocking_rule_ids", "missing_fields", "rule_results", "decision_trace")}
    view["trace_sha256"] = hashlib.sha256(
        json.dumps(result["trace"], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return view


class OutputContractTest(unittest.TestCase):
    """Khóa toàn bộ output của 138 ca. Thay đổi có chủ đích: UPDATE_GOLDEN=1 rồi review diff golden."""

    @classmethod
    def setUpClass(cls):
        cls.engine = ClinicalRuleEngine(str(RULES))
        cls.outputs = {case["id"]: cls.engine.classify_patient(copy.deepcopy(case["du_lieu"])) for case in CASES}

    def test_output_keys_are_stable(self):
        for case_id, result in self.outputs.items():
            with self.subTest(case=case_id):
                self.assertEqual(set(result), CONTRACT_KEYS)

    def test_outputs_match_golden(self):
        current = {case_id: contract_view(result) for case_id, result in sorted(self.outputs.items())}
        if os.environ.get("UPDATE_GOLDEN") == "1":
            GOLDEN.parent.mkdir(exist_ok=True)
            GOLDEN.write_text(json.dumps(current, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        self.assertEqual(sorted(golden), sorted(current))
        for case_id in current:
            with self.subTest(case=case_id):
                self.assertEqual(current[case_id], golden[case_id])

    def test_cache_does_not_leak_between_patients(self):
        fresh = ClinicalRuleEngine(str(RULES))
        reversed_ids = [case["id"] for case in reversed(CASES)]
        for case_id in reversed_ids:
            with self.subTest(case=case_id):
                result = fresh.classify_patient(copy.deepcopy(CASES_BY_ID[case_id]["du_lieu"]))
                self.assertEqual(contract_view(result), contract_view(self.outputs[case_id]))


class EngineIndependenceTest(unittest.TestCase):
    def test_engine_does_not_import_streamlit(self):
        code = "import sys; import src.classify, src.preprocess, src.anonymize; sys.exit('streamlit' in sys.modules)"
        completed = subprocess.run([sys.executable, "-c", code], cwd=ROOT)
        self.assertEqual(completed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
