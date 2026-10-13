# Workflow chuẩn cho hệ thống rule-based mề đay

**Trạng thái:** đặc tả quy trình đề xuất, ngày 09/10/2026; chưa phải pipeline đã triển khai. Tài liệu chuẩn hóa bản tóm tắt của người dùng và các phát hiện trong [explore_codebase.md](explore_codebase.md), đối chiếu [đặc tả luật](01_rules.md), `schema/`, từ điển dữ liệu và source tại commit `34a1ad1`.

> **Cập nhật 13/10/2026 (commit `f9ee49b`):** Pipeline đích, workflow quản lý gói luật và kế hoạch MVP hiện nằm trong [gói hướng dẫn triển khai](implementation-guide/README.md), chủ yếu ở [04 — Workflow và pipeline](implementation-guide/04-workflows-and-pipeline.md). Mục 0 tóm tắt thay đổi; mục 1–13 giữ đặc tả cũ để truy vết. Các link `explore_codebase.md`, `superpowers/plans/...`, `.archify/` và thư mục `tests/` được nhắc trong tài liệu này **không có trong Git** tại commit trên.

Mục tiêu là dữ liệu có hợp đồng rõ ràng, suy diễn đúng phụ thuộc và thứ tự ưu tiên, kết quả tái lập được. AI hỗ trợ đọc tài liệu, đề xuất và kiểm tra; người phụ trách dữ liệu/chuyên môn chốt ý nghĩa biến, mapping và tiêu chí nghiệp vụ. Khi chạy một bộ luật đã chốt, không cần AI tự diễn giải lại từng bệnh án.

## 0. Pipeline đích và thay đổi so với đặc tả 09/10

| Nội dung | Đặc tả 09/10 (mục 2) | Cập nhật theo gói hướng dẫn |
| --- | --- | --- |
| Phạm vi | Từng bệnh án, dữ liệu giả | Thêm demo public (ca giả) và import dữ liệu thật có auth/quyền, chạy theo batch/run |
| Pin phiên bản | Gắn version cho schema/mapping/luật | Resolve và **pin toàn bộ** package/schema/mapping/preprocess/build ngay lúc tiếp nhận, trước RAW validation; batch cố định version từ đầu đến cuối |
| Tiếp nhận | Tách nhãn thật | Tạo `import_id`/`record_id`; tách dữ kiện, định danh và ground truth thành ba luồng |
| Kiểm tra | RAW → preprocess → re-check CANONICAL | Giữ; sai contract → `INVALID_DATA`, mapping/cohort chưa chốt → `NEEDS_REVIEW`, sửa dữ liệu có nguồn rồi quay lại RAW |
| Bảo mật | Áp chính sách khi xuất/nghiên cứu | Áp identity/privacy policy trước engine, re-check bản dùng và lưu snapshot theo version đã pin |
| Đầu ra | Result + audit | Result envelope có `run_id`, `record_id`, `input_revision`, classifier/package version + hash; audit không chứa PII |
| Thay đổi luật | Chưa mô tả | Draft → validate → nghiệm thu/so sánh → bác sĩ duyệt → phát hành gói bất biến → kích hoạt → theo dõi/rollback ([05](implementation-guide/05-rule-versioning-and-change-management.md)) |
| AI | Không | Adapter chạy song song sau MVP, dùng cùng contract CANONICAL/result; không cần cho MVP |

```mermaid
flowchart TD
    DEMO["Demo public: ca giả"] --> RECEIVE["Nhận dữ liệu, tạo import_id"]
    REAL["Dữ liệu thật: auth + quyền"] --> RECEIVE
    RECEIVE --> PIN["Pin gói/schema/mapping/preprocess/build"]
    PIN --> SPLIT["Tách dữ kiện, định danh, ground truth"]
    SPLIT --> GT["Nhãn thật riêng cho evaluator"]
    SPLIT --> RAW["Validate RAW"]
    RAW -->|Sai| INVALID["INVALID_DATA"]
    RAW --> MAP["Mapping + preprocessing có provenance"]
    MAP --> CAN["Re-check CANONICAL"]
    CAN -->|Sai contract| INVALID
    CAN -->|Chưa chốt mapping/cohort| REVIEW["NEEDS_REVIEW"]
    CAN --> POLICY["Identity/privacy policy + snapshot"]
    POLICY --> ENGINE["Rule-based engine"]
    ENGINE --> RESULT["Result + explanation + version"]
    RESULT --> VIEW["Trực quan hóa + export theo quyền"]
    RESULT --> COMP["Evaluation"]
    GT --> COMP
    RESULT --> AUDIT["Audit không PII"]
    INVALID --> FIX["Sửa dữ liệu có nguồn"]
    REVIEW --> FIX
    FIX --> RAW
```

**Hiện trạng tại `f9ee49b`:** chỉ đoạn `ca giả/JSON → engine → result → Streamlit` đang chạy. `validate.py`, `pipeline.py`, `evaluate.py`, `validation_rules.yaml` trống; `preprocess.py` và `anonymize.py` có code nhưng chưa nối và còn lỗi.

**Lỗi chặn pipeline** — trạng thái cập nhật 13/10 ([chi tiết](implementation-guide/01-current-state-and-findings.md)):

| ID | Ưu tiên | Lỗi | ID cũ | Trạng thái |
| --- | --- | --- | --- | --- |
| TECH-01 | P1 | `<_formula` không kiểm tra kiểu HATT: list/object gây TypeError, bool trả sốc | F-12 | Đã sửa 13/10 |
| TECH-02 | P1 | `preprocess.py` điền tuổi 25, HATT 120 khi thiếu và ghi đè tuổi có sẵn | — | Đã sửa 13/10 |
| DATA-01 | P1 | Nhánh cấp thường không khả đạt do shape triệu chứng không thống nhất | F-01 | Mở, chờ chốt shape |
| SEC-01 | P1 | `anonymize.py` giữ `ma_benh_nhan` gốc; record thiếu ID cùng nhận token từ `UNKNOWN` | — | Đã sửa 13/10 (allowlist export còn mở) |
| TECH-03 | P2 | `missing_fields` báo sai operand thực sự thiếu trong công thức HATT | liên quan F-13 | Đã sửa 13/10 (phần công thức; F-13 còn mở) |
| QA-01 | P2 | Thư mục `tests/` không có trong Git dù tài liệu nêu 43 test | — | Đã thêm tests/, chưa có CI |

