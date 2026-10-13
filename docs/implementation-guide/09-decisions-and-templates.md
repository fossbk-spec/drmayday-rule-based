# Quyết định cần chốt và mẫu làm việc

## Decision log khởi tạo

Tất cả mục dưới đây đang **OPEN** trong bộ hướng dẫn, trừ khi source mới hoặc người dùng cung cấp xác nhận khác. Không coi việc có đề xuất trong tài liệu là đã được duyệt.

| ID | Cần chốt | Người phù hợp | Chặn phần nào / có thể tiếp tục |
| --- | --- | --- | --- |
| D-01 | Template import đầu tiên, nguồn, đơn vị, RAW/CANONICAL, sentinel, nhãn tách riêng | Chủ dữ liệu + bác sĩ + developer | Chặn import thật; vẫn sửa engine và adapter JSON giả |
| D-02 | Shape triệu chứng cấp, path ngứa/phù mạch, tập dấu nặng chung, ảnh | Bác sĩ + chủ dữ liệu | Chặn clinical fix cấp thường; kỹ thuật type/missing độc lập |
| D-03 | Tuổi/ngày khám, khoảng tuổi, mốc sáu tuần và nguồn thời gian | Bác sĩ + chủ dữ liệu | Chặn clinical thresholds; bỏ defaults và ghi conflict được làm trước |
| D-04 | Dị nguyên nghi ngờ/đã biết, thời điểm, ref R-SOC, sàng lọc chung/applicability | Bác sĩ | Chặn mở phạm vi phản vệ/sốc và mapping liên biểu mẫu |
| D-05 | CIndU Ice cube/Adrenergic/đa thể và đồng mắc | Bác sĩ | Chặn clinical rules/tie/coexisting policy |
| D-06 | CSU/cohort/Stella/fallback, OUT_OF_SCOPE | Bác sĩ + chủ nghiên cứu | Chặn các nhánh cohort/phân type chưa duyệt |
| D-07 | Ai truy cập/export, mục đích, retention/xóa, linked visits và token | Chủ sản phẩm + chủ dữ liệu | Chặn dữ liệu thật; demo giả tiếp tục |
| D-08 | Nguồn ground truth, adjudication, nhãn/taxonomy và protocol | Bác sĩ + người đánh giá | Chặn claim accuracy/AI evaluation, không chặn test logic |
| D-09 | Stack web/API, auth, DB, hosting, môi trường và deployment quyền | Chủ sản phẩm + developer/ops | Chặn triển khai phần phụ thuộc; core/API contract tiếp tục |
| D-10 | Người soạn/duyệt/release, có gộp vai trò không, scope active package | Chủ sản phẩm + bác sĩ | Chặn production activate; registry local có thể xây |
| D-11 | Model AI, nơi inference, dữ liệu được phép gửi, scope và chi phí | Chủ dữ liệu + bác sĩ + developer | Sau MVP; không gửi dữ liệu thật ra dịch vụ ngoài |

Liên hệ gate cũ: B-01 ↔ D-04; B-02 ↔ D-01/D-03; B-03 ↔ D-03; B-04 ↔ D-02; B-05 ↔ D-06; B-06 ↔ D-05; B-07 ↔ D-07. F-01..F-13 ở báo cáo repo là finding IDs, không phải quyết định đã đóng.

## Mẫu ghi một quyết định

```markdown
# D-XX — Tên quyết định

- Trạng thái: OPEN / PROPOSED / APPROVED / SUPERSEDED
- Owner và người xác nhận:
- Ngày:
- Requirement/finding liên quan:
- Nguồn/bằng chứng:
- Các lựa chọn và tác động:
- Quyết định đã xác nhận:
- Scope: field/path, type, enum, đơn vị, missing, nguồn/mapping, applicability
- Version sẽ thay đổi:
- Acceptance cases trước/tại/sau ngưỡng và dữ kiện thiếu:
- Người/ngày duyệt:
- Phụ thuộc/migration/rollback:
```

Không chỉ đánh dấu done; ghi quyết định có thể triển khai được và nguồn xác nhận.

## Mẫu yêu cầu mới / issue

```markdown
# REQ-XX — Vấn đề hoặc hành vi cần bổ sung

- Người đề xuất / owner:
- Loại: clinical rule / data mapping / software / UI / security / AI
- Lý do và người dùng bị ảnh hưởng:
- Hành vi hiện tại (version):
- Hành vi mong muốn:
- Ví dụ dữ liệu giả hoặc fixture ID:
- Scope và ngoài scope:
- Acceptance criteria:
- Quyết định còn mở:
- Test cần thêm:
- Priority và release dự kiến:
```

