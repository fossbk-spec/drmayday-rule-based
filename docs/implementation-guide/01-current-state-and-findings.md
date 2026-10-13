# Hiện trạng và phát hiện review

## Mốc và phạm vi

Repo: `trangdoanthu26/rule_based_mayday`, commit `f9ee49b342d47300f9880823e987d3b3e5ca62b4`, YAML `1.2.1`. Review đọc source/docs và chạy engine bằng Python 3.12, `PyYAML==6.0.3` với dữ liệu giả. Chưa chạy giao diện Streamlit, chưa thẩm định tiêu chí y khoa ngoài repo. Source có thể đã thay đổi sau mốc này.

## Thành phần đang có

| Thành phần | Hiện trạng tại baseline |
| --- | --- |
| `main.py` | Demo Streamlit: chọn ca, sửa JSON, parse envelope, bỏ metadata, gọi engine, hiện kết quả/trace, tải JSON |
| `src/classify.py` | Nạp YAML, kiểm tra rule/ref/vòng, cache mỗi record, logic ba trạng thái, chọn theo priority, trả trace và hash |
| `rules/classification_rules.yaml` | 23 luật, 18 luật đích, 12 nhãn bệnh và 2 nhãn theo dõi |
| `schema/*.json` | Schema biểu mẫu hiện có; chưa thống nhất với input CANONICAL mà YAML đọc |
| `src/preprocess.py` | Có code; còn defaults và ghi đè nguy hiểm; chưa nối vào demo |
| `src/anonymize.py` | Có code; còn giữ mã bệnh nhân gốc; chưa nối vào demo |
| `src/validate.py`, `src/pipeline.py`, `src/evaluate.py` | File trống |
| `rules/validation_rules.yaml` | File trống |
| `data/synthetic/` | 138 ca logic và 53 hồ sơ giả lập cũ |
| `tests/` | Không có trong tracked tree dù README/docs mô tả 43 test methods |
| `docs/diagrams/` | Ba SVG mô tả quy trình, phân tầng và cây CSU |
| `requirements.txt` | PyYAML 6.0.3; Streamlit 1.50.0 |

Không suy từ docs rằng code/test/deployment đã tồn tại. `INVALID_DATA` và `OUT_OF_SCOPE` nằm trong tập tên status nhưng pipeline xác định chúng chưa triển khai.

## Sáu phát hiện chính

| ID mới | Ưu tiên | Vị trí baseline | Tái hiện và việc cần làm |
| --- | --- | --- | --- |
| TECH-01 | P1 | `src/classify.py:344-366` | `<_formula` không kiểm tra HATT: list/object gây TypeError; bool trả sốc. Kiểm tra cả operand và biến ngưỡng, số hữu hạn, loại bool. Tương ứng F-12 của repo. |
| TECH-02 | P1 | `src/preprocess.py:49-64`, defaults ở 15/22/43 | `tuoi=5`, không ngày sinh → 25; HATT 85 đổi Phản vệ sang Sốc. HATT thiếu → 120, từ thiếu dữ kiện sang classified. Bảo toàn giá trị hợp lệ và missing. |
| DATA-01 | P1 | `rules/classification_rules.yaml:262-281` | Cấp thường đồng thời cần object `.danh_sach_chon` và phủ định so sánh scalar/string. Hai ca object/string đều NEEDS_REVIEW. Cần thống nhất shape với bác sĩ/dữ liệu, sửa nặng/thường đồng bộ. Tương ứng F-01. |
| SEC-01 | P1 | `src/anonymize.py:45-49` | Tạo token nhưng giữ `ma_benh_nhan` trong output. Loại mã gốc; kiểm tra cả export allowlist và trường lồng/free text. |
| TECH-03 | P2 | `src/classify.py:344-359` | HATT 95, nền null/unknown: missing_fields báo HATT hiện tại thay vì HATT nền. Gắn reason vào operand thực sự thiếu/sai. |
| QA-01 | P2 | `README.md:156`; tree Git | README nói 43 test nhưng thiếu tests. Discovery báo `Start directory is not importable: 'tests'`. Bổ sung test vào Git và CI. |

P1: cần sửa trước khi đưa luồng liên quan vào vận hành với dữ liệu thật. P2: ảnh hưởng giải thích/tái lập, phải xử lý trong MVP. Không có nghĩa đây là review exhaustive.