Thứ tự triển khai: Đợt 1 sửa lõi/hợp đồng dữ liệu → Đợt 2 pipeline/batch/registry → Đợt 3 website MVP → Đợt 4 pilot ([kế hoạch](implementation-guide/06-mvp-implementation-plan.md)). Ngưỡng y khoa, mapping và cohort vẫn chờ bác sĩ chốt ([quyết định mở](implementation-guide/09-decisions-and-templates.md)).

## 1. Hai phần công việc phải tách biệt

| Phần | Thực hiện khi nào | Đầu ra |
| --- | --- | --- |
| Xây dựng và chốt tri thức | Khi thêm nguồn dữ liệu hoặc đổi schema/luật | Hợp đồng dữ liệu, validation rules, mapping, công thức, ca kiểm thử và phiên bản đã chốt |
| Chạy trên bệnh án | Với từng bản ghi, sử dụng phiên bản cố định | Dữ liệu đã kiểm tra, kết quả điều kiện, nhãn/trạng thái, dấu vết audit; đánh giá riêng nếu có nhãn thật |

Không biến câu trả lời của AI thành mapping hoặc ngưỡng đang có hiệu lực. Chỗ chưa thống nhất được ghi thành vấn đề cần chốt; bản ghi phụ thuộc vấn đề đó chưa được kết luận bằng giả định.

## 2. Quy trình chuẩn từ tài liệu đến audit

### A. Chuẩn bị tri thức và kiểm thử

1. **Đọc và đối chiếu nguồn.** Với từng biến, ghi tên/path, ý nghĩa, kiểu, đơn vị, miền giá trị, điều kiện bắt buộc và cách biểu diễn missing/unknown/N/A. So sánh từ điển ↔ schema ↔ YAML ↔ fixtures; đánh dấu các lệch kiểu hoặc thiếu trường đã nêu trong báo cáo khám phá.
2. **Đề xuất validation rules và khoảng 20 ca kiểm thử.** Bao gồm cấu trúc JSON, kiểu/enum, khoảng số đã được xác nhận, quan hệ giữa trường, nguồn biến dẫn xuất, dữ liệu thiếu và các ranh giới phân loại. Ca có ngưỡng chưa chốt kiểm tra trạng thái chờ rà soát, không tự đặt đáp án lâm sàng.
3. **Chốt và đóng băng hợp đồng.** Người phụ trách xác nhận mapping, đơn vị, điều kiện nghiên cứu, ranh giới tuổi và chính sách bảo mật. Gắn phiên bản cho schema, validation, preprocessing, mapping và tri thức; kiểm tra YAML nạp được, rule ID duy nhất, tham chiếu tồn tại và không có vòng phụ thuộc.
4. **Triển khai validate + preprocess theo hợp đồng.** Đây là bước phát triển sau, chưa thực hiện trong tác vụ viết tài liệu này. Script phải kiểm tra và làm sạch dữ liệu, tính biến từ nguồn xác định, trả lỗi có cấu trúc; encoding chỉ là một phần của chuẩn hóa. Chạy các ca hồi quy trước khi dùng phiên bản mới.

### B. Xử lý từng bệnh án

5. **Nhận dữ liệu và tách nhãn thật.** Giữ bản gốc trong phạm vi truy cập phù hợp. `nhan`, tên file và các trường chẩn đoán/đáp án không được dùng để tạo biến suy diễn; nhãn thật chỉ dành cho đánh giá sau cùng. Khi gộp fixtures, dùng khóa nguồn-file + `id` để không mất ca do ID trùng.
6. **Validate đầu vào.** Kiểm tra JSON/envelope, cấu trúc nguồn và khả năng chuẩn hóa theo mapping đã duyệt. Đây là kiểm tra RAW, không áp toàn bộ schema CANONICAL trước khi chuyển các dạng legacy hợp lệ; cũng không bắt có sẵn chẩn đoán đích. Bản ghi sai dữ liệu → cách ly, ghi lỗi đã lọc định danh, yêu cầu sửa và chạy lại; không âm thầm bỏ ca khỏi mẫu số.
7. **Làm sạch, chuẩn hóa và tính biến.** Chỉ dùng mapping đã chốt. Chuẩn hóa ký hiệu test, object/list, bảng triệu chứng và số theo đúng nguồn; tính tuổi tại ngày khám, HATT thấp nhất từ số đo hợp lệ, thời gian khởi phát/theo dõi nếu đủ dữ kiện. Không thay tuổi thiếu bằng 25, HATT thiếu bằng 120 hoặc thời gian thiếu bằng 0/1.
8. **Re-check sau preprocessing.** Áp hợp đồng/schema CANONICAL cho kiểu, range, đơn vị, trạng thái thiếu, mapping, quan hệ trường và các ca biên. Mỗi biến dẫn xuất phải có nguồn/công thức; trạng thái thiếu chỉ chặn những kết luận thực sự phụ thuộc nó. Dữ liệu sai → quay về sửa; dữ liệu chưa đủ để chọn kết luận → ghi các trường cần bổ sung. RAW/CANONICAL là hai thời điểm kiểm tra trong các module hiện có, không yêu cầu tạo hai tầng framework.
9. **Bảo mật theo mục đích sử dụng.** Nếu xuất dữ liệu hoặc dùng cho nghiên cứu, áp dụng chính sách đã chốt: token ổn định khi cần liên kết, bỏ mã gốc và thông tin nhận diện khỏi bản xuất, rà soát trường tự do/bảng lồng nhau. Randomize tên chỉ khi tạo dữ liệu giả; không sửa số đo hoặc randomize độc lập ID giữa các lần khám. Tính biến phụ thuộc ngày trước khi lược bỏ ngày, rồi re-check bản thực sự đưa vào suy diễn/xuất. Không ghi salt, khóa bí mật hoặc định danh gốc vào log audit.
10. **Tính phụ thuộc rồi chọn kết luận.** Dùng cache riêng cho bản ghi, tính các điều kiện được tham chiếu trước khi xét luật phụ thuộc; sau đó mới áp dụng thứ tự các tầng ở mục 4. Không dùng `priority` thay cho thứ tự giải quyết phụ thuộc.
11. **Ghi audit và đánh giá.** Ghi phiên bản, mapping/công thức đã dùng, trường lỗi/thiếu, kết quả điều kiện và lý do chọn/dừng. Nếu có ground truth, so sánh sau suy diễn với ánh xạ nhãn đã chốt; báo cáo từng lớp, ca lỗi, ca cần bổ sung và kiểm tra khả năng chạy lại.

