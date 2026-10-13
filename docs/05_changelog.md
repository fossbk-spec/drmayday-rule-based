# Nhật ký thay đổi và hướng dẫn kiểm tra demo

## Quy ước ghi nhận cho cộng tác viên

Mỗi đợt sửa thêm một mục mới ở đầu phần nhật ký; giữ nguyên các mục lịch sử. Ghi ngày giờ theo **Asia/Ho_Chi_Minh (UTC+07:00)**, họ tên đầy đủ, branch/commit, file sửa, hành vi trước/sau, lệnh và kết quả kiểm tra, lỗi còn mở. Người sửa và người review là hai vai trò riêng; chỉ ghi đã review/phê duyệt khi có xác nhận.

```text
Ngày giờ: YYYY-MM-DD HH:mm:ss +07:00
Họ tên người sửa đổi: <họ tên đầy đủ>
Branch / commit: <branch; SHA sau khi commit>
File và thay đổi: <vấn đề → hành vi mới>
Kiểm tra: <lệnh, số test đạt/thất bại/expectedFailure>
Lỗi hoặc giới hạn còn mở: <ID, ca tái hiện>
Review: <họ tên, ngày, kết luận khi đã xác nhận>
```

Không sửa ngày hoặc gán tên cho các lần thay đổi không có bằng chứng. Các phần hướng dẫn phía dưới được cập nhật cùng giao diện; kết quả kiểm tra của từng mục nhật ký vẫn giữ theo thời điểm đã chạy.

## Nhật ký — 13/10/2026

- **Ngày ghi nhận:** 2026-10-13 (+07:00).
- **Người sửa đổi:** Claude Code (AI), theo yêu cầu của người dùng; chưa có người review.
- **Branch:** `docs/implementation-guide` (local), từ `f9ee49b`.
- **File và thay đổi:**
  - `src/classify.py` — TECH-01 (F-12): `<_formula` kiểm tra HATT đo được là số hữu hạn, không phải bool; bool/chuỗi/list/object trả `NEEDS_REVIEW` thay vì kết luận sốc hoặc `TypeError`. TECH-03: trường thiếu ở vế ngưỡng (`huyet_ap_tam_thu_nen`/`tuoi`) được báo đúng trong `missing_fields`.
  - `src/preprocess.py` — TECH-02: bỏ mặc định tuổi 25, HATT 120 (đo và nền), thời gian khởi phát 0/1 và ngày khám bằng ngày chạy; không ghi đè tuổi hợp lệ có sẵn; ngày khám trước ngày sinh → không tính tuổi. Chính sách khi tuổi mâu thuẫn ngày sinh vẫn chờ chốt.
  - `src/anonymize.py` — SEC-01: xóa `ma_benh_nhan` khỏi bản xuất; thiếu mã → `patient_token_id = null`, không gộp chung token; tên chỉ có khoảng trắng không crash.
  - `data/synthetic/rule_logic_cases.json` — 5 ca F-12 (`SOC-INVALID-BOOL-TRUE/FALSE`, `SOC-INVALID-LIST/OBJECT`, `SOC-MISSING-80`) đổi kỳ vọng sang `NEEDS_REVIEW`. `rule_logic_results.json` giữ nguyên làm bản lịch sử ngày 10/10.
  - `main.py` — bỏ cảnh báo F-12 vì lỗi đã sửa; `tests/` mới; `.gitignore`.
- **Trước/sau trên 138 ca:** 94 CLASSIFIED / 18 INSUFFICIENT_DATA / 6 NEEDS_REVIEW / 17 UNRESOLVED / 3 TypeError → 92 / 18 / 11 / 17 / 0. Chỉ 6 ca đổi: 5 ca F-12 và `SOC-NEN-MISSING` (missing_fields đúng trường nền).
- **Kiểm tra:** `python -m unittest discover -s tests -v` (Python 3.14.7, PyYAML 6.0.3): 21 tests, 21 đạt, 0 expectedFailure. Chạy cùng test trên source cũ: 18 fail + 10 error, xác nhận test bắt được lỗi. Chưa chạy demo Streamlit.
- **Lỗi còn mở:** DATA-01 (F-01), F-02..F-11, F-13, QA-01 (chưa có CI). Không thay đổi YAML hay ngưỡng y khoa.

## Nhật ký — 10/10/2026, 09:10:41

