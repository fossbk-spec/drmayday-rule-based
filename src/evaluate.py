"""Evaluate all labelled records, including abstentions and errors."""

from collections import Counter


def evaluate(results, records, label_map):
    if len(results) != len(records):
        raise ValueError("results and records must have equal length")
    pairs = []
    classified = 0
    for result, record in zip(results, records):
        if record.ground_truth is None:
            continue
        if record.ground_truth not in label_map:
            raise ValueError(f"nhãn thật chưa có trong label_map: {record.ground_truth}")
        status = result.get("status")
        if status == "CLASSIFIED":
            classified += 1
        prediction = (result.get("predicted_label") if status == "CLASSIFIED" else
                      f"({status})" if status else "(ERROR)")
        pairs.append((label_map[record.ground_truth], prediction))
    actual = sorted({a for a, _ in pairs})
    predicted = sorted(set(actual) | {p for _, p in pairs})
    matrix = {a: {p: sum(x == a and y == p for x, y in pairs) for p in predicted} for a in actual}
    metrics = {}
    for label in actual:
        tp = sum(a == label and p == label for a, p in pairs)
        support = sum(a == label for a, _ in pairs)
        predicted_count = sum(p == label for _, p in pairs)
        precision = tp / predicted_count if predicted_count else 0.0
        recall = tp / support if support else 0.0
        metrics[label] = {"support": support, "precision": precision, "recall": recall,
                          "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0}
    denominator = len(pairs)
    return {"denominator": denominator, "coverage_denominator": denominator,
            "accuracy_denominator": denominator, "classified": classified,
            "confusion_matrix": matrix, "per_class": metrics,
            "macro": {key: sum(metric[key] for metric in metrics.values()) / len(metrics) if metrics else 0.0
                      for key in ("precision", "recall", "f1")},
            "accuracy": sum(a == p for a, p in pairs) / denominator if denominator else 0.0,
            "coverage": classified / denominator if denominator else 0.0}