### Diagram Archify: quy trình chuẩn

[Mở diagram HTML tương tác](../.archify/workflow-me-day-20261009-214006/quy-trinh/quy-trinh.html) · [Candidate JSON](../.archify/workflow-me-day-20261009-214006/quy-trinh/candidate.json)

![Quy trình chuẩn: chốt dữ liệu và validation, xử lý bản ghi, suy diễn, audit](diagrams/rule-based-quy-trinh.svg)

Các nhánh cách ly/thiếu dữ kiện cũng ghi audit đã lọc PII. Mũi tên “Re-check bản dùng” bao gồm kiểm tra dữ liệu sau bước bảo mật; bước bảo mật áp dụng theo chính sách, không mặc định randomize tất cả bệnh án.

## 3. Hợp đồng chuẩn hóa và trạng thái thiếu

### Các mapping phải được chốt trước khi viết script

| Nhóm | Đích cần thống nhất | Điều không được suy đoán |
| --- | --- | --- |
| Triệu chứng | Object có `danh_sach_chon`; giữ danh sách lựa chọn hợp lệ | Không dùng substring của ghi chú như bằng chứng dương; không coi list/chuỗi legacy là object đã hợp lệ |
| Tác nhân nghi ngờ | Tách trạng thái `co_khong` và phần ghi rõ theo hợp đồng | Không tự suy ra “dị nguyên đã biết” từ chuỗi mô tả nghi ngờ |
| Lưới sẩn phù cấp | Giữ array theo schema; tổng hợp các dạng tổn thương ở bước preprocess với tên/path đã chốt | Không đọc `array.dang_ton_thuong` như object đơn |
| Test ASST/ELISA/kích thích | Ví dụ đề xuất: `(-)` → `(−)`, giữ `(+)`, tách `(+/−)` là chưa rõ | Không coi thiếu test hoặc kết quả chưa rõ là âm tính |
| Số và đơn vị | Chuyển chuỗi số khi hợp đồng cho phép; quy đổi giờ/tuần từ đơn vị có nguồn | Không đoán đơn vị từ con số hoặc ép `unknown`, `N/A`, `-1` thành số đo |
| Ngày và biến dẫn xuất | Tuổi tại ngày khám; số ngày theo dõi từ mốc được xác nhận | Không dùng ngày chạy chương trình thay ngày khám hoặc tuổi xấp xỉ gây khoảng trống |
| Trường cấp ↔ phản vệ | Mapping có nguồn giữa các biểu mẫu cho sàng lọc chung | Không bỏ sàng lọc phản vệ chỉ vì bản ghi không mang hậu tố `_pv` |
| Nhãn đánh giá | `Cấp nặng/thường` ↔ nhãn đầy đủ của engine theo bảng riêng | Không đưa mapping nhãn thật vào preprocessing dữ kiện bệnh án |

Đây là danh sách cần thống nhất, không phải thông báo rằng mapping đã được duyệt hoặc đã viết vào YAML. Không yêu cầu encoding số cho giá trị mà engine có thể so sánh trực tiếp; nếu encoding cần thiết, bảng mã phải có phiên bản và giữ nghĩa của các trạng thái thiếu.

### Ba trạng thái của một điều kiện

- **TRUE:** có bằng chứng hợp lệ rằng điều kiện đúng.
- **FALSE:** có bằng chứng hợp lệ rằng điều kiện không đúng.
- **UNKNOWN:** dữ kiện thiếu, chưa biết, không áp dụng hoặc mapping/ngưỡng chưa giải quyết nên chưa thể đánh giá điều kiện này. Vẫn giữ riêng nguyên nhân missing, unknown và N/A trong dữ liệu/audit.

Với AND: có FALSE thì FALSE; tất cả TRUE mới TRUE; còn lại UNKNOWN. Với OR: có TRUE thì TRUE; tất cả FALSE mới FALSE; còn lại UNKNOWN. NOT UNKNOWN vẫn UNKNOWN. Ví dụ một test IgG dương đủ làm nhóm IgG dương dù test kia chưa biết; hai test IgG không có kết quả không đủ để nói nhóm IgG âm.

**Quy tắc chọn kết luận:** UNKNOWN ở một tầng có thể thay đổi kết luận ưu tiên phải chuyển sang bổ sung/rà soát, không tự đi theo nhánh FALSE xuống bệnh nhẹ hơn. UNKNOWN ở nhánh không ảnh hưởng kết luận đang đủ bằng chứng không bắt buộc chặn mọi xử lý. Lõi engine đã triển khai quy tắc ba trạng thái và chọn kết luận theo hợp đồng này; mapping và tiêu chí áp dụng vẫn chờ chốt ở các gate pipeline.

## 4. Logic các tầng: phụ thuộc trước, ưu tiên sau

### Pha 1 — đánh giá điều kiện, chưa trả nhãn

- Tính `R01-PV`, `R02-PV`, `R03-PV` rồi mới dùng các kết quả cần thiết cho `R-SOC`. Quan hệ hiện có của `R-SOC` là `R02-PV OR R03-PV`, không tự mở rộng sang `R01-PV` khi chưa chốt chuyên môn.
- Tính `R-SANGLOC-CAP` trước cấp nặng/thường; tính `R-CindU-00` trước các thể CIndU.
- Tính `R-CSU-00` → `R-GD-01`/`R-GD-02` → luật type/overlap/unknown; nếu áp dụng nhánh loại nghiên cứu, bổ sung hợp đồng cho `R-GD-03` đang chỉ có trong tài liệu.
- Không trả ngay nhãn phản vệ khi chưa đánh giá xong khả năng sốc; không để luật cơ sở mặc định priority 99 khiến luật đích đọc cache rỗng. Cache thiếu là chưa đánh giá, không phải FALSE.

### Pha 2 — chọn kết luận hoặc điểm dừng

