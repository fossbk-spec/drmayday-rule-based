"""Streamlit demo of the existing engine, not the unimplemented RAW pipeline."""

import json
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from src.classifiers import RuleBasedClassifier


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


@st.cache_resource
def get_classifier():
    return RuleBasedClassifier.from_active("demo")


def render():
    st.set_page_config(page_title="Rule-based · Mề đay", page_icon="🔎", layout="wide")
    classifier = get_classifier()
    from app.components import render_header
    from app.pages import about, batch, demo, rules
    pages = [
        st.Page(demo.render, title="Demo ca bệnh", url_path="demo"),
        st.Page(rules.render, title="Luật & phiên bản", url_path="rules"),
        st.Page(batch.render, title="Batch dữ liệu giả", url_path="batch"),
        st.Page(about.render, title="Giới thiệu", url_path="about"),
    ]
    page = st.navigation(pages)
    render_header(classifier)
    page.run()


if __name__ == "__main__":
    render()