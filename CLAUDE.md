# Chỉ dẫn thực hiện project rule_based_mayday

> **Tiếp tục công việc:** đọc [docs/HANDOFF.md](docs/HANDOFF.md) trước – tiến độ, việc tiếp theo, quy tắc merge và thiết lập máy mới (cập nhật file đó khi kết thúc mỗi phiên).

## Nhiệm vụ và nguồn chuẩn

Đọc toàn bộ gói hướng dẫn trước khi lập kế hoạch thay đổi. Các file `01-...md` đến `09-...md` nằm cùng thư mục với file này hoặc dưới `docs/implementation-guide/` sau khi được đưa vào repo. Đọc README của gói để biết mục lục.

Mục tiêu: xây MVP rule-based có website demo public, import dữ liệu thật được bảo vệ, trực quan hóa input/kết quả, giải thích, version và cập nhật liên tục; chuẩn bị adapter cho AI trong tương lai.

Baseline được review: `f9ee49b342d47300f9880823e987d3b3e5ca62b4`. Ngày tài liệu: 13/10/2026. Trước khi sửa, xác minh HEAD, nhánh, trạng thái working tree và mọi `AGENTS.md`/`CLAUDE.md` có hiệu lực. Không reset, xóa hoặc ghi đè thay đổi của người dùng.

Các hướng dẫn có thẩm quyền cao hơn và chỉ đạo hiện tại của người dùng luôn được ưu tiên. Chỗ tài liệu khác với source mới phải được đối chiếu và ghi rõ, không giữ kết luận cũ chỉ để bám kế hoạch.

## Cách bắt đầu

1. Kiểm tra source, dependency, test và docs thực tế; không dựa riêng vào số test ghi trong README.
2. Chạy baseline với dependency đúng phiên bản trong môi trường riêng; không nâng Python hoặc package hệ thống.
3. Xác minh các lỗi ở `01-current-state-and-findings.md`; phân biệt lỗi đã được sửa và lỗi còn mở.
4. Lập backlog theo `06-mvp-implementation-plan.md`, bắt đầu Đợt 1.
5. Viết ca hồi quy tái hiện hành vi sai trước khi sửa; sửa nhỏ, có thể review và rollback.
6. Chạy kiểm tra liên quan; chỉ mở rộng kiểm thử khi thay đổi hoặc lỗi mới cần nó.
7. Cập nhật hướng dẫn, changelog, manifest và báo cáo đúng phần đã thực hiện.

Nếu task chỉ được giao Đợt 1, không tự triển khai/deploy toàn MVP. Trong phạm vi đợt được giao, hoàn thành phần độc lập và không dừng chỉ vì một quyết định không liên quan đang mở.

## Quyền quyết định

Claude có thể xử lý lỗi kỹ thuật, cấu trúc code, test và tài liệu trong phạm vi được giao. Các điều sau cần bằng chứng/phê duyệt của người phụ trách:

- Ngưỡng y khoa, khoảng tuổi, mốc sáu tuần, tiêu chí phản vệ/sốc và Stella.
- Định nghĩa biến, mapping có thể đổi ý nghĩa bệnh án, chính sách đồng mắc/cohort.
- Mục đích xử lý dữ liệu thật, quyền truy cập, thời hạn lưu và dịch vụ được phép nhận dữ liệu.
- Đưa bản phát hành chuyên môn vào hoạt động, triển khai môi trường public và thay đổi production.

Không hỏi lại để xin phép các sửa lỗi thường lệ đã được giao. Chỉ hỏi quyết định thực sự thiếu và ảnh hưởng bước phụ thuộc; ghi rõ lựa chọn, tác động và bằng chứng.

## Những điều bắt buộc giữ

- Không lấy `nhan`, chẩn đoán đích, tên file hoặc mô tả ca có đáp án để tạo feature.
- Không tự điền tuổi 25, huyết áp 120, thời gian 0/1 hoặc triệu chứng âm tính khi thiếu.
- Không coi UNKNOWN là FALSE. Không hạ xuống nhãn nhẹ hơn khi UNKNOWN có thể đổi kết luận ưu tiên.
- Số đo phải là số hữu hạn, loại `bool`. Công thức cấu hình phải thuộc tập cho phép; không dùng `eval`, mã tùy ý hoặc plugin Python do người nhập luật cung cấp.
- Kết quả phải chỉ ra rule/package/engine version đã dùng. Một batch cố định phiên bản từ đầu đến cuối.
- Không sửa bản luật đã phát hành tại chỗ; tạo revision/gói mới.
- Một record lỗi không làm mất cả batch hoặc bị bỏ khỏi báo cáo số ca.
- Không đưa PII hoặc giá trị bệnh án thật vào log chung, test fixture, repo, prompt hoặc dịch vụ AI bên ngoài khi chưa có chính sách và quyền phù hợp.
- Khử định danh phải loại mã gốc khỏi bản xuất; che một phần tên/SĐT không đủ để tuyên bố dữ liệu đã vô danh.
- Cơ chế xác thực/phân quyền phải được kiểm tra ở server, không chỉ ẩn nút ở UI.
- Không trình bày số điều kiện khớp như xác suất bệnh.
- Không gọi fixture `expected_engine` là ground truth lâm sàng.

## Nguyên tắc kiến trúc

Giữ engine độc lập với Streamlit/API/storage. Tái sử dụng Python và YAML hiện tại. Tách module theo trách nhiệm, không tạo microservices hoặc framework tổng quát khi MVP chưa cần. Một ứng dụng triển khai được với service/module nội bộ là đủ.

Chọn stack web, auth, DB và hosting bằng ADR dựa trên môi trường thực tế. Không giới thiệu dependency mới chỉ để bắt chước sơ đồ. Các tên endpoint/entity trong tài liệu là hợp đồng đề xuất, chưa phải API sẵn có.

Không cần huấn luyện model AI cho MVP. Chỉ giữ điểm mở rộng classifier và output contract; chạy AI song song ở giai đoạn sau.

## Nhịp làm việc và bàn giao

Với mỗi task: nêu vấn đề/ca tái hiện, sửa, kiểm tra và báo tác động. Thay đổi luật có thêm báo cáo trước/sau và ca nghiệm thu được bác sĩ duyệt. Không cam kết lịch tuyệt đối khi chưa có nguồn lực.

Bàn giao gồm:

1. Phần đã hoàn thành và đường dẫn source/config.
2. Lệnh và kết quả kiểm thử thực chạy; tách pass, fail, skip, expected failure.
3. Phiên bản và migration nếu có.
4. Rủi ro/hạn chế còn thực tế, quyết định cần chốt và các task phụ thuộc.
5. Bước tiếp theo đủ cụ thể để một agent khác tiếp tục.

Không tuyên bố website đã public, dữ liệu đã được bảo vệ hoàn chỉnh, tiêu chí đã được duyệt hoặc model đạt accuracy mới khi chưa có bằng chứng.
