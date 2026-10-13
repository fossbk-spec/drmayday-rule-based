"""Thin canonical ingest, validation, classification, and evaluation pipeline."""

import argparse
import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.classifiers import RuleBasedClassifier, make_envelope
from src.evaluate import evaluate
from src.ingest import load_records
from src.knowledge import load_package
from src.validate import validate_canonical
from src.version import RESULT_SCHEMA_VERSION


def run_batch(records, classifier, *, fields, run_id=None):
    run_id = run_id or "run-" + uuid.uuid4().hex[:12]
    results = []
    inputs = []
    seen_inputs = set()
    package_id = getattr(classifier, "knowledge_package_id", None)
    package_hash = getattr(classifier, "knowledge_package_hash", None)
    for record in records:
        source = (record.metadata.get("file"), record.metadata.get("sha256"))
        if source[0] is not None and source not in seen_inputs:
            inputs.append({"path": source[0], "sha256": source[1]})
            seen_inputs.add(source)
        if record.error:
            results.append({"record_id": record.record_id, "error": record.error})
            continue
        try:
            issues = validate_canonical(record.snapshot, fields)
            if any(issue["severity"] == "error" for issue in issues):
                result = make_envelope(classifier_id=classifier.classifier_id,
                                       classifier_version=classifier.classifier_version,
                                       knowledge_package_id=package_id,
                                       knowledge_package_hash=package_hash,
                                       run_id=run_id, record_id=record.record_id,
                                       status="INVALID_DATA", details={})
            else:
                result = classifier.classify(record.snapshot, record_id=record.record_id, run_id=run_id)
            result["issues"] = issues
            results.append(result)
        except Exception as exc:
            results.append({"record_id": record.record_id, "error": type(exc).__name__})
    statuses = Counter(result["status"] for result in results if "status" in result)
    manifest = {"run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(),
                "classifier_id": classifier.classifier_id,
                "classifier_version": classifier.classifier_version,
                "knowledge_package_id": package_id,
                "knowledge_package_hash": package_hash,
                "fields_version": fields.get("version"), "inputs": inputs,
                "counts": {"received": len(records), "classified_by_status": dict(statuses),
                           "invalid_data": statuses["INVALID_DATA"],
                           "errors": sum("error" in result for result in results),
                           "with_ground_truth": sum(record.ground_truth is not None for record in records)},
                "result_schema_version": RESULT_SCHEMA_VERSION}
    return manifest, results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--env", default="demo")
    source.add_argument("--package")
    source.add_argument("--rules")
    parser.add_argument("--out", required=True)
    parser.add_argument("--label-map", default="data/synthetic/label_map.yaml")
    args = parser.parse_args()
    if args.rules:
        rules = Path(args.rules)
        classifier = RuleBasedClassifier(rules)
        fields_path = rules.parent / "fields.yaml"
    elif args.package:
        package = load_package(args.package)
        classifier = RuleBasedClassifier.from_package(args.package)
        fields_path = package.fields_path
    else:
        classifier = RuleBasedClassifier.from_active(args.env)
        fields_path = load_package(classifier.knowledge_package_id).fields_path
    fields = yaml.safe_load(fields_path.read_text(encoding="utf-8"))
    records = load_records(args.input)
    manifest, results = run_batch(records, classifier, fields=fields)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "results.jsonl").write_text("".join(json.dumps(result, ensure_ascii=False) + "\n" for result in results), encoding="utf-8")
    lines = [f"# Tổng kết run {manifest['run_id']}", "", f"Classifier: {manifest['classifier_id']} {manifest['classifier_version']}",
             f"Knowledge: {manifest['knowledge_package_id']} ({manifest['knowledge_package_hash']})",
             f"Fields: {manifest['fields_version']}; result schema: {manifest['result_schema_version']}",
             "", f"Số record: {manifest['counts']['received']}", "", "## Trạng thái", ""]
    lines.extend(f"- {status}: {count}" for status, count in sorted(manifest["counts"]["classified_by_status"].items()))
    lines.extend([f"- Lỗi: {manifest['counts']['errors']}", "", "## Record lỗi hoặc dữ liệu không hợp lệ", ""])
    for result in results:
        if "error" in result:
            lines.append(f"- {result['record_id']}: {result['error']}")
        elif result["status"] == "INVALID_DATA":
            codes = ", ".join(sorted({issue["code"] for issue in result["issues"] if issue["severity"] == "error"}))
            lines.append(f"- {result['record_id']}: {codes}")
    if manifest["counts"]["with_ground_truth"]:
        label_map = yaml.safe_load(Path(args.label_map).read_text(encoding="utf-8"))
        assessment = evaluate(results, records, label_map)
        (out / "evaluation.json").write_text(json.dumps(assessment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines.extend(["", "## Đánh giá", "", f"Mẫu số: {assessment['denominator']} record có nhãn.",
                      f"Accuracy: {assessment['accuracy']:.4f}; coverage: {assessment['coverage']:.4f}."])
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
