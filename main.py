"""Streamlit demo of the existing engine, not the unimplemented RAW pipeline."""

import json
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from src.classify import ClinicalRuleEngine


ROOT = Path(__file__).resolve().parent
ISSUE_HELP = {
    "F-01": "Cấp thông thường chưa khả đạt: cùng biến triệu chứng đang được yêu cầu vừa là object vừa là chuỗi.",
    "F-02": "Tuổi dưới một tháng, 10,5 và 17,5 chưa được các khoảng sốc hiện tại bao phủ; không tự làm tròn tuổi.",
    "F-03": "Đúng 6 tuần: cấp dùng <=1008 giờ, mạn dùng >6 tuần; ranh giới và nguồn thời gian cần chốt.",
    "F-04": "R03 dùng tác nhân nghi ngờ thay tiêu chí dị nguyên đã biết; các rule phản vệ chưa kiểm tra thời điểm.",
    "F-05": "Sốc chỉ tham chiếu R02/R03; ca chỉ đạt R01 dù HATT thấp vẫn không vào rule sốc hiện tại.",
    "F-06": "CIndU khác chưa loại Ice cube dương; Adrenergic chưa có nhánh; nhiều test dương cần chính sách phân thể.",
    "F-07": "Chưa có validator enum/range: giá trị test sai có thể được coi là không dương; HATT âm vẫn có thể thỏa rule.",
    "F-08": "Stella FALSE/UNKNOWN vẫn có thể vào CSU GĐ2 vì IgE <40; YAML khác workflow, chưa có nhánh loại cohort.",
    "F-09": "Thiếu sàng lọc phản vệ chung có thể chặn CSU dù xét nghiệm đầy đủ; không tự điền Không vào trường thiếu.",
    "F-10": "CIndU được chọn trước CSU khi cùng khớp; điều kiện cohort và biểu diễn đồng mắc chưa chốt.",
    "F-11": "ASST null có thể kích hoạt fallback ngoài CSU; rule UNKNOWN ưu tiên cao vẫn có thể chặn fallback.",
    "F-12": "Đã sửa 13/10/2026 (TECH-01): HATT sai kiểu (bool/chuỗi/list/object) ở công thức giờ trả NEEDS_REVIEW, không crash và không kết luận sốc.",
    "F-13": "Lý do UNKNOWN có thể bị lẫn với lỗi kiểu từ nhánh OR đã đủ bằng chứng, làm sai lý do cần rà soát.",
}
STATUS_HELP = {
    "CLASSIFIED": "Có nhãn theo YAML hiện tại.",
    "INSUFFICIENT_DATA": "Thiếu dữ kiện hoặc chưa đủ thời gian; xem rule chặn và trường cần bổ sung.",
    "NEEDS_REVIEW": "Chưa có kết luận bệnh: có xung đột hoặc dữ liệu cần rà soát; xem điều kiện và trace của các rule chặn.",
    "UNRESOLVED": "Không có rule đích phù hợp sau đánh giá hiện tại.",
}
LAYERS = (
    ("T1 · Sốc phản vệ", ("R-SOC",)),
    ("T2 · Phản vệ và theo dõi", ("R01-PV", "R02-PV", "R03-PV", "R-PV-THEODOI")),
    ("T3 · Mày đay cấp", ("R-SANGLOC-CAP", "R01-CAP-NANG", "R01-CAP-THUONG")),
    ("T4 · Mày đay cảm ứng mạn tính — CIndU", (
        "R-CindU-00", "R-CindU-01", "R-CindU-02", "R-CindU-03", "R-CindU-04",
    )),
    ("T5 · Mày đay tự phát mạn tính — CSU", (
        "R-CSU-00", "R-GD-01", "R-GD-02", "R-CSU-T1-01", "R-CSU-T1-02",
        "R-CSU-T2-01", "R-CSU-OVL-01", "R-CSU-UNK-01", "R-CSU-UNK-02",
    )),
    ("T6 · Chưa đủ dữ kiện / ngoại lệ", ("R-DEFAULT",)),
)


def clear_result() -> None:
    st.session_state["result"] = None
    st.session_state["run_error"] = None


def reject_constant(value: str) -> None:
    raise ValueError("JSON không hỗ trợ NaN hoặc Infinity.")


def parse_patient(text: str) -> Dict[str, Any]:
    data = json.loads(text, parse_constant=reject_constant)
    if not isinstance(data, dict):
        raise ValueError("Đầu vào phải là một JSON object.")
    patient = data.get("du_lieu", data)
    if not isinstance(patient, dict):
        raise ValueError("du_lieu phải là một JSON object.")
    metadata = {"nhan", "expected_engine", "workflow_gap", "id", "mo_ta"}
    return {key: value for key, value in patient.items() if key not in metadata}


