"""Streamlit smoke and interaction tests for the synthetic demo."""

import json
import unittest
from pathlib import Path

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None

from src.classifiers import RuleBasedClassifier
from src.ingest import load_records
from src.knowledge import load_package
from src.pipeline import run_batch


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(AppTest is not None, "Streamlit is not installed")
class AppTests(unittest.TestCase):
    def page(self, name):
        if name == "demo":
            return AppTest.from_file(str(ROOT / "main.py"), default_timeout=30).run()
        return AppTest.from_string(f"from app.pages import {name}; {name}.render()", default_timeout=30).run()

    def assert_clean(self, app):
        self.assertEqual(len(app.exception), 0)

    def test_pages_render(self):
        for name in ("demo", "rules", "batch", "about"):
            with self.subTest(page=name):
                self.assert_clean(self.page(name))

    def test_demo_result_and_input_change(self):
        app = self.page("demo")
        case = json.loads((ROOT / "data/synthetic/rule_logic_cases.json").read_text(encoding="utf-8"))["cases"][0]
        expected = RuleBasedClassifier.from_active("demo").classify(case["du_lieu"])
        app.button(key="classify").click().run()
        self.assert_clean(app)
        self.assertEqual(app.session_state["result"]["status"], expected["status"])
        self.assertEqual(app.session_state["result"]["predicted_label"], expected["predicted_label"])
        snapshot = dict(case["du_lieu"])
        snapshot["tuoi"] = 31
        app.text_area(key="patient_json").set_value(json.dumps(snapshot, ensure_ascii=False)).run()
        self.assert_clean(app)
        self.assertIsNone(app.session_state["result"])

    def test_missing_pressure_threshold(self):
        app = self.page("demo")
        snapshot = json.loads(app.session_state["patient_json"])
        snapshot.pop("huyet_ap_tam_thu_nen", None)
        app.text_area(key="patient_json").set_value(json.dumps(snapshot, ensure_ascii=False)).run()
        self.assert_clean(app)
        text = " ".join(str(element.value) for element in app.markdown)
        self.assertIn("0,7×huyet_ap_tam_thu_nen: không tính được", text)
        self.assertNotIn("0,7×huyet_ap_tam_thu_nen: 0 mmHg", text)

    def test_rules_comparison(self):
        app = self.page("rules")
        self.assertIn("kb-1.2.1", " ".join(str(item.value) for item in app.markdown))
        app.button(key="compare_run").click().run()
        self.assert_clean(app)
        self.assertEqual(app.session_state["comparison"][3], [])
        self.assertTrue(any("Không có thay đổi" in item.value for item in app.success))

    def test_batch_counts(self):
        app = self.page("batch")
        app.button(key="batch_run").click().run()
        self.assert_clean(app)
        manifest = app.session_state["batch_result"][1]
        from main import get_classifier
        import yaml
        classifier = get_classifier()
        fields = yaml.safe_load(load_package(classifier.knowledge_package_id).fields_path.read_text(encoding="utf-8"))
        records = load_records([str(ROOT / "data/synthetic/rule_logic_cases.json")])
        expected, _ = run_batch(records, classifier, fields=fields)
        self.assertEqual(manifest["counts"], expected["counts"])


if __name__ == "__main__":
    unittest.main()
