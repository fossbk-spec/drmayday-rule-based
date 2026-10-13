"""Update or check the rule-to-field references in rules/fields.yaml."""

import argparse
import re
from collections import defaultdict
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules" / "classification_rules.yaml"
FIELDS = ROOT / "rules" / "fields.yaml"


def rule_field_usage(document):
    usage = defaultdict(set)

    def visit(node, rule_id):
        if isinstance(node, list):
            for child in node:
                visit(child, rule_id)
        elif isinstance(node, dict):
            if "field" in node:
                usage[node["field"]].add(rule_id)
            if node.get("operator") == "<_formula":
                # Formula identifiers are additional input paths read by the engine.
                for identifier in re.findall(r"[A-Za-z_][A-Za-z_0-9]*", node["formula"]):
                    usage[identifier].add(rule_id)
            for child in node.values():
                visit(child, rule_id)

    for rule in document["rules"]:
        visit(rule["conditions"], rule["rule_id"])
    return {path: sorted(rule_ids) for path, rule_ids in usage.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify coverage and used_by without editing")
    args = parser.parse_args()
    rules = yaml.safe_load(RULES.read_text(encoding="utf-8"))
    fields = yaml.safe_load(FIELDS.read_text(encoding="utf-8"))
    usage = rule_field_usage(rules)
    entries = fields["fields"]
    missing = sorted(set(usage) - set(entries))
    if missing:
        print("Missing field paths: " + ", ".join(missing))
    stale = []
    for path in sorted(set(entries) & set(usage)):
        if entries[path].get("used_by") != usage[path]:
            stale.append(path)
            if not args.check:
                entries[path]["used_by"] = usage[path]
    if args.check:
        if stale:
            print("Stale used_by: " + ", ".join(stale))
    elif stale:
        FIELDS.write_text(yaml.safe_dump(fields, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print("Updated used_by: " + ", ".join(stale))
    return 1 if missing or (args.check and stale) else 0


if __name__ == "__main__":
    raise SystemExit(main())