def render() -> None:
    st.set_page_config(page_title="Rule-based · Mề đay", page_icon="🔎", layout="wide")
    st.title("Hệ thốngRule-based mề đay")
    st.caption("Bệnh án giả định → đánh giá phụ thuộc → chọn kết luận → giải thích từng tầng")
    st.info(
        "14 đầu ra mặt bệnh = 12 nhóm bệnh + 2 nhãn theo dõi."
    )
    with st.expander("Cách đọc kết quả và check logic"):
        st.markdown(
            "1. Chọn đầu ra và ca giả định; bấm **Phân loại và giải thích**.\n"
            "2. Xem trạng thái, rule được chọn và rule chặn; mở **6 tầng phân loại** để đối chiếu điều kiện.\n"
            "3. Sửa một biến mỗi lần, thử trước/tại/sau ngưỡng hoặc xóa một trường rồi chạy lại.\n"
            "4. Kết quả kỳ vọng chỉ thuộc **ca gốc**; JSON đã sửa có thể có kết quả riêng. Ghi ca sai lệch (lưu **JSON đã sửa + kết quả mong đợi + kết quả thực tế**) để re-check."
        )
        st.table([{"Trạng thái": status, "Ý nghĩa": explanation} for status, explanation in STATUS_HELP.items()])
        st.caption("TRUE/FALSE/UNKNOWN là trạng thái điều kiện, không phải nhãn bệnh. Ưu tiên số nhỏ hơn được xét trước.")
        st.caption("INVALID_DATA / OUT_OF_SCOPE thuộc pipeline chưa triển khai; JSON sai hiện được demo báo lỗi nhập.")
        st.caption("Hướng dẫn và nhật ký thay đổi: docs/05_changelog.md. Phân tích đầy đủ: docs/06_rule_logic_review.md.")
    try:
        engine = ClinicalRuleEngine(str(ROOT / "rules/classification_rules.yaml"))
        fixture = json.loads((ROOT / "data/synthetic/rule_logic_cases.json").read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        st.error(f"Không nạp được cấu hình demo ({type(exc).__name__}). Kiểm tra YAML và bộ ca giả định.")
        return

    rules = {rule["rule_id"]: rule for rule in engine.rules}
    targets = [rule for rule in engine.rules if "target_label" in rule]
    labels = list(dict.fromkeys(rule["target_label"] for rule in targets))
    st.sidebar.header("Chọn nội dung minh họa")
    selected_label = st.sidebar.selectbox(
        "Đầu ra cần minh họa", ["Tất cả"] + labels, key="output_label", on_change=clear_result,
    )
    selected_rules = {rule["rule_id"] for rule in targets if rule["target_label"] == selected_label}
    cases = [case for case in fixture["cases"] if selected_label == "Tất cả"
             or case["expected_engine"].get("matched_rule_id") in selected_rules
             or selected_rules.intersection(case["expected_engine"].get("rule_results", {}))]
    if not cases:
        st.warning("Chưa có ca minh họa cho đầu ra này trong bộ dữ liệu hiện tại.")
        return
    by_id = {case["id"]: case for case in cases}
    if st.session_state.get("case_id") not in by_id:
        st.session_state["case_id"] = cases[0]["id"]
    case_id = st.sidebar.selectbox(
        "Bệnh án giả định", list(by_id), key="case_id", on_change=clear_result,
        format_func=lambda identifier: f"{identifier} · {by_id[identifier]['mo_ta']}",
    )
    selected_case = by_id[case_id]
    if st.session_state.get("loaded_case") != case_id:
        st.session_state["patient_json"] = json.dumps(selected_case["du_lieu"], ensure_ascii=False, indent=2)
        st.session_state["loaded_case"] = case_id
        clear_result()
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("run_error", None)
    st.sidebar.caption(f"{len(fixture['cases'])} ca · YAML {engine.rules_version}")
    st.sidebar.caption("Chỉ sử dụng bệnh án giả định trong demo này.")

    input_tab, layers_tab, catalog_tab, diagrams_tab = st.tabs([
        "Bệnh án & kết quả", "6 tầng phân loại", "14 mặt bệnh & điều kiện", "Workflow & diagram",
    ])
    with input_tab:
        left, right = st.columns([1, 1])
        with left:
            st.subheader("Dữ liệu đầu vào")
            st.write(selected_case["mo_ta"])
            st.text_area("JSON bệnh án · có thể sửa để thử ca biên", height=380,
                         key="patient_json", on_change=clear_result)
            try:
                current_patient = parse_patient(st.session_state["patient_json"])
            except (ValueError, RecursionError):
                current_patient = None
            input_changed = current_patient != selected_case["du_lieu"]
            if st.button("Phân loại và giải thích", key="classify", type="primary"):
                clear_result()
                try:
                    patient = parse_patient(st.session_state["patient_json"])
                except (ValueError, RecursionError):
                    st.session_state["run_error"] = (
                        "JSON không hợp lệ. Cần một object CANONICAL hoặc object có du_lieu là object; "
                        "không dùng NaN/Infinity."
                    )
                else:
                    try:
                        st.session_state["result"] = engine.classify_patient(patient)
                    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
                        # The demo must show an engine failure, not invent a label.
                        st.session_state["run_error"] = (
                            f"Engine không hoàn tất ({type(exc).__name__}). Kiểm tra kiểu dữ liệu. "
                            "Không có kết luận bệnh."
                        )
            with st.expander("Kỳ vọng của ca gốc — để đối chiếu sau suy diễn"):
                if input_changed:
                    st.warning("JSON hiện tại đã khác ca gốc: kỳ vọng bên dưới không tự cập nhật; hãy xác định kỳ vọng cho biến thể mới.")
                st.json(selected_case["expected_engine"])
                st.caption("Kỳ vọng mô tả hành vi hiện tại, không phải nhãn chuẩn lâm sàng; không truyền vào engine.")

        result = st.session_state["result"]
        with right:
            st.subheader("Kết quả hệ thống")
            if st.session_state["run_error"]:
                st.error(st.session_state["run_error"])
            elif result is None:
                st.info("Bấm Phân loại và giải thích để xem kết quả cho JSON hiện tại.")
            else:
                a, b = st.columns(2)
                a.metric("Trạng thái", result["status"])
                b.metric("Ưu tiên", result["priority"])
                explanation = f"**{result['status']}** — {STATUS_HELP[result['status']]}"
                if result["status"] == "NEEDS_REVIEW":
                    st.error(explanation)
                elif result["status"] in {"INSUFFICIENT_DATA", "UNRESOLVED"}:
                    st.warning(explanation)
                else:
                    st.info(explanation)
                st.subheader(result["predicted_label"] or "Chưa kết luận bệnh")
                st.write(result["decision_trace"])
                st.write("**Rule được chọn:**", result["matched_rule_id"] or "Không có")
                st.write("**Rule cùng khớp:**", ", ".join(result["matched_rule_ids"]) or "Không có")
                st.write("**Rule chặn / xung đột:**", ", ".join(result["blocking_rule_ids"]) or "Không có")
                if result["missing_fields"]:
                    st.write("**Trường cần bổ sung:**")
                    st.write(result["missing_fields"])
                st.caption(f"YAML {result['rules_version']} · SHA-256 {result['rules_sha256']}")
                with st.expander("Kết quả và trace đầy đủ"):
                    st.json(result)
                st.download_button("Tải kết quả JSON", json.dumps(result, ensure_ascii=False, indent=2),
                                   file_name="rule_result.json", mime="application/json")
            if selected_case["workflow_gap"]:
                issue_id = selected_case["workflow_gap"]
                st.warning(
                    f"**Ca gốc · {issue_id}** — {ISSUE_HELP[issue_id]} "
                    "Đây là chú thích của ca gốc; JSON đã sửa có thể có vấn đề khác."
                )

    with layers_tab:
        st.subheader("Pha 1 · Đánh giá điều kiện và phụ thuộc")
        st.markdown(
            "**Mục tiêu của pha này là biết từng rule TRUE, FALSE hay UNKNOWN; chưa chọn nhãn bệnh.**\n\n"
            "Ví dụ `R-SOC` (sốc phản vệ) cần kết quả `R02-PV` hoặc `R03-PV` (phản vệ):\n\n"
            "1. Khi gặp một rule được tham chiếu nhưng chưa tính, engine tính rule đó trước.\n"
            "2. Kết quả được lưu vào **cache — bảng nhớ tạm**, chẳng hạn `R02-PV = TRUE`.\n"
            "3. `R-SOC` lấy kết quả đã lưu, kết hợp điều kiện huyết áp để đánh giá sốc. "
            "Rule khác cần `R02-PV` cũng dùng lại kết quả, không tính lại trong lần chạy đó.\n"
            "4. Engine tiếp tục tính các rule còn lại: phản vệ, cấp, CIndU, CSU và theo dõi; "
            "không dừng ngay khi một rule khớp."
        )
        st.info(
            "Mỗi lần phân loại có một bảng nhớ mới. Kết quả bệnh án A không dùng cho bệnh án B; "
            "sửa JSON rồi chạy lại cũng tính lại từ dữ liệu mới. UNKNOWN được lưu nguyên là UNKNOWN, không đổi thành FALSE."
        )
        st.subheader("Pha 2 · Chọn kết luận theo ưu tiên")
        st.write(
            "Sau khi đã có kết quả toàn bộ rule, engine mới chọn kết luận. Ưu tiên số nhỏ hơn được xét trước: "
            "nếu cả sốc và phản vệ đều TRUE, chọn sốc làm nhãn chính. UNKNOWN có thể đổi kết luận ở ưu tiên cao "
            "sẽ chặn việc chọn bệnh ở tầng thấp; các nhãn khác nhau cùng ưu tiên cần rà soát. "
            "Thứ tự tính phụ thuộc ở pha 1 khác thứ tự chọn nhãn ở pha 2."
        )
        st.caption("TRUE = đủ bằng chứng đúng · FALSE = đủ bằng chứng sai · UNKNOWN = chưa đánh giá được. Không coi UNKNOWN là FALSE.")
        for title, identifiers in LAYERS:
            with st.expander(title, expanded=True):
                for identifier in identifiers:
                    rule = rules[identifier]
                    value = result["rule_results"][identifier] if result else None
                    state = "Chưa chạy" if result is None else "UNKNOWN" if value is None else "TRUE" if value else "FALSE"
                    marker = ""
                    if result and identifier == result["matched_rule_id"]:
                        marker = " · KẾT LUẬN CHÍNH"
                    elif result and identifier in result["blocking_rule_ids"]:
                        marker = " · CHẶN / XUNG ĐỘT"
                    elif result and identifier in result["matched_rule_ids"]:
                        marker = " · KHỚP"
                    st.markdown(f"**{identifier} — {rule['name']}** · `{state}`{marker}")
                    st.caption("Điều kiện cơ sở" if rule.get("is_base_condition") else
                               f"Ưu tiên {rule['priority']} · {rule['target_label']}")
                    with st.expander(f"Điều kiện và bằng chứng · {identifier}"):
                        st.json(rule["conditions"])
                        if result:
                            events = [event for event in result["trace"] if event["rule_id"] == identifier]
                            st.dataframe([dict(event, result="UNKNOWN" if event["result"] is None else
                                              "TRUE" if event["result"] else "FALSE") for event in events],
                                         hide_index=True, width="stretch")
        st.caption("INVALID_DATA và OUT_OF_SCOPE cần validator/cohort trong pipeline; demo không tự suy ra hai trạng thái này.")

    with catalog_tab:
        st.subheader("Mỗi output và các rule liên quan tới output đó")
        st.caption("Hai nhãn theo dõi có target_status INSUFFICIENT_DATA; predicted_label của kết quả không phải nhãn bệnh.")
        for label in labels:
            associated = [rule for rule in targets if rule["target_label"] == label]
            with st.expander(label, expanded=label == selected_label):
                for rule in associated:
                    st.write(f"**{rule['rule_id']}** · ưu tiên {rule['priority']} · {rule.get('target_status', 'CLASSIFIED')}")
                    st.write(rule.get("decision_trace", ""))
                    st.json(rule["conditions"])
                if label == "Mày đay cấp thông thường":
                    st.warning("F-01: chưa có ca JSON thỏa rule cấp thường; danh mục này mô tả rule đang có, không xác nhận nhánh đã hoạt động.")

    with diagrams_tab:
        st.subheader("Workflow đề xuất và phạm vi đang chạy")
        st.write("Demo chạy: JSON CANONICAL → engine → giải thích. RAW validation, preprocessing, re-check, anonymization và đánh giá batch chưa được nối.")
        diagram_name = st.selectbox("Diagram Archify", ["Luồng phân tầng", "Cây CSU", "Quy trình chuẩn"])
        diagram_files = {
            "Luồng phân tầng": "rule-based-phan-tang.svg",
            "Cây CSU": "rule-based-cay-csu.svg",
            "Quy trình chuẩn": "rule-based-quy-trinh.svg",
        }
        path = ROOT / "docs/diagrams" / diagram_files[diagram_name]
        if path.exists():
            st.image(path.read_text(encoding="utf-8"), width="stretch")
        else:
            st.warning("Không tìm thấy SVG. Xem docs/02_workflow.md để đối chiếu workflow.")
        st.caption("Bản SVG Archify hiện có mô tả workflow; tab Sáu tầng hiển thị kết quả YAML thực tế của ca đang chạy.")


if __name__ == "__main__":
    render()