| Tầng nghiệp vụ | Ưu tiên trong YAML hiện tại | Nhánh và điều kiện chính |
| --- | --- | --- |
| **T1 — Sốc phản vệ** | 1 | `R-SOC`: điều kiện phản vệ được tham chiếu + HATT theo tuổi/nền đủ bằng chứng. Khi TRUE, không chọn nhãn tầng thấp hơn. |
| **T2 — Phản vệ / cảnh báo** | 2; cảnh báo 3 | `R01-PV`/`R02-PV`/`R03-PV`; xét cảnh báo `R-PV-THEODOI` sau khi không đạt sốc/phản vệ. Cảnh báo khác kết luận bệnh và phải nêu lý do. |
| **T3 — Mày đay cấp** | Nặng 4; thường 5 | Qua `R-SANGLOC-CAP`: sẩn phù, dạng tổn thương hợp lệ, ảnh và thời gian theo hợp đồng repo. Xét dấu nặng trước; thường chỉ khi có sẩn phù và đủ bằng chứng loại các dấu nặng. |
| **T4 — CIndU** | 6 | Qua sàng lọc mạn > 6 tuần, có yếu tố kích thích và điều kiện áp dụng; phân thể theo test. Nhóm “khác” cần âm tính rõ với các thể phải loại và test khác dương. |
| **T5 — CSU** | 7 | Qua điều kiện CSU/nhóm nghiên cứu đã chốt, sau đó ASST, thời gian theo dõi/Stella và ELISA theo mục 5. CIndU thiếu test không tự được coi là CSU đơn thuần. |
| **T6 — Ngoại lệ** | Fallback 8; engine unresolved 99 | Thiếu dữ kiện, chưa có luật phù hợp hoặc ngoài phạm vi áp dụng. Không dùng thiếu ASST làm fallback chung cho mọi bệnh án cấp/phản vệ. |

Các trạng thái lỗi/UNKNOWN có thể dừng sớm ở bất kỳ bước nào, không phải đợi đến T6. Thứ tự trên là thứ tự chọn kết luận chính; các luật cùng tầng không được tự quyết bằng thứ tự xuất hiện trong YAML khi nhiều thể cùng khớp. Nếu cần một nhãn chính, phải chốt quy tắc tie-break và giữ các kết quả cùng khớp trong trace. Từ điển cho phép CSU đồng mắc CIndU; việc biểu diễn đồng mắc còn cần chính sách riêng.

### Diagram Archify: luồng phân tầng

[Mở diagram HTML tương tác](../.archify/workflow-me-day-20261009-214006/phan-tang/phan-tang.html) · [Candidate JSON](../.archify/workflow-me-day-20261009-214006/phan-tang/candidate.json)

![Luồng phân tầng: giải quyết UNKNOWN, sốc phản vệ, phản vệ, cấp nặng/thường, CIndU, CSU và ngoại lệ](diagrams/rule-based-phan-tang.svg)

Nhánh FALSE trong diagram luôn là **đã xác minh không đạt**. Cổng UNKNOWN đầu sơ đồ thể hiện việc kiểm tra dữ kiện chưa rõ có chặn kết luận ưu tiên hay không; thiếu dữ kiện không được tự chuyển thành nhánh “Không”.

## 5. Cây CSU và các điểm dừng

### Điều kiện vào cây

Theo đặc tả repo, chốt `R-CSU-00` gồm CSU đơn thuần, diễn biến mạn, tuổi ≥ 16, ngừng kháng histamine ≥ 8 ngày, ngừng corticoid ≥ 30 ngày, lưu huyết thanh và các điều kiện loại trừ. Tên trường và nguồn tính phải thống nhất; hiện schema/fixtures thiếu một số biến và YAML chưa kiểm tra toàn bộ điều kiện này.

Không đạt điều kiện nghiên cứu là **ngoài phạm vi phân type của quy trình**, không chứng minh bệnh nhân không mắc CSU. Nếu điều kiện chưa biết, yêu cầu bổ sung thay vì kết luận “không đạt”.

### Nhánh ASST dương — giai đoạn 1

1. `ASST = (+)` → `R-GD-01`.
2. Chưa đủ 60 ngày theo dõi → tiếp tục theo dõi; thiếu mốc/thời gian → bổ sung dữ kiện.
3. Khi đủ thời gian, xác định nhóm IgG kháng FcεRIα/IgE: dương khi ít nhất một test dương; âm khi **cả hai** test âm. Kết hợp với IgE kháng IL-24 theo bảng dưới.

| Nhóm IgG | IgE kháng IL-24 | Kết luận / rule ID |
| --- | --- | --- |
| Âm | Dương | CSU type I — `R-CSU-T1-01` |
| Dương | Âm | CSU type IIb — `R-CSU-T2-01` |
| Dương | Dương | CSU overlap — `R-CSU-OVL-01` |
| Âm | Âm | CSU unknown — `R-CSU-UNK-01` |
| Chưa xác định nhóm IgG hoặc IL-24 | Chưa đủ để dùng một hàng trên | Bổ sung xét nghiệm; không phải CSU unknown |

### Nhánh ASST âm — giai đoạn 2

1. `ASST = (−)` → kiểm tra **đầy đủ Stella** theo đặc tả repo: không dị ứng đồng mắc, IgE toàn phần < 40 với số đo hợp lệ và test lẩy da dị nguyên hô hấp âm. Không thay toàn bộ Stella bằng riêng IgE < 40 hoặc giá trị `-1`.
2. Stella FALSE → loại khỏi nhóm nghiên cứu theo hợp đồng `R-GD-03`; Stella UNKNOWN → bổ sung. Stella TRUE mới vào `R-GD-02`.
3. IgE kháng IL-24 dương → CSU type I (`R-CSU-T1-02`); âm → CSU unknown (`R-CSU-UNK-02`); thiếu/chưa rõ → bổ sung. Không áp ngầm điều kiện 60 ngày của giai đoạn 1 sang giai đoạn 2.

ASST thiếu hoặc `(+/−)` cũng đi đến bổ sung/rà soát. **CSU unknown là kết luận endotype từ các test âm đã đủ bằng chứng**, khác với thiếu test, chưa đủ thời gian và ngoài nhóm nghiên cứu.

### Diagram Archify: cây CSU

[Mở diagram HTML tương tác](../.archify/workflow-me-day-20261009-214006/cay-csu/cay-csu.html) · [Candidate JSON](../.archify/workflow-me-day-20261009-214006/cay-csu/candidate.json)

![Cây CSU: điều kiện vào nhóm, ASST, giai đoạn 1/2 và phân type theo ELISA](diagrams/rule-based-cay-csu.svg)

Các mũi tên trong cây thể hiện điều kiện xác định; nhánh UNKNOWN của ASST được vẽ riêng. UNKNOWN ở điều kiện vào nhóm, Stella, thời gian hoặc ELISA đều dừng để bổ sung/rà soát theo mục 3, không đi theo FALSE hay suy ra type. Ở giai đoạn 1, cặp dấu trên mũi tên lần lượt là **IgG / IL-24**.

