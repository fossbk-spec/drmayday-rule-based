"""Project context and existing diagrams."""

import streamlit as st

from main import ROOT, ISSUE_HELP


def render():
    st.title("Giới thiệu")
    st.write("Nền tảng phân loại bệnh án có phiên bản, gồm ba phần: quản lý tri thức bác sĩ, pipeline xử lý bệnh án và website trình bày kết quả. Rule-based là bộ phân loại đầu tiên; các model AI sau này dùng chung dữ liệu chuẩn hóa (CANONICAL) để so sánh trên cùng nhãn tham chiếu độc lập.")
    st.write("Hiện trạng: đã có engine rule-based, gói tri thức bất biến, pipeline CANONICAL và demo Streamlit dùng dữ liệu giả. Khối dữ liệu thật, đăng nhập và đánh giá lâm sàng chưa triển khai.")
    st.subheader("Workflow & diagram")
    diagrams = {
        "Luồng phân tầng": "rule-based-phan-tang.svg",
        "Cây CSU": "rule-based-cay-csu.svg",
        "Quy trình chuẩn": "rule-based-quy-trinh.svg",
    }
    for title, filename in diagrams.items():
        with st.expander(title):
            path = ROOT / "docs/diagrams" / filename
            if path.exists():
                st.image(path.read_text(encoding="utf-8"), width="stretch")
            else:
                st.warning("Không tìm thấy SVG.")
    with st.expander("Cảnh báo F-01..F-13"):
        for code, message in ISSUE_HELP.items():
            st.write(f"**{code}** · {message}")
    st.markdown("[Repo](https://github.com/fossbk-spec/drmayday-rule-based) · [Tài liệu](https://github.com/fossbk-spec/drmayday-rule-based/tree/main/docs) · [Changelog](https://github.com/fossbk-spec/drmayday-rule-based/blob/main/docs/05_changelog.md)")
