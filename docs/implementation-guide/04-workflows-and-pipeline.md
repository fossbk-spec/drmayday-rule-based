# Workflow và pipeline

## A. Luồng hiện tại tại baseline

Nét liền là luồng đang chạy; nét đứt là module chưa nối hoặc chưa triển khai. Không gọi sơ đồ này là pipeline đầy đủ.

```mermaid
flowchart TD
    INPUT["Chọn ca giả hoặc nhập JSON"] --> PARSE["main.py: parse JSON/envelope"]
    PARSE --> DATA["Lấy du_lieu, loại metadata/nhãn"]
    YAML["YAML 1.2.1"] --> LOAD["Nạp và kiểm tra config/ref/vòng"]
    DATA --> EVAL["Engine: tính toàn bộ luật và phụ thuộc"]
    LOAD --> EVAL
    EVAL --> PICK["Chọn theo priority và UNKNOWN"]
    PICK --> OUT["Status, nhãn, rule, trace, trường thiếu, version/hash"]
    OUT --> WEB["Streamlit: hiển thị và tải JSON"]
    EVAL -->|Exception| ERR["Demo báo lỗi, không kết luận"]
    PRE["preprocess.py: có code, còn lỗi"] -.-> DATA
    ANON["anonymize.py: có code, còn lỗi"] -.-> DATA
    EMPTY["validate / pipeline / evaluate: trống"] -.-> DATA
```

## B. Workflow thay đổi yêu cầu chuyên môn

```mermaid
flowchart TD
    REQ["Bác sĩ đề xuất thay đổi + ca minh họa"] --> DRAFT["Draft: điều kiện/ngưỡng/priority/giải thích"]
    DRAFT --> CHECK["Validate config và tính tương thích"]
    CHECK --> TEST["Nghiệm thu + hồi quy + so sánh active/draft"]
    TEST --> APPROVE{"Duyệt chuyên môn"}
    APPROVE -->|Cần sửa| DRAFT
    APPROVE -->|Chấp thuận| RELEASE["Phát hành gói bất biến"]
    RELEASE --> ACT["Kích hoạt cho run mới"]
    ACT --> WATCH["Theo dõi lỗi và thay đổi kết luận"]
    WATCH -->|Cần quay lại| BACK["Rollback active pointer"]
```

Những phần DSL đã hỗ trợ có thể cập nhật qua YAML/form. Biến mới cần dictionary/schema/mapping; toán tử/công thức mới cần code và test. Không nhập script Python tùy ý để đạt flexible.

## C. Pipeline đích của từng bệnh án/batch

```mermaid
flowchart TD
    DEMO["Demo public: ca giả"] --> RECEIVE["Nhận dữ liệu và tạo import_id"]
    REAL["Dữ liệu thật: auth + quyền"] --> RECEIVE
    RECEIVE --> PIN["Resolve và pin gói/schema/mapping/preprocess/build"]
    PIN --> SPLIT["Tách dữ kiện, định danh và ground truth"]
    SPLIT --> GT["Nhãn thật riêng cho evaluator"]
    SPLIT --> RAW["Validate RAW"]
    RAW -->|Hợp lệ để chuẩn hóa| MAP["Mapping + preprocessing có version/provenance"]
    RAW -->|Sai| INVALID["INVALID_DATA + lỗi theo dòng/trường"]
    MAP --> CAN["Re-check CANONICAL"]
    CAN -->|Sai contract| INVALID
    CAN -->|Mapping/cohort chưa chốt| REVIEW["NEEDS_REVIEW"]
    CAN -->|Đủ điều kiện xử lý| POLICY["Áp identity/privacy policy"]
    POLICY --> RECHECK["Re-check bản dùng và lưu snapshot theo version đã pin"]
    RECHECK --> ENGINE["Rule-based engine"]
    ENGINE --> RESULT["Result + explanation + version"]
    RECHECK -.-> AI["AI adapter sau MVP"]
    AI -.-> COMP["Comparison/evaluation"]
    RESULT --> VIEW["Trực quan hóa + export theo quyền"]
    RESULT --> AUDIT["Audit không chứa PII"]
    INVALID --> AUDIT
    REVIEW --> AUDIT
    RESULT --> COMP
    GT --> COMP
    INVALID --> FIX["Sửa dữ liệu có nguồn/xác nhận"]
    REVIEW --> FIX
    FIX --> RAW
```

Dữ kiện thiếu hợp lệ có thể đi vào engine và trả INSUFFICIENT_DATA. Không đặt gate đòi mọi field có giá trị trước khi chạy. Không dùng thiếu dữ kiện để suy bệnh ngoài phạm vi.

### Quy định từng bước

1. **Tiếp nhận:** kiểm tra quyền, kích thước/file type, tạo ID và đếm record; resolve và pin toàn bộ version trước validation/mapping; lưu bản gốc chỉ theo policy. Nếu version import và run khác, phải kiểm tra compatibility hoặc reprocess theo bộ mới, không tự đổi adapter.
2. **Tách:** nhãn/file name/chẩn đoán đích không tham gia feature; identity mapping giữ riêng và được bảo vệ.
3. **RAW validation:** kiểm tra cấu trúc nguồn có thể mapping, không áp schema canonical vào raw legacy.
4. **Mapping/preprocess:** chỉ dùng mapping được duyệt; mỗi biến dẫn xuất ghi nguồn và công thức. Ngày khám cố định, không thay bằng clock runtime.
5. **CANONICAL validation:** type/enum/range/đơn vị/quan hệ trường; bảo toàn missing và phát hiện mâu thuẫn.
6. **Privacy:** tính feature cần ngày trước khi lược bỏ ngày; loại định danh không cần cho classifier. Các token có phạm vi và khóa được quản lý.
7. **Re-check:** bản dữ kiện thực sự dùng vẫn đủ nguồn và đúng schema đã pin; lưu input revision/snapshot cùng package/build. Xác minh toàn bộ bước vừa chạy dùng đúng version đã resolve lúc tiếp nhận.
8. **Engine:** tính phụ thuộc và ba trạng thái, sau đó chọn kết luận; giữ trace không chứa giá trị nguồn.
9. **Trình bày:** lắp bằng chứng từ snapshot theo quyền; hiển thị unknown/blockers và việc cần làm.
10. **Audit/evaluate:** ghi version/actor/provenance; giữ lỗi/chưa kết luận trong báo cáo. Ground truth chỉ join sau inference bằng record key.

