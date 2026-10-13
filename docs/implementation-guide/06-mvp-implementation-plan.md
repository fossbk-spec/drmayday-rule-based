# Kế hoạch thực hiện MVP

## Cách tổ chức

Bốn đợt có bản chạy được và tiêu chí nghiệm thu. Không gán ngày cam kết khi chưa biết nguồn lực; giả định có developer và bác sĩ xác nhận. Có thể triển khai phần độc lập trong khi chờ quyết định, nhưng không mở chức năng dữ liệu thật trước security/clinical gates tương ứng.

## Đợt 1: lõi và hợp đồng dữ liệu

| Task | Việc thực hiện | Phụ thuộc / hoàn tất |
| --- | --- | --- |
| M1-01 | Kiểm tra HEAD/instructions/working tree, chạy baseline, lập bảng lỗi | So sánh với baseline, không bỏ qua thay đổi người dùng |
| M1-02 | Đưa test vào Git, CI tối thiểu, giữ fixture giả | Test discovery từ checkout sạch; CI có lệnh thật |
| M1-03 | Sửa formula operand type/bool/finite/overflow | TECH-01; list/object/string không crash, bool không làm số đo |
| M1-04 | Sửa field attribution và nguyên nhân UNKNOWN | TECH-03/F-13; báo đúng field thực sự chặn, không lẫn nhánh đã đủ |
| M1-05 | Sửa preprocess defaults, age overwrite và nguồn ngày | TECH-02; giữ tuổi hợp lệ, missing không thành số giả |
| M1-06 | Sửa anonymizer/export ID và tên trắng/ID thiếu | SEC-01; không mã gốc trong export, không merge bệnh nhân thiếu ID |
| M1-07 | Chốt CANONICAL symptom shape và tập dấu nặng | D-02/B-04; sửa nhánh nặng/thường đồng bộ sau quyết định |
| M1-08 | Chốt dictionary/contract RAW-CANONICAL và ca nghiệm thu | D-01..D-06 theo phạm vi; không lấy nhãn làm input |
| M1-09 | Xác minh engine chạy độc lập khỏi UI; chỉ tách code nếu còn phụ thuộc; thêm contract tests/changelog | Giữ API hiện tại hoặc adapter tương thích rõ ràng |

### Việc có thể bắt đầu ngay

M1-01..M1-06 là chủ yếu kỹ thuật. Với M1-05, chốt chính sách conflict nếu tuổi sẵn có khác ngày sinh; trong lúc chưa chốt không overwrite âm thầm. M1-07/M1-08 có quyết định chuyên môn; giữ pending và tiếp tục phần không phụ thuộc.

### Nghiệm thu

- Công thức số xử lý malformed operand có cấu trúc; không biến bool thành huyết áp.
- Tuổi thiếu không thành 25, HATT thiếu không thành 120, không dùng clock thay ngày khám.
- Input không bị sửa; cache không rò giữa bệnh án.
- Missing_fields và blockers đúng nguyên nhân; test AND/OR/NOT/count/ref đầy đủ.
- Branch cấp thường có ca hợp lệ được bác sĩ duyệt hoặc được giữ rõ blocked, không tuyên bố đã hoàn tất.
- Test tracked, CI từ checkout sạch. Cập nhật counts thực chạy, không sao chép số 43 cũ.

## Đợt 2: pipeline, batch và registry

| Task | Việc thực hiện | Hoàn tất |
| --- | --- | --- |
| M2-00 | ADR stack/API/auth/storage/hosting trước phần phụ thuộc | D-09; có thể dùng adapter local cho phần độc lập, chưa deploy khi thiếu quyền |
| M2-01 | Chọn template import đầu tiên + ví dụ hợp lệ/sai | D-01 được ghi; mapping có nguồn |
| M2-02 | Ingestion/RAW validation/tách label và identity | Row/path errors; nhãn không vào feature |
| M2-03 | Mapping/preprocess/CANONICAL validation | Version/provenance, missing và conflict đúng |
| M2-04 | Identity/privacy policy + re-check bản dùng | Không PII không cần cho classifier; export allowlist |
| M2-05 | Batch/run lifecycle, record result, retry/idempotency | Một dòng lỗi không hủy/mất batch; counters đối chiếu được |
| M2-06 | Manifest/package/rule revision và compatibility | Gói immutable; validate trước load |
| M2-07 | Draft/approve/activate/compare/rollback | Chỉ approved release được active; approvals invalidated khi draft sửa |
| M2-08 | Pin package/schema/mapping/preprocess/build trước RAW validation; lưu snapshot và version vào import/run | Update giữa batch không đổi chuẩn hóa/inference; reprocess version mới tạo lượt mới |
| M2-09 | Audit/result storage và API contract | Auth boundary, error envelope, run ownership |