Các test tái hiện phải dùng dữ liệu giả. Khi sửa lỗi kỹ thuật, không thay ngưỡng y khoa chỉ để làm ca pass.

## Kết quả xác nhận

| Trạng thái trên 138 ca logic | Số ca |
| --- | ---: |
| CLASSIFIED | 94 |
| INSUFFICIENT_DATA | 18 |
| NEEDS_REVIEW | 6 |
| UNRESOLVED | 17 |
| TypeError | 3 |

Không có lệch với các trường kỳ vọng được lưu trong `expected_engine`; input giữ nguyên trong lượt chạy review. Điều này xác nhận hành vi hiện tại, kể cả hành vi sai đã được fixture ghi lại, không chứng minh đúng y khoa.

Truyền trực tiếp 53 hồ sơ RAW cũ vào engine, không mapping: 34 INSUFFICIENT_DATA, 19 NEEDS_REVIEW, 0 CLASSIFIED. Đây là kiểm tra tương thích, không phải accuracy sau pipeline. Accuracy 81,13% trong README là lịch sử.

## Các vấn đề đã được repo ghi nhận cần đối chiếu

Đọc `docs/06_rule_logic_review.md` và `docs/03_implementation_readiness.md`. Không gọi các lỗi F-01/F-12 là mới được phát hiện nếu báo cáo release.

- F-02/F-03: khoảng tuổi bỏ trống và mốc sáu tuần/nguồn giờ-tuần.
- F-04/F-05/F-09: dị nguyên nghi ngờ/đã biết, thời điểm, phạm vi R-SOC và sàng lọc xuyên biểu mẫu.
- F-06/F-10: Ice cube, Adrenergic, nhiều thể CIndU, đồng mắc CSU/CIndU.
- F-07: enum/range/sentinel chưa được validate.
- F-08: Stella và điều kiện nghiên cứu khác giữa workflow/YAML.
- F-11: fallback thiếu ASST chưa có phạm vi phù hợp.
- F-13: lý do UNKNOWN bị lẫn với lỗi trong nhánh OR đã có đủ bằng chứng.

Một phát hiện bổ sung cần ca hồi quy: các hồ sơ thiếu ID cùng nhận token từ `UNKNOWN`, gây trùng. Tên chỉ có khoảng trắng có thể làm `_mask_name` truy cập danh sách rỗng. Đây là kiểm tra kỹ thuật cần xác nhận lại, không nằm trong sáu mục chính ban đầu.

## Tái lập trên checkout mới

Ví dụ lệnh chuẩn, thực hiện tại root checkout; điều chỉnh executable Python theo môi trường, không dùng đường dẫn máy của tác giả tài liệu:

```powershell
git rev-parse HEAD
git status --short
git ls-files tests
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Sau khi đã đưa test vào repo, chạy trên Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Trên Linux/macOS, dùng `.venv/bin/python` thay cho `.venv\Scripts\python.exe`. Test discovery hiện thất bại tại baseline vì không có thư mục test; không tạo thư mục rỗng để làm lệnh trả 0 test rồi coi là pass. Pin/runtime tương thích phải được kiểm tra nếu môi trường mới khác Python 3.9+ mà repo ban đầu dùng.

1. Xác minh commit bằng Git; tạo virtual environment riêng.
2. Cài `requirements.txt`; nếu chỉ kiểm tra engine, PyYAML đúng pin đủ cho luồng đó.
3. Kiểm tra `git ls-files tests`, không chỉ sự tồn tại thư mục local.
4. Với 138 ca: chỉ truyền `du_lieu`; so sánh từng trường expected và expected exception; đếm status/error và kiểm tra input không bị sửa.
5. Với 53 ca cũ: báo rõ RAW không mapping, không tính thành accuracy lâm sàng mới.
6. Sau khi sửa engine, cập nhật fixture lỗi kỹ thuật bằng kỳ vọng đúng đã được mô tả; giữ ca hồi quy phát hiện lỗi. Không dùng expectedFailure cho lỗi P1 đã tuyên bố sửa.

Nếu HEAD mới khác baseline, ghi bảng lỗi còn mở/đã sửa/chưa xác minh trước khi tiếp tục.