## 6. Những điểm chuyên môn phải chốt trước khi triển khai

| Điểm từ báo cáo khám phá | Quy tắc thực hiện trong workflow |
| --- | --- |
| Tuổi thập phân có khoảng trống (10,11), (17,18); ngày sinh nhật 18 có thể thành 17,999 | Chốt cách tính tuổi lịch và khoảng tuổi liên tục; chưa chốt thì không tự đưa ra ngưỡng thay thế. |
| Luật cấp dùng `<=1008` giờ, mạn dùng `>6` tuần; tiêu đề tài liệu ghi “<6 tuần” | Trong diagram giữ dấu `<=` của điều kiện hiện có để không giấu khác biệt; quyết định đúng tại sáu tuần phải được chốt và kiểm thử. |
| Ảnh là điều kiện sàng lọc cấp trong repo | Chốt đây là điều kiện nghiên cứu hay điều kiện bắt buộc phân loại; thiếu ảnh không tự được coi là không mắc bệnh. |
| “Ngứa nhiều” / “phù mạch đáng kể” không khớp kiểu object và enum | Chốt biến mức độ/dấu nặng, không lấy chẩn đoán đã có làm bằng chứng đầu vào. |
| Dị nguyên nghi ngờ khác dị nguyên đã biết; thiếu điều kiện thời điểm ở luật phản vệ | Chốt trường và tiêu chí thời gian; không bổ sung ngưỡng y khoa do AI tự suy đoán. |
| Adrenergic, test khác và nhiều test CIndU cùng dương chưa thống nhất | Chốt ánh xạ, điều kiện loại thể và cách biểu diễn nhiều kết quả; không coi test thiếu là âm. |
| Điều kiện loại trừ/Stella khác nhau giữa tài liệu và YAML | Chốt mục đích phân loại bệnh hay tuyển nhóm nghiên cứu; không trộn hai loại kết luận. |

Các tiêu chí số trên được dẫn từ repo để mô tả luồng, không phải bộ hướng dẫn y khoa mới được thẩm định bên ngoài. Các phép kiểm tra cấu trúc dữ liệu không thay thế việc chốt tiêu chí chuyên môn.

## 7. Đặc tả 20 ca kiểm thử tối thiểu

Đây là **đặc tả nghiệm thu toàn pipeline**, chưa được thực thi đầy đủ. Ngày 10/10/2026 đã bổ sung [138 ca kiểm tra trực tiếp lõi](../data/synthetic/rule_logic_cases.json) và [test hồi quy](../tests/test_rule_logic_cases.py); phạm vi và sai khác được ghi ở [báo cáo kiểm tra logic](06_rule_logic_review.md). Mỗi ca/biến thể nghiệm thu vẫn cần rule/mapping version và kết quả kỳ vọng theo hợp đồng đã chốt; test hành vi YAML hiện tại không thay nghiệm thu workflow.

| ID | Tình huống | Kỳ vọng |
| --- | --- | --- |
| RB-01 | Bản ghi hợp lệ đúng cấu trúc và đơn vị | Qua validation/re-check; các giá trị lâm sàng giữ nguyên nghĩa. |
| RB-02 | JSON hỏng, file rỗng hoặc thiếu lớp `du_lieu` | INVALID_DATA; lỗi có vị trí, không đoán nội dung để tiếp tục. |
| RB-03 | Triệu chứng/tác nhân dạng chuỗi hoặc list legacy | Chỉ chuyển khi có mapping đã chốt; ngoài mapping thì cách ly/rà soát. |
| RB-04 | Lưới `dac_diem_san_phu_cap` có nhiều object | Tổng hợp đúng các dòng hợp lệ; không dùng đường dẫn qua array như dict. |
| RB-05 | Test `(-)`, `(−)`, `(+)`, `(+/−)` và giá trị ngoài enum | Hai dạng âm chỉ tương đương theo mapping đã chốt; dạng chưa rõ không thành âm. |
| RB-06 | `null`, `unknown`, `-1`, `N/A`, chuỗi rỗng ở trường số | Giữ nguyên nhân thiếu; không ép số hoặc để IgE -1 thỏa tiêu chí IgE thấp. |
| RB-07 | HATT < HATTr, số âm hoặc đơn vị huyết áp không rõ | INVALID_DATA hoặc rà soát đơn vị; không âm thầm sử dụng. |
| RB-08 | Thiếu HATT/nền hoặc trường đơn lẻ mâu thuẫn bảng sinh hiệu | Không tự điền 120; áp chính sách nguồn ưu tiên/min đã chốt và ghi trace. |
| RB-09 | Tuổi 10,5; 17,5; đúng sinh nhật 18; ngày sinh tương lai | Không rơi vào khoảng trống do xấp xỉ; không sửa ngày sai thành tuổi 0. Ngưỡng chưa chốt → NEEDS_REVIEW. |
| RB-10 | Đúng sáu tuần, trước/sau mốc và giờ/tuần mâu thuẫn | Theo ranh giới đã chốt; không có hai cách quy đổi cho cùng dữ kiện. |
| RB-11 | Cờ cha “Không” nhưng danh sách con có triệu chứng dương | Phát hiện mâu thuẫn; không chọn một bên theo suy đoán. |
| RB-12 | Bệnh án cấp có dữ kiện cần sàng lọc phản vệ nhưng không có hậu tố `_pv` | Mapping chung đã chốt bảo đảm đánh giá; không bỏ sót do khác tên biểu mẫu. |
| RB-13 | `R-SOC` tham chiếu `R02-PV`/`R03-PV` xuất hiện sau; hoặc config có ref sai/vòng | Phụ thuộc hợp lệ tính trước sốc; ref sai/vòng chặn nạp config, không trả FALSE giả. |
| RB-14 | Ca đồng thời khớp sốc/phản vệ/cấp nặng | Sốc là nhãn chính nếu đủ bằng chứng; trace vẫn giữ các điều kiện cùng khớp. |
| RB-15 | Tầng nguy hiểm UNKNOWN, tầng thấp có vẻ khớp | NEEDS_REVIEW/INSUFFICIENT_DATA; không kết luận bệnh nhẹ hơn. |
| RB-16 | Cấp đủ sàng lọc: từng dấu nặng, đủ loại dấu nặng, hoặc dấu nặng còn thiếu | Nặng/thường/thiếu dữ kiện tách biệt; không đọc object bằng phép bằng chuỗi. |
| RB-17 | CIndU: test khác dương, test phổ biến thiếu/âm; Adrenergic; nhiều test dương | Thiếu không thành âm; các thể và tie-break/đồng mắc theo chính sách đã chốt. |
| RB-18 | CSU ASST dương: <60 ngày, thiếu ngày/ELISA, đủ ngày với bốn tổ hợp IgG–IL24 | Theo dõi/bổ sung hoặc đúng bốn endotype; thiếu không thành CSU unknown. |
| RB-19 | CSU ASST âm: Stella FALSE/UNKNOWN/TRUE; IL-24 dương/âm/chưa rõ | Ngoài nghiên cứu/bổ sung/type I/unknown đúng nhánh; IgE thấp riêng lẻ không thay Stella. |
| RB-20 | Tên trắng, thiếu/trùng ID, xuất PII và chạy lại cùng phiên bản | Không crash/gộp bệnh nhân; bản xuất/log không lộ PII; kết quả và dấu vết tái lập được. |

