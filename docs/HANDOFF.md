# Bàn giao trạng thái — tiếp tục trên máy khác

**Cập nhật:** 14/10/2026 · **HEAD:** `main` sau PR #5 · **Repo:** <https://github.com/fossbk-spec/drmayday-rule-based> (bản gốc: `trangdoanthu26/rule_based_mayday`).

## 0. Bắt đầu ngay trên máy mới

**Bước 1 – thiết lập** (PowerShell, cần Git + Python ≥3.9; thêm `-ForCodex` nếu dùng Codex trên máy đó):

```powershell
git clone git@github.com:fossbk-spec/drmayday-rule-based.git
cd drmayday-rule-based
powershell -ExecutionPolicy Bypass -File tools\setup_machine.ps1 -ForCodex
```

Script tạo `.venv` (với `-ForCodex`: từ bản Python copy vào `..\.tools\` để sandbox Codex đọc được), cài `requirements.txt`, chạy 52 test và kiểm tra gói tri thức/từ điển trường.

**Bước 2 – mở Claude Code trong thư mục repo và dán:**

```text
Đọc CLAUDE.md và docs/HANDOFF.md. Kiểm tra git log/status so với mục "Tiến độ", chạy test một lần,
rồi tóm tắt trạng thái và đề xuất việc tiếp theo theo mục "Việc tiếp theo". Làm việc theo
"Cách làm việc đã thống nhất" (brief → Codex → review → PR → tự merge PR kỹ thuật khi CI xanh;
luật y khoa, active real, dữ liệu thật, deploy khu dữ liệu thật chờ người dùng/bác sĩ).
Cuối phiên cập nhật docs/HANDOFF.md và push.
```

Đọc theo thứ tự: file này → [CLAUDE.md](../CLAUDE.md) → [docs/07 mục 7 – Lộ trình tối ưu](07_phuong_an_mo_rong.md#7-lộ-trình-tối-ưu) → [changelog](05_changelog.md).

## 1. Tiến độ

| Bước | Trạng thái | Nơi xem |
| --- | --- | --- |
| 0. Nền móng (CI, test hợp đồng, sửa lỗi review Codex) | ✅ | `.github/workflows/tests.yml`, `tests/` |
| 1. Ba hợp đồng | ✅ PR #1 | `src/classifiers/`, `src/version.py`, `rules/fields.yaml` |
| 2. Quản lý tri thức tối thiểu | ✅ PR #2 | `knowledge/`, `src/knowledge.py`, `tools/*`, `.github/workflows/impact.yml`, `docs/knowledge_release.md` |
| 3. Pipeline mỏng | ✅ PR #3 | `src/ingest.py`, `src/validate.py`, `src/pipeline.py`, `src/evaluate.py` |
| 4. Web demo | ✅ PR #4 (chưa deploy) | `main.py`, `app/` |
| Sửa dữ liệu giả lập | ✅ PR #5 | `data/synthetic/`, changelog 14/10 |
| 5. Khu dữ liệu thật | ⛔ chờ D-01, D-07, nơi host | docs/07 mục 7 |
| 6. Pilot + `kb-1.3.0` | ⛔ chờ bác sĩ duyệt | docs/07 mục 7 |

Số liệu hiện tại: 52 test pass; CI Python 3.9 + 3.12; pipeline trên 191 record giả: 91 CLASSIFIED, 7 INVALID_DATA (đều là ca cố ý sai F-07/F-12); 53 ca cũ có nhãn chưa phân loại được vì là RAW (cần mapping D-01).

## 2. Việc tiếp theo

**Người dùng / bác sĩ:**
1. Deploy demo lên Streamlit Community Cloud (repo `fossbk-spec/drmayday-rule-based`, nhánh `main`, file `main.py`) – cần tài khoản người dùng.
2. Buổi review với bác sĩ: 24 mục `todo` trong `rules/fields.yaml`; F-01 (shape triệu chứng cấp, nhánh cấp thường); `R-PV-THEODOI` lệch `docs/01_rules.md`; ngưỡng F-02..F-11; quyết định D-01..D-11 ([09](implementation-guide/09-decisions-and-templates.md)).
3. Chốt D-07 (dữ liệu thật: ai truy cập, có lưu không) và nơi host khu dữ liệu thật → mở Bước 5.

**Kỹ thuật làm được ngay (không chờ quyết định):**
- Soạn tài liệu "danh sách quyết định cho bác sĩ" kèm ca minh họa giả (đã đề xuất, chưa làm).
- `extract_min_sbp` khi có cả giá trị sẵn và bảng sinh hiệu – cần người dùng chọn chính sách trước.
- Allowlist trường xuất + PII lồng nhau/ghi chú trong `src/anonymize.py` – cần D-07.

## 3. Cách làm việc đã thống nhất

- **Mỗi bước:** Claude viết brief `docs/tasks/BN-*.md` → Codex thực hiện → Claude review diff, sửa nhỏ trực tiếp, commit (author "Codex") → mở PR → CI + báo cáo tác động → **Claude tự merge PR kỹ thuật khi CI xanh**.
- **Luôn chờ người:** thay đổi điều kiện/ngưỡng/nhãn luật (báo cáo tác động có ca đổi) cần bác sĩ duyệt; kích hoạt `knowledge/active.yaml` `real:`; dữ liệu bệnh án thật; secret; deploy khu dữ liệu thật.
- **Tiết kiệm token:** một phiên Codex mỗi lúc, effort `medium`, prompt ngắn chỉ liệt kê file cần đọc; Codex không mở trình duyệt (kiểm tra UI bằng `streamlit.testing.AppTest`); review = chạy test một lần + đọc diff.
- **Không tự điền** trường thiếu trong dữ liệu; không đổi ngưỡng y khoa để test pass.

## 4. Thiết lập máy mới

```powershell
git clone git@github.com:fossbk-spec/drmayday-rule-based.git
cd drmayday-rule-based
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONDONTWRITEBYTECODE = "1"
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests      # 52 test
.\.venv\Scripts\python.exe -m streamlit run main.py                    # demo local
```

- **Codex trên Windows:** sandbox của Codex không đọc được Python trong `%LOCALAPPDATA%`; `tools\setup_machine.ps1 -ForCodex` tự copy Python vào `..\.tools\` và tạo `.venv` từ đó (làm tay: copy thư mục cài Python vào thư mục sandbox đọc được rồi `<bản copy>\python.exe -m venv .venv`). Kiểm tra: `codex exec -s read-only` chạy lệnh test trả `OK`.
- Chạy Codex: `codex exec -m <model> -c model_reasoning_effort=medium -C <repo> -s workspace-write -o <report.md> - < prompt.txt`. Sandbox không ghi được `.git` → Claude commit.
- Python có ký tự tiếng Việt trên console Windows: thêm `-X utf8`.
- Working tree Windows dùng CRLF; `.gitattributes` buộc LF cho `knowledge/`, `rules/`, `tests/golden/`; hash gói tính trên bytes đã chuẩn hóa LF.
- Golden test: thay đổi engine/luật có chủ đích → `UPDATE_GOLDEN=1` rồi review diff `tests/golden/engine_outputs.json` trong PR.
- Anonymizer cần biến môi trường `DRMAYDAY_TOKEN_SALT` (không có salt mặc định).
