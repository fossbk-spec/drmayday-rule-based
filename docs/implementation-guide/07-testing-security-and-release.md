# Kiểm thử, bảo vệ dữ liệu và phát hành

## Chiến lược kiểm thử

Tách bộ **hành vi kỹ thuật**, **nghiệm thu chuyên môn** và **đánh giá lâm sàng**. Pass fixture YAML không thay thế nhãn tham chiếu độc lập. Không thêm test chỉ phản chiếu implementation; dùng lỗi tái hiện, contract và các hành vi quan trọng.

| Nhóm | Ca cần có |
| --- | --- |
| Config | YAML sai, duplicate ID, priority sai, ref thiếu/vòng, field/operator/type/công thức không hỗ trợ |
| Logic | AND/OR/NOT/count với TRUE/FALSE/UNKNOWN, ref/cache, đảo thứ tự YAML không đổi kết quả |
| Số/công thức | int/float, bool, string/list/object, null/sentinel, NaN/Infinity/overflow; thiếu operand/ngưỡng |
| Selection | Priority, conflict cùng ưu tiên, cùng nhãn nhiều rule, unknown có/không đổi kết luận, fallback |
| Preprocess | Giữ tuổi hợp lệ, thiếu/ngày sai/tương lai, tuổi conflict, BP thiếu/conflict, giờ-tuần và ký hiệu test |
| Privacy/identity | Mã gốc không ra export/log; tên trắng; ID thiếu/trùng; linked visits theo policy |
| Pipeline | RAW hợp lệ/sai, mapping chưa chốt, label isolation, provenance, canonical invalid/missing |
| Batch | Một dòng lỗi, counter conservation, retry/idempotency, cancellation, update giữa run, ownership |
| Version | Immutable release, draft edit invalidates approval, compatibility, compare, rollback build/package |
| Web | Demo, input change stale result, errors, import preview, evidence tree, export, mobile/keyboard |
| Auth | Không login, thiếu quyền, đổi ID đoán batch khác, export/admin trái quyền, session/logout |

### Hồi quy baseline cần giữ

- `SOC-INVALID-BOOL-TRUE/FALSE`, `SOC-INVALID-LIST/OBJECT` và trường hợp HATT string.
- HATT nền null/unknown khi HATT hiện tại 95: báo đúng trường nền.
- `tuoi=5`, không ngày sinh, HATT 85: không overwrite tuổi làm đổi kết luận.
- Thiếu HATT không thành 120 và không classified nhờ default.
- `CAP-THUONG-OBJECT/STRING`: đưa thành nghiệm thu shape đã chốt, không sửa expected để che mâu thuẫn.
- Ca F-13: nhánh OR đã TRUE không làm nguyên nhân chặn thành invalid type không liên quan.
- Export record giả có mã gốc: output không giữ mã đó.
- Missing ID không làm hai bệnh nhân giả bị gộp.

Các test P1 đã sửa phải pass thật, không để expectedFailure/skip rồi tuyên bố đạt. Lưu bộ 138 case như lịch sử nếu cần; tạo version fixture mới và change rationale cho kỳ vọng đã sửa.

## Ca chuyên môn tối thiểu

Đọc RB-01..RB-20 trong `docs/02_workflow.md` baseline; gắn task/test IDs trong bộ mới. Bác sĩ xác nhận điều kiện/expected riêng:

- Trước/tại/sau ngưỡng tuổi, HATT, thời gian, xét nghiệm.
- Đủ/thiếu bằng chứng phản vệ/sốc và nguy cơ ưu tiên cao chặn nhánh thấp.
- Từng dấu nặng, cấp thường khi đã loại đủ dấu nặng.
- CIndU test phổ biến/khác, nhiều test dương, Adrenergic và đồng mắc.
- CSU giai đoạn 1/2, 59/60/61 ngày, Stella, ELISA, unknown endotype và ngoài cohort.

Nếu tiêu chí pending, test xác nhận trạng thái pending/review theo policy được duyệt; không tự đặt nhãn bệnh đúng.

## CI và môi trường

Mỗi change chạy lệnh từ checkout sạch: cài dependency pin trong môi trường riêng, test discovery, config/schema validation và các integration/UI/security tests liên quan. Kiểm tra test nằm trong tracked tree. Không yêu cầu một coverage % tùy ý thay cho hành vi quan trọng.

Tách development/staging/production. Development dùng dữ liệu giả. Staging dùng dữ liệu giả hoặc dữ liệu được phép theo policy; không copy production mặc định. Deployment phải dùng secret management ngoài Git; không nhúng credential vào YAML/demo.

