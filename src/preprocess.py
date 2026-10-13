"""
Module tiền xử lý dữ liệu và tính toán biến phái sinh (Feature Engineering).
Tính tuổi theo năm/tháng, thời gian mắc bệnh theo tuần, cờ tổn thương cơ quan.

Nguyên tắc: không tự điền giá trị khi thiếu dữ kiện. Trường thiếu được giữ nguyên
(vắng mặt hoặc None) để engine trả INSUFFICIENT_DATA thay vì kết luận trên số giả.
"""

import math
from datetime import datetime
from typing import Any, Dict, Optional


def _is_number(value: Any) -> bool:
    """Số hữu hạn, không phải bool."""
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


class MedicalPreprocessor:
    @staticmethod
    def calculate_age(ngay_sinh_str: Any, ngay_kham_str: Any) -> Optional[float]:
        """Tính tuổi thập phân từ ngày sinh và ngày khám; None nếu thiếu hoặc không hợp lệ."""
        if not isinstance(ngay_sinh_str, str) or not isinstance(ngay_kham_str, str):
            return None
        try:
            ns = datetime.strptime(ngay_sinh_str[:10], "%Y-%m-%d")
            nk = datetime.strptime(ngay_kham_str[:10], "%Y-%m-%d")
        except ValueError:
            return None
        diff_days = (nk - ns).days
        if diff_days < 0:
            return None  # Ngày khám trước ngày sinh: dữ liệu mâu thuẫn, không đoán
        return round(diff_days / 365.25, 3)

    @staticmethod
    def extract_min_sbp(record: Dict[str, Any]) -> Optional[float]:
        """HATT thấp nhất từ biến chỉ điểm hoặc lưới sinh hiệu; None nếu không có số đo hợp lệ."""
        val = record.get("huyet_ap_tam_thu_thap_nhat")
        if _is_number(val) and val > 0:
            return float(val)

        # Tìm trong lưới sinh hiệu nếu biến đơn chưa được tính
        vitals = record.get("bang_theo_doi_dau_hieu_sinh_ton")
        if not isinstance(vitals, list):
            return None
        sbp_list = []
        for row in vitals:
            if not isinstance(row, dict):
                continue
            bp_str = row.get("huyet_ap")
            if isinstance(bp_str, str) and "/" in bp_str:
                try:
                    sbp = float(bp_str.split("/")[0].strip())
                except ValueError:
                    continue
                if math.isfinite(sbp) and sbp > 0:
                    sbp_list.append(sbp)
        return min(sbp_list) if sbp_list else None

    def preprocess_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Chuẩn hóa dữ liệu thô sang dữ liệu sạch sẵn sàng nạp cho Rule Engine."""
        processed = record.copy()

        # 1. Tuổi: giữ tuổi hợp lệ đã có; chỉ tính khi có cả ngày sinh và ngày khám.
        # Không dùng ngày chạy chương trình thay ngày khám. Chính sách khi tuổi có sẵn
        # mâu thuẫn với ngày sinh chưa được chốt, nên không ghi đè.
        if not _is_number(processed.get("tuoi")):
            age = self.calculate_age(processed.get("ngay_sinh"), processed.get("ngay_kham"))
            if age is not None:
                processed["tuoi"] = age

        # 2. HATT thấp nhất: chỉ ghi khi tìm được số đo hợp lệ; HATT nền không có mặc định.
        min_sbp = self.extract_min_sbp(processed)
        if min_sbp is not None:
            processed["huyet_ap_tam_thu_thap_nhat"] = min_sbp

        # 3. Chuẩn hóa thời gian khởi phát mày đay cấp về số giờ
        thoi_gian_gio = processed.get("thoi_gian_khoi_phat_gio")
        if thoi_gian_gio is None:
            # Nếu là bệnh án phản vệ, trường tên là thoi_gian_khoi_phat_pv
            thoi_gian_gio = processed.get("thoi_gian_khoi_phat_pv")
        if _is_number(thoi_gian_gio):
            processed["thoi_gian_khoi_phat_gio"] = float(thoi_gian_gio)

        # 4. Làm phẳng danh sách triệu chứng dạng checkbox lồng nhau
        for sys_field in ["trieu_chung_da_hien_tai_pv", "trieu_chung_da_hien_tai"]:
            if sys_field in processed and isinstance(processed[sys_field], dict):
                ds = processed[sys_field].get("danh_sach_chon", [])
                processed[f"{sys_field}_flatten"] = ds if isinstance(ds, list) else [str(ds)]

        return processed