Sau bộ ca tối thiểu, đánh giá lại toàn bộ **53 fixtures** theo hợp đồng mới, không dùng accuracy lịch sử làm tiêu chí duy nhất. Ghi số ca từng trạng thái và từng lớp, recall của sốc phản vệ, ma trận nhầm lẫn; giữ cả ca lỗi/chưa đủ dữ kiện trong báo cáo.

## 8. Output và audit để tái lập

### Trạng thái đầu ra đề xuất

| Trạng thái | Ý nghĩa |
| --- | --- |
| `CLASSIFIED` | Đã đủ bằng chứng cho kết luận bệnh/endotype theo phiên bản luật. |
| `INSUFFICIENT_DATA` | Chưa đủ dữ kiện/xét nghiệm hoặc chưa đủ thời gian; liệt kê điều kiện chặn. |
| `INVALID_DATA` | Dữ liệu không hợp lệ; không dùng để kết luận bệnh. |
| `NEEDS_REVIEW` | Mapping/ngưỡng mơ hồ, dữ liệu cần xác nhận hoặc nhiều nhánh chưa có chính sách chọn. |
| `OUT_OF_SCOPE` | Không đáp ứng phạm vi nhóm nghiên cứu/quy trình; không phủ định bệnh. |
| `UNRESOLVED` | Dữ liệu đủ cho các kiểm tra áp dụng nhưng không có luật đích phù hợp. |

Lõi engine hiện trả `CLASSIFIED`, `INSUFFICIENT_DATA`, `NEEDS_REVIEW` hoặc `UNRESOLVED` theo kết quả luật và mức ưu tiên. `INVALID_DATA` và `OUT_OF_SCOPE` vẫn thuộc trách nhiệm validator/cohort ở pipeline; đây không phải kết quả mà lõi hiện tự suy ra từ dữ liệu thô.

Quyết định trạng thái theo dữ kiện cụ thể: vi phạm hợp đồng dữ liệu → `INVALID_DATA`; mapping/ngưỡng chưa chốt hoặc các kết luận cùng ưu tiên khác nhau → `NEEDS_REVIEW`; chỉ thiếu dữ kiện đã có hợp đồng → `INSUFFICIENT_DATA`. `OUT_OF_SCOPE` cần bằng chứng không đạt tiêu chí áp dụng, không dùng cho trường hợp chưa biết. `UNRESOLVED` chỉ dùng khi các điều kiện áp dụng đều đã đánh giá FALSE, không còn UNKNOWN có thể đổi kết luận. Khi nhiều vấn đề cùng xảy ra ở pipeline, ưu tiên lỗi dữ liệu rồi vấn đề cần rà soát rồi dữ kiện thiếu; engine lõi không thay cho validator đầy đủ.

### Nội dung phải lưu cho mỗi lần chạy

- Khóa bản ghi đã bảo mật, nguồn/batch và phiên bản schema, validation, mapping, preprocessing, bộ luật; hash cấu hình, phiên bản code và thời điểm đánh giá cố định khi ảnh hưởng phép tính.
- Mỗi phép chuyển đổi thực sự áp dụng: trường nguồn → trường đích, mapping/công thức/đơn vị, lý do chuẩn hóa và trạng thái thiếu. Giá trị nhận diện được lược bỏ; log lỗi cũng theo chính sách này.
- Kết quả TRUE/FALSE/UNKNOWN của các điều kiện được xét, thứ tự phụ thuộc, các luật cùng khớp, `matched_rule_id`, tầng/priority, nhãn chính/trạng thái và các trường cần bổ sung. Văn bản `decision_trace` tĩnh không đủ thay thế dấu vết này.
- Với đánh giá: bảng ánh xạ nhãn, ID ca lỗi/thiếu, số ca được nhận/xử lý và các chỉ số từng lớp. Seed chỉ dùng để tái lập việc tạo fixtures giả khi cần; không lưu bí mật tạo token trong log chung.

Gói tái lập gồm dữ liệu đầu vào đã bảo mật theo chính sách, cấu hình phiên bản cố định và trace. Cùng input, code, mapping, bộ luật và mốc đánh giá phải cho cùng output; nếu không, ghi rõ nguồn không xác định thay vì tuyên bố tái lập.

## 9. Hiện trạng repo và bằng chứng diagram

`pipeline.py`, `validate.py`, `evaluate.py` và `validation_rules.yaml` vẫn trống; fixtures chưa thống nhất schema. Phần lõi đã sửa lỗi cú pháp YAML, kiểm tra cấu hình, tính phụ thuộc, giữ UNKNOWN và chọn đầu ra theo ưu tiên. Workflow vẫn là đích cho toàn pipeline, không xác nhận rằng các gate dữ liệu/chuyên môn trong [explore_codebase.md](explore_codebase.md) đã được giải quyết.

Ba diagram dùng **Archify workflow v2**, nguồn repository được pin tại commit `34a1ad10ba0062bc672d16eb3ed86b2b27d5b5d6`, liên kết source ở chế độ local-only. Candidate và HTML nằm trong `.archify/workflow-me-day-20261009-214006/`; các SVG trong `docs/diagrams/` là bản tĩnh trích từ hình học/CSS của HTML để nhúng Markdown, không thay cho receipt kiểm tra HTML.