Nghiệm thu: import → validate → preprocess → classify → export chạy từ đầu đến cuối trên dữ liệu giả. Run cũ và run mới phân biệt; rerun version cũ cho cùng kết quả nghiệp vụ, trừ run ID/timing. Có thể rollback package/build tương thích.

## Đợt 3: website MVP

| Task | Việc thực hiện | Hoàn tất |
| --- | --- | --- |
| M3-01 | Thực hiện deployment model theo ADR M2-00; xác nhận auth/môi trường trước mở web | D-09; môi trường staging/production rõ |
| M3-02 | Demo public với case selector/editor | Chỉ ca giả mặc định; sửa input làm result stale |
| M3-03 | Auth và quyền server-side cho import/results/export/admin | Negative tests chống truy cập batch khác |
| M3-04 | Import preview/mapping/errors và rerun record revision | Không sửa history, có source key |
| M3-05 | Input: timeline, BP/test/symptom groups, missing/conflict | Nguồn/đơn vị/version rõ; thiếu không vẽ 0 |
| M3-06 | Result: status/label/tree/evidence/blockers/actions | Trace kỹ thuật và giá trị lâm sàng bảo vệ riêng |
| M3-07 | Batch dashboard/filter/pagination/export | Giữ đủ số ca; kiểm tra quyền mỗi query/export |
| M3-08 | Admin review/compare/approve/activate/rollback | MVP YAML/form đơn giản, không cần drag-drop |
| M3-09 | Upload limits, safe messages, monitoring và retention | D-07/D-09; thử xóa/end-to-end access; D-08 chỉ chặn đánh giá cần ground truth |

Nghiệm thu: người dùng thử tự hoàn thành demo và import → sửa lỗi → chạy → hiểu giải thích → export. Không yêu cầu terminal. Khách không mở được dữ liệu thật; log public không chứa payload. Dữ liệu thật chỉ mở khi các gate ở file 07 đạt.

## Đợt 4: pilot và release

- M4-01: pilot nhóm nhỏ với dữ liệu được phép; bác sĩ review có cấu trúc.
- M4-02: phân loại incident: software/data/missing/clinical-change/UX.
- M4-03: sửa lỗi nghiêm trọng, thêm hồi quy, ghi hạn chế chưa đóng.
- M4-04: diễn tập rollback luật/build và backup/restore nếu lưu dữ liệu.
- M4-05: duyệt gói tri thức, scope, release checklist, hướng dẫn người dùng và hỗ trợ.
- M4-06: deploy đúng quyền, smoke tests từ web thật, xác nhận URL và version đang phục vụ.

Hoàn tất MVP khi có bằng chứng cho các chức năng trong phạm vi, không còn P1 mở ở luồng release, tests/security/pilot đạt và clinical package được duyệt. Nếu một chức năng chưa đạt, giữ disabled và ghi MVP scope thực tế; không gọi full MVP complete.

## Definition of Done mỗi task

1. Có issue/requirement ID, ví dụ và expected behavior.
2. Code/config và docs liên quan được cập nhật.
3. Ca hồi quy có ý nghĩa; kiểm tra đã thực chạy và output được ghi.
4. Version/compatibility/migration được xét; clinical change có approval nếu cần.
5. Không leak PII, không phá history/quyền/contract.
6. Bàn giao tác động, hạn chế, quyết định mở và bước kế tiếp.

## Quản lý phạm vi và lịch

Ưu tiên safety/correctness, reproducibility và auth trước editor đẹp/AI. Chia task đủ nhỏ để một change có thể review và rollback. Mỗi tuần đối chiếu backlog với evidence; chu kỳ hai tuần là đề xuất vận hành, không deadline bắt buộc.

Không chuyển việc bác sĩ chưa chốt thành quyết định kỹ thuật của Claude. Nếu D-01 chưa chốt, vẫn sửa engine/test và xây adapter cho JSON fixture; template dữ liệu thật giữ pending. Nếu hosting chưa chốt, hoàn thiện local/staging theo quyền đã có, không giả định production.