- **Ngày giờ ghi nhận:** 2026-10-10 09:10:41 +07:00.
- **Họ tên người sửa đổi:** **Đồng Minh Dương**.
- **Branch:** `Feat-demo-warning-changelog`; cập nhật nội dung giải thích, không thêm tính năng hoặc sửa logic.
- **File:** `main.py`, `docs/giai_thich_thuat_ngu.md`, `docs/05_changelog.md`.
- **Thay đổi:** viết rõ hai pha; dùng ví dụ R-SOC tham chiếu R02-PV/R03-PV; giải thích cache là bảng nhớ tạm được tạo mới mỗi lần phân loại, kể cả chạy lại JSON đã sửa; phân biệt cache engine với kết quả còn hiển thị trong Streamlit.
- **Kiểm tra:** kiểm tra cú pháp Python và `git diff --check`; không chạy lại bộ test cho thay đổi câu chữ. Số liệu test 43 methods của mục trước là kết quả lịch sử, không phải lượt chạy mới.
- **Giới hạn/review:** giữ nguyên engine, YAML và các lỗi đang mở; chưa ghi nhận phê duyệt chuyên môn.

## Nhật ký — 10/10/2026, 04:20:43

- **Ngày giờ ghi nhận:** 2026-10-10 04:20:43 +07:00.
- **Họ tên người sửa đổi:** **Đồng Minh Dương**.
- **Branch:** `Feat-demo-warning-changelog`.
- **Commit:** chưa tạo commit trong đợt này; file nằm trong working tree.
- **Review:** chưa ghi nhận phê duyệt chuyên môn; test kỹ thuật không thay review tiêu chí bệnh.

### Thay đổi trong đợt này

| File | Trước | Sau |
| --- | --- | --- |
| [main.py](../main.py) | Cảnh báo F-01/F-12 ở cuối phần kết quả, dễ bị bỏ qua; ca lỗi chủ yếu chỉ hiện ID. | Khung lỗi đỏ ở đầu trang, hai khối F-01/F-12 riêng; giải thích F-01–F-13 theo ca gốc; hướng dẫn đọc/check logic ngay trên giao diện. |
| [main.py](../main.py) | Người đọc có thể hiểu trạng thái là chẩn đoán đã xác nhận hoặc dùng kỳ vọng ca gốc cho JSON đã sửa. | Giải thích trạng thái ngay cạnh kết quả; NEEDS_REVIEW báo đỏ, thiếu dữ kiện/chưa có rule báo vàng; thông báo JSON khác ca gốc; HATT boolean báo đỏ dù engine vẫn trả nhãn. |
| [tests/test_main.py](../tests/test_main.py) | Sáu test giao diện. | Thêm bốn test cho cảnh báo quan trọng, giải thích Stella, JSON sửa thành HATT boolean và trạng thái xung đột; test lỗi nhập/runtime kiểm tra đúng thông báo để không bị khung lỗi chung che lỗi. |
| `docs/05_changelog.md` | File trống. | Nhật ký có ngày giờ/tác giả, hướng dẫn demo, ý nghĩa các hiển thị, ca thực hành và sổ lỗi còn mở. |
| `README.md`, `docs/02_workflow.md`, `docs/03_implementation_readiness.md` | Ghi nhận 39 test/sáu test giao diện của đợt demo trước. | Đồng bộ 43 test/mười test giao diện và liên kết hướng dẫn tại changelog. |

**Phạm vi:** thay đổi cách trình bày và hướng dẫn, giữ nguyên engine, điều kiện YAML, schema và bệnh án giả định. Cảnh báo HATT boolean không sửa, chặn hoặc đổi kết quả suy diễn; nó đánh dấu kết quả hiện tại không đáng tin cậy để người review thấy lỗi.

### Tổng hợp những phần demo đã có trước đợt này

Demo Streamlit ở root `main.py` gọi `ClinicalRuleEngine` với JSON CANONICAL; bộ dữ liệu có 138 ca giả định, metadata/kỳ vọng được tách khỏi dữ liệu suy diễn. `requirements.txt` pin PyYAML 6.0.3 và Streamlit 1.50.0; dependency được cài trong `.venv`. Có sáu tầng, danh mục 14 đầu ra, trace/download JSON và ba SVG Archify dùng lại. `tests/` đã được bỏ khỏi `.gitignore` để test đi cùng source. Các mục này là tổng hợp trạng thái hiện có, không phải toàn bộ đều được sửa trong branch hiện tại.