| Diagram | Kiểm tra cấu trúc/artifact | Receipt cuối |
| --- | --- | --- |
| Quy trình chuẩn | `validate`, `deliver`, strict `check`: 9/9 showcase; 0 lỗi, 0 cảnh báo ở các gate này | [Receipt](../.archify/workflow-me-day-20261009-214006/quy-trinh/chrome-20261009-230736/quy-trinh.finalize-summary.json) |
| Luồng phân tầng | Như trên | [Receipt](../.archify/workflow-me-day-20261009-214006/phan-tang/chrome-20261009-230736/phan-tang.finalize-summary.json) |
| Cây CSU | Như trên; bản giữ các nhánh xác định, UNKNOWN ở mọi cổng được quy định bằng văn bản | [Receipt](../.archify/workflow-me-day-20261009-214006/cay-csu/chrome-20261009-230736/cay-csu.finalize-summary.json) |

**Xác nhận thủ công:** Người dùng xác nhận diagram đã được sử dụng thành công ngày 09/10/2026. Đây là xác nhận sử dụng/hiển thị của người dùng, không phải kết quả browser-check tự động hay xác nhận toàn bộ tiêu chí chuyên môn.

**Giới hạn kiểm tra tự động:** Đã chạy lại cả ba diagram với Google Chrome `155.0.8059.40` tại Applications; `browser-check` thất bại trước khi đo giao diện vì pipe DevTools kết thúc. Crash log của Chrome xác nhận `SIGABRT` tại `_RegisterApplication` của macOS. `finalize` chưa đạt toàn bộ gate; receipt vẫn giữ `visual_review: not_requested`. Không thay receipt thành PASS theo xác nhận thủ công. Vấn đề này không chặn việc lập kế hoạch lõi Python. Nội dung diagram là tiếng Việt; Viewer cố định dùng fallback tiếng Anh. Phép kiểm tra phiên bản Archify không truy cập được cache.


## 10. Cấu hình Chrome đã có trong Applications

Máy đã có Google Chrome `155.0.8059.40`; cấu hình hiện dùng browser này, không yêu cầu tải thêm Chrome for Testing. Executable đã được kiểm tra bằng `--version`. Extension ChatGPT đã kết nối, nhưng lệnh kiểm tra DevTools của Archify không phụ thuộc extension.

Từ thư mục gốc repository, kích hoạt cấu hình cho phiên Terminal:

```sh
source .tools/chrome-for-testing/env.sh
"$ARCHIFY_CHROME" --version
node /Users/mercedes/.agents/skills/archify/bin/archify.mjs browser-check .archify/workflow-me-day-20261009-214006/phan-tang/phan-tang.html --require-provenance --out-dir .archify/workflow-me-day-20261009-214006/phan-tang/terminal-check --json
```

`ARCHIFY_CHROME` trỏ đến `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`. File cấu hình giữ trong thư mục local đã bỏ qua trong Git; chỉ có hiệu lực với shell đã source. Không thay Node hoặc Edge, không sửa cấu hình shell toàn máy. Archify tạo `--user-data-dir` tạm riêng cho mỗi lượt, không dùng profile đăng nhập Chrome hằng ngày.

**Trạng thái hiện tại:** Cấu hình executable đã xác minh; kiểm tra cấu trúc 9/9 đạt, kiểm tra headless chưa đạt. Công cụ Browser Use cũng từ chối mở HTML cục bộ qua `file://` vì chỉ cho phép HTTP/HTTPS; không dùng cách vòng qua chính sách này. Các receipt Chrome mới được liên kết ở mục 9. Lệnh trên dành cho việc thử lại từ Terminal thông thường; chưa xác nhận kết quả ngoài môi trường chạy hiện tại.

## 11. Phạm vi đợt đầu đã chọn và hợp đồng lõi kỹ thuật

Người dùng chọn **lõi kỹ thuật trước, pipeline sau**. [Rà soát mức sẵn sàng](03_implementation_readiness.md) ghi những quyết định còn mở; [plan lõi](superpowers/plans/2026-10-09-rule-engine-core.md) chỉ triển khai cơ chế nạp luật, phụ thuộc, TRUE/FALSE/UNKNOWN, chọn kết luận và trace. Chưa triển khai batch, mapping bệnh án, validator schema, anonymizer hoặc evaluator trong đợt này.

