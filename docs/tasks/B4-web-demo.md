# B4 — Web demo public: trực quan input/kết quả, luật & phiên bản, batch dữ liệu giả

Bước 4 của [lộ trình tối ưu](../07_phuong_an_mo_rong.md#7-lộ-trình-tối-ưu); yêu cầu R4/R5 ở [docs/07 mục 5](../07_phuong_an_mo_rong.md#5-website-r3-r4-r5) và [02 — sản phẩm](../implementation-guide/02-product-and-mvp.md#trực-quan-hóa-input). Chỉ **dữ liệu giả**; không có đăng nhập, không import dữ liệu thật (Bước 5). Mở rộng `main.py` hiện có, không viết lại từ đầu.

## Ràng buộc

- Không sửa `src/classify.py`, `rules/`, `knowledge/`, `data/`, `tests/golden/`. Logic phân loại/validate/pipeline gọi qua `src/classifiers`, `src/validate.py`, `src/pipeline.py`, `src/knowledge.py` – UI không tự tính lại kết quả.
- Streamlit 1.50.0 + thư viện chuẩn + PyYAML (Altair đi kèm Streamlit được dùng cho biểu đồ). Python 3.9.
- Không ghi log/lưu payload người dùng nhập; không đọc biến môi trường bí mật.
- Không hiển thị "số điều kiện khớp" như xác suất. Giá trị thiếu không vẽ thành 0.
- Giữ cảnh báo F-01..F-13 hiện có (`ISSUE_HELP`) và ba diagram SVG.

## 1. Cấu trúc

`main.py` dùng `st.navigation` với 4 trang; code tách vào `app/` (mới): `app/pages/demo.py`, `app/pages/rules.py`, `app/pages/batch.py`, `app/pages/about.py`, và `app/components.py` (hàm vẽ dùng chung). Classifier mặc định: `RuleBasedClassifier.from_active("demo")`, cache bằng `st.cache_resource`.

Mọi trang có thanh trên cùng: gói tri thức đang dùng (`kb-…` + 12 ký tự đầu hash), engine version, ghi chú "Chỉ dữ liệu giả – không nhập bệnh án thật".

## 2. Trang "Demo ca bệnh" (giữ chức năng hiện tại + trực quan)

Chọn ca giả (138 ca) → xem/sửa JSON → bấm phân loại. Đổi input xóa kết quả cũ (giữ hành vi hiện có). Kỳ vọng ca gốc vẫn hiện trong expander.

**Trực quan input** (`render_input(snapshot, fields)`):
- Thẻ theo `group` trong `fields.yaml` của gói (da, hô hấp, tuần hoàn, tiêu hóa, xét nghiệm, thời gian…): mỗi trường một dòng với nhãn trạng thái **Có giá trị / Chưa biết (`unknown`, -1) / Không áp dụng (`N/A`) / Thiếu** và giá trị; list/object hiển thị gọn.
- Huyết áp: nếu có `huyet_ap_tam_thu_thap_nhat`, hiển thị cùng hai ngưỡng của luật sốc khi tính được (`70 + 2×tuoi`, `0,7×huyet_ap_tam_thu_nen`); ngưỡng không tính được → ghi "không tính được: thiếu …", không vẽ.
- Bảng **chất lượng dữ liệu** từ `validate_canonical` (path, mã, mức độ). Có lỗi `error` → nêu rõ pipeline sẽ trả `INVALID_DATA`; demo vẫn cho xem kết quả classifier để học, ghi chú điều này.

**Trực quan kết quả** (`render_result(envelope)`), theo thứ tự:
1. Thẻ tóm tắt: status (màu theo status), nhãn hoặc "Chưa kết luận bệnh", gói + engine version, lý do chính (`explanation.summary`), **việc cần làm**: danh sách `missing_fields` cần bổ sung / rule chặn cần rà soát.
2. **Cây 6 tầng** (dùng `LAYERS` hiện có): mỗi rule một chip màu TRUE (xanh) / FALSE (xám) / UNKNOWN (vàng); đánh dấu rule được chọn, rule cùng khớp nhưng thua priority, rule chặn.
3. **Bằng chứng từng điều kiện**: expander theo rule, bảng từ `details.trace` (điều kiện, trường, toán tử, kết quả, lý do) kèm giá trị trường trong snapshot (dữ liệu giả).
4. Tải envelope JSON.

## 3. Trang "Luật & phiên bản"

- Danh sách gói trong `knowledge/` (manifest: id, version, ngày, tóm tắt, hash, engine hỗ trợ) và con trỏ `active.yaml` (demo/real).
- Luật của gói đang chọn theo 6 tầng: rule_id, nhãn đích, priority, `decision_trace`, điều kiện YAML trong expander.
- **So sánh**: chọn hai nguồn trong {các gói, bản nháp `rules/`} → chạy 138 ca giả bằng hai classifier trong-process → bảng đếm status trước/sau và danh sách ca đổi status/nhãn/rule (tái dùng hàm so sánh của `tools/impact_report.py` nếu tách được, không gọi subprocess).
- Link `docs/knowledge_release.md` và changelog.

## 4. Trang "Batch dữ liệu giả"

Chọn một hoặc nhiều file trong `data/synthetic/` (trừ `rule_logic_results.json`) → `run_batch` với classifier đang dùng → hiển thị run manifest (version, đếm), biểu đồ cột phân bố status và nhãn, bảng kết quả (record_id, status, nhãn, mã issue), danh sách `INVALID_DATA` kèm mã issue; nếu có ground truth: confusion matrix (bảng) + precision/recall/F1 từng lớp và mẫu số từ `src/evaluate.py`, kèm ghi chú "dữ liệu RAW cũ chưa mapping – không phải đánh giá lâm sàng". Tải `results.jsonl`.

## 5. Trang "Giới thiệu"

Mô tả nền tảng (đoạn đầu README), hiện trạng, ba diagram SVG, link repo/tài liệu.

## 6. Triển khai

- `.streamlit/config.toml`: `server.maxUploadSize = 1`, `browser.gatherUsageStats = false`, `client.showErrorDetails = false`.
- README: mục "Triển khai demo" – chạy local và các bước deploy Streamlit Community Cloud (repo `fossbk-spec/drmayday-rule-based`, nhánh `main`, file `main.py`). Không deploy (cần tài khoản của người dùng).

## 7. Test — `tests/test_app.py` (`streamlit.testing.v1.AppTest`)

Bỏ qua cả file (`skipUnless`) nếu không import được streamlit. Mỗi test `timeout` đủ rộng (30s).
1. Mỗi trang render không exception.
2. Demo: chọn một ca CLASSIFIED (vd `SOC-NEN-MISSING` không – chọn ca có nhãn trong 138 ca), bấm phân loại → hiển thị status và nhãn khớp `RuleBasedClassifier`; đổi JSON → kết quả bị xóa.
3. Demo: ca thiếu `huyet_ap_tam_thu_nen` → ngưỡng 0,7×nền ghi "không tính được", không có giá trị 0.
4. Luật & phiên bản: hiển thị `kb-1.2.1`; so sánh `kb-1.2.1` với `rules/` → "không có thay đổi".
5. Batch: chạy trên `rule_logic_cases.json` → đếm khớp `run_batch`.

## Hoàn tất khi

- Toàn bộ test pass (47 cũ + mới), golden không đổi; `tools/check_packages.py`, `tools/build_fields.py --check` thoát 0.
- `streamlit run main.py` khởi động được (kiểm tra bằng AppTest là đủ; **không mở trình duyệt**).
- Báo cáo cuối: file tạo/sửa, test, giới hạn đã biết, `ASSUMPTION:`.