## D. Workflow suy diễn: phụ thuộc trước, ưu tiên sau

```mermaid
flowchart TD
    START["CANONICAL + gói luật"] --> PHASE["Pha 1: cache riêng mỗi record"]
    PHASE --> PV["R01/R02/R03-PV"]
    PV --> SOC["R-SOC: ref R02 hoặc R03"]
    PHASE --> CAP["R-SANGLOC-CAP → nặng/thường"]
    PHASE --> CI["R-CindU-00 → các thể"]
    PHASE --> CSU["R-CSU-00 → giai đoạn → endotype"]
    PHASE --> FOLLOW["Theo dõi và fallback"]
    SOC --> RESULTS["TRUE / FALSE / UNKNOWN toàn bộ luật"]
    PV --> RESULTS
    CAP --> RESULTS
    CI --> RESULTS
    CSU --> RESULTS
    FOLLOW --> RESULTS
    RESULTS --> PRIORITY["Pha 2: mức priority nhỏ nhất có TRUE/UNKNOWN"]
    PRIORITY --> HAS{"Có candidate?"}
    HAS -->|Không| UNRES["UNRESOLVED"]
    HAS -->|Có| SELECT{"Kết quả tại mức ưu tiên đang xét"}
    SELECT -->|TRUE khác nhãn/status| REV["NEEDS_REVIEW"]
    SELECT -->|UNKNOWN có thể đổi kết luận| CAUSE{"Nguyên nhân chặn"}
    CAUSE -->|Thiếu| INSUFF["INSUFFICIENT_DATA"]
    CAUSE -->|Sai kiểu/non-finite| REV
    SELECT -->|Kết luận đủ bằng chứng| TARGET{"target_status"}
    TARGET -->|Luật bệnh| CLASS["CLASSIFIED + nhãn"]
    TARGET -->|Theo dõi| INSUFF
```

| Tầng | Priority baseline | Nhóm |
| --- | --- | --- |
| T1 | 1 | Sốc phản vệ |
| T2 | 2 / 3 | Phản vệ / theo dõi phản vệ |
| T3 | 4 / 5 | Cấp nặng / cấp thường |
| T4 | 6 | CIndU |
| T5 | 7 | CSU |
| T6 | 8 / 99 | Fallback / unresolved |

Engine tính toàn bộ, không dừng khi gặp TRUE đầu tiên trong YAML. Cùng nhãn/status có thể dùng rule_id nhỏ nhất làm đại diện; giữ tất cả matched IDs. Unknown cùng priority chỉ không chặn khi không thể thêm kết luận khác; unknown thấp hơn không chặn kết luận cao hơn đã đủ.

## E. Cây CSU để đối chiếu yêu cầu

Đây là cây **đích theo tài liệu**, không khẳng định YAML baseline đã thực hiện mọi nhánh. Điều kiện vào cohort, Stella và OUT_OF_SCOPE còn cần bác sĩ chốt. YAML baseline dùng `stella_dat OR IgE < 40`, khác đặc tả đầy đủ.

```mermaid
flowchart TD
    A["Kiểm tra CSU và phạm vi phân type"] --> B{"Điều kiện đã chốt?"}
    B -->|Chưa đủ dữ kiện| WAIT["Bổ sung / review"]
    B -->|Không đạt cohort đã xác nhận| OUT["OUT_OF_SCOPE của quy trình phân type"]
    B -->|Đạt| ASST{"ASST"}
    ASST -->|Thiếu/chưa rõ| WAIT
    ASST -->|Dương| DAYS{"Theo dõi đủ 60 ngày?"}
    DAYS -->|Chưa đủ/thiếu mốc| WAIT
    DAYS -->|Đủ| LAB["Nhóm IgG và IgE kháng IL-24"]
    LAB --> TYPES["IgG âm / IL24 dương: type I<br/>IgG dương / IL24 âm: type IIb<br/>Cả hai dương: overlap<br/>Cả hai âm: unknown"]
    LAB -->|Không đủ xác định test| WAIT
    ASST -->|Âm| STELLA{"Stella đầy đủ theo tiêu chí duyệt"}
    STELLA -->|Thiếu| WAIT
    STELLA -->|Không đạt| OUT
    STELLA -->|Đạt| IL{"IgE kháng IL-24"}
    IL -->|Dương| T1["Type I"]
    IL -->|Âm| UNK["CSU unknown"]
    IL -->|Thiếu/chưa rõ| WAIT
```

Nhóm IgG dương nếu ít nhất một test dương; âm nếu cả hai âm. Không tự áp điều kiện 60 ngày của giai đoạn 1 vào giai đoạn 2. Không coi OUT_OF_SCOPE là không mắc CSU. Các số/điều kiện trên lấy từ repo, không thay cho thẩm định y khoa.
