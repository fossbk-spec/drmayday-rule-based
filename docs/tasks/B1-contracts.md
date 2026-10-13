# B1 — Ba hợp đồng: result envelope v1, giao diện Classifier, từ điển CANONICAL v0

Bước 1 của [lộ trình tối ưu](../07_phuong_an_mo_rong.md#7-lộ-trình-tối-ưu). Mục tiêu: rule-based và AI sau này dùng chung **đầu vào** (CANONICAL) và **đầu ra** (result envelope); gói tri thức có định danh. Không đổi hành vi phân loại.

## Ràng buộc

- **Không sửa** `rules/classification_rules.yaml`, logic chọn kết luận trong `src/classify.py`, `data/`, `tests/golden/`. `ClinicalRuleEngine.classify_patient` giữ nguyên output (golden test phải tiếp tục pass không cần `UPDATE_GOLDEN`).
- Chỉ dùng thư viện chuẩn + PyYAML. Tương thích Python 3.9 (không dùng `X | Y`, `match`).
- Không đưa ngưỡng/enum y khoa mới: chỉ ghi lại những gì YAML và từ điển dữ liệu hiện có; chỗ chưa rõ ghi `todo: "..."`.

## 1. Version engine — `src/version.py` (mới)

```python
ENGINE_VERSION = "1.1.0"   # 1.0.0 = trước 13/10/2026; 1.1.0 = sửa TECH-01/03 + sentinel trong list
RESULT_SCHEMA_VERSION = "1.0.0"
```

## 2. Giao diện Classifier — `src/classifiers/` (mới)

`src/classifiers/__init__.py`, `base.py`, `rule_based.py`.

`base.py`: lớp trừu tượng `Classifier` với thuộc tính `classifier_id: str`, `classifier_version: str` và phương thức
`classify(self, snapshot: Dict[str, Any], *, record_id: Optional[str] = None, run_id: Optional[str] = None) -> Dict[str, Any]` trả **result envelope v1**. Thêm hàm `make_envelope(...)` dùng chung để mọi classifier tạo đúng khung.

`rule_based.py`: `RuleBasedClassifier(rules_path)` bọc `ClinicalRuleEngine`; `classifier_id = "rule-based"`, `classifier_version = ENGINE_VERSION`. Không sửa `snapshot` (deepcopy nếu cần).

### Result envelope v1

```json
{
  "result_schema_version": "1.0.0",
  "classifier_id": "rule-based",
  "classifier_version": "1.1.0",
  "knowledge_package_id": "kb-1.2.1",
  "knowledge_package_hash": "sha256:<rules_sha256>",
  "run_id": null,
  "record_id": null,
  "status": "CLASSIFIED",
  "predicted_label": "Phản vệ",
  "missing_fields": [],
  "explanation": {"summary": "<decision_trace>"},
  "issues": [],
  "details": {
    "matched_rule_id": "R02-PV",
    "matched_rule_ids": ["R02-PV"],
    "blocking_rule_ids": [],
    "priority": 2,
    "rule_results": {"R02-PV": true},
    "trace": []
  }
}
```

- Trường cấp trên cùng là **chung cho mọi classifier** (AI sau này cũng trả đúng bộ này). Thông tin riêng rule-based nằm trong `details`.
- `knowledge_package_id = "kb-" + rules_version` từ YAML (gói thật có ở Bước 2). Classifier không dùng gói luật đặt `null`.
- `issues`: list rỗng ở v1 (validator Bước 3 sẽ điền).
- `patient_token_id` của engine **không** đưa vào envelope (định danh không thuộc kết quả phân loại).
- `status` thuộc tập `ClinicalRuleEngine.STATUSES`.

## 3. Từ điển CANONICAL v0 — `rules/fields.yaml` (mới)

Liệt kê **mọi field path mà YAML luật đọc** (48 path qua khóa `field`, cộng `tuoi` và `huyet_ap_tam_thu_nen` dùng trong `<_formula`). Mỗi mục:

```yaml
version: "0.1.0"
missing_conventions: {missing: null, unknown: ["unknown", -1], not_applicable: "N/A"}
fields:
  huyet_ap_tam_thu_thap_nhat:
    type: number            # number | string | boolean | list | object
    unit: mmHg              # nếu có
    values: []              # enum nếu từ điển/YAML liệt kê; rỗng nếu không
    group: tuan_hoan        # nhóm hiển thị UI: hanh_chinh, da, ho_hap, tuan_hoan, tieu_hoa, than_kinh, xet_nghiem, thoi_gian, khac
    form: phan_ve           # cap | man | phan_ve | chung
    source: "docs/01_data_dictionary/phan_ve.md"   # hoặc "rules only" nếu từ điển không có
    used_by: [R-SOC]        # rule_id đọc trường này (tự sinh)
    todo: ""                # mâu thuẫn kiểu/enum giữa từ điển và YAML, hoặc thiếu thông tin
```

- Path lồng (`a.b`) giữ nguyên dạng chấm như YAML.
- Lấy `type/unit/values` từ `docs/01_data_dictionary/{cap,man,phan_ve}.md`; nếu từ điển và YAML mâu thuẫn (ví dụ YAML so sánh chuỗi nhưng từ điển ghi object), **không tự quyết** — ghi vào `todo`.
- Viết `tools/build_fields.py` để sinh/kiểm tra `used_by` và phát hiện path thiếu; chạy được lại (`python tools/build_fields.py --check` trả mã lỗi ≠ 0 nếu YAML luật đọc path không có trong `fields.yaml`).

## 4. Test — `tests/test_contracts.py` (mới)

1. Envelope của `RuleBasedClassifier` cho cả 138 ca trong `data/synthetic/rule_logic_cases.json`: đúng bộ khóa cấp trên và trong `details`; `status/predicted_label/missing_fields/explanation.summary` và các trường `details` **bằng đúng** output `ClinicalRuleEngine.classify_patient` tương ứng; `knowledge_package_hash` bắt đầu `sha256:`; `record_id/run_id` được truyền qua; input không bị sửa.
2. Một classifier giả (`DummyClassifier` trong test) dùng `make_envelope` trả envelope hợp lệ với `knowledge_package_id = None` và không có `details` riêng → chứng minh hợp đồng không phụ thuộc rule-based.
3. `fields.yaml`: mọi path rule đọc đều có mục; `type` thuộc tập cho phép; `used_by` khớp YAML; `tools/build_fields.py --check` thoát 0.

## Hoàn tất khi

- `python -X utf8 -m unittest discover -s tests` pass toàn bộ (29 test cũ + test mới), golden không đổi.
- Không có thay đổi ngoài các file nêu trên, trừ một đoạn ngắn trong `README.md` mục 6 mô tả `RuleBasedClassifier` và `fields.yaml`.
- Báo cáo cuối: file đã tạo/sửa, kết quả test, danh sách `todo` trong `fields.yaml` (số lượng + 5 ví dụ), giả định đã đặt.
