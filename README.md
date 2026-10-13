## Kiểm thử hệ thống Rule-Based bằng bệnh án giả lập

### 1. Tạo bộ dữ liệu bệnh án giả lập

Để kiểm thử hệ thống Rule-Based mà không để nhãn bệnh ảnh hưởng đến quá trình suy luận, các bệnh án giả lập được tạo bằng **NotebookLM** dựa trên bảng biến và các giá trị hợp lệ đã được định nghĩa trong nguồn dữ liệu.

Mỗi nhóm bệnh được yêu cầu tạo các bệnh án có đặc điểm đa dạng, bao gồm:

1. **Ca điển hình**: các triệu chứng và thông tin phù hợp rõ ràng với nhóm bệnh.
2. **Ca điển hình nhưng thay đổi đặc điểm**: thay đổi tuổi, giới tính hoặc yếu tố khởi phát nhưng vẫn đảm bảo phù hợp với bệnh.
3. **Ca thiếu dữ liệu**: cố ý để trống nhiều biến nhằm kiểm tra khả năng xử lý dữ liệu không đầy đủ.
4. **Ca sát ranh giới**: tạo các trường hợp có biểu hiện gần với ranh giới phân loại giữa các mức độ bệnh. (chỉ áp dụng với cấp và phản vệ)  ### mình tạo thấy lâu quá nên đã bỏ qua tiêu chí này với các loại còn lại =}}
6. **Có nhiễu**: bệnh nền, thuốc đang dùng, triệu chứng không liên quan  (chỉ dùng với phản vệ) ### cái này cũng thế

Bệnh án được tạo dưới dạng JSON với cấu trúc:

```json
{
  "id": "BA_xxx",
  "nhan": "[TÊN LOẠI]",
  "du_lieu": {
    "...": "..."
  }
}
```

Trong quá trình tạo dữ liệu, các quy tắc sau được áp dụng:

* Khóa `nhan` là nơi duy nhất chứa tên bệnh/nhãn phân loại.
* Các biến dùng làm nhãn và các trường chẩn đoán như `chan_doan_tuyen_truoc`, `chan_doan_ban_dau_phong_kham`, `chan_doan_tai_kham` được để trống.
* Các trường ghi chú tự do không chứa tên bệnh hoặc kết luận chẩn đoán.
* Chỉ sử dụng các giá trị hợp lệ theo bảng biến.
* Dữ liệu được xây dựng theo hướng hợp lý về mặt lâm sàng.
* ID của bệnh án được tạo ngẫu nhiên và không chứa thông tin gợi ý về nhãn.

### 2. Tách nhãn và chạy Rule-Based

Sau khi tạo bộ bệnh án, trường `nhan` được **tách riêng khỏi dữ liệu đầu vào**.

Hệ thống Rule-Based chỉ nhận phần `du_lieu` của từng bệnh án để thực hiện suy luận và đưa ra nhãn dự đoán.

Quy trình kiểm thử:

```text
Bệnh án giả lập
       │
       ├── nhan ───────────────► Nhãn thực tế (Ground Truth)
       │
       └── du_lieu ─────────────► Rule-Based
                                      │
                                      ▼
                               Nhãn dự đoán
                                      │
                                      ▼
                         So sánh với Ground Truth
                                      │
                                      ▼
                             Confusion Matrix
```

Cách thực hiện này giúp đánh giá khả năng suy luận của bộ luật mà không đưa trực tiếp nhãn bệnh vào dữ liệu đầu vào.

### 3. Kết quả kiểm thử

Bộ kiểm thử gồm **53 bệnh án giả lập**, thuộc 12 nhóm phân loại:

* Cấp nặng: 5 ca
* Cấp thường: 5 ca
* 8 nhóm con của CindU và CSU: 3 ca/nhóm, tổng cộng 24 ca
* Phản vệ: 10 ca
* Sốc phản vệ: 9 ca  ### đang chạy thì hết token =}}

Kết quả cho thấy hệ thống phân loại đúng **43/53 ca**, tương ứng:

**Accuracy = 81,13%**

| Nhóm                    | Đúng/Tổng | Recall |
| ----------------------- | --------: | -----: |
| Cấp nặng                |       5/5 |   100% |
| Cấp thường              |       4/5 |    80% |
| Mày đay CSU overlap     |       3/3 |   100% |
| Mày đay CSU type 1      |       3/3 |   100% |
| Mày đay CSU type 2      |       3/3 |   100% |
| Mày đay CSU unknown     |       3/3 |   100% |
| Mày đay CIndU Choline   |       3/3 |   100% |
| Mày đay CIndU da vẽ nổi |       3/3 |   100% |
| Mày đay CIndU do lạnh   |       3/3 |   100% |
| Mày đay CIndU khác      |       3/3 |   100% |
| Phản vệ                 |     10/10 |   100% |
| Sốc phản vệ             |       0/9 |     0% |

### 4. Phân tích Confusion Matrix

Kết quả confusion matrix cho thấy phần lớn các lớp được phân loại chính xác trên bộ dữ liệu kiểm thử.

Đặc biệt:

* Các nhóm **mày đay** được phân loại đúng toàn bộ 24/24 ca.
* **Cấp nặng** được phân loại đúng 5/5 ca.
* **Phản vệ** được phân loại đúng 10/10 ca.
* Có **1 ca cấp thường bị dự đoán thành cấp nặng**.
* Có **9/9 ca sốc phản vệ bị dự đoán thành phản vệ**.

