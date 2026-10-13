"""Shared views for synthetic inputs and classifier envelopes."""

import json
from collections import defaultdict

import streamlit as st

from main import LAYERS
from src.validate import validate_canonical


def render_header(classifier):
    digest = (classifier.knowledge_package_hash or "").removeprefix("sha256:")
    st.caption(f"Gói tri thức: {classifier.knowledge_package_id} · SHA-256 {digest[:12]} · Engine {classifier.classifier_version}")
    st.warning("Chỉ dữ liệu giả – không nhập bệnh án thật")


def field_value(snapshot, path):
    value = snapshot
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    return True, value


def compact(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def render_input(snapshot, fields):
    st.subheader("Trực quan input")
    groups = defaultdict(list)
    for path, spec in fields.get("fields", {}).items():
        present, value = field_value(snapshot, path)
        if not present or value is None:
            state, shown = "Thiếu", "—"
        elif value == "N/A":
            state, shown = "Không áp dụng", "N/A"
        elif value == "unknown" or (type(value) is int and value == -1):
            state, shown = "Chưa biết", compact(value)
        else:
            state, shown = "Có giá trị", compact(value)
        groups[spec.get("group", "khac")].append({"Trường": path, "Trạng thái": state, "Giá trị": shown})
    for group, rows in groups.items():
        with st.expander(group.replace("_", " ").title(), expanded=group == "tuan_hoan"):
            st.dataframe(rows, hide_index=True, width="stretch")
    present, pressure = field_value(snapshot, "huyet_ap_tam_thu_thap_nhat")
    if present and pressure is not None:
        st.markdown(f"**Huyết áp tâm thu thấp nhất:** {compact(pressure)} mmHg")
        for path, label, formula in (
            ("tuoi", "70 + 2×tuoi", lambda x: 70 + 2 * x),
            ("huyet_ap_tam_thu_nen", "0,7×huyet_ap_tam_thu_nen", lambda x: .7 * x),
        ):
            exists, value = field_value(snapshot, path)
            if not exists or value is None or value in ("unknown", "N/A", -1):
                st.write(f"{label}: không tính được: thiếu {path}")
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                st.write(f"{label}: {formula(value):g} mmHg")
            else:
                st.write(f"{label}: không tính được: {path} sai kiểu")
    issues = validate_canonical(snapshot, fields)
    st.subheader("Chất lượng dữ liệu")
    if issues:
        st.dataframe([{"path": i["path"], "mã": i["code"], "mức độ": i["severity"]} for i in issues], hide_index=True, width="stretch")
    else:
        st.success("Không có issue theo từ điển trường.")
    if any(i["severity"] == "error" for i in issues):
        st.error("Pipeline sẽ trả INVALID_DATA. Demo vẫn cho xem kết quả classifier để học; đây không phải kết quả pipeline.")


def render_result(envelope, snapshot):
    details = envelope.get("details", {})
    status = envelope["status"]
    message = f"**{status}** · {envelope.get('predicted_label') or 'Chưa kết luận bệnh'}"
    if status == "CLASSIFIED":
        st.success(message)
    elif status in ("NEEDS_REVIEW", "INVALID_DATA"):
        st.error(message)
    else:
        st.warning(message)
    st.caption(f"{envelope.get('knowledge_package_id')} · Engine {envelope.get('classifier_version')}")
    st.write(envelope.get("explanation", {}).get("summary", ""))
    st.markdown("**Việc cần làm**")
    for path in envelope.get("missing_fields", []):
        st.write(f"Bổ sung: {path}")
    for rule_id in details.get("blocking_rule_ids", []):
        st.write(f"Rà soát rule chặn: {rule_id}")
    if not envelope.get("missing_fields") and not details.get("blocking_rule_ids"):
        st.write("Không có trường thiếu hoặc rule chặn được báo cáo.")
    st.subheader("Cây 6 tầng")
    rule_results = details.get("rule_results", {})
    for title, identifiers in LAYERS:
        with st.expander(title, expanded=True):
            for identifier in identifiers:
                value = rule_results.get(identifier)
                state = "UNKNOWN" if value is None else "TRUE" if value else "FALSE"
                marker = " · ĐƯỢC CHỌN" if identifier == details.get("matched_rule_id") else (
                    " · RULE CHẶN" if identifier in details.get("blocking_rule_ids", []) else (
                        " · KHỚP, THUA PRIORITY" if identifier in details.get("matched_rule_ids", []) else ""))
                color = {"TRUE": "#167a50", "FALSE": "#68737d", "UNKNOWN": "#a36a00"}[state]
                st.markdown(f"<span style='color:{color};font-weight:700'>● {identifier} · {state}{marker}</span>", unsafe_allow_html=True)
    st.subheader("Bằng chứng từng điều kiện")
    grouped = defaultdict(list)
    for event in details.get("trace", []):
        path = event.get("field_path")
        present, value = field_value(snapshot, path) if path else (False, None)
        result = event.get("result")
        grouped[event["rule_id"]].append({
            "Điều kiện": event.get("condition_path"), "Trường": path or "—",
            "Toán tử": event.get("operator"), "Kết quả": "UNKNOWN" if result is None else "TRUE" if result else "FALSE",
            "Lý do": event.get("reason") or "—", "Giá trị": compact(value) if present else "Thiếu",
        })
    for title, identifiers in LAYERS:
        for identifier in identifiers:
            if identifier in grouped:
                with st.expander(f"{identifier} · bằng chứng"):
                    st.dataframe(grouped[identifier], hide_index=True, width="stretch")
    st.download_button("Tải envelope JSON", json.dumps(envelope, ensure_ascii=False, indent=2), file_name="result.json", mime="application/json")
