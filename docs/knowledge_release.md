# Phát hành gói kiến thức

1. Tạo yêu cầu thay đổi luật với ca minh họa giả và sửa bản nháp trong `rules/` qua PR.
2. Đọc báo cáo tác động trên 138 ca giả trong PR. Bác sĩ duyệt nội dung và các ca thay đổi.
3. Sau khi duyệt, chạy `python tools/release_package.py --version X.Y.Z --summary "..."` để tạo gói mới. Gói đã phát hành là bất biến; không sửa trực tiếp.
4. Merge PR chứa gói mới. Tạo PR riêng để đổi `knowledge/active.yaml` cho môi trường cần kích hoạt, rồi merge sau khi duyệt.
5. Khi cần rollback, tạo PR trả con trỏ trong `knowledge/active.yaml` về gói trước đó. Kiểm tra báo cáo tác động và duyệt PR trước khi merge.

`demo` dùng cho trình diễn. `real` chỉ trỏ tới gói đã qua duyệt chuyên môn.