Lỗi lớn nhất nằm ở cặp **Phản vệ – Sốc phản vệ**. Hệ thống hiện tại đã nhận diện được các ca phản vệ nhưng chưa phân biệt được các ca sốc phản vệ với phản vệ. Do đó, mặc dù accuracy tổng thể đạt 81,13%, **Recall của lớp Sốc phản vệ chỉ đạt 0%**.

Các chỉ số trung bình theo lớp:

* **Macro Precision ≈ 86,33%**
* **Macro Recall = 90,00%**
* **Macro F1 ≈ 87,40%**

Tuy nhiên, các chỉ số tổng hợp cần được diễn giải cùng với confusion matrix. Đặc biệt, Macro Recall cao không phản ánh đầy đủ vấn đề của lớp Sốc phản vệ, do nhiều lớp khác đạt recall 100%.

### 5. Nhận xét

Kết quả kiểm thử cho thấy bộ Rule-Based đã phân biệt tốt các nhóm bệnh có đặc trưng rõ ràng trong bộ dữ liệu giả lập. Tuy nhiên, **khả năng phân biệt giữa phản vệ và sốc phản vệ vẫn là điểm cần cải thiện chính**.

Ngoài ra, số lượng bệnh án ở một số lớp còn nhỏ, đặc biệt các nhóm mày đay chỉ có 3 ca/nhóm. Vì vậy, kết quả 100% trên các lớp này mới phản ánh hiệu năng trên **bộ kiểm thử giả lập hiện tại**, chưa đủ để kết luận về khả năng tổng quát hóa trên dữ liệu bệnh án thực tế.

## 6. Lõi hiện tại và cách chạy

Số liệu 53 ca ở trên là kết quả lịch sử, chưa được chạy lại theo hợp đồng lõi mới. Engine nhận một dictionary CANONICAL; mapping hồ sơ legacy, validation/schema, preprocessing, anonymization, batch và evaluator chưa được nối vào pipeline.

Pipeline đích, quy trình quản lý phiên bản luật và kế hoạch MVP bốn đợt nằm trong [gói hướng dẫn triển khai](docs/implementation-guide/README.md); tóm tắt ở [workflow mục 0](docs/02_workflow.md#0-pipeline-đích-và-thay-đổi-so-với-đặc-tả-0910). Chỉ dẫn cho agent ở [CLAUDE.md](CLAUDE.md). Ngày 13/10/2026 đã sửa TECH-01 (F-12), TECH-02, TECH-03 và SEC-01; xem [changelog](docs/05_changelog.md).

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

```python
from src.classify import ClinicalRuleEngine

engine = ClinicalRuleEngine("rules/classification_rules.yaml")
result = engine.classify_patient(canonical_patient_data)
```

Kết quả giữ sáu trường public hiện có và bổ sung kết quả từng luật, luật khớp/chặn, trường thiếu, trace không chứa giá trị bệnh án, version và SHA-256 của YAML. Lõi trả `CLASSIFIED`, `INSUFFICIENT_DATA`, `NEEDS_REVIEW` hoặc `UNRESOLVED`; các gate pipeline còn mở được ghi ở `docs/03_implementation_readiness.md`.

## 7. Demo Streamlit

Demo ở `main.py` dùng 138 ca giả định và engine hiện tại, trình bày hai pha tính phụ thuộc/chọn kết luận cùng sáu tầng trong workflow. Danh mục có **14 đầu ra: 12 nhãn bệnh và 2 nhãn theo dõi**, không phải 14 bệnh. Có thể chọn ca, sửa JSON, xem rule/điều kiện/trace và đối chiếu ba diagram Archify.

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run main.py --server.address 127.0.0.1
```

Mở địa chỉ localhost mà Streamlit in ra. [Streamlit 1.50.0](https://pypi.org/project/streamlit/1.50.0/) hỗ trợ Python 3.9.6 của `.venv` hiện tại; PyYAML giữ phiên bản 6.0.3. Không cần cài Graphviz hay thư viện vẽ riêng để xem SVG có sẵn.

Input demo là object CANONICAL hoặc envelope `{"du_lieu": {...}}`; metadata/nhãn thật không được truyền vào suy diễn. Demo không tự mapping RAW hoặc điền trường thiếu. Đổi input sẽ xóa kết quả cũ, cần bấm phân loại lại. Các bước validator/preprocessing/batch chưa triển khai được ghi rõ; diagram thể hiện workflow đề xuất, còn kết quả từng rule lấy trực tiếp từ engine.

Nhánh cấp thường chưa khả đạt (F-01) và các lệch còn mở được hiển thị khi review ca giả định. Demo bắt lỗi thực thi để tiếp tục sử dụng giao diện, không sửa kết quả bệnh hoặc giả lập một pipeline đã hoàn thiện. Xem [báo cáo logic](docs/06_rule_logic_review.md) trước khi diễn giải đầu ra.

Kiểm tra ngày 13/10/2026: `tests/` (trước đó không có trong Git) gồm 21 test methods cho engine, preprocessing và anonymization, tất cả đạt; chưa có test giao diện Streamlit (số 43 test cũ là lịch sử, các file đó không được commit). Ý nghĩa hiển thị, ca thực hành và ngày/tác giả sửa đổi được ghi trong [changelog và hướng dẫn demo](docs/05_changelog.md).

