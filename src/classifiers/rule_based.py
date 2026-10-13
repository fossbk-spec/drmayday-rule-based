"""Adapter for the existing clinical rule engine."""

from typing import Any, Dict, Optional

from src.classify import ClinicalRuleEngine
from src.version import ENGINE_VERSION

from .base import Classifier, make_envelope


class RuleBasedClassifier(Classifier):
    classifier_id = "rule-based"
    classifier_version = ENGINE_VERSION

    def __init__(self, rules_path: str):
        self.engine = ClinicalRuleEngine(str(rules_path))

    def classify(
        self, snapshot: Dict[str, Any], *, record_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        result = self.engine.classify_patient(snapshot)
        details = {key: result[key] for key in (
            "matched_rule_id", "matched_rule_ids", "blocking_rule_ids", "priority",
            "rule_results", "trace",
        )}
        return make_envelope(
            classifier_id=self.classifier_id,
            classifier_version=self.classifier_version,
            knowledge_package_id=("kb-" + result["rules_version"] if result["rules_version"] else None),
            knowledge_package_hash="sha256:" + result["rules_sha256"],
            run_id=run_id, record_id=record_id,
            status=result["status"], predicted_label=result["predicted_label"],
            missing_fields=result["missing_fields"], summary=result["decision_trace"],
            details=details,
        )
