# Danh sách quyết định cần bác sĩ chốt — kèm ca minh họa giả lập

| | |
| --- | --- |
| **Người soạn** | TS. Hoàng Quang Huy (kỹ sư trưởng) |
| **Phiên bản / ngày** | 1.0 — 2026-11-13 |
| **Trạng thái** | DỰ THẢO — chờ buổi review với bác sĩ |
| **Gói luật tham chiếu** | `kb-1.2.1` (`rules/classification_rules.yaml`), engine `1.1.0`, 138 ca giả `data/synthetic/rule_logic_cases.json` |
| **Mục đích** | Gom mọi câu hỏi chuyên môn còn mở vào **một buổi review**, mỗi câu có ca giả minh họa chạy được trên trang Demo, để chốt `kb-1.3.0` và mở Bước 5–6 của [lộ trình](07_phuong_an_mo_rong.md#7-lộ-trình-tối-ưu). |

**Tài liệu gốc:** [06 — kiểm tra logic](06_rule_logic_review.md) (F-01..F-13), [09 — quyết định D-01..D-11](implementation-guide/09-decisions-and-templates.md), [02 — workflow](02_workflow.md), [01 — luật](01_rules.md), [từ điển dữ liệu](01_data_dictionary/), [HANDOFF](HANDOFF.md).

---

## 0. Cách dùng tài liệu này

- **Mỗi mục** gồm: câu hỏi → hành vi engine hiện tại (đã chạy lại trên `kb-1.2.1`) → ca giả minh họa (ID trong `rule_logic_cases.json`; mở trang *Demo ca bệnh*, chọn ID để xem trace) → các lựa chọn → ô ghi quyết định.
- **Không coi YAML hiện tại là đáp án.** Hành vi hiện tại chỉ là mô tả; bác sĩ chốt theo chuyên môn, kỹ thuật sửa theo.
- **Mọi ca đều là dữ liệu giả 100%**, không có bệnh nhân thật.
- Sau buổi review, mỗi câu trả lời ghi theo mẫu `D-XX` (mục 8); kỹ thuật sửa YAML có phiên bản → PR → **báo cáo tác động** (ca nào đổi nhãn) → bác sĩ xác nhận lại trên báo cáo → phát hành `kb-1.3.0`.
- Thời lượng gợi ý: 90 phút. Thứ tự: nhóm A (an toàn) → B → C/D → E (từ điển, có thể giao về sau).

### Bảng tổng hợp

| # | Câu hỏi | Nhóm | Mã gốc | Chặn gì nếu chưa chốt | Người chốt |
| --- | --- | --- | --- | --- | --- |
| Q1 | Khoảng tuổi của ngưỡng sốc còn 3 khoảng trống | A | F-02 / D-03 | Ca sốc ở tuổi trống bị hạ thành "Phản vệ" | Bác sĩ |
| Q2 | Sốc có được xét khi **không rõ dị nguyên** (kịch bản 1)? | A | F-05 / D-04 | Ca tụt HA đo được nhưng không ra "Sốc" | Bác sĩ |
| Q3 | "Nghi ngờ" có đủ thay "đã biết"? Có cần điều kiện thời điểm khởi phát? | A | F-04 / D-04 | Phạm vi phản vệ quá rộng/hẹp | Bác sĩ |
| Q4 | `R-PV-THEODOI`: tài liệu có nhánh tự động, YAML chỉ có cờ bác sĩ | A | 01_rules ≠ YAML | Ca "dị nguyên + 1 triệu chứng da" rơi UNRESOLVED | Bác sĩ |
| Q5 | HATT thấp nhất lấy từ đâu khi có cả ô nhập và bảng sinh hiệu; khoảng hợp lệ HA | A | `extract_min_sbp`, todo | Tiền xử lý dữ liệu thật | Bác sĩ + kỹ thuật |
| Q6 | Dạng dữ liệu "ngứa nhiều" / "phù mạch đáng kể" ở mày đay cấp | B | F-01 / D-02, F-13 | **Nhãn "Cấp thông thường" chưa bao giờ đạt được** | Bác sĩ + chủ dữ liệu |
| Q7 | Mốc đúng 6 tuần thuộc cấp hay mạn | B | F-03 / D-03 | Ca ranh giới | Bác sĩ |
| Q8 | Dạng tổn thương "bờ rõ" là thuộc tính riêng hay suy từ dạng | B | todo `dac_diem_san_phu_cap` | Sàng lọc cấp với dữ liệu thật | Bác sĩ + chủ dữ liệu |
| Q9 | CIndU: loại trừ, Adrenergic, nhiều test dương | C | F-06 / D-05 | Ca đa thể trả NEEDS_REVIEW / UNRESOLVED | Bác sĩ |
| Q10 | Ký hiệu kết quả test: `(-)` ASCII, `(+/−)`, giá trị lạ | C | F-07 | Validator cho dữ liệu thật | Bác sĩ + chủ dữ liệu |
| Q11 | Stella đầy đủ hay chỉ IgE < 40; có `OUT_OF_SCOPE`? | D | F-08 / D-06 | Tách chẩn đoán khỏi tuyển nghiên cứu | Bác sĩ + chủ nghiên cứu |
| Q12 | Đồng mắc CSU + CIndU: nhãn chính/phụ | D | F-10 / D-05 | Hợp đồng kết quả đồng mắc | Bác sĩ |
| Q13 | Thiếu ASST có được rơi vào "Chưa đủ dữ liệu" chung? | D | F-11 | Định tuyến trạng thái | Bác sĩ |
| Q14 | Bệnh án mạn thiếu trường sàng lọc phản vệ: coi là gì? | D | F-09 / D-04 | **53 ca cũ và mọi bệnh án mạn thật** | Bác sĩ + chủ dữ liệu |
| Q15 | 24 trường `todo` trong `rules/fields.yaml` | E | D-01 | Validator / mapping | Chủ dữ liệu + bác sĩ |
| Q16 | D-01, D-07, D-09, D-10 (không thuộc bác sĩ nhưng chặn Bước 5) | F | 09 | Khu dữ liệu thật | Chủ dữ liệu / chủ sản phẩm |

---

## 1. Nhóm A — Phản vệ và sốc phản vệ (an toàn, ưu tiên cao nhất)

### Q1. Khoảng tuổi của ngưỡng tụt huyết áp (F-02 / D-03)

**Hiện tại** `R-SOC` chỉ TRUE khi `R02-PV` hoặc `R03-PV` TRUE **và** HATT thấp nhất dưới ngưỡng theo tuổi:

| Khoảng tuổi trong YAML | Ngưỡng HATT |
| --- | --- |
| 1 tháng (0,083) ≤ tuổi < 1 | < 70 |
| 1 ≤ tuổi ≤ 10 | < 70 + 2 × tuổi |
| 11 ≤ tuổi ≤ 17 | < 90 |
| tuổi ≥ 18 | < 90 **hoặc** < 0,7 × HATT nền |

Ba khoảng **không thuộc dòng nào**: dưới 1 tháng; (10, 11); (17, 18). Tuổi tính thập phân từ ngày sinh (`preprocess.py`), nên trẻ 10 tuổi 6 tháng rơi vào khoảng trống.

**Ca minh họa** (`SOC-GAP-0.05`, `SOC-GAP-10.5`, `SOC-GAP-17.5`): dị nguyên thức ăn, sẩn phù + khó thở, HATT thấp nhất 80, nền 120 → `R02-PV` TRUE, `R-SOC` FALSE → kết quả **"Phản vệ"**, không phải "Sốc phản vệ".

**Lựa chọn:**
1. Khoảng liên tục: [1 tháng, 1) / [1, 11) / [11, 18) / ≥ 18 — tuổi thập phân, không làm tròn.
2. Làm tròn tuổi xuống số nguyên rồi áp khoảng hiện tại.
3. Dưới 1 tháng: nêu ngưỡng riêng, hoặc trả `NEEDS_REVIEW` (không tự phân loại).
4. Người lớn: giữ "hoặc < 0,7 × nền"; có áp tiêu chí giảm 30% cho trẻ em không?

**Ghi quyết định:** ☐ Lựa chọn ___ ; ngưỡng dưới 1 tháng: ___ ; nguồn tham chiếu (WAO 2020 mục ___): ___

### Q2. Sốc khi không rõ dị nguyên (F-05 / D-04)

**Hiện tại** `R-SOC` chỉ tham chiếu `R02-PV`/`R03-PV` (có yếu tố nghi ngờ). Kịch bản 1 (`R01-PV`, không có yếu tố nghi ngờ) dù tụt HA đo được vẫn **không** vào sốc.

**Ca minh họa** `PV-07`: không yếu tố nghi ngờ, sẩn phù + khó thở, HATT 80/nền 120 → **"Phản vệ"** (`R01-PV`), `R-SOC` FALSE.

**Lựa chọn:** (a) mở rộng `R-SOC` cho cả `R01-PV`; (b) giữ nguyên, ghi rõ lý do chuyên môn vào `decision_trace`.

**Ghi quyết định:** ☐ ___

### Q3. "Nghi ngờ" thay cho "đã biết"; điều kiện thời điểm (F-04 / D-04)

**Hiện tại** `R02-PV`/`R03-PV` dùng bốn trường `yeu_to_nghi_ngo_pv_*.co_khong == "Có"`; không có trường "dị nguyên đã biết" và **không có điều kiện thời điểm khởi phát** (phút–giờ sau tiếp xúc).

**Ca minh họa** `PV-06`: nghi ngờ thuốc + **ngất đơn độc**, không triệu chứng da/hô hấp → **"Phản vệ"** qua `R03-PV`.

**Lựa chọn:**
1. `R03-PV` yêu cầu "dị nguyên **đã biết** với bệnh nhân này" → cần thêm trường (từ điển hiện chỉ có `tien_su_phan_ung_yeu_to_*`); `R02-PV` dùng "nghi ngờ" như hiện nay.
2. Giữ "nghi ngờ" cho cả hai; ghi rõ là sàng lọc nhạy, chấp nhận dương giả.
3. Thêm điều kiện thời gian tiếp xúc → khởi phát (trường nào, ngưỡng giờ bao nhiêu, thiếu thì làm gì).

**Ghi quyết định:** ☐ ___

### Q4. `R-PV-THEODOI`: tài liệu khác YAML

**Tài liệu** [01_rules](01_rules.md) mục 1: `tiep_tuc_theo_doi_chua_du_du_kien == true` **HOẶC** (tiếp xúc dị nguyên **và** có 1 triệu chứng da nhưng chưa đủ 2 hệ cơ quan).
**YAML** chỉ có vế đầu (cờ bác sĩ tích).

**Ca minh họa** (dựng từ `PV-07`): yếu tố nghi ngờ thức ăn = Có, chỉ sẩn phù, hô hấp/tuần hoàn/tiêu hóa đều "Không có", HATT 120, cờ = false → engine trả **UNRESOLVED** ("Không có luật đích phù hợp"), không ra "Theo dõi phản vệ".

**Lựa chọn:** (a) thêm nhánh tự động vào YAML đúng như tài liệu; (b) sửa tài liệu về đúng YAML (chỉ cờ); (c) nhánh tự động trả trạng thái khác (`NEEDS_REVIEW`) thay vì nhãn theo dõi.

**Ghi quyết định:** ☐ ___

### Q5. Nguồn HATT thấp nhất; khoảng hợp lệ của huyết áp

**Hiện tại** `MedicalPreprocessor.extract_min_sbp`: nếu ô `huyet_ap_tam_thu_thap_nhat` có số dương thì dùng ngay; **chỉ khi ô trống** mới lấy min từ bảng sinh hiệu (`bang_theo_doi_dau_hieu_sinh_ton[].huyet_ap`).

**Ca minh họa** (dựng): ô nhập 95; bảng sinh hiệu 110/70 lúc 10:00 và **80/50** lúc 10:15 → engine dùng **95** → không sốc, dù bảng có 80.

**Lựa chọn:** (a) ô nhập thắng (hiện tại); (b) lấy **min** của cả hai nguồn; (c) hai nguồn lệch → `NEEDS_REVIEW` kèm cả hai giá trị; (d) bảng sinh hiệu thắng vì có thời điểm.

Kèm theo: từ điển `phan_ve.md` để trống khoảng hợp lệ `huyet_ap_tam_thu_nen` (*"TODO: Bác sĩ cho biết khoảng hợp lệ?"*) và HATT thấp nhất. Ca `NEGATIVE-SBP` (HATT = −2) hiện vẫn ra "Sốc phản vệ" ở tầng engine; pipeline chặn bằng validator nhưng cần khoảng chính thức.

**Ghi quyết định:** ☐ nguồn HATT: ___ ; khoảng hợp lệ HATT thấp nhất: [___, ___] mmHg; HA nền: [___, ___] mmHg

---

## 2. Nhóm B — Mày đay cấp

### Q6. Dạng dữ liệu của "ngứa nhiều" và "phù mạch đáng kể" (F-01 / D-02; kéo theo F-13)

**Vấn đề:** `R01-CAP-NANG` và `R01-CAP-THUONG` so sánh `trieu_chung_da_hien_tai == "Ngứa nhiều"` / `== "Phù mạch đáng kể"` (chuỗi), nhưng từ điển định nghĩa trường này là **object checkbox** với danh sách `Phù mạch, Sẩn phù, Ban dát sẩn, Không có, Khác` — không có hai giá trị trên. `R01-CAP-THUONG` lại cần `trieu_chung_da_hien_tai.danh_sach_chon contains "Sẩn phù"` (object). Một bản ghi không thể vừa là object vừa là chuỗi ⇒ **nhãn "Mày đay cấp thông thường" chưa bao giờ đạt được** trên 138 ca.

**Ca minh họa:**
- `CAP-THUONG-OBJECT`: object `{"danh_sach_chon": ["Sẩn phù"]}`, mọi dấu nặng âm, có ảnh, 24 giờ → **NEEDS_REVIEW** (so sánh chuỗi trên object → UNKNOWN).
- `CAP-THUONG-STRING`: chuỗi `"Sẩn phù"` → **NEEDS_REVIEW** (không đọc được `.danh_sach_chon`).
- `CAP-ANH-None` (F-13): như ca object nhưng `anh_san_phu = null` → NEEDS_REVIEW, trace lẫn lý do thiếu ảnh với lý do sai kiểu.
- `CAP-NANG-CHITIET`: `dau_hieu_nang_chi_tiet = ["Phù mạch đáng kể"]` → **CLASSIFIED "cấp nặng"** — nhánh nặng đạt được nhờ trường riêng này, nhưng nhánh thường **không** phủ định trường này (lệch tập dấu nặng).

**Cần chốt:**
1. "Ngứa nhiều" ghi ở đâu: trường riêng (ví dụ `ngua_muc_do` enum nhẹ/vừa/nhiều, hay thang 0–10 với ngưỡng), hay là một mục trong `dau_hieu_nang_chi_tiet`?
2. "Phù mạch đáng kể" = `dau_hieu_nang_chi_tiet contains` (như ca CHITIET) **hay** suy từ `vi_tri_phu_mach` (mi mắt/lưỡi/thanh quản/môi) + `so_lan_phu_mach_nang_can_vien ≥ 1`? Nếu cả hai thì quan hệ OR?
3. **Một tập dấu nặng chung** cho cả hai nhánh (nặng = any; thường = none) — xác nhận danh sách: phù mạch đáng kể, ngứa nhiều, >50% BSA, >50 nốt, nôn, đau bụng quặn, buồn nôn/tiêu chảy, khò khè/nghẹn họng. Thiếu/thừa mục nào?
4. Thiếu ảnh (`anh_san_phu` null): chặn hẳn hay chỉ cảnh báo?

**Ghi quyết định:** ☐ ___

### Q7. Đúng 6 tuần (F-03 / D-03)

**Hiện tại** cấp: `thoi_gian_khoi_phat_gio <= 1008` (≤ 6 tuần, **gồm** mốc); mạn: `thoi_gian_khoi_phat_tuan > 6` (**không gồm** mốc). Tiêu đề tài liệu ghi "cấp < 6 tuần".

**Ca minh họa:** `CAP-6TUAN-1008` (1008 giờ) → vào cấp; `CSU-WEEKS-6`, `CINDU-WEEKS-6` (6 tuần) → `R-CSU-00`/`R-CindU-00` FALSE → UNRESOLVED.

**Lựa chọn:** (a) đúng 6 tuần = cấp (như YAML, sửa tiêu đề thành "≤ 6 tuần"); (b) đúng 6 tuần = mạn (đổi cấp thành `< 1008`, mạn `>= 6`); (c) nguồn thời gian chung: giờ hay tuần, tính từ ngày khởi phát nào.

**Ghi quyết định:** ☐ ___

### Q8. "Bờ rõ" trong dạng tổn thương

**Hiện tại** `R-SANGLOC-CAP` yêu cầu `dac_diem_san_phu_cap.dang_ton_thuong contains_any ["Hình vòng (bờ rõ)", "Hình tròn (bờ rõ)", "Hình bản đồ (bờ rõ)"]`. Từ điển `cap.md` chỉ có `Hình vòng, Hình đứt đoạn, Hình bản đồ, Hình tròn, Dát sẩn, Khác` — **không có hậu tố "(bờ rõ)"**, và cấu trúc là lưới nhiều dòng (dạng, kích thước mm, thời gian tồn tại, thời điểm).

**Lựa chọn:** (a) "bờ rõ" là thuộc tính riêng mỗi dòng (thêm cột `bo_ro: Có/Không`); (b) ba dạng vòng/tròn/bản đồ mặc nhiên là bờ rõ → luật chỉ cần dạng; (c) bỏ điều kiện này khỏi sàng lọc.

Kèm: đơn vị "thời gian tồn tại" của mỗi dòng (từ điển ghi *TODO: Đơn vị?*).

**Ghi quyết định:** ☐ ___

---

## 3. Nhóm C — Mày đay mạn cảm ứng (CIndU)

### Q9. Loại trừ, Adrenergic, nhiều test dương (F-06 / D-05)

**Hiện tại:**
- `R-CindU-03` (lạnh) = TempTest **hoặc** Ice cube dương.
- `R-CindU-04` (khác) loại trừ da vẽ nổi, cholinergic, **TempTest** dương — **không loại Ice cube** → lạnh và khác có thể cùng TRUE.
- Không có luật nào đọc `adrenergic_ket_qua` (có trong schema).
- Nhiều thể cùng TRUE ở cùng priority → `NEEDS_REVIEW`, không có tie-break.

**Ca minh họa:** `CINDU-ICE-OTHER` (Ice cube + áp lực dương, TempTest âm) → **NEEDS_REVIEW** (lạnh và khác cùng TRUE). `CINDU-ADRENERGIC` (Adrenergic dương đơn độc) → **UNRESOLVED**.

**Cần chốt:**
1. Nhóm "khác" loại trừ đủ cả Ice cube?
2. Adrenergic là thể riêng (nhãn gì) hay gộp vào "khác"?
3. Nhiều test dương: trả **nhiều nhãn** (đa thể), hay nhãn chính theo thứ tự ưu tiên nào, hay luôn `NEEDS_REVIEW`?
4. Test **thiếu** (null) có được coi là âm khi xét loại trừ không? (workflow RB-17 nói "thiếu không thành âm" — xác nhận.)

**Ghi quyết định:** ☐ ___

### Q10. Ký hiệu kết quả xét nghiệm (F-07)

**Hiện tại** engine so sánh chuỗi đúng ký tự: `(+)`, `(−)` (dấu trừ Unicode U+2212). Giá trị khác → không khớp, có thể rơi vào nhánh `!= "(+)"` của nhóm "khác".

**Ca minh họa:** `CINDU-NONENUM` (da vẽ nổi = `"abc"`, áp lực dương) → **CLASSIFIED "CIndU khác"** vì `abc != (+)`. `CSU-ASST-(-)` (gạch ASCII) và `CSU-ASST-(+/−)` → UNRESOLVED.

**Cần chốt:** bảng giá trị hợp lệ cho mọi trường `*_ket_qua`: `(+)`, `(−)`, có cho phép `(+/−)` (nghĩa là gì: nghi ngờ? → UNKNOWN?), `Chưa làm`, `N/A`. Validator sẽ: chuẩn hóa `(-)` ASCII → `(−)`; giá trị ngoài bảng → `INVALID_DATA`.

**Ghi quyết định:** ☐ ___

---

## 4. Nhóm D — CSU và nhóm nghiên cứu

### Q11. Stella đầy đủ hay IgE < 40 (F-08 / D-06)

**Hiện tại** `R-GD-02` = ASST `(−)` **và** (`stella_dat == true` **hoặc** `ige_toan_phan < 40`). Workflow mục 5 yêu cầu Stella **đầy đủ** (không dị ứng đồng mắc, IgE < 40, test lẩy da hô hấp âm) và Stella FALSE → **loại khỏi nghiên cứu** (`R-GD-03`/`OUT_OF_SCOPE`, chưa có trong YAML).

**Ca minh họa:** `CSU-STELLA-False-39.9` (Stella = false, IgE 39,9) và `CSU-STELLA-None-39.9` (Stella chưa đánh giá) → cả hai **CLASSIFIED "CSU unknown"** qua `R-GD-02` nhờ vế IgE < 40.

**Cần chốt:**
1. `R-GD-02` chỉ dùng `stella_dat` (bỏ vế IgE)? `stella_dat` do ai tính: bác sĩ tích, hay engine suy từ 3 điều kiện con (cần 3 trường)?
2. Stella FALSE → `OUT_OF_SCOPE` (ngoài nghiên cứu) nhưng **vẫn có chẩn đoán CSU**? Tức tách hai kết luận: nhãn bệnh và tình trạng tuyển.
3. Stella null → `INSUFFICIENT_DATA`.
4. Đơn vị IgE: `cap.md` thiếu, `man.md` ghi UI/mL — xác nhận và khoảng hợp lệ.

**Ghi quyết định:** ☐ ___

### Q12. Đồng mắc CSU + CIndU (F-10 / D-05)

**Hiện tại** CIndU (priority 6) thắng CSU (priority 7); CSU vẫn nằm trong trace. `R-CSU-00` chưa kiểm tra "CSU đơn thuần" (loại trừ yếu tố kích thích) như workflow.

**Ca minh họa** `CSU-CINDU`: da vẽ nổi dương **và** đủ CSU (ASST +, theo dõi 60 ngày, ELISA đủ) → **"CIndU da vẽ nổi"**, CSU chỉ ở trace.

**Lựa chọn:** (a) nhãn chính CIndU, nhãn phụ CSU (hợp đồng kết quả cần thêm `secondary_labels`); (b) nhãn chính CSU; (c) nhãn ghép "CSU + CIndU"; (d) `hoan_canh_xuat_hien_san_phu` = "Cả hai" quyết định đồng mắc, chỉ test dương không đủ.

**Ghi quyết định:** ☐ ___

### Q13. Thiếu ASST và luật mặc định (F-11)

**Hiện tại** `R-DEFAULT` (priority 8) khớp khi `asst_ket_qua` null, kể cả khi không qua `R-CSU-00`.

**Ca minh họa:** `DEFAULT-NO-CSU` (không đủ CSU, ASST null) → **INSUFFICIENT_DATA** qua `R-DEFAULT`. `CSU-ASST-None` (đủ CSU, ASST null) → INSUFFICIENT_DATA nhưng `matched_rule_id` null (UNKNOWN tầng 7 chặn tầng 8).

**Cần chốt:** `R-DEFAULT` chỉ áp dụng khi đã qua `R-CSU-00`? Thiếu ASST ở bệnh nhân không thuộc CSU → trạng thái gì (UNRESOLVED hay OUT_OF_SCOPE)?

**Ghi quyết định:** ☐ ___

### Q14. Bệnh án mạn thiếu trường sàng lọc phản vệ (F-09 / D-04) — **ảnh hưởng lớn nhất đến dữ liệu thật**

**Hiện tại** mọi bản ghi đều được chạy qua tầng phản vệ. Bệnh án mạn (biểu mẫu `man.md`) **không có** các trường `*_pv` → luật phản vệ UNKNOWN → chặn kết luận.

**Ca minh họa** `CSU-NO-PV`: đủ xét nghiệm CSU, không có khối `_pv` → **INSUFFICIENT_DATA**. Đây cũng là lý do **53 ca cũ có nhãn đạt 0/53** (12 ca CSU → INSUFFICIENT_DATA).

**Lựa chọn:**
1. **Applicability theo biểu mẫu:** bệnh án mạn → bỏ qua tầng phản vệ (ghi trace "không áp dụng"), chỉ chạy khi có dữ kiện `_pv`.
2. **Mapping liên biểu mẫu:** từ các trường cấp/mạn (triệu chứng hô hấp, tuần hoàn, yếu tố nghi ngờ) suy ra khối `_pv` tương đương — cần bác sĩ duyệt bảng mapping (workflow mục "Trường cấp ↔ phản vệ").
3. Bắt buộc mọi biểu mẫu có khối sàng lọc phản vệ tối thiểu (sửa biểu mẫu giấy).

Nguyên tắc đã thống nhất: **không tự điền** `_pv = Không` khi thiếu.

**Ghi quyết định:** ☐ ___

---

## 5. Nhóm E — 24 trường `todo` trong `rules/fields.yaml` (D-01)

Gộp theo loại; có thể giao cho chủ dữ liệu xử lý sau buổi review, trừ hai dòng đầu đã nằm trong Q6/Q8.

| Loại | Trường | Việc cần chốt |
| --- | --- | --- |
| Shape object ≠ chuỗi (**= Q6**) | `trieu_chung_da_hien_tai`, `hoan_canh_xuat_hien_san_phu` | Object checkbox hay chuỗi; luật so sánh ở path nào |
| Hậu tố "(bờ rõ)" (**= Q8**) | `dac_diem_san_phu_cap.dang_ton_thuong` | Thuộc tính riêng hay suy từ dạng |
| Path lồng chưa có trong từ điển (13) | `muc_do_lan_rong_va_phan_bo_ton_thuong.muc_do_lan_rong`; `trieu_chung_da_hien_tai.danh_sach_chon`; `trieu_chung_da_hien_tai_pv.danh_sach_chon`; `trieu_chung_ho_hap_hien_tai.danh_sach_chon`; `trieu_chung_ho_hap_hien_tai_pv.danh_sach_chon`; `trieu_chung_tuan_hoan_hien_tai_pv.danh_sach_chon`; `trieu_chung_tieu_hoa_hien_tai.{non, dau_bung_quan_that, buon_non_tieu_chay}`; `trieu_chung_tieu_hoa_hien_tai_pv.{dau_bung_quan_that, non_so_lan}`; `vi_tri_phu_mach.danh_sach_chon` | Xác nhận quy ước chung: object checkbox lưu `{"danh_sach_chon": [...], "khac_ghi_ro": "..."}`; tiêu hóa lưu boolean/số theo từng triệu chứng. Chốt một lần cho tất cả. |
| Enum "Có (ghi rõ)" vs `co_khong` (4) | `yeu_to_nghi_ngo_pv_{thuc_an, thuoc, con_trung_dot, khac}.co_khong` | Lưu `{"co_khong": "Có", "ghi_ro": "..."}`; luật so sánh `co_khong` |
| Chưa có dòng từ điển (3) | `tuoi` (số, năm thập phân, suy từ `ngay_sinh` và `ngay_kham`), `so_ngay_theo_doi` (số ngày, tính từ mốc nào?), `stella_dat` (boolean, ai tính — **= Q11**) | Thêm dòng từ điển với nguồn tính |
| Khoảng / đơn vị (2) | `huyet_ap_tam_thu_nen` (**= Q5**), `ige_toan_phan` (**= Q11.4**) | Khoảng hợp lệ, đơn vị |

**Ghi quyết định:** ☐ quy ước object checkbox: ___ ; `so_ngay_theo_doi` tính từ: ___

---

## 6. Nhóm F — Quyết định của chủ dữ liệu / chủ sản phẩm (chặn Bước 5)

Không cần bác sĩ nhưng nên chốt cùng buổi để mở Bước 5 (khu dữ liệu thật). Chi tiết ở [07 mục 8](07_phuong_an_mo_rong.md#8-quyết-định-cần-bạnbác-sĩ-chốt-sớm) và [09](implementation-guide/09-decisions-and-templates.md).

| ID | Câu hỏi | Gợi ý tối thiểu để mở Bước 5 |
| --- | --- | --- |
| D-01 | Template import đầu tiên: nguồn (HIS? Excel?), RAW hay CANONICAL, sentinel, nhãn tách riêng | Một file JSON/CSV mẫu **giả** đúng cấu trúc thật + bảng mapping RAW→CANONICAL do chủ dữ liệu ký |
| D-07 | Ai được upload/xem/export; có lưu sau phiên không; retention | Hợp đồng rút gọn: **không lưu** bệnh án sau phiên, chỉ lưu run manifest không PII (07 mục 7) |
| D-09 | Host demo và host khu dữ liệu thật; OIDC provider | Demo: Streamlit Community Cloud; khu thật: máy chủ bệnh viện hoặc VPS riêng có OIDC |
| D-10 | Ai soạn luật, bác sĩ nào duyệt, ai bấm release; có gộp vai trò | Tên cụ thể cho 3 vai trò; duyệt = approve PR trên GitHub |

---

## 7. Danh sách ca minh họa và cách chạy

Tất cả ID dưới đây có trong `data/synthetic/rule_logic_cases.json` trừ hai ca "dựng" (Q4, Q5) mô tả trực tiếp trong mục. Chạy local:

```powershell
.\.venv\Scripts\python.exe -m streamlit run main.py   # trang "Demo ca bệnh" → chọn ID
```

| Câu | Ca | Kết quả hiện tại (kb-1.2.1, engine 1.1.0, chạy 2026-11-12) |
| --- | --- | --- |
| Q1 | `SOC-GAP-0.05`, `SOC-GAP-10.5`, `SOC-GAP-17.5` | CLASSIFIED — Phản vệ (R-SOC FALSE) |
| Q2 | `PV-07` | CLASSIFIED — Phản vệ (R01-PV) |
| Q3 | `PV-06` | CLASSIFIED — Phản vệ (R03-PV) |
| Q4 | dựng từ `PV-07` | UNRESOLVED |
| Q5 | dựng; `NEGATIVE-SBP` | 95 được chọn; NEGATIVE-SBP: CLASSIFIED — Sốc (engine), pipeline chặn INVALID_DATA |
| Q6 | `CAP-THUONG-OBJECT`, `CAP-THUONG-STRING`, `CAP-ANH-None`, `CAP-NANG-CHITIET` | NEEDS_REVIEW ×3; CLASSIFIED — cấp nặng |
| Q7 | `CAP-6TUAN-1008`, `CSU-WEEKS-6`, `CINDU-WEEKS-6` | CLASSIFIED cấp; UNRESOLVED ×2 |
| Q9 | `CINDU-ICE-OTHER`, `CINDU-ADRENERGIC` | NEEDS_REVIEW; UNRESOLVED |
| Q10 | `CINDU-NONENUM`, `CSU-ASST-(-)`, `CSU-ASST-(+/−)` | CLASSIFIED — CIndU khác; UNRESOLVED ×2 |
| Q11 | `CSU-STELLA-False-39.9`, `CSU-STELLA-None-39.9` | CLASSIFIED — CSU unknown ×2 |
| Q12 | `CSU-CINDU` | CLASSIFIED — CIndU da vẽ nổi |
| Q13 | `DEFAULT-NO-CSU`, `CSU-ASST-None` | INSUFFICIENT_DATA ×2 |
| Q14 | `CSU-NO-PV` | INSUFFICIENT_DATA |

Khi `kb-1.3.0` được soạn, báo cáo tác động (`tools/impact_report.py`, CI đăng vào PR) sẽ liệt kê đúng các ca này đổi trạng thái/nhãn — bác sĩ đối chiếu với quyết định đã ghi trước khi duyệt.

---

## 8. Sau buổi review

1. Mỗi câu trả lời → một mục `D-XX` theo mẫu ở [09](implementation-guide/09-decisions-and-templates.md#mẫu-ghi-một-quyết-định), lưu tại `docs/decisions/D-XX.md` (thư mục mới), trạng thái APPROVED kèm tên bác sĩ và ngày.
2. Kỹ thuật: brief `docs/tasks/B6-kb-1.3.0.md` → sửa `rules/*.yaml` + `fields.yaml` + từ điển + ca nghiệm thu mới (trước/tại/sau ngưỡng) → `UPDATE_GOLDEN=1` → PR.
3. CI chạy test + báo cáo tác động; bác sĩ xem báo cáo, approve PR = duyệt chuyên môn (D-10).
4. Phát hành `knowledge/kb-1.3.0/` + manifest; `active.yaml` `demo:` trỏ sang; `real:` chỉ bật sau D-07.
5. Câu chưa chốt được trong buổi: giữ OPEN, engine giữ hành vi hiện tại và **ghi rõ trong trace** là chưa duyệt — không tự chọn ngưỡng thay.
