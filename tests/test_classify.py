import copy
import json
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


if __name__ == "__main__":
    unittest.main()
