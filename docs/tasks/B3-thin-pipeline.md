# B3 — Pipeline mỏng: ingest → validate → phân loại → đánh giá, có run manifest

Bước 3 của [lộ trình tối ưu](../07_phuong_an_mo_rong.md#7-lộ-trình-tối-ưu). Pipeline đích ở [02_workflow mục 0](../02_workflow.md#0-pipeline-đích-và-thay-đổi-so-với-đặc-tả-0910). Đầu vào là **JSON đã ở dạng CANONICAL** (dữ liệu giả); mapping RAW → CANONICAL và khử định danh chờ D-01/D-07, **không làm ở bước này**.

## Ràng buộc

- Không sửa `src/classify.py`, `rules/`, `knowledge/`, `data/` (trừ thêm `data/synthetic/label_map.yaml`), `tests/golden/`. Golden test pass không cần `UPDATE_GOLDEN`.
- Thư viện chuẩn + PyYAML; Python 3.9. Pipeline dùng `Classifier` (`src/classifiers`) – không gọi `ClinicalRuleEngine` trực tiếp.
- Nhãn thật (`nhan`), `expected_engine`, `workflow_gap`, `mo_ta`, tên file **không bao giờ** vào snapshot gửi classifier.
- Một record lỗi không làm hỏng batch và **không bị bỏ khỏi số đếm**.

## 1. `src/ingest.py`

`load_records(paths) -> List[Record]` với `Record(record_id, snapshot, ground_truth, metadata)`:
- Chấp nhận file là list record, hoặc object có `cases` (list), hoặc một record đơn. Record có `du_lieu` → snapshot = `du_lieu`; không có `du_lieu` → snapshot = record bỏ các khóa metadata.
- `record_id = "<tên file>:<id>"` (không có `id` → `<tên file>:#<chỉ số>`); trùng id trong cùng file → thêm hậu tố, ghi vào metadata.
- `ground_truth = nhan` nếu có, ngược lại `None`. Metadata giữ `id`, `mo_ta`, `expected_engine`, `workflow_gap`, tên file – **tách khỏi snapshot**.
- Snapshot không phải object, JSON hỏng → record lỗi (`error`), vẫn được đếm.
- Ghi `sha256` (bytes đã chuẩn hóa LF, dùng `src.knowledge.normalized_bytes`) của từng file input.

## 2. `src/validate.py`

`validate_canonical(snapshot, fields) -> List[Issue]`, `Issue = {path, code, severity, message}`; `fields` là nội dung `fields.yaml` của **gói đang dùng** (nếu chạy từ đường dẫn rules thì `rules/fields.yaml`).
- Chỉ xét path có trong `fields.yaml` (đọc path lồng theo dấu chấm); trường thiếu/không có trong từ điển bỏ qua (thiếu dữ kiện là việc của engine → `INSUFFICIENT_DATA`).
- Giá trị theo `missing_conventions` (`null`, `"unknown"`, `-1`, `"N/A"`) hợp lệ.
- `code`: `INVALID_TYPE` (sai `type`; `number` = số hữu hạn không phải bool), `NON_FINITE`, `INVALID_VALUE` (không thuộc `values` khi `values` khác rỗng; với list xét từng phần tử).
- `severity`: `error`; nhưng nếu trường có `todo` khác rỗng → `warning` (hợp đồng v0 chưa chốt, không được chặn record vì nó).
- Không tự sửa/ép kiểu giá trị.

## 3. `src/pipeline.py`

`run_batch(records, classifier, *, fields, run_id=None) -> (manifest, results)`:
- Có issue `error` → **không** gọi classifier; envelope `status = INVALID_DATA` (dùng `make_envelope`, `details = {}`), `issues` = danh sách issue. Chỉ có warning → gọi classifier, gắn warning vào `issues` của envelope.
- Record lỗi ingest hoặc classifier ném ngoại lệ → kết quả `{"record_id", "error": "<tên ngoại lệ>"}`, không có giá trị bệnh án.
- `run_id` mặc định `run-<uuid4 hex 12>`.
- **Run manifest**: `run_id`, `created_at` (UTC ISO), `classifier_id/version`, `knowledge_package_id/hash`, `fields_version`, `inputs` (đường dẫn + sha256), `counts` (`received`, `classified_by_status`, `invalid_data`, `errors`, `with_ground_truth`), `result_schema_version`. Bất biến: `received = tổng các status + errors`.

CLI `python -m src.pipeline --input F [--input F ...] (--env demo | --package kb-X | --rules PATH) --out DIR [--label-map PATH]` ghi:
- `DIR/run_manifest.json`, `DIR/results.jsonl` (một envelope/dòng, `ensure_ascii=False`), `DIR/evaluation.json` + phần đánh giá trong `DIR/summary.md` khi có ground truth.
- `summary.md` tiếng Việt: version, đếm theo status, danh sách record lỗi/invalid (chỉ id + mã lỗi).
- Mặc định `--env demo`.

## 4. `src/evaluate.py` + `data/synthetic/label_map.yaml`

`label_map.yaml` ánh xạ nhãn thật của dữ liệu giả → nhãn engine, ví dụ `Cấp thường: Mày đay cấp thông thường`, `Cấp nặng: Mày đay cấp có dấu hiệu nặng`; các nhãn trùng tên giữ nguyên. Đây là cấu hình **đánh giá**, không dùng trong preprocessing. Nhãn không có trong map → báo lỗi rõ.

`evaluate(results, records, label_map) -> dict` trên các record có ground truth:
- Cột dự đoán = `predicted_label` khi `CLASSIFIED`, ngược lại `"(" + status + ")"`, lỗi → `"(ERROR)"`.
- Confusion matrix đầy đủ (hàng = nhãn thật đã map, cột = dự đoán), precision/recall/F1 từng lớp, macro trung bình, accuracy trên **toàn bộ** record có nhãn, `coverage` = tỉ lệ CLASSIFIED; ghi rõ mẫu số. Không loại record chưa kết luận khỏi mẫu số.

## 5. Test — `tests/test_pipeline.py`

1. Ingest 138 ca + 53 ca giả cũ: đủ số record, `record_id` duy nhất, snapshot không chứa `nhan/expected_engine/workflow_gap/mo_ta`.
2. Pipeline trên 138 ca với `--env demo`: ca không có issue `error` cho envelope **bằng** `RuleBasedClassifier.classify` trực tiếp; ca có error là `INVALID_DATA` với issues; bất biến đếm đúng; manifest có id/hash `kb-1.2.1`.
3. `validate_canonical`: bool cho trường `number` → `INVALID_TYPE`; giá trị ngoài `values` → `INVALID_VALUE`; trường có `todo` → `warning`; sentinel hợp lệ.
4. Classifier giả ném ngoại lệ ở một record → batch vẫn xong, record đó là `error`, được đếm.
5. `evaluate` trên ví dụ nhỏ tự dựng: confusion matrix, recall và mẫu số đúng; record `INSUFFICIENT_DATA` nằm trong mẫu số.
6. CLI chạy trong thư mục tạm, ghi đủ file.

## Hoàn tất khi

- Toàn bộ test pass (40 cũ + mới), golden không đổi; `tools/check_packages.py` và `tools/build_fields.py --check` thoát 0.
- Chạy thật CLI trên `data/synthetic/*.json` trừ `rule_logic_results.json` (ra thư mục tạm, không commit) và báo trong báo cáo cuối: counts theo status, số `INVALID_DATA` và 3 mã issue phổ biến nhất, accuracy/coverage trên 53 ca có nhãn (ghi rõ: dữ liệu RAW cũ chưa mapping nên không phải đánh giá lâm sàng).
- Đoạn ngắn trong README mục 6 cách chạy pipeline.
- Báo cáo cuối: file tạo/sửa, test, số liệu trên, `ASSUMPTION:`.
