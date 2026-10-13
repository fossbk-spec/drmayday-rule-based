"""Compare synthetic-case classification across two complete checkouts."""

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


CHILD = r'''
import hashlib
import json
import sys
from pathlib import Path
from src.classify import ClinicalRuleEngine

root, cases_file = map(Path, sys.argv[1:3])
raw = (root / "rules" / "classification_rules.yaml").read_bytes().replace(b"\r\n", b"\n")
engine = ClinicalRuleEngine(str(root / "rules" / "classification_rules.yaml"))
cases = json.loads(cases_file.read_text(encoding="utf-8"))["cases"]
targets = {rule["rule_id"]: rule["target_label"] for rule in engine.rules if "target_label" in rule}
rows = []
for case in cases:
    row = {"id": case["id"], "description": next((str(case[key]) for key in ("description", "mo_ta", "mô_tả") if key in case), "")}
    try:
        result = engine.classify_patient(case["du_lieu"])
        row.update({key: result[key] for key in ("status", "predicted_label", "matched_rule_id", "blocking_rule_ids", "missing_fields")})
        row["candidates"] = sorted({label for rule_id, label in targets.items() if result["rule_results"].get(rule_id) is not False})
    except Exception as exc:
        row["error"] = type(exc).__name__
    rows.append(row)
print(json.dumps({"version": engine.rules_version, "hash": "sha256:" + hashlib.sha256(raw).hexdigest(), "cases": rows}, ensure_ascii=False))
'''

COMPARE_KEYS = ("status", "predicted_label", "matched_rule_id", "blocking_rule_ids", "missing_fields", "candidates")
HIGH_RISK = {"Sốc phản vệ", "Phản vệ"}


def run_root(root, cases):
    root = Path(root).resolve()
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", CHILD, str(root), str(Path(cases).resolve())],
        cwd=root, env=__import__("os").environ.copy(), capture_output=True, text=True,
    )
    if result.returncode:
        raise ValueError(f"{root}: subprocess failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def _cell(value):
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ")


def report(base, head):
    before = {row["id"]: row for row in base["cases"]}
    after = {row["id"]: row for row in head["cases"]}
    if set(before) != set(after):
        raise ValueError("case IDs differ between checkouts")
    lines = ["<!-- impact-report -->", "# Báo cáo tác động luật", "",
             f"- Trước: version {_cell(base['version'])}, YAML {_cell(base['hash'])}",
             f"- Sau: version {_cell(head['version'])}, YAML {_cell(head['hash'])}", "",
             "## Số ca theo status", "", "| Status | Trước | Sau |", "|---|---:|---:|"]
    old_counts = Counter(row.get("status", "ERROR") for row in before.values())
    new_counts = Counter(row.get("status", "ERROR") for row in after.values())
    for status in sorted(old_counts.keys() | new_counts.keys()):
        lines.append(f"| {_cell(status)} | {old_counts[status]} | {new_counts[status]} |")
    counts = {key: sum(before[case_id].get(key) != after[case_id].get(key) for case_id in before)
              for key in COMPARE_KEYS}
    labels = {"status": "status", "predicted_label": "nhãn", "matched_rule_id": "matched_rule_id",
              "blocking_rule_ids": "blocking_rule_ids", "missing_fields": "missing_fields",
              "candidates": "candidate"}
    lines += ["", "## Số ca thay đổi", ""]
    lines += [f"- {labels[key]}: {counts[key]}" for key in COMPARE_KEYS]
    changed = [case_id for case_id in before if any(before[case_id].get(key) != after[case_id].get(key)
               for key in COMPARE_KEYS) or before[case_id].get("error") != after[case_id].get("error")]
    lines += ["", "## Các ca thay đổi", ""]
    if not changed:
        lines.append("Không có thay đổi kết quả.")
    else:
        lines += ["| ID | Mô tả ngắn | Trước → Sau |", "|---|---|---|"]
        for case_id in changed:
            old, new = before[case_id], after[case_id]
            differences = [f"{labels[key]}: {_cell(old.get(key))} → {_cell(new.get(key))}"
                           for key in COMPARE_KEYS if old.get(key) != new.get(key)]
            if old.get("error") != new.get("error"):
                differences.append(f"lỗi: {_cell(old.get('error'))} → {_cell(new.get('error'))}")
            lines.append(f"| {_cell(case_id)} | {_cell(new['description'])} | {'; '.join(differences)} |")
    lines += ["", "## Ca Sốc phản vệ hoặc Phản vệ thay đổi", ""]
    high_risk = [case_id for case_id in changed if any(
        risk in label for risk in HIGH_RISK for label in
        [before[case_id].get("predicted_label"), after[case_id].get("predicted_label")]
        + before[case_id].get("candidates", []) + after[case_id].get("candidates", [])
        if isinstance(label, str))]
    if high_risk:
        lines += ["| ID | Mô tả ngắn | Trước → Sau |", "|---|---|---|"]
        for case_id in high_risk:
            old, new = before[case_id], after[case_id]
            lines.append(f"| {_cell(case_id)} | {_cell(new['description'])} | "
                         f"{_cell(old.get('predicted_label') or old.get('candidates'))} → "
                         f"{_cell(new.get('predicted_label') or new.get('candidates'))} |")
    else:
        lines.append("Không có ca thuộc nhóm này thay đổi.")
    lines += ["", "## Ngoại lệ", ""]
    errors = [(case_id, side, row["error"]) for side, group in (("trước", before), ("sau", after))
              for case_id, row in group.items() if "error" in row]
    lines += [f"- {_cell(case_id)} ({side}): {_cell(error)}" for case_id, side, error in errors] or ["Không có ngoại lệ."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--head-root", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        markdown = report(run_root(args.base_root, args.cases), run_root(args.head_root, args.cases))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, str(exc) + "\n")
    if args.out:
        with args.out.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(markdown)
    else:
        print(markdown, end="")


if __name__ == "__main__":
    main()
