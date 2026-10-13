"""Batch classification of repository synthetic files."""

import json
from collections import Counter

import streamlit as st
import yaml

from main import ROOT
from src.evaluate import evaluate
from src.ingest import load_records
from src.knowledge import load_package
from src.pipeline import run_batch


def render():
    from main import get_classifier
    classifier = get_classifier()
    st.title("Batch dữ liệu giả")
    files = sorted(path for path in (ROOT / "data/synthetic").glob("*.json") if path.name != "rule_logic_results.json")
    names = [path.name for path in files]
    selected = st.multiselect("Chọn file dữ liệu giả", names, default=["rule_logic_cases.json"])
    if st.button("Chạy batch", key="batch_run"):
        if not selected:
            st.warning("Chọn ít nhất một file.")
        else:
            fields = yaml.safe_load(load_package(classifier.knowledge_package_id).fields_path.read_text(encoding="utf-8"))
            records = load_records([str(ROOT / "data/synthetic" / name) for name in selected])
            manifest, results = run_batch(records, classifier, fields=fields)
            st.session_state["batch_result"] = (selected, manifest, results)
    run = st.session_state.get("batch_result")
    if not run:
        return
    used, manifest, results = run
    st.subheader("Run manifest")
    st.json(manifest)
    statuses = manifest["counts"]["classified_by_status"]
    labels = Counter(result.get("predicted_label") for result in results if result.get("predicted_label"))
    st.subheader("Phân bố status")
    st.vega_lite_chart([{"status": key, "count": value} for key, value in statuses.items()],
                       {"mark": "bar", "encoding": {"x": {"field": "status", "type": "nominal"},
                                                       "y": {"field": "count", "type": "quantitative"}}})
    st.subheader("Phân bố nhãn")
    if labels:
        st.vega_lite_chart([{"label": key, "count": value} for key, value in labels.items()],
                           {"mark": "bar", "encoding": {"x": {"field": "label", "type": "nominal"},
                                                           "y": {"field": "count", "type": "quantitative"}}})
    else:
        st.info("Không có nhãn bệnh trong batch này.")
    rows, invalid = [], []
    for result in results:
        codes = sorted({issue["code"] for issue in result.get("issues", [])})
        row = {"record_id": result.get("record_id"), "status": result.get("status", "ERROR"),
               "nhãn": result.get("predicted_label"), "mã issue": ", ".join(codes)}
        rows.append(row)
        if result.get("status") == "INVALID_DATA":
            invalid.append(row)
    st.subheader("Kết quả")
    st.dataframe(rows, hide_index=True, width="stretch")
    st.subheader("INVALID_DATA")
    if invalid:
        st.dataframe(invalid, hide_index=True, width="stretch")
    else:
        st.write("Không có record INVALID_DATA.")
    if manifest["counts"]["with_ground_truth"]:
        records = load_records([str(ROOT / "data/synthetic" / name) for name in used])
        label_map = yaml.safe_load((ROOT / "data/synthetic/label_map.yaml").read_text(encoding="utf-8"))
        assessment = evaluate(results, records, label_map)
        st.subheader("Đánh giá trên nhãn giả")
        st.write(f"Mẫu số: {assessment['denominator']}")
        st.dataframe(assessment["confusion_matrix"], width="stretch")
        metrics = [{"Lớp": label, **values} for label, values in assessment["per_class"].items()]
        st.dataframe(metrics, hide_index=True, width="stretch")
        st.caption("dữ liệu RAW cũ chưa mapping – không phải đánh giá lâm sàng")
    content = "".join(json.dumps(result, ensure_ascii=False) + "\n" for result in results)
    st.download_button("Tải results.jsonl", content, file_name="results.jsonl", mime="application/jsonl")
