"""Knowledge package catalog and in-process impact comparison."""

import json
from collections import Counter

import streamlit as st
import yaml

from main import LAYERS, ROOT
from src.classifiers import RuleBasedClassifier
from src.knowledge import KNOWLEDGE_ROOT, load_package, resolve_active


def sources():
    return [path.name for path in sorted(KNOWLEDGE_ROOT.iterdir()) if path.is_dir() and path.name.startswith("kb-")] + ["rules/"]


@st.cache_resource
def source_classifier(source):
    return RuleBasedClassifier(ROOT / "rules/classification_rules.yaml") if source == "rules/" else RuleBasedClassifier.from_package(source)


@st.cache_data
def compare(before, after):
    cases = json.loads((ROOT / "data/synthetic/rule_logic_cases.json").read_text(encoding="utf-8"))["cases"]
    first, second = source_classifier(before), source_classifier(after)
    old_counts, new_counts, changed = Counter(), Counter(), []
    for case in cases:
        old, new = first.classify(case["du_lieu"]), second.classify(case["du_lieu"])
        old_counts[old["status"]] += 1
        new_counts[new["status"]] += 1
        keys = ("status", "predicted_label")
        rule_old, rule_new = old["details"]["matched_rule_id"], new["details"]["matched_rule_id"]
        if any(old[key] != new[key] for key in keys) or rule_old != rule_new:
            changed.append({"Ca": case["id"], "Status trước": old["status"], "Status sau": new["status"],
                            "Nhãn trước": old["predicted_label"], "Nhãn sau": new["predicted_label"],
                            "Rule trước": rule_old, "Rule sau": rule_new})
    counts = [{"Status": key, "Trước": old_counts[key], "Sau": new_counts[key]} for key in sorted(old_counts.keys() | new_counts.keys())]
    return counts, changed


def render():
    st.title("Luật & phiên bản")
    ids = sources()
    rows = []
    for package_id in ids:
        if package_id == "rules/":
            continue
        package = load_package(package_id)
        manifest = package.manifest
        rows.append({"ID": package_id, "Version": manifest.get("package_version"), "Ngày": manifest.get("released_at"),
                     "Tóm tắt": manifest.get("change_summary"), "Hash": package.package_hash,
                     "Engine hỗ trợ": ", ".join(manifest.get("supported_engine_versions", []))})
    st.subheader("Gói tri thức")
    st.dataframe(rows, hide_index=True, width="stretch")
    st.write(f"Con trỏ active.yaml · demo: {resolve_active('demo') or '—'} · real: {resolve_active('real') or '—'}")
    selected = st.selectbox("Gói xem luật", ids[:-1])
    classifier = source_classifier(selected)
    rules = {rule["rule_id"]: rule for rule in classifier.engine.rules}
    for title, identifiers in LAYERS:
        with st.expander(title):
            for identifier in identifiers:
                rule = rules[identifier]
                st.markdown(f"**{identifier}** · {rule.get('target_label', 'Điều kiện cơ sở')} · priority {rule.get('priority', '—')}")
                st.write(rule.get("decision_trace", ""))
                with st.expander(f"Điều kiện YAML · {identifier}"):
                    st.code(yaml.safe_dump(rule["conditions"], allow_unicode=True, sort_keys=False), language="yaml")
    st.subheader("So sánh 138 ca giả")
    before = st.selectbox("Nguồn trước", ids, index=0, key="compare_before")
    after = st.selectbox("Nguồn sau", ids, index=len(ids)-1, key="compare_after")
    if st.button("So sánh", key="compare_run"):
        st.session_state["comparison"] = (before, after, *compare(before, after))
    comparison = st.session_state.get("comparison")
    if comparison:
        old_source, new_source, counts, changed = comparison
        st.caption(f"{old_source} → {new_source}")
        st.dataframe(counts, hide_index=True, width="stretch")
        if changed:
            st.dataframe(changed, hide_index=True, width="stretch")
        else:
            st.success("Không có thay đổi status, nhãn hoặc rule.")
    st.markdown("[Quy trình phát hành tri thức](https://github.com/fossbk-spec/drmayday-rule-based/blob/main/docs/knowledge_release.md) · [Changelog](https://github.com/fossbk-spec/drmayday-rule-based/blob/main/docs/05_changelog.md)")
