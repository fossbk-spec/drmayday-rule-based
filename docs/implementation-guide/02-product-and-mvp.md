# Yêu cầu sản phẩm và phạm vi MVP

## Yêu cầu từ người dùng

1. Yêu cầu rule-based của bác sĩ có thể thay đổi; cập nhật nhanh và flexible.
2. Đánh version luật và truy được bản đã dùng cho mỗi kết quả.
3. Website public có demo với dữ liệu giả lập; có chức năng import dữ liệu thật, phân loại và giải thích.
4. Trực quan hóa input.
5. Trực quan hóa kết quả và lý do.
6. Sau này kết hợp/phát triển AI để so sánh với rule-based.
7. Thực hiện MVP rồi tiếp tục cập nhật theo thời gian/yêu cầu mới.

Website có địa chỉ public không có nghĩa bệnh án thật hoặc chức năng quản trị được public. Thiết kế đề xuất: demo public; xử lý dữ liệu thật và quản trị sau đăng nhập/phân quyền.

## Người dùng và quyền đề xuất

| Vai trò | Quyền |
| --- | --- |
| Khách demo | Xem/chạy dữ liệu giả; không xem dữ liệu thật, không kích hoạt luật |
| Người nhập/review dữ liệu | Import, sửa bản nháp, chạy và export các batch thuộc phạm vi được cấp |
| Bác sĩ phụ trách | Review ca, xác nhận tiêu chí và nghiệm thu tác động thay đổi luật |
| Người soạn luật | Tạo/sửa draft, chạy preview, đề nghị duyệt |
| Người phát hành | Kích hoạt bản đã được duyệt, rollback, xem lịch sử phát hành |
| Quản trị vận hành | Quản lý tài khoản/quyền/môi trường; quyền hạ tầng không mặc nhiên cho phép duyệt chuyên môn |

MVP có thể gộp vai trò trong nhóm nhỏ, nhưng permission phải tách trong code và audit phải ghi ai soạn/duyệt/kích hoạt. Nếu cùng người làm nhiều vai trò, ghi rõ chính sách đã chấp thuận.

## Có trong MVP

- Engine và pipeline ổn định, không crash do kiểu input phổ biến, giữ missing.
- Một định dạng import được chốt, template và validate theo từng record/trường.
- Demo public, khu vực dữ liệu thật có auth và kiểm tra quyền ở server.
- Preview RAW/CANONICAL, mapping có nguồn; không tự suy diễn đơn vị.
- Batch chạy theo phiên bản cố định; lỗi từng dòng được giữ trong báo cáo.
- Kết quả từng ca, trực quan hóa, giải thích có bằng chứng và export.
- Luật có revision; gói tri thức bất biến; draft/approve/activate/rollback.
- So sánh tác động bản nháp trên bộ ca giả định được duyệt.
- CI, staging, audit đã lọc định danh, pilot và hướng dẫn sử dụng.

## Sau MVP

- Editor kéo thả cây luật đầy đủ; import nhiều biểu mẫu và connector bệnh viện.
- Huấn luyện AI, tích hợp dịch vụ AI ngoài, quyết định ensemble.
- Dashboard nghiên cứu nâng cao, multi-tenant quy mô lớn, microservices.

Vẫn thiết kế classifier contract và dữ liệu có version trong MVP để không phải viết lại khi thêm AI. Không triển khai các tính năng ngoài phạm vi chỉ vì đã có chỗ mở rộng.

## Luồng demo

Chọn ca giả → xem input nhóm/timeline/test → sửa bản nháp → phân loại → xem status/nhãn/luật/bằng chứng → tải JSON kết quả. Đổi input phải xóa hoặc đánh dấu kết quả cũ là stale và yêu cầu chạy lại.

Input demo tùy chỉnh phải được validate giống contract áp dụng. Không lưu nội dung người dùng paste theo mặc định. Nếu demo cho paste JSON tùy ý, hiển thị yêu cầu chỉ dùng dữ liệu giả, hạn chế/rate-limit upload và đảm bảo log không ghi payload.

## Luồng dữ liệu thật

Đăng nhập → chọn template/version → import → xem preview/errors → xác nhận mapping đã được cấu hình → chạy batch → review từng ca → export theo quyền → xóa hoặc lưu theo chính sách.

- File sai cấu trúc toàn bộ có thể bị từ chối; file đọc được có lỗi record vẫn báo từng record.
- Sửa record tạo revision dữ liệu mới; không sửa kết quả của lượt chạy đã lưu.
- Nhãn thật được giữ riêng cho evaluator nếu có; không truyền vào classifier.
- Người dùng xem số record nhận/đọc được/chạy được/lỗi/chưa kết luận; không âm thầm bỏ record.

## Luồng thay đổi luật

Soạn YAML/form có cấu trúc → validate cấu hình → preview → so sánh bản active/draft → bác sĩ duyệt bằng ca nghiệm thu → release → activate cho run mới. MVP không bắt buộc editor kéo thả; form đơn giản hoặc Git/YAML cùng review UI đủ.

## Trực quan hóa input

| Loại dữ liệu | Hiển thị và điều kiện |
| --- | --- |
| Tuổi/ngày/thời gian | Timeline tại ngày khám; nguồn/công thức; thiếu mốc hiện thiếu, không dùng ngày chạy thay thế |
| Huyết áp | Chuỗi thời điểm và ngưỡng của phiên bản luật nếu có dữ liệu; đơn vị rõ |
| Triệu chứng | Nhóm hệ cơ quan; Có/Không/Chưa biết; không trộn thiếu với âm tính |
| Xét nghiệm | ASST/ELISA/test kích thích, ký hiệu chuẩn và giá trị nguồn |
| Chất lượng dữ liệu | Thiếu/sai kiểu/mâu thuẫn/đơn vị chưa rõ; link đến trường gây vấn đề |
| Dữ liệu chuẩn hóa | RAW cạnh CANONICAL; chuyển đổi nào đã áp dụng và vì sao |

Không cần body map hoặc hình ảnh mới nếu biểu mẫu nhóm và bảng đã giải thích đủ. Giá trị thiếu không được vẽ như 0.

## Trực quan hóa kết quả

Hiển thị theo thứ tự: trạng thái → kết luận nếu có → phiên bản → lý do chính → việc cần làm. Cho mở chi tiết cây luật TRUE/FALSE/UNKNOWN, cùng khớp/chặn, bằng chứng từng điều kiện và nguồn biến.

Cần phân biệt:

- Rule khớp nhưng không được chọn vì priority.
- Rule UNKNOWN thực sự có thể đổi kết luận.
- Xung đột cùng ưu tiên khác kết luận.
- Theo dõi/chưa đủ dữ kiện với một nhãn bệnh.
- CSU unknown là endotype đủ test âm; không đồng nhất với thiếu test.

Các giá trị lâm sàng trong giải thích được bảo vệ như bệnh án. Trace/audit chung giữ ID/path/operator/result/reason, không ghi giá trị bệnh án gốc. Không dùng tỷ lệ điều kiện khớp làm xác suất.

## Tiêu chí sử dụng

Người thử nghiệm hoàn thành demo hoặc import → sửa lỗi → chạy → đọc được vì sao/chưa đủ điều gì → export mà không cần terminal. Toàn bộ kết quả chỉ về đúng snapshot dữ liệu và gói phiên bản; truy cập trái quyền bị từ chối ở API.
