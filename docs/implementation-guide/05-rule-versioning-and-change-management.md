# Version và thay đổi luật

## Nguyên tắc

Luật bệnh, hợp đồng dữ liệu và code thực thi cùng quyết định output. Vì vậy dùng **gói tri thức bất biến**, kèm revision từng luật và engine build, thay vì chỉ thêm trường version YAML.

Phân biệt:

- `rule_id`: ID ổn định biểu diễn một khái niệm luật; đổi nghĩa căn bản có thể cần ID mới.
- `revision`: tăng mỗi lần đổi nội dung luật; kể cả giải thích nếu nội dung release thay đổi.
- `knowledge_package_id`/version: gói cụ thể chứa rule, schema, mapping, preprocessing, taxonomy và ca nghiệm thu.
- `engine_version`: code đánh giá/selection; bug fix engine có thể đổi output dù YAML giữ nguyên.
- `result_schema_version`: contract API/export.

## Manifest đề xuất

```yaml
knowledge_package_id: kb-1.3.0
package_version: 1.3.0
schema_version: canonical-2.0.0
mapping_version: mapping-1.1.0
preprocessing_version: preproc-1.1.0
label_taxonomy_version: labels-1.0.0
rules_file: classification_rules.yaml
supported_engine_versions: [engine-1.1.0]
created_at: "2026-10-13T00:00:00Z"
previous_package_id: kb-1.2.1
```

Ví dụ là **format đích**; các version/ID không chứng minh release đó đã tồn tại. Không thêm lifecycle mutable hoặc chữ ký tự tham chiếu vào bytes đã hash. Manifest và file nội dung được hash; approvals, trạng thái release và active pointer lưu riêng, append audit.

Mỗi rule bổ sung metadata ngoài conditions: revision, change_reason, clinical_source, author, effective scope và acceptance_case_ids. Loader/version compatibility phải được kiểm thử trước khi dùng metadata mới.

## DSL có giới hạn và linh hoạt

Giữ cây AND/OR/NOT/ref_rule; operator số, equality, contains, count systems và công thức allowlist. Từ điển field định nghĩa kiểu/đơn vị/enum và applicability. Editor chọn biến/toán tử từ danh sách hợp lệ, không nhập text tự do thành expression.

| Thay đổi | Có thể chỉ sửa config? | Kiểm tra |
| --- | --- | --- |
| Ngưỡng/giá trị trong operator đã hỗ trợ | Có nếu biến/type/đơn vị ổn định | Trước/tại/sau ngưỡng và chuyên môn |
| AND/OR/ref/priority/label | Có trong DSL | Ref/cycle, conflict, coverage và impact |
| Biến mới | Không chỉ sửa YAML | Dictionary, nguồn, schema, mapping, UI, missing |
| Công thức/operator mới | Cần code | Allowlist, type, finite/overflow, compatibility |
| Đổi ý nghĩa/đơn vị field | Cần schema/mapping version | Migration và dữ liệu cũ |

Không dùng eval hoặc sinh code runtime. Có thể thêm form chỉnh sửa dễ dùng trước, editor cây sau MVP. AI chỉ đề xuất draft, không tự duyệt/kích hoạt.

## Lifecycle

`DRAFT → VALIDATED → APPROVED → RELEASED`; release được chọn bởi active pointer theo môi trường/use case. Retired vẫn giữ để tái lập khi policy cho phép. Draft sửa sau approval phải làm mất hiệu lực approval cũ.

Gate trước approve/release:

1. Parse YAML/manifest; schema cấu hình; ID/revision hợp lệ.
2. Field/operator/operand type và công thức hợp lệ.
3. Ref tồn tại, không vòng, có luật đích hợp lệ.
4. Engine/schema/mapping compatibility được xác nhận.
5. Bộ nghiệm thu và hồi quy liên quan đạt; lỗi còn mở có phạm vi rõ.
6. Báo cáo impact được review, không chỉ đọc diff YAML.
7. Người phụ trách xác nhận tiêu chí chuyên môn và change reason.

## Version policy đề xuất

- MAJOR: thay đổi không tương thích contract/ý nghĩa nhãn/feature cần migration.
- MINOR: thêm hoặc thay đổi hành vi phân loại tương thích contract.
- PATCH: sửa lỗi/giải thích trong contract hiện có; vẫn có thể làm đổi kết quả.

SemVer không đảm bảo clinical output giống nhau. Mọi release phải chạy impact; nếu đổi code engine, pin build mới và thông báo thay đổi hành vi.

## Báo cáo so sánh active và draft

Chạy trên cùng snapshot dữ liệu, mốc đánh giá, input contract và bộ case. Nếu mapping thay đổi, báo riêng tác động từ mapping và từ luật khi có thể cô lập.

Báo cáo gồm số ca đổi status/nhãn/priority/rule/blocker/missing; breakdown theo nhóm; ca từ classified sang chưa kết luận và ngược lại; ca sốc/phản vệ thay đổi; exception và lý do; case mới được chấp thuận.

Không coi mọi ca đổi nhãn là cải thiện. Bác sĩ review ca tiêu biểu/nguy cơ; dữ liệu AI tạo theo luật chỉ là test logic.

## Activate và rollback

- Activate atomic: đổi active pointer sang release đã duyệt và tương thích engine build.
- Run mới resolve pointer một lần; lưu package/hash/engine build vào run; run đang chạy không đổi.
- Không xóa/sửa historical result. Chạy lại tạo run_id mới, liên kết run trước nếu cần.
- Rollback cả engine/schema/mapping liên quan khi release phụ thuộc chúng, không chỉ đổi YAML.
- Nếu store migration không tương thích, chuẩn bị backup/restore hoặc đường migration ngược trước release.
- Ghi actor, reason, thời điểm, từ phiên bản nào sang nào; không log input bệnh án.

## Yêu cầu chưa chốt

Khoảng tuổi, mốc sáu tuần, symptom shape, dị nguyên/thời điểm, phạm vi R-SOC, Stella, cohort, đồng mắc và fallback: xem decision log. Tạo draft/test chỉ rõ pending; không kích hoạt clinical change đến khi có xác nhận. Sửa operand bool/type là bug kỹ thuật, không cần tự đổi ngưỡng.
