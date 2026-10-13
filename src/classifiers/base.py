"""Shared classifier output contract."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.classify import ClinicalRuleEngine
from src.version import RESULT_SCHEMA_VERSION


def make_envelope(
    *, classifier_id: str, classifier_version: str, status: str,
    predicted_label: Optional[str] = None,
    missing_fields: Optional[List[str]] = None,
    summary: str = "",
    knowledge_package_id: Optional[str] = None,
    knowledge_package_hash: Optional[str] = None,
    run_id: Optional[str] = None,
    record_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the common v1 envelope; optional classifier details stay separate."""
    if status not in ClinicalRuleEngine.STATUSES:
        raise ValueError("unsupported classifier status: " + str(status))
    envelope = {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "classifier_id": classifier_id,
        "classifier_version": classifier_version,
        "knowledge_package_id": knowledge_package_id,
        "knowledge_package_hash": knowledge_package_hash,
        "run_id": run_id,
        "record_id": record_id,
        "status": status,
        "predicted_label": predicted_label,
        "missing_fields": [] if missing_fields is None else missing_fields,
        "explanation": {"summary": summary},
        "issues": [],
        "details": {} if details is None else details,
    }
    return envelope


class Classifier(ABC):
    classifier_id: str
    classifier_version: str

    @abstractmethod
    def classify(
        self, snapshot: Dict[str, Any], *, record_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Classify one canonical snapshot and return result envelope v1."""
