"""Adapter for the existing clinical rule engine."""

from typing import Any, Dict, Optional

from src.classify import ClinicalRuleEngine
from src.knowledge import load_package, resolve_active
from src.version import ENGINE_VERSION

from .base import Classifier, make_envelope


class RuleBasedClassifier(Classifier):
    classifier_id = "rule-based"
    classifier_version = ENGINE_VERSION

    def __init__(self, rules_path: str):
        self.engine = ClinicalRuleEngine(str(rules_path))
        self._package_id = None
        self._package_hash = None

    @classmethod
    def from_package(cls, package_id: str) -> "RuleBasedClassifier":
        package = load_package(package_id)
        instance = cls(package.rules_path)
        instance._package_id = package.package_id
        instance._package_hash = package.package_hash
        return instance

    @classmethod
    def from_active(cls, environment: str) -> "RuleBasedClassifier":
        package_id = resolve_active(environment)
        if package_id is None:
            raise ValueError(f"no active knowledge package for environment: {environment}")
        return cls.from_package(package_id)

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
            knowledge_package_id=self._package_id or ("kb-" + result["rules_version"] if result["rules_version"] else None),
            knowledge_package_hash=self._package_hash or "sha256:" + result["rules_sha256"],
            run_id=run_id, record_id=record_id,
            status=result["status"], predicted_label=result["predicted_label"],
            missing_fields=result["missing_fields"], summary=result["decision_trace"],
            details=details,
        )
