"""
Bộ máy suy diễn Rule-based (Clinical Inference Engine).
Nạp quy tắc từ rules/classification_rules.yaml và đánh giá từng bản ghi bệnh nhân.
"""

import hashlib
import math
import re
from typing import Any, Dict, List, Optional, Set
import yaml

TOKEN_PATTERN = re.compile(r"PT_[0-9A-F]{16}")


class ClinicalRuleEngine:
    STATUSES = {
        "CLASSIFIED", "INSUFFICIENT_DATA", "INVALID_DATA",
        "NEEDS_REVIEW", "OUT_OF_SCOPE", "UNRESOLVED",
    }
    OPERATORS = {"==", "!=", "<", "<=", ">", ">=", "contains", "contains_any"}
    FORMULAS = {"70 + 2 * tuoi", "0.7 * huyet_ap_tam_thu_nen"}

    def __init__(self, rules_file_path: str):
        try:
            with open(rules_file_path, "rb") as stream:
                raw = stream.read()
            document = yaml.safe_load(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
            raise ValueError(f"{rules_file_path}: cannot read valid YAML ({type(exc).__name__})") from None

        if not isinstance(document, dict):
            raise ValueError(f"{rules_file_path}: root must be an object")
        version = document.get("version")
        if version is not None and (not isinstance(version, str) or not version.strip()):
            raise ValueError(f"{rules_file_path}: version must be a non-empty string")
        rules = document.get("rules")
        if not isinstance(rules, list) or not rules:
            raise ValueError(f"{rules_file_path}: rules must be a non-empty list")

        self.rules: List[Dict[str, Any]] = rules
        self._rules_by_id: Dict[str, Dict[str, Any]] = {}
        self.rules_version: Optional[str] = version
        self.rules_sha256 = hashlib.sha256(raw).hexdigest()
        references: Dict[str, Set[str]] = {}

        for index, rule in enumerate(self.rules):
            context = f"{rules_file_path}: rules[{index}]"
            if not isinstance(rule, dict):
                raise ValueError(f"{context}: rule must be an object")
            rule_id = rule.get("rule_id")
            if not isinstance(rule_id, str) or not rule_id.strip():
                raise ValueError(f"{context}: rule_id must be a non-empty string")
            if rule_id in self._rules_by_id:
                raise ValueError(f"{context} ({rule_id}): duplicate rule_id")
            self._rules_by_id[rule_id] = rule

            is_target = "target_label" in rule
            if is_target:
                label = rule["target_label"]
                priority = rule.get("priority")
                if not isinstance(label, str) or not label.strip():
                    raise ValueError(f"{context} ({rule_id}): target_label must be non-empty")
                if isinstance(priority, bool) or not isinstance(priority, int) or priority <= 0:
                    raise ValueError(f"{context} ({rule_id}): target priority must be a positive integer")
                if rule.get("is_base_condition"):
                    raise ValueError(f"{context} ({rule_id}): rule cannot be both base and target")
                if "target_status" in rule and (
                    not isinstance(rule["target_status"], str) or rule["target_status"] not in self.STATUSES
                ):
                    raise ValueError(f"{context} ({rule_id}): unsupported target_status")
            elif "target_status" in rule:
                raise ValueError(f"{context} ({rule_id}): target_status requires target_label")
            elif "priority" in rule and (
                isinstance(rule["priority"], bool) or not isinstance(rule["priority"], int) or rule["priority"] < 0
            ):
                raise ValueError(f"{context} ({rule_id}): base priority must be a non-negative integer")

        for rule_id, rule in self._rules_by_id.items():
            if not isinstance(rule.get("conditions"), dict):
                raise ValueError(f"{rules_file_path}: rule {rule_id} conditions must be an object")
            references[rule_id] = set()
            self._validate_condition(rule["conditions"], rules_file_path, rule_id, "conditions", references[rule_id])

        for rule_id, ref_ids in references.items():
            for ref_id in ref_ids:
                if ref_id not in self._rules_by_id:
                    raise ValueError(f"{rules_file_path}: rule {rule_id} references unknown rule {ref_id}")
        self._validate_reference_cycles(references, rules_file_path)
        self._dependencies = references

    @classmethod
    def _validate_condition(
        cls, condition: Dict[str, Any], source: str, rule_id: str, path: str, references: Set[str]
    ) -> None:
        if not isinstance(condition, dict):
            raise ValueError(f"{source}: rule {rule_id} {path} must be an object")
        structural = [key for key in ("all_of", "any_of", "not", "ref_rule") if key in condition]
        if structural:
            if len(structural) != 1 or len(condition) != 1:
                raise ValueError(f"{source}: rule {rule_id} {path} must contain one condition form")
            kind = structural[0]
            if kind == "ref_rule":
                ref_id = condition["ref_rule"]
                if not isinstance(ref_id, str) or not ref_id:
                    raise ValueError(f"{source}: rule {rule_id} {path}.ref_rule must be a string")
                references.add(ref_id)
                return
            if kind == "not":
                cls._validate_condition(condition["not"], source, rule_id, f"{path}.not", references)
                return
            children = condition[kind]
            if not isinstance(children, list) or not children:
                raise ValueError(f"{source}: rule {rule_id} {path}.{kind} must be a non-empty list")
            for index, child in enumerate(children):
                cls._validate_condition(child, source, rule_id, f"{path}.{kind}[{index}]", references)
            return

        operator = condition.get("operator")
        if operator == "count_matching_systems_gte":
            systems = condition.get("systems")
            minimum = condition.get("min_count", 2)
            if not isinstance(systems, dict) or not systems:
                raise ValueError(f"{source}: rule {rule_id} {path}.systems must be a non-empty object")
            if isinstance(minimum, bool) or not isinstance(minimum, int) or not 1 <= minimum <= len(systems):
                raise ValueError(f"{source}: rule {rule_id} {path}.min_count is out of bounds")
            for name, child in systems.items():
                cls._validate_condition(child, source, rule_id, f"{path}.systems.{name}", references)
            return

        if not isinstance(operator, str) or (operator not in cls.OPERATORS and operator != "<_formula"):
            raise ValueError(f"{source}: rule {rule_id} {path}.operator is unsupported")
        field = condition.get("field")
        if not isinstance(field, str) or not field.strip():
            raise ValueError(f"{source}: rule {rule_id} {path}.field must be non-empty")
        if operator == "<_formula":
            formula = condition.get("formula")
            if not isinstance(formula, str) or formula not in cls.FORMULAS:
                raise ValueError(f"{source}: rule {rule_id} {path}.formula is unsupported")
        elif "value" not in condition:
            raise ValueError(f"{source}: rule {rule_id} {path}.value is required")
        elif isinstance(condition["value"], float) and not math.isfinite(condition["value"]):
            raise ValueError(f"{source}: rule {rule_id} {path}.value must be finite")
        elif operator in {"<", "<=", ">", ">="}:
            value = condition.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or (
                isinstance(value, float) and not math.isfinite(value)
            ):
                raise ValueError(f"{source}: rule {rule_id} {path}.value must be a finite number")
        elif operator == "contains_any" and not isinstance(condition.get("value"), list):
            raise ValueError(f"{source}: rule {rule_id} {path}.value must be a list")

    @staticmethod
    def _validate_reference_cycles(references: Dict[str, Set[str]], source: str) -> None:
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(rule_id: str) -> None:
            if rule_id in visiting:
                raise ValueError(f"{source}: reference cycle includes rule {rule_id}")
            if rule_id in visited:
                return
            visiting.add(rule_id)
            for dependency in references[rule_id]:
                visit(dependency)
            visiting.remove(rule_id)
            visited.add(rule_id)

        for rule_id in references:
            visit(rule_id)

    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """Read a canonical field path without converting malformed shapes."""
        parts = field_path.split(".")
        cur = data
        for part in parts:
            if cur is None:
                raise KeyError("field is missing")
            if not isinstance(cur, dict):
                raise ValueError("field path crosses a non-object")
            if part not in cur:
                raise KeyError("field is missing")
            cur = cur[part]
        return cur

    @staticmethod
    def _safe_token(value: Any) -> str:
        """Echo only anonymizer tokens; free text in this field may carry PII."""
        if isinstance(value, str) and TOKEN_PATTERN.fullmatch(value):
            return value
        return "UNKNOWN"

    @staticmethod
    def _unknown_reason(value: Any) -> Optional[str]:
        if value is None:
            return "MISSING_VALUE"
        if isinstance(value, str) and value.strip().lower() in {"", "unknown", "n/a"}:
            return "UNKNOWN_SENTINEL"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if isinstance(value, float) and not math.isfinite(value):
                return "NON_FINITE"
            if value == -1:
                return "UNKNOWN_SENTINEL"
        return None

    @staticmethod
    def _safe_equal(actual: Any, expected: Any) -> Optional[bool]:
        numeric_types = (int, float)
        actual_numeric = isinstance(actual, numeric_types) and not isinstance(actual, bool)
        expected_numeric = isinstance(expected, numeric_types) and not isinstance(expected, bool)
        if isinstance(actual, bool) != isinstance(expected, bool):
            if actual_numeric or expected_numeric or isinstance(actual, bool) or isinstance(expected, bool):
                return None
        if actual_numeric and expected_numeric:
            return actual == expected
        if type(actual) is not type(expected):
            return None
        if not isinstance(actual, (str, bool, type(None))):
            return None
        return actual == expected

    @staticmethod
    def _append_trace(
        trace: List[Dict[str, Any]], rule_id: str, condition_path: str,
        field_path: Optional[str], operator: str, result: Optional[bool], reason: Optional[str],
    ) -> None:
        trace.append({
            "rule_id": rule_id,
            "condition_path": condition_path,
            "field_path": field_path,
            "operator": operator,
            "result": result,
            "reason": reason,
        })

    def _eval_rule(
        self, rule_id: str, data: Dict[str, Any], cache: Dict[str, Optional[bool]],
        trace: List[Dict[str, Any]],
    ) -> Optional[bool]:
        if rule_id in cache:
            return cache[rule_id]
        rule = self._rules_by_id[rule_id]
        result = self._eval_condition(rule["conditions"], data, cache, trace, rule_id)
        cache[rule_id] = result
        return result

    def _dependency_closure(self, rule_ids: List[str]) -> Set[str]:
        related: Set[str] = set()
        pending = list(rule_ids)
        while pending:
            current = pending.pop()
            if current not in related:
                related.add(current)
                pending.extend(self._dependencies[current] - related)
        return related

    def _eval_condition(
        self, cond: Dict[str, Any], data: Dict[str, Any], cache: Dict[str, Optional[bool]],
        trace: List[Dict[str, Any]], rule_id: str, condition_path: str = "conditions",
    ) -> Optional[bool]:
        if "all_of" in cond:
            results = [self._eval_condition(child, data, cache, trace, rule_id,
                       f"{condition_path}.all_of[{index}]") for index, child in enumerate(cond["all_of"])]
            if False in results:
                return False
            return True if all(result is True for result in results) else None

        if "any_of" in cond:
            results = [self._eval_condition(child, data, cache, trace, rule_id,
                       f"{condition_path}.any_of[{index}]") for index, child in enumerate(cond["any_of"])]
            if True in results:
                return True
            return False if all(result is False for result in results) else None

        if "not" in cond:
            result = self._eval_condition(cond["not"], data, cache, trace, rule_id,
                                          f"{condition_path}.not")
            return None if result is None else not result

        if "ref_rule" in cond:
            ref_id = cond["ref_rule"]
            result = self._eval_rule(ref_id, data, cache, trace)
            self._append_trace(trace, rule_id, condition_path, None, "ref_rule", result, None)
            return result

        op = cond.get("operator")

        if op == "count_matching_systems_gte":
            trace_start = len(trace)
            results = [self._eval_condition(child, data, cache, trace, rule_id,
                       f"{condition_path}.systems.{name}") for name, child in cond["systems"].items()]
            matched = sum(result is True for result in results)
            minimum = cond.get("min_count", 2)
            result = True if matched >= minimum else (
                False if matched + sum(value is None for value in results) < minimum else None
            )
            reasons = {event["reason"] for event in trace[trace_start:] if event["reason"]}
            reason = next((value for value in ("INVALID_TYPE", "NON_FINITE", "UNKNOWN_SENTINEL", "MISSING_VALUE")
                           if value in reasons), None)
            self._append_trace(trace, rule_id, condition_path, None, op, result,
                               reason if result is None else None)
            return result

        field_path = cond["field"]
        expected = cond.get("value")
        reason = None
        missing = False
        try:
            actual = self._get_nested_field(data, field_path)
        except KeyError:
            actual, reason, missing = None, "MISSING_VALUE", True
        except ValueError:
            actual, reason = None, "INVALID_TYPE"

        if op in {"==", "!="} and expected is None:
            if reason == "INVALID_TYPE":
                result = None
            elif missing or actual is None:
                reason = None
                result = op == "=="
            else:
                reason = self._unknown_reason(actual)
                result = None if reason else op == "!="
        else:
            if reason is None:
                reason = self._unknown_reason(actual)
            result = None
            if reason is None:
                if op in {"<", "<=", ">", ">="}:
                    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
                        reason = "INVALID_TYPE"
                    elif isinstance(actual, float) and not math.isfinite(actual):
                        reason = "NON_FINITE"
                    else:
                        result = {
                            "<": actual < expected, "<=": actual <= expected,
                            ">": actual > expected, ">=": actual >= expected,
                        }[op]
                elif op in {"==", "!="}:
                    equal = self._safe_equal(actual, expected)
                    if equal is None:
                        reason = "INVALID_TYPE"
                    else:
                        result = equal if op == "==" else not equal
                elif op in {"contains", "contains_any"}:
                    if not isinstance(actual, list):
                        reason = "INVALID_TYPE"
                    else:
                        expected_values = [expected] if op == "contains" else expected
                        # A missing/sentinel element is unknown, not a non-matching value.
                        comparisons = [None if self._unknown_reason(item) else self._safe_equal(item, candidate)
                                       for item in actual for candidate in expected_values]
                        result = True if True in comparisons else (
                            None if None in comparisons else False
                        )
                        if result is None:
                            reasons = [self._unknown_reason(item) for item in actual]
                            reason = next((value for value in reasons if value), "INVALID_TYPE")
                elif op == "<_formula":
                    # Both operands must be finite non-bool numbers; blame the operand that fails.
                    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
                        reason = "INVALID_TYPE"
                    measure_path = "tuoi" if cond["formula"] == "70 + 2 * tuoi" else "huyet_ap_tam_thu_nen"
                    measure = None
                    if reason is None:
                        try:
                            measure = self._get_nested_field(data, measure_path)
                        except KeyError:
                            reason = "MISSING_VALUE"
                        except ValueError:
                            reason = "INVALID_TYPE"
                        if reason is None:
                            reason = self._unknown_reason(measure)
                        if reason is None and (isinstance(measure, bool) or not isinstance(measure, (int, float))):
                            reason = "INVALID_TYPE"
                        if reason is not None:
                            field_path = measure_path
                    if reason is None:
                        try:
                            threshold = 70.0 + 2.0 * measure if measure_path == "tuoi" else 0.7 * measure
                            if isinstance(threshold, float) and not math.isfinite(threshold):
                                reason = "NON_FINITE"
                            else:
                                result = actual < threshold
                        except OverflowError:
                            reason = "NON_FINITE"

        self._append_trace(trace, rule_id, condition_path, field_path, op, result, reason)
        return result

    def classify_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate all rules, then select a result without treating unknown as false."""
        if not isinstance(patient_data, dict):
            raise ValueError("patient_data must be an object")

        cache: Dict[str, Optional[bool]] = {}
        trace: List[Dict[str, Any]] = []
        for rule_id in sorted(self._rules_by_id):
            self._eval_rule(rule_id, patient_data, cache, trace)

        targets = [rule for rule in self.rules if "target_label" in rule]
        matched = sorted(rule["rule_id"] for rule in targets if cache[rule["rule_id"]] is True)
        candidates = [rule for rule in targets if cache[rule["rule_id"]] is not False]
        priority = min((rule["priority"] for rule in candidates), default=99)
        active = [rule for rule in candidates if rule["priority"] == priority]
        active_true = [rule for rule in active if cache[rule["rule_id"]] is True]
        active_unknown = [rule for rule in active if cache[rule["rule_id"]] is None]
        pairs = {(rule["target_label"], rule.get("target_status", "CLASSIFIED"))
                 for rule in active_true}

        status = "UNRESOLVED"
        representative = None
        blockers: List[str] = []
        relevant_rule_ids: Set[str] = set()
        if not active:
            decision_trace = "Không có luật đích phù hợp với dữ liệu đã đánh giá."
        elif len(pairs) > 1:
            status = "NEEDS_REVIEW"
            blockers = sorted(rule["rule_id"] for rule in active_true)
            decision_trace = "Nhiều kết luận khác nhau cùng mức ưu tiên cần được rà soát."
        elif active_unknown:
            known_pair = next(iter(pairs)) if pairs else None
            changing_unknowns = [rule for rule in active_unknown if (
                known_pair is None or
                (rule["target_label"], rule.get("target_status", "CLASSIFIED")) != known_pair
            )]
            if changing_unknowns:
                blockers = sorted(rule["rule_id"] for rule in changing_unknowns)
                if active_true and known_pair is not None:
                    blockers = sorted(set(blockers) | {
                        rule["rule_id"] for rule in active_true
                        if (rule["target_label"], rule.get("target_status", "CLASSIFIED")) != known_pair
                    })
                relevant_rule_ids = self._dependency_closure(blockers)
                reasons = {event["reason"] for event in trace
                           if event["rule_id"] in relevant_rule_ids and event["result"] is None}
                status = "NEEDS_REVIEW" if reasons.intersection({"INVALID_TYPE", "NON_FINITE"}) else "INSUFFICIENT_DATA"
                missing_fields = sorted({
                    event["field_path"] for event in trace
                    if event["rule_id"] in relevant_rule_ids
                    and event["reason"] in {"MISSING_VALUE", "UNKNOWN_SENTINEL"}
                    and event["field_path"]
                })
                decision_trace = "Cần rà soát kiểu dữ liệu hoặc bổ sung các trường: " + ", ".join(missing_fields) \
                    if missing_fields else "Có dữ kiện chưa đủ hoặc không hợp lệ ở luật ưu tiên cao nhất."
            else:
                representative = min(active_true, key=lambda rule: rule["rule_id"])
                status = representative.get("target_status", "CLASSIFIED")
                decision_trace = representative.get("decision_trace", "")
        else:
            representative = min(active_true, key=lambda rule: rule["rule_id"])
            status = representative.get("target_status", "CLASSIFIED")
            decision_trace = representative.get("decision_trace", "")

        if representative is None and not active_unknown and active_true and len(pairs) == 1:
            representative = min(active_true, key=lambda rule: rule["rule_id"])
        if status == "UNRESOLVED":
            priority = 99

        return {
            "patient_token_id": self._safe_token(patient_data.get("patient_token_id")),
            "predicted_label": representative["target_label"] if status == "CLASSIFIED" and representative else None,
            "matched_rule_id": representative["rule_id"] if representative else None,
            "priority": priority,
            "decision_trace": decision_trace,
            "status": status,
            "rule_results": {rule_id: cache[rule_id] for rule_id in sorted(cache)},
            "matched_rule_ids": matched,
            "blocking_rule_ids": sorted(blockers),
            "missing_fields": sorted({
                event["field_path"] for event in trace
                if event["rule_id"] in relevant_rule_ids
                and event["reason"] in {"MISSING_VALUE", "UNKNOWN_SENTINEL"}
                and event["field_path"]
            }),
            "trace": trace,
            "rules_version": self.rules_version,
            "rules_sha256": self.rules_sha256,
        }
