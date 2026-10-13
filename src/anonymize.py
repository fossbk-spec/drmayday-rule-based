"""
Module khử định danh dữ liệu bệnh nhân (Anonymization).
Loại bỏ và mã hóa các trường nhận dạng cá nhân (PII) như Họ tên, SĐT, Số thẻ BHYT, Địa chỉ chi tiết.
"""

import hashlib
import os
import re
from typing import Any, Dict, Optional


class PatientAnonymizer:
    SALT_ENV = "DRMAYDAY_TOKEN_SALT"

    def __init__(self, salt: Optional[str] = None):
        # Không dùng salt mặc định trong source: ai đọc code cũng dò được token từ mã dễ đoán.
        salt = salt if salt is not None else os.environ.get(self.SALT_ENV)
        if not salt:
            raise ValueError(f"Cần salt bí mật: truyền salt hoặc đặt biến môi trường {self.SALT_ENV}.")
        self.salt = salt

    def _hash_value(self, value: str) -> str:
        """Tạo mã băm SHA-256 kèm salt cho mã định danh."""
        if not value:
            return ""
        salted = f"{value}_{self.salt}".encode("utf-8")
        return hashlib.sha256(salted).hexdigest()[:16].upper()

    def _mask_name(self, name: str) -> str:
        """Che giấu họ tên (VD: Nguyễn Văn Anh -> N*** Anh)."""
        if not name or not isinstance(name, str):
            return "UNKNOWN_PATIENT"
        parts = name.strip().split()
        if not parts:
            return "UNKNOWN_PATIENT"
        if len(parts) == 1:
            return parts[0][0] + "***"
        return f"{parts[0][0]}*** {parts[-1]}"

    def _mask_phone(self, phone: str) -> str:
        """Che giấu số điện thoại (VD: 0912345678 -> 091****678)."""
        if not phone or not isinstance(phone, str):
            return ""
        clean_phone = re.sub(r"\D", "", phone)
        if len(clean_phone) >= 7:
            return f"{clean_phone[:3]}****{clean_phone[-3:]}"
        return "****"

    def anonymize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Khử định danh bản ghi bệnh án.
        Giữ nguyên các chỉ số lâm sàng, cận lâm sàng và chẩn đoán.
        """
        anon_record = record.copy()
        raw_id = anon_record.pop("ma_benh_nhan", None)

        # 1. Sinh token ID; mã gốc không còn trong bản xuất. Thiếu mã → token None,
        # không gộp mọi bản ghi thiếu ID thành cùng một bệnh nhân.
        raw_id = str(raw_id).strip() if raw_id is not None else ""
        anon_record["patient_token_id"] = f"PT_{self._hash_value(raw_id)}" if raw_id else None

        # 2. Xóa hoặc che giấu PII trực tiếp
        if "ho_ten" in anon_record:
            anon_record["ho_ten"] = self._mask_name(anon_record["ho_ten"])

        if "so_dien_thoai" in anon_record:
            anon_record["so_dien_thoai"] = self._mask_phone(anon_record["so_dien_thoai"])

        if "bhyt_so_the" in anon_record and anon_record["bhyt_so_the"]:
            anon_record["bhyt_so_the"] = self._hash_value(str(anon_record["bhyt_so_the"]))

        # 3. Làm sạch địa chỉ chi tiết, chỉ giữ lại cấp tỉnh/thành nếu cần nghiên cứu
        if "dia_chi_so_nha_thon_pho" in anon_record:
            anon_record["dia_chi_so_nha_thon_pho"] = "[MASKED_STREET]"
        if "nguoi_nha_ho_ten_dia_chi" in anon_record:
            anon_record["nguoi_nha_ho_ten_dia_chi"] = "[MASKED_CONTACT]"
        if "nguoi_nha_so_dien_thoai" in anon_record:
            anon_record["nguoi_nha_so_dien_thoai"] = self._mask_phone(anon_record["nguoi_nha_so_dien_thoai"])

        return anon_record