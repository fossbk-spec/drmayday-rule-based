# B2 — Quản lý tri thức tối thiểu: gói bất biến, con trỏ active, báo cáo tác động trong PR

Bước 2 của [lộ trình tối ưu](../07_phuong_an_mo_rong.md#7-lộ-trình-tối-ưu). Nguyên tắc ở [05 — version và thay đổi luật](../implementation-guide/05-rule-versioning-and-change-management.md). Quy trình dùng GitHub: **PR = bản nháp**, **review = duyệt**, **merge gói mới = phát hành**, **PR đổi `active.yaml` = kích hoạt/rollback**. Không đổi hành vi phân loại.

## Ràng buộc

- Không sửa logic `src/classify.py`, nội dung `rules/classification_rules.yaml`, `data/`, `tests/golden/`. Golden test phải pass không cần `UPDATE_GOLDEN`.
- Thư viện chuẩn + PyYAML; tương thích Python 3.9. Không dùng GitHub Action bên thứ ba ngoài `actions/checkout`, `actions/setup-python`.
- Hash phải giống nhau trên Windows và Linux.

## 1. Bố cục

```text
rules/                         # bản làm việc (draft), sửa qua PR như hiện nay
knowledge/
  kb-1.2.1/                    # gói đã phát hành – bất biến
    manifest.yaml
    classification_rules.yaml  # bản sao rules/ tại thời điểm phát hành
    fields.yaml
  active.yaml                  # con trỏ theo môi trường
```

`manifest.yaml`:

```yaml
knowledge_package_id: kb-1.2.1
package_version: 1.2.1          # = version trong classification_rules.yaml
fields_version: 0.1.0           # = version trong fields.yaml
supported_engine_versions: ["1.1.0"]
previous_package_id: null
released_at: "2026-10-13"
change_summary: "Gói đầu tiên: đóng gói YAML 1.2.1 hiện có; chưa qua duyệt chuyên môn."
files:
  classification_rules.yaml: "sha256:<hex>"
  fields.yaml: "sha256:<hex>"
```

`knowledge/active.yaml`:

```yaml
demo: kb-1.2.1
real: null        # chưa có gói được duyệt cho dữ liệu thật
```

**Hash gói** (`knowledge_package_hash`) = `sha256:` + SHA-256 của bytes `manifest.yaml`. Thêm `.gitattributes` buộc LF cho `knowledge/**`, `rules/**`, `tests/golden/**` (ví dụ `knowledge/** text eol=lf`) để hash ổn định giữa hệ điều hành; sau khi thêm, kiểm tra hash tính trên Windows (working tree) khớp với CI.

## 2. Code

`src/knowledge.py` (mới):

- `load_package(package_id, root=ROOT/"knowledge") -> KnowledgePackage` – đọc manifest, **kiểm tra hash từng file** khớp manifest (sai → `ValueError` nêu file), kiểm tra `ENGINE_VERSION` thuộc `supported_engine_versions`, trả đối tượng có `package_id`, `package_hash`, `rules_path`, `fields_path`, `manifest`.
- `resolve_active(environment, root=...) -> Optional[str]` – đọc `active.yaml`; môi trường không có/`null` → `None`.

`src/classifiers/rule_based.py`: thêm `RuleBasedClassifier.from_package(package_id)` và `RuleBasedClassifier.from_active(environment)` (môi trường không có gói active → `ValueError` rõ ràng). Envelope khi tạo từ gói: `knowledge_package_id` = id manifest, `knowledge_package_hash` = hash gói. Giữ nguyên constructor theo đường dẫn YAML (dùng cho bản nháp) và hành vi hiện tại của nó.

## 3. Công cụ

`tools/release_package.py --version X.Y.Z [--summary "..."] [--previous kb-...]`:
- Kiểm tra `version` trong `rules/classification_rules.yaml` == X.Y.Z; thư mục `knowledge/kb-X.Y.Z` **chưa tồn tại** (đã có → lỗi); `tools/build_fields.py --check` đạt; YAML nạp được bằng engine.
- Sao chép `rules/classification_rules.yaml`, `rules/fields.yaml` vào gói, ghi manifest có hash. Không sửa `active.yaml` (kích hoạt là bước riêng).
- Dùng tool này để tạo `knowledge/kb-1.2.1`.

`tools/check_packages.py [--base-ref REF]`:
- Mọi gói: hash file khớp manifest; `knowledge_package_id` = tên thư mục; `package_version` khớp YAML trong gói; `previous_package_id` (nếu có) tồn tại.
- `active.yaml`: mỗi giá trị là `null` hoặc gói tồn tại.
- Với `--base-ref`: dùng `git diff --name-status <base-ref>...HEAD -- knowledge/` – **sửa hoặc xóa** file trong một gói đã có ở base → lỗi (chỉ được **thêm** gói mới; `active.yaml` được sửa).

`tools/impact_report.py --base-root DIR --head-root DIR --cases FILE [--out report.md]`:
- Mỗi root là một checkout đầy đủ (code + rules). Chạy **trong subprocess với code của chính root đó** (để bắt cả thay đổi engine lẫn luật), phân loại mọi ca trong FILE bằng `ClinicalRuleEngine(<root>/rules/classification_rules.yaml)` (chỉ truyền `du_lieu`), xuất JSON; ngoại lệ một ca ghi tên lỗi, không dừng cả lượt.
- So sánh và viết Markdown tiếng Việt: version/hash YAML hai bên; bảng đếm status trước/sau; số ca đổi status, nhãn, `matched_rule_id`, `blocking_rule_ids`, `missing_fields`; bảng các ca thay đổi (id, mô tả ngắn, trước → sau); **mục riêng các ca có nhãn/candidate Sốc phản vệ hoặc Phản vệ thay đổi**; ngoại lệ. Không có ca nào đổi → ghi rõ "Không có thay đổi kết quả".
- Báo cáo chỉ chứa dữ liệu giả từ FILE, không ghi giá trị bệnh án ngoài id/mô tả ca.

## 4. CI và mẫu yêu cầu

`.github/workflows/tests.yml`: thêm bước `python tools/check_packages.py` (trên PR: `--base-ref origin/${{ github.base_ref }}`, cần `fetch-depth: 0`) và `python tools/build_fields.py --check`.

`.github/workflows/impact.yml` (mới), chạy trên `pull_request` khi đổi `rules/**`, `src/**`, `knowledge/**`:
- checkout head (path `head`) và base ref (path `base`), Python 3.12, cài `requirements.txt`;
- chạy `impact_report.py --base-root base --head-root head --cases head/data/synthetic/rule_logic_cases.json --out report.md`;
- ghi `report.md` vào `$GITHUB_STEP_SUMMARY` và đăng/cập nhật một comment trên PR bằng `gh` (`permissions: pull-requests: write`; tìm comment cũ có marker `<!-- impact-report -->` để sửa thay vì tạo mới). Không đăng được (PR từ fork) → chỉ ghi summary, job không fail.

`.github/ISSUE_TEMPLATE/rule-change.md`: mẫu yêu cầu thay đổi luật cho bác sĩ, theo mẫu REQ trong [09](../implementation-guide/09-decisions-and-templates.md) (loại, lý do, hành vi hiện tại kèm version gói, hành vi mong muốn, ca minh họa **giả**, acceptance, quyết định còn mở). Nhắc rõ: không dán dữ liệu bệnh nhân thật.

## 5. Tài liệu

`docs/knowledge_release.md` (mới, ngắn, tiếng Việt): quy trình thay đổi luật → PR (đọc báo cáo tác động) → bác sĩ duyệt → `release_package.py` → merge → PR kích hoạt `active.yaml` → rollback bằng PR trả `active.yaml` về gói trước. Link từ README mục 6.

## 6. Test — `tests/test_knowledge.py`

1. `load_package("kb-1.2.1")` hợp lệ; envelope từ `from_package` có id/hash gói; kết quả phân loại 138 ca **bằng** bản dùng `rules/` (cùng nội dung).
2. Gói giả trong thư mục tạm có file bị sửa → `load_package` báo lỗi hash; engine không hỗ trợ → lỗi.
3. `resolve_active("demo") == "kb-1.2.1"`, `resolve_active("real") is None`, `from_active("real")` → `ValueError`.
4. `release_package` trên root tạm: tạo gói đúng manifest; chạy lại cùng version → lỗi.
5. `impact_report` với hai root tạm giống nhau → "Không có thay đổi kết quả"; với head có một ngưỡng luật bị sửa (chỉ trong thư mục tạm) → báo cáo liệt kê ca thay đổi.
6. `check_packages.py` (không `--base-ref`) thoát 0 trên repo.

## Hoàn tất khi

- `python -X utf8 -m unittest discover -s tests` pass toàn bộ (33 cũ + mới), golden không đổi; `tools/check_packages.py` và `tools/build_fields.py --check` thoát 0.
- Báo cáo cuối: file tạo/sửa, kết quả test, hash `kb-1.2.1`, giả định (`ASSUMPTION:`), phần chưa kiểm chứng được local (ví dụ workflow GitHub).