Không paste PII vào issue public hoặc prompt agent. Thay bệnh án thật bằng ca giả bảo toàn tình huống khi được phép.

## Mẫu task cho Claude

```text
Thực hiện M1-03 trong repo đã mở. Đọc CLAUDE.md và guide trước.
Xác minh lỗi <_formula ở HEAD hiện tại, thêm hồi quy cho bool/string/list/object/null/non-finite
và operand/ngưỡng thiếu. Sửa kiểm tra kiểu/số hữu hạn để không crash và không coi bool là số đo.
Giữ ngưỡng/điều kiện/label y khoa hiện tại. Chạy test liên quan, cập nhật changelog và báo evidence.
Không deploy hoặc thay luật production trong task này.
```

Khi chuyển đợt, thay ID/scope/acceptance rõ ràng. Bàn giao task tiếp theo cần actual HEAD, phần đã làm và decisions còn mở.

## Mẫu rule change request

```markdown
# RC-XX — Thay đổi luật

- Package active / draft:
- Rule ID / revision cũ → mới:
- Điều kiện hoặc giải thích trước/sau:
- Lý do và nguồn chuyên môn:
- Schema/mapping/đơn vị bị ảnh hưởng:
- Ca nghiệm thu được bác sĩ xác nhận:
- Impact report: đổi status/nhãn/rule/blocker/error và ca nguy cơ:
- Người soạn / người duyệt / phạm vi hiệu lực:
- Compatibility và rollout/rollback:
```

## Mẫu ADR kỹ thuật

```markdown
# ADR-XX — Quyết định kiến trúc

- Trạng thái / ngày / owner:
- Bối cảnh và ràng buộc hiện có:
- Lựa chọn đã cân nhắc:
- Quyết định và lý do:
- Tác động đến MVP, vận hành, bảo mật và chi phí:
- Migration/rollback:
- Khi nào cần xem lại:
```

## Mẫu báo cáo một lượt chạy / release

```markdown
# Báo cáo RUN/RELEASE-XX

- Commit/build, runtime/dependency:
- Package ID/hash, engine/schema/mapping/preprocessing/taxonomy versions:
- Fixture/cohort/snapshot được phép, input revision và mốc đánh giá:
- Lệnh/check thực chạy:
- Test pass/fail/skip/expectedFailure:
- Record counts: nhận/đọc được/invalid/classified/insufficient/review/unresolved/out-of-scope/error:
- Impact so với bản trước và case IDs:
- Evaluation: ground truth/protocol/mẫu số nếu có; nếu không, ghi test logic:
- Clinical/security approvals cần thiết:
- Lỗi/giới hạn còn mở và feature disabled:
- Migration/rollback/backup evidence:
- Deployment URL/version thực xác nhận, hoặc chưa deploy:
- Owner hỗ trợ và bước tiếp theo:
```

Dùng counts không trùng nhau cho status cuối mỗi record; error execution là category riêng khi không có record result nghiệp vụ. Count import-level failures riêng khi chưa đọc được record. Ghi definition để tổng đối chiếu đúng.

## Checklist bàn giao giữa các agent/người phát triển

- HEAD/nhánh và working tree, thay đổi người dùng cần giữ.
- Task đã xong/chưa xong, file và test liên quan.
- Lệnh thực chạy, môi trường, kết quả và lỗi còn mở.
- Version đang active/draft, approvals và scope.
- Decision IDs đang chặn task nào.
- Không đưa token secret hoặc bệnh án thật vào handoff.
- Bước tiếp theo cụ thể, quyền đã có và hành động chưa được cấp quyền.

## Câu hỏi kiểm tra khả năng dùng tài liệu

1. Claude bắt đầu ở đâu và baseline nào đã được xác minh?
2. Sửa gì ngay mà không tự quyết chuyên môn?
3. Vì sao demo public không đồng nghĩa dữ liệu thật public?
4. Gói luật khác version engine thế nào, batch được pin ra sao?
5. UNKNOWN, INVALID_DATA và OUT_OF_SCOPE thuộc trách nhiệm nào?
6. Tiêu chí nào cho phép mở MVP với dữ liệu thật?
7. Khi bác sĩ đổi ngưỡng, ai duyệt và so sánh tác động thế nào?
8. AI sau MVP nhận dữ liệu/ground truth và được so sánh ra sao?
9. Sau xóa snapshot, còn cam kết rerun được không?
10. Quyết định chưa chốt nào thực sự chặn bước kế tiếp?

Reader review phải trả lời được từ gói file này, không cần lịch sử chat. Nếu thiếu, sửa tài liệu trước khi bàn giao.
