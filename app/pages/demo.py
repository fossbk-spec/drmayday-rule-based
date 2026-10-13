"""Interactive synthetic case demo."""

import json

import streamlit as st
import yaml

from app.components import render_input, render_result
from main import ISSUE_HELP, ROOT, clear_result, parse_patient
from src.knowledge import load_package


def render():
    from main import get_classifier
    classifier = get_classifier()
    fields = yaml.safe_load(load_package(classifier.knowledge_package_id).fields_path.read_text(encoding="utf-8"))
    fixture = json.loads((ROOT / "data/synthetic/rule_logic_cases.json").read_text(encoding="utf-8"))
    rules = classifier.engine.rules
    targets = [rule for rule in rules if "target_label" in rule]
    labels = list(dict.fromkeys(rule["target_label"] for rule in targets))
    st.title("Demo ca bệnh")
    st.caption("Bệnh án giả định → đánh giá phụ thuộc → chọn kết luận → giải thích từng tầng")
    with st.expander("Cách đọc kết quả và check logic"):
        st.write("Chọn ca giả, sửa JSON nếu cần rồi bấm Phân loại và giải thích. Kỳ vọng chỉ áp dụng cho ca gốc.")
        st.caption("TRUE/FALSE/UNKNOWN là trạng thái điều kiện. Ưu tiên số nhỏ hơn được xét trước.")
    selected_label = st.sidebar.selectbox("Đầu ra cần minh họa", ["Tất cả"] + labels, key="output_label", on_change=clear_result)
    selected_rules = {rule["rule_id"] for rule in targets if rule["target_label"] == selected_label}
    cases = [case for case in fixture["cases"] if selected_label == "Tất cả"
             or case["expected_engine"].get("matched_rule_id") in selected_rules
             or selected_rules.intersection(case["expected_engine"].get("rule_results", {}))]
    if not cases:
        st.warning("Chưa có ca minh họa cho đầu ra này.")
        return
    by_id = {case["id"]: case for case in cases}
    if st.session_state.get("case_id") not in by_id:
        st.session_state["case_id"] = cases[0]["id"]
    case_id = st.sidebar.selectbox("Bệnh án giả định", list(by_id), key="case_id", on_change=clear_result,
                                    format_func=lambda identifier: f"{identifier} · {by_id[identifier]['mo_ta']}")
    selected_case = by_id[case_id]
    if st.session_state.get("loaded_case") != case_id:
        st.session_state["patient_json"] = json.dumps(selected_case["du_lieu"], ensure_ascii=False, indent=2)
        st.session_state["loaded_case"] = case_id
        clear_result()
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("run_error", None)
    st.sidebar.caption(f"{len(fixture['cases'])} ca · YAML {classifier.engine.rules_version}")
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Dữ liệu đầu vào")
        st.write(selected_case["mo_ta"])
        st.text_area("JSON bệnh án · có thể sửa để thử ca biên", height=380, key="patient_json", on_change=clear_result)
        try:
            snapshot = parse_patient(st.session_state["patient_json"])
        except (ValueError, RecursionError):
            snapshot = None
            st.error("JSON không hợp lệ. Cần một object CANONICAL hoặc object có du_lieu là object; không dùng NaN/Infinity.")
        if st.button("Phân loại và giải thích", key="classify", type="primary"):
            clear_result()
            if snapshot is None:
                st.session_state["run_error"] = "JSON không hợp lệ."
            else:
                try:
                    st.session_state["result"] = classifier.classify(snapshot)
                except (TypeError, ValueError, OverflowError, RecursionError) as exc:
                    st.session_state["run_error"] = f"Engine không hoàn tất ({type(exc).__name__}). Không có kết luận bệnh."
        with st.expander("Kỳ vọng của ca gốc — để đối chiếu sau suy diễn"):
            if snapshot != selected_case["du_lieu"]:
                st.warning("JSON hiện tại đã khác ca gốc: kỳ vọng bên dưới không tự cập nhật.")
            st.json(selected_case["expected_engine"])
            st.caption("Kỳ vọng mô tả hành vi hiện tại, không phải nhãn chuẩn lâm sàng.")
        if snapshot is not None:
            render_input(snapshot, fields)
    with right:
        st.subheader("Kết quả hệ thống")
        if st.session_state["run_error"]:
            st.error(st.session_state["run_error"])
        elif st.session_state["result"] is None:
            st.info("Bấm Phân loại và giải thích để xem kết quả cho JSON hiện tại.")
        else:
            render_result(st.session_state["result"], snapshot)
        if selected_case.get("workflow_gap"):
            issue_id = selected_case["workflow_gap"]
            st.warning(f"Ca gốc · {issue_id} — {ISSUE_HELP[issue_id]} Đây là chú thích của ca gốc.")
