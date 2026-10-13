"""Validate only paths described by a canonical fields dictionary."""

import math
from typing import Any, Dict, List


Issue = Dict[str, str]
_ABSENT = object()


def _sentinel(value, conventions):
    candidates = [conventions.get("missing"), conventions.get("not_applicable")]
    candidates.extend(conventions.get("unknown", []))
    return any(type(value) is type(item) and value == item for item in candidates)


def validate_canonical(snapshot: Dict[str, Any], fields: Dict[str, Any]) -> List[Issue]:
    issues = []
    conventions = fields.get("missing_conventions", {})
    for path, spec in fields.get("fields", {}).items():
        value = snapshot
        for part in path.split("."):
            value = value.get(part, _ABSENT) if isinstance(value, dict) else _ABSENT
            if value is _ABSENT:
                break
        if value is _ABSENT or _sentinel(value, conventions):
            continue
        expected = spec.get("type")
        severity = "warning" if spec.get("todo") else "error"
        def add(code):
            issues.append({"path": path, "code": code, "severity": severity,
                           "message": f"{path}: {code}"})
        if expected == "number" and isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(value):
            add("NON_FINITE")
            continue
        valid_type = {
            "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "string": lambda v: isinstance(v, str),
            "boolean": lambda v: isinstance(v, bool),
            "list": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict),
        }.get(expected, lambda v: True)(value)
        if not valid_type:
            add("INVALID_TYPE")
            continue
        values = spec.get("values") or []
        if values:
            items = value if isinstance(value, list) else [value]
            if any(not _sentinel(item, conventions) and item not in values for item in items):
                add("INVALID_VALUE")
    return issues