Version API/export/engine/package hiển thị ở staging và production. Có smoke test sau deploy kiểm tra health, package active, demo, auth và đường xử lý chính.

## Dữ liệu thật: yêu cầu kỹ thuật

Đây là yêu cầu thiết kế sản phẩm; không phải kết luận tuân thủ pháp lý. Chủ dữ liệu xác nhận quyền/mục đích xử lý, thời hạn lưu và nơi dữ liệu được phép đi trước pilot dữ liệu thật.

- TLS cho truyền dữ liệu; bảo vệ storage và quyền truy cập thích hợp với hosting đã chọn.
- Auth qua cơ chế đã được kiểm chứng; quyền server-side cho import/read/export/admin, sở hữu/phạm vi batch.
- Least privilege; tài khoản vận hành không mặc nhiên xem bệnh án hoặc duyệt chuyên môn.
- File upload có allowlist, size/row/time limits; tên file không thành path thực thi; không thực thi nội dung/macros.
- Không render HTML tùy ý từ ghi chú/tên rule; escape nội dung, messages không leak stack/payload.
- Export có allowlist, kiểm tra PII và phòng formula injection nếu CSV mở bằng spreadsheet.
- Demo input tùy chỉnh không được ghi vào log/analytics mặc định; rate limit và không cho upload nội dung không giới hạn.
- Logs chỉ actor/run/record kỹ thuật, action, version, duration/error code; không giá trị bệnh án.
- Clinical evidence và input snapshot lưu trong kho có quyền như bệnh án, không nhúng vào log chung hoặc URL public.
- Token ổn định nếu cần linked visits: cơ chế có khóa bí mật và scope được chốt; không dùng salt public cố định như một bảo đảm vô danh.
- Danh tính gốc/mapping token tách quyền; free text và cấu trúc lồng phải được xét trong policy export.
- Retention/xóa: raw, canonical, evidence/results, file export và backup có lịch rõ; kiểm tra xóa thực tế.
- Sự cố/breach/escalation có người phụ trách và quy trình ghi nhận; không gửi payload thật vào bug tracker public.

Quyền xuất và lưu phải có audit. Mọi access check áp dụng cho ID được caller cung cấp, không chỉ trang web ẩn nút.

## Tái lập và xóa dữ liệu

Trong thời gian được phép lưu snapshot, giữ input revision/hash, code build, package/schema/mapping/preprocessing versions, mốc đánh giá và trace. Rerun cùng các thành phần cho cùng kết quả nghiệp vụ, không so sánh run_id/timestamp/duration.

Sau khi policy yêu cầu xóa input, không thể cam kết rerun đầy đủ chỉ từ hash. Giữ metadata tối thiểu được phép và ghi rõ snapshot đã xóa; privacy policy ưu tiên hơn lời hứa lưu dữ liệu mãi để tái lập.

## Release gates

### Demo public

- Test engine và demo đạt trong phạm vi release; limitations được hiển thị đúng.
- Chỉ package release được phép công bố; ca giả, payload tùy chỉnh không lưu mặc định.
- Health/rate limits/errors/escaping kiểm tra, credentials không public.

### Dữ liệu thật

- Hợp đồng import/mapping và clinical package được duyệt cho scope cụ thể.
- Không P1 còn mở trong luồng được bật; authentication/authorization/export/privacy tests đạt.
- Retention, phạm vi truy cập và môi trường xử lý được chủ dữ liệu xác nhận.
- Pilot có review; rollback đã thử; backup/restore nếu lưu dữ liệu đã kiểm tra.
- Có hướng dẫn, support owner, changelog, version và giới hạn sản phẩm rõ.

Không bật chức năng thật chỉ vì demo đã chạy. Nếu feature chưa đạt gate, giữ disabled, phản ánh scope MVP thực tế. Việc đưa lên public/production tuân theo quyền deployment đã được người dùng cấp.

## Báo cáo kiểm thử/phát hành

Lưu commit/build/package/hash, dependency/runtime, case set và số pass/fail/skip/expectedFailure. Đếm record nhận/không đọc được/invalid/chạy được/chưa kết luận/exception; đối chiếu tổng và không âm thầm loại ca lỗi khỏi mẫu số.

Mẫu báo cáo nằm ở file 09. Chỉ báo accuracy/precision/recall/F1 khi có ground truth độc lập, taxonomy mapping và evaluation protocol rõ.