- Giữ `ClinicalRuleEngine(rules_file_path: str)` và `classify_patient(patient_data: Dict[str, Any]) -> Dict[str, Any]`; đầu vào lõi là object CANONICAL. Không chuyển cấu trúc legacy trong engine.
- `True`, `False`, `None` biểu diễn ba trạng thái bằng giá trị Python sẵn có. Trường thiếu/null và sentinel chung của repo (`unknown`, `N/A`, chuỗi rỗng, số `-1`) không làm bằng chứng dương/âm; kiểu sai hoặc số không hữu hạn được ghi lý do rà soát. `== null`/`!= null` trong cấu hình là kiểm tra trống/có giá trị rõ ràng, không phải xét nghiệm âm tính.
- `contains`/`contains_any` chỉ xét phần tử bằng nhau trong list hợp lệ; không stringify object hay tìm substring của văn bản tự do. So sánh số và công thức chỉ dùng số hữu hạn, không coi boolean là số; hai công thức huyết áp hiện có được nhận diện chính xác, không `eval` và không tự điền tuổi/nền.
- Cache kết quả riêng cho mỗi lần gọi, kể cả UNKNOWN. Tính toàn bộ kết quả luật trước chọn nhãn; không giữ state bệnh án trên instance. Trace chỉ chứa rule/path/operator/kết quả/lý do, không ghi giá trị bệnh án gốc. Output thêm version và SHA-256 của bytes YAML đã nạp; không lấy clock hoặc chạy Git để tạo metadata bệnh án.
- Hai kết luận TRUE cùng ưu tiên nhưng khác nhãn hoặc trạng thái → `NEEDS_REVIEW`. Nếu cùng nhãn/trạng thái, chọn rule ID nhỏ nhất theo thứ tự chữ làm ID đại diện và giữ tất cả ID khớp. UNKNOWN cùng ưu tiên có thể thêm kết luận khác cũng chặn chọn nhãn; UNKNOWN thấp hơn không chặn kết luận cao hơn đã đủ bằng chứng.
- Cho phép metadata `target_status`, mặc định `CLASSIFIED` để giữ các luật bệnh hiện có. Đề xuất gán `INSUFFICIENT_DATA` cho `R-PV-THEODOI` và `R-DEFAULT`, tăng phiên bản tri thức từ `1.2.0` lên `1.2.1`; đây là thay đổi trạng thái, không đổi điều kiện lâm sàng. Kết quả chưa kết luận bệnh có `predicted_label = null`; rule cảnh báo đã khớp vẫn được ghi trong `matched_rule_id` và trace. Engine trực tiếp quyết định CLASSIFIED/INSUFFICIENT_DATA/NEEDS_REVIEW/UNRESOLVED; validator và phép xác định cohort ở giai đoạn sau sở hữu INVALID_DATA/OUT_OF_SCOPE.
- Nền thực thi của đợt này: Python **3.9+**, `PyYAML==6.0.3`, `unittest` và thư viện chuẩn. Cài dependency trong `.venv` khi thực thi, không nâng cấp Python hệ thống hoặc thêm framework test/validator cho phạm vi lõi. [PyYAML 6.0.3 hỗ trợ Python ≥3.8](https://pypi.org/project/PyYAML/6.0.3/).

Lõi kỹ thuật trên đã được triển khai trong `src/classify.py`, với dependency ở `requirements.txt` và kiểm thử tại `tests/test_classify.py`. Bản luật là `1.2.1`; thay đổi metadata không sửa điều kiện/ngưỡng lâm sàng. Hoàn thành lõi không làm các khoảng tuổi, mapping, điều kiện nghiên cứu hoặc kết quả 53 ca trở nên đã được duyệt.

## 12. Đối chiếu bằng bệnh án giả định — 10/10/2026

[Báo cáo chi tiết](06_rule_logic_review.md) và [kết quả từng ca](../data/synthetic/rule_logic_results.json) kiểm tra YAML/source hiện tại, giữ nguyên điều kiện bệnh. Bộ mới có 138 ca: 94 CLASSIFIED, 18 INSUFFICIENT_DATA, 6 NEEDS_REVIEW, 17 UNRESOLVED và 3 TypeError. Có 11 nhãn bệnh xuất hiện, 17/18 rule đích khớp; `R01-CAP-THUONG` chưa khả đạt với kiểu JSON hiện tại. 33 test methods gồm 31 đạt và 2 `expectedFailure` cho lỗi công thức; không gọi bộ kiểm thử là hoàn toàn đạt.

Workflow đủ mô tả các tầng và các bước xử lý, nhưng còn thiếu hợp đồng được xác nhận cho các mục sau:

| Nội dung phải hoàn tất | Bằng chứng / yêu cầu nghiệm thu |
| --- | --- |
| Kiểu HATT ở `<_formula` | F-12: chuỗi/list/object không crash; bool không được xem là số đo; kết quả lỗi được xử lý có cấu trúc. |
| Path triệu chứng cấp và tập dấu nặng thống nhất | F-01/F-13: phân loại được cấp thường khi đã loại nặng; dấu nặng TRUE không bị trace lỗi ở nhánh đã giải quyết làm sai lý do thiếu dữ kiện. Đưa `dau_hieu_nang_chi_tiet` vào cùng tập loại trừ khi sửa nhánh thường. |
| Tuổi và thời gian chung | F-02/F-03: khoảng tuổi không bỏ trống; mốc sáu tuần dùng cùng nguồn và dấu so sánh đã duyệt; không tự làm tròn/quy đổi để chọn bệnh. |
| Applicability phản vệ/sốc | F-04/F-05/F-09: phân biệt tác nhân nghi ngờ/đã biết, thời điểm và phạm vi tham chiếu sốc; có dữ kiện sàng lọc chung trước khi bỏ nhánh nguy hiểm. |
| CIndU và CSU/cohort | F-06/F-08/F-10: loại trừ Ice cube ở nhóm khác, xử lý Adrenergic/đa thể/đồng mắc; Stella đầy đủ và OUT_OF_SCOPE có nguồn xác nhận. |
| Validator, mapping và fallback | F-07/F-11: enum/range/sentinel được kiểm tra; `(+/−)` không bị coi là âm hoặc tự rơi vào UNRESOLVED; fallback thiếu ASST có phạm vi phù hợp. |

Replay trực tiếp 53 fixture cũ không mapping trả 34 INSUFFICIENT_DATA và 19 NEEDS_REVIEW, chưa phải đánh giá sau pipeline. Không dùng nhãn thật để làm đầy input. Kỳ vọng `expected_engine` chỉ ghi hành vi hiện tại; kỳ vọng workflow được nghiệm thu sau khi các quyết định B-01–B-06 được xác nhận. Với bộ mới chỉ dùng dữ liệu giả không định danh, B-07 về dữ liệu thật/export được giữ cho giai đoạn tương ứng.

## 13. Demo Streamlit — phạm vi triển khai

`main.py` tại root minh họa engine hiện tại bằng bộ 138 ca, hoặc JSON CANONICAL do người dùng sửa. Dữ liệu `du_lieu` được tách khỏi metadata/kỳ vọng trước suy diễn. Giao diện trình bày hai pha tính phụ thuộc/chọn kết luận, sáu tầng, kết quả từng rule, rule khớp/chặn, điều kiện YAML và trace; danh mục gồm 12 nhãn bệnh và 2 nhãn theo dõi. Ba SVG Archify được dùng lại để đối chiếu, không giả lập rằng những bước chưa có code đã chạy.

Demo chỉ kiểm tra JSON/envelope và loại NaN/Infinity ở biên nhập; đây không thay validator lâm sàng, mapping hoặc preprocess. JSON sai và exception của engine được hiển thị có cấu trúc, không tự gán nhãn bệnh. Đổi dữ liệu sẽ xóa kết quả trước, cần chạy lại; các hạn chế F-01/F-12 được nêu rõ. Các bước RAW validation, preprocessing, re-check, anonymization/batch/evaluation vẫn chưa được nối. Không sửa điều kiện YAML hoặc engine trong đợt demo.

Dependency được pin trong `requirements.txt`, cài vào `.venv` trước kiểm thử. Có mười test AppTest cho demo; toàn bộ repo hiện có 43 test methods, 41 đạt và 2 `expectedFailure` cho lỗi F-12 đã ghi nhận. Cách chạy tại [README](../README.md#7-demo-streamlit); ý nghĩa hiển thị/cách check logic và ngày/tác giả sửa đổi tại [changelog](05_changelog.md).