### Kiểm tra trong đợt này

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -m unittest discover -s tests -v
git diff --check
```

Kết quả toàn bộ sau cập nhật: **43 test methods, 41 đạt và 2 `expectedFailure`**; mười test giao diện đạt. Hai expectedFailure tái hiện lỗi F-12 còn mở, không được diễn giải là đã sửa lỗi. `pip check` không có dependency hỏng. Thay đổi UI không tạo một lần đánh giá accuracy lâm sàng mới.

Kiểm tra live trên Edge trong đợt này gặp `ERR_CONNECTION_REFUSED` tại `127.0.0.1:8501`; chưa xác nhận trực quan bản cảnh báo mới trên trình duyệt. Bằng chứng giao diện hiện là AppTest. Cần chạy lại lệnh Streamlit bên dưới để xem bản cập nhật.

## Demo minh họa điều gì?

Demo là phòng thử nghiệm **hành vi của YAML/engine hiện tại**: quan sát phụ thuộc, so sánh điều kiện, dữ liệu thiếu, ưu tiên và xung đột trên bệnh án giả định. Nó không phải pipeline bệnh án hoàn chỉnh hay công cụ đưa ra chẩn đoán đã được thẩm định.

**14 đầu ra = 12 nhãn bệnh + 2 nhãn theo dõi:**

| Nhóm/tầng | Các đầu ra | Ưu tiên |
| --- | --- | --- |
| T1 | Sốc phản vệ | 1 |
| T2 | Phản vệ; Theo dõi phản vệ (Chưa đủ dữ kiện) | 2; theo dõi 3 |
| T3 | Mày đay cấp có dấu hiệu nặng; Mày đay cấp thông thường | 4; 5 |
| T4 | CIndU da vẽ nổi; Choline (do nóng); do lạnh; khác | 6 |
| T5 | CSU type 1; type 2; overlap; unknown | 7 |
| T6 | Chưa phân loại (Tiếp tục theo dõi) | 8 |

Engine có thể trả UNRESOLVED với priority 99; đó là trạng thái khi không có rule đích phù hợp, không phải một bệnh thứ 15. **CSU unknown** là tên endotype trong YAML khi đủ test âm, khác **UNKNOWN** của một điều kiện do thiếu/chưa đánh giá được dữ kiện. Nhánh cấp thường vẫn có trong danh mục nhưng chưa khả đạt với JSON hiện tại; bộ 138 ca chỉ tạo được 11 nhãn bệnh.

RAW validation, mapping, preprocessing, re-check lâm sàng, anonymization, batch và evaluator chưa được nối vào demo. Parser hiện chỉ kiểm tra JSON/object/envelope và loại NaN/Infinity. Không tự encode, điền âm tính hoặc suy giá trị còn thiếu.

## Các hiển thị trong Streamlit có ý nghĩa gì?

| Hiển thị | Cách đọc |
| --- | --- |
| **Khung lỗi đỏ đầu trang** | F-01/F-12 đang mở trên toàn bộ demo, không khẳng định chúng xảy ra với mọi ca. Cảnh báo hiện trước khi bấm phân loại. |
| **Đầu ra cần minh họa** ở sidebar | Lọc ca gốc liên quan theo metadata để dễ review; lựa chọn này không được truyền làm đáp án hay điều kiện vào engine. Ca được lọc có thể minh họa trường hợp FALSE/UNKNOWN, không nhất thiết cho nhãn đã chọn. |
| **Bệnh án giả định** | Chọn một ca cố định trong bộ 138 ca. Đổi ca sẽ nạp lại JSON và xóa kết quả cũ. |
| **JSON bệnh án** | Dữ liệu thực sự đưa vào engine. Chấp nhận object trực tiếp hoặc `{"du_lieu": {...}}`. `nhan`, `expected_engine` và metadata không dùng suy diễn. |
| **Kỳ vọng của ca gốc** | Kỳ vọng hành vi engine đã ghi cho ca nguyên bản, không phải ground truth y khoa. JSON đã sửa có cảnh báo kỳ vọng không tự cập nhật. |
| **Trạng thái / Ưu tiên** | Trạng thái là kết quả xử lý; priority nhỏ hơn được xét trước. Không phải xác suất, độ tin cậy hoặc mức điểm bệnh. |
| **Rule được chọn** | Rule đại diện cho kết quả; có thể là rule theo dõi, không nhất thiết kết luận bệnh. Có thể null khi bị chặn/xung đột. |
| **Rule cùng khớp** | Các rule đích TRUE trong toàn bộ lần chạy, kể cả ưu tiên thấp hơn; không có nghĩa tất cả là nhãn chính. |
| **Rule chặn / xung đột** | Rule UNKNOWN có thể đổi kết luận hoặc các rule TRUE khác nhãn cùng ưu tiên. Xem điều kiện/trace; không tự chọn theo thứ tự YAML. |
| **Trường cần bổ sung** | Trường thiếu/sentinel mà engine ghi nhận trong các phụ thuộc liên quan; chưa thay kiểm tra schema đầy đủ, và lý do chặn còn có hạn chế F-13. |
| **Sáu tầng suy diễn** | Kết quả điều kiện thực tế của ca đang chạy, tách hai pha tính phụ thuộc rồi chọn kết luận. Tầng thấp vẫn được tính, dù nhãn chính thuộc tầng cao. |
| **Điều kiện và bằng chứng** | Điều kiện YAML và trace từng phép kiểm tra; `all_of` = AND, `any_of` = OR, `not` = NOT, `ref_rule` = phụ thuộc một rule khác. Trace không phải toàn bộ giá trị bệnh án. |
| **14 đầu ra & điều kiện** | Danh mục bộ tri thức hiện có; việc xuất hiện trong danh mục không chứng minh nhánh hoạt động hoặc đã được duyệt chuyên môn. |
| **Workflow & diagram** | Ba SVG Archify mô tả quy trình đề xuất, luồng phân tầng và cây CSU; diagram không tự chạy hoặc đổi theo JSON hiện tại. |
| **YAML version / SHA-256 / tải JSON** | Nhận diện bộ luật và lưu kết quả/trace để đối chiếu; không phải chứng nhận đúng y khoa. File tải không phải bản bệnh án đầu vào. |

### Trạng thái cần phân biệt

| Trạng thái | Ý nghĩa trong demo |
| --- | --- |
| TRUE / FALSE / UNKNOWN | Trạng thái của **điều kiện**: đủ bằng chứng đúng / đủ bằng chứng sai / chưa đánh giá được. UNKNOWN không phải FALSE. |
| CLASSIFIED | Có nhãn theo YAML hiện tại; vẫn có thể sai do rule hoặc dữ liệu chưa được validate, như F-12 với HATT boolean. |
| INSUFFICIENT_DATA | Thiếu dữ kiện hoặc chưa đủ thời gian; chưa có kết luận bệnh. |
| NEEDS_REVIEW | Có xung đột hoặc lỗi dữ liệu cần rà soát; chưa có kết luận bệnh. |
| UNRESOLVED | Không có rule đích phù hợp theo đánh giá hiện tại; không chứng minh không mắc bệnh hoặc input đã hợp lệ. |
| INVALID_DATA / OUT_OF_SCOPE | Trạng thái thuộc validator/cohort của pipeline chưa triển khai. JSON sai hiện được UI báo lỗi nhập, không giả làm hai kết quả này. |

**Màu cảnh báo:** đỏ = lỗi đang mở, cần rà soát hoặc kết quả có thể sai; vàng = thiếu dữ kiện, chưa có rule, hạn chế của ca gốc hoặc kỳ vọng đã lệch input; xanh thông tin = giải thích trạng thái/phạm vi, không phải dấu xác nhận kết luận đúng.

## Cách dùng demo để check logic

1. Chạy bằng `.venv`, mở địa chỉ local:

   ```sh
   source .venv/bin/activate
   python -m streamlit run main.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
   ```

2. Chọn **Tất cả** để tìm đúng ID ca trong bảng dưới, đọc mô tả và kỳ vọng ca gốc; bấm **Phân loại và giải thích**.
3. Xem trạng thái trước nhãn, rồi rule được chọn/chặn. Trong tab sáu tầng, đối chiếu rule cơ sở, rule tham chiếu và trace; UNKNOWN ở tầng có thể đổi kết luận không được tự đi xuống bệnh nhẹ hơn.
4. Mỗi lần chỉ sửa **một biến**; thử trước/tại/sau ngưỡng, giá trị null, trường bị xóa hoặc kiểu sai. Giữ nguyên các dữ kiện sàng lọc đã xác nhận của ca đối chứng; không thêm giá trị âm để làm ca chạy qua.
5. Khi JSON khác ca gốc, đặt kỳ vọng riêng cho biến thể trước khi bấm chạy lại. Kiểm tra kết quả cũ đã được xóa. Với ngưỡng chưa chốt, ghi nhận vấn đề cần review, không tự kết luận rằng output hiện tại là đáp án đúng.
6. Lưu ID, JSON đã sửa, kỳ vọng, output thực tế, rule/trace, YAML version/hash, ngày và người review. Tải kết quả JSON để giữ trace; lưu input giả định riêng. Không đưa nhãn kỳ vọng vào dữ kiện bệnh án.

### Ca thực hành có thể tái hiện

| ID ca | Thử gì? | Hành vi hiện tại cần thấy |
| --- | --- | --- |
| `PV-01` | Dị nguyên nghi ngờ + da/hô hấp, HA bình thường | Phản vệ; R02/R03 cùng khớp, R02 đại diện cùng nhãn. |
| `SOC-NEN-139.9` | HA nền 200, đổi HATT từ 139,9 → 140 → 140,1 | Dấu `<0.7*nền`: sốc trước mốc, phản vệ tại/sau mốc; không tự đổi thành `<=`. HATT tính bằng mmHg trong ca mẫu. |
| `SOC-NEN-NOTNEEDED` | HATT 80, thiếu HA nền | Vẫn đủ rule sốc từ HATT <90; nhánh nền UNKNOWN không bắt buộc chặn khi OR đã TRUE. |
| `CAP-THUONG-OBJECT` | Sẩn phù object, các dấu nặng còn lại âm | NEEDS_REVIEW; mở trace thấy F-01, không sửa kỳ vọng thành cấp thường để che lỗi. |
| `CINDU-TIE` | Da vẽ nổi/cholinergic cùng dương | NEEDS_REVIEW; hai rule khác nhãn cùng ưu tiên, không chọn theo thứ tự file. |
| `CSU-T1-GD1` | CSU GĐ1, đổi 60 ngày theo dõi xuống 59 | Từ type 1 sang thiếu dữ kiện/theo dõi; mở rule ngày để đối chiếu. |
| `CSU-STELLA-False-39.9` | Stella FALSE nhưng IgE thấp | YAML vẫn vào GĐ2; cảnh báo F-08 vì khác workflow, không coi là tiêu chí đã được duyệt. |
| `SOC-MISSING-80` | HATT là chuỗi `"80"` | Engine TypeError được UI bắt, không có kết luận; đây không phải chuyển chuỗi thành số. |
| `SOC-INVALID-BOOL-TRUE` | HATT là boolean true | Engine vẫn trả sốc, UI báo đỏ “HATT boolean”; minh họa F-12, không phải bệnh án hợp lệ. |

## Lưu ý và lỗi còn mở

**F-01 và F-12 cần ưu tiên xử lý; làm nổi cảnh báo không sửa các lỗi này.**

| ID | Vấn đề còn mở |
| --- | --- |
| F-01 | Xung đột scalar/object làm cấp thường chưa khả đạt; cần thống nhất trường triệu chứng và cùng tập dấu nặng. |
| F-02–F-03 | Khoảng tuổi bỏ trống và mốc sáu tuần chưa chốt; không tự làm tròn hoặc quy đổi thời gian để chọn bệnh. |
| F-04–F-05 | Nghi ngờ/đã biết, thời điểm phản vệ và phạm vi rule sốc còn khác hoặc thiếu so với mô tả. |
| F-06 | CIndU khác chưa loại đủ test lạnh; Adrenergic/đa thể chưa được xử lý hoàn chỉnh. |
| F-07 | Thiếu validator enum/range và mapping; ký hiệu chưa rõ/sai có thể đi sai nhánh. |
| F-08 | Stella trong YAML dùng OR IgE thấp, khác workflow yêu cầu đầy đủ; chưa có nhánh loại cohort. |
| F-09–F-10 | Sàng lọc chung xuyên biểu mẫu, điều kiện cohort và đồng mắc chưa chốt. |
| F-11 | Fallback ASST chưa có phạm vi phù hợp; TRUE ở fallback không bảo đảm nó được chọn. |
| F-12 | Công thức thiếu kiểm tra kiểu HATT: crash với chuỗi/list/object hoặc nhãn sốc sai với bool. |
| F-13 | Nguyên nhân UNKNOWN có thể bị lẫn với lỗi kiểu từ nhánh đã đủ bằng chứng. |

Chi tiết và bằng chứng: [báo cáo logic](06_rule_logic_review.md), [workflow](02_workflow.md), [sổ quyết định](03_implementation_readiness.md). Nhãn **CLASSIFIED không tự đóng các gate chuyên môn**. Kết quả replay 53 bệnh án cũ là 34 INSUFFICIENT_DATA/19 NEEDS_REVIEW trước mapping, không phải accuracy mới. Chỉ dùng bệnh án giả định; chưa kiểm tra bệnh án thật, chưa xác nhận toàn bộ pipeline hay tiêu chí lâm sàng.
