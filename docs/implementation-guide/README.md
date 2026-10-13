# Hướng dẫn triển khai rule_based_mayday cho Claude

Ngày tổng hợp: **13/10/2026**. Phiên bản bộ hướng dẫn: **1.0.0**.

Repository: <https://github.com/trangdoanthu26/rule_based_mayday>.

Mốc source đã review: `f9ee49b342d47300f9880823e987d3b3e5ca62b4`, nhánh `main`; YAML `1.2.1`. Claude phải kiểm tra HEAD thực tế trước khi thay đổi. Tài liệu này không khẳng định repo chưa thay đổi kể từ mốc trên.

## Mục tiêu

Phát triển sản phẩm phân loại bệnh án bằng rule-based: bác sĩ có thể thay đổi luật nhanh, mọi kết quả có phiên bản và giải thích; có website demo public, import dữ liệu thật có kiểm soát truy cập và nền tảng so sánh model AI trong tương lai.

Đây là **gói hướng dẫn thực hiện**, không phải thông báo đã triển khai MVP, đã duyệt tiêu chí y khoa hoặc đã có website public.

## Thứ tự đọc

| File | Nội dung |
| --- | --- |
| [CLAUDE.md](../../CLAUDE.md) | Chỉ dẫn bắt đầu, giới hạn quyền quyết định, cách làm việc và bàn giao |
| [01-current-state-and-findings.md](01-current-state-and-findings.md) | Hiện trạng, bằng chứng review, lỗi cần sửa và giới hạn đánh giá |
| [02-product-and-mvp.md](02-product-and-mvp.md) | Yêu cầu sản phẩm, phạm vi MVP, vai trò, luồng sử dụng và trực quan hóa |
| [03-architecture-and-contracts.md](03-architecture-and-contracts.md) | Kiến trúc module, hợp đồng dữ liệu/API/kết quả và lưu trữ |
| [04-workflows-and-pipeline.md](04-workflows-and-pipeline.md) | Sơ đồ hiện tại, workflow quản lý tri thức và pipeline đích |
| [05-rule-versioning-and-change-management.md](05-rule-versioning-and-change-management.md) | Gói tri thức, revision luật, duyệt, kích hoạt, so sánh và rollback |
| [06-mvp-implementation-plan.md](06-mvp-implementation-plan.md) | Backlog bốn đợt, phụ thuộc, việc bắt đầu ngay và tiêu chí nghiệm thu |
| [07-testing-security-and-release.md](07-testing-security-and-release.md) | Kiểm thử, bảo vệ dữ liệu, CI, staging, pilot và release gates |
| [08-continuous-delivery-and-ai.md](08-continuous-delivery-and-ai.md) | Vận hành, cập nhật liên tục, theo dõi và lộ trình AI |
| [09-decisions-and-templates.md](09-decisions-and-templates.md) | Quyết định còn mở và mẫu yêu cầu, ADR, change request, release report |

## Sử dụng cùng repo

1. Đặt `CLAUDE.md` ở root repo sau khi đọc và hợp nhất với hướng dẫn hiện có; không ghi đè mù quáng.
2. Đặt các file còn lại của gói này dưới `docs/implementation-guide/` và giữ cấu trúc phẳng.
3. Sau khi đưa `CLAUDE.md` lên root và README này vào `docs/implementation-guide/`, đổi link `CLAUDE.md` trong mục lục README thành `../../CLAUDE.md`. Chỉnh các đường dẫn khác nếu bố trí khác; CLAUDE đã nêu quy tắc tìm tài liệu ở root của gói hoặc `docs/implementation-guide/`.
4. Nếu chỉ gửi gói này cho Claude, gửi cùng quyền truy cập repo hoặc checkout. Gói không chứa toàn bộ source.
5. Dùng prompt khởi động dưới đây. Đừng yêu cầu Claude triển khai toàn bộ mà bỏ qua các gate dữ liệu/chuyên môn.

## Prompt khởi động

```text
Hãy đọc CLAUDE.md và toàn bộ docs/implementation-guide/ (hoặc các file cùng thư mục với CLAUDE.md).
Kiểm tra repo rule_based_mayday và hướng dẫn hiện có. Đối chiếu HEAD hiện tại với baseline f9ee49b.
Tóm tắt những khác biệt ảnh hưởng kế hoạch, cập nhật backlog theo bằng chứng rồi thực hiện Đợt 1.
Hoàn thành các sửa lỗi kỹ thuật đã được xác định, thêm kiểm thử hồi quy có ý nghĩa và báo kết quả thực chạy.
Giữ nguyên ngưỡng/tiêu chí y khoa chưa được bác sĩ duyệt. Với quyết định còn mở, ghi vào decision log;
tiếp tục các phần độc lập. Không đưa bệnh án thật vào dịch vụ bên ngoài hoặc deploy public khi chưa có
quyền phù hợp. Kết thúc bằng thay đổi, kiểm thử, hạn chế, quyết định cần chốt và bước kế tiếp.
```

## Cách hiểu trạng thái

- **Hiện trạng đã xác minh:** thuộc commit baseline, có nguồn hoặc lượt chạy review.
- **Yêu cầu:** xuất phát từ nhu cầu người dùng trong cuộc trao đổi.
- **Thiết kế đề xuất:** phương án thực hiện, chưa phải code đang chạy.
- **Cần chốt:** bác sĩ/chủ sản phẩm phải xác nhận; Claude không tự biến giả định thành yêu cầu đã duyệt.

Các sơ đồ Mermaid có thể xem trên GitHub hoặc trình đọc Markdown hỗ trợ Mermaid. Mũi tên nét đứt trong sơ đồ hiện trạng biểu diễn module chưa nối; trong sơ đồ đích, toàn bộ luồng là thiết kế cần triển khai.

## Kết quả mong đợi

MVP có demo public, khu vực dữ liệu thật có đăng nhập, pipeline đáng tin cậy, gói luật có phiên bản, giải thích có bằng chứng và khả năng tái lập. Giai đoạn tiếp theo bổ sung editor trực quan và AI qua cùng hợp đồng dữ liệu, không thay đổi âm thầm kết quả cũ.
