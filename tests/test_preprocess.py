import copy
import unittest

from src.preprocess import MedicalPreprocessor


class PreprocessNoDefaultsTest(unittest.TestCase):
    """TECH-02: không điền tuổi 25, HATT 120, thời gian 0/1 và không dùng ngày chạy chương trình."""

    def setUp(self):
        self.pre = MedicalPreprocessor()

    def test_existing_age_is_kept_without_birth_date(self):
        self.assertEqual(self.pre.preprocess_record({"tuoi": 5})["tuoi"], 5)

    def test_existing_age_is_not_overwritten_by_dates(self):
        out = self.pre.preprocess_record({"tuoi": 5, "ngay_sinh": "1990-01-01", "ngay_kham": "2026-01-01"})
        self.assertEqual(out["tuoi"], 5)

    def test_age_computed_from_dates(self):
        out = self.pre.preprocess_record({"ngay_sinh": "2016-01-01", "ngay_kham": "2026-01-01"})
        self.assertAlmostEqual(out["tuoi"], 10.0, places=1)

    def test_missing_age_stays_missing(self):
        for record in ({}, {"ngay_sinh": "2016-01-01"}, {"ngay_sinh": "bad", "ngay_kham": "2026-01-01"},
                       {"ngay_sinh": "2027-01-01", "ngay_kham": "2026-01-01"}):
            with self.subTest(record=record):
                self.assertNotIn("tuoi", self.pre.preprocess_record(record))

    def test_missing_blood_pressure_is_not_filled(self):
        out = self.pre.preprocess_record({})
        self.assertNotIn("huyet_ap_tam_thu_thap_nhat", out)
        self.assertNotIn("huyet_ap_tam_thu_nen", out)
        out = self.pre.preprocess_record({"huyet_ap_tam_thu_thap_nhat": None, "huyet_ap_tam_thu_nen": None})
        self.assertIsNone(out["huyet_ap_tam_thu_thap_nhat"])
        self.assertIsNone(out["huyet_ap_tam_thu_nen"])

    def test_min_sbp_from_vitals(self):
        out = self.pre.preprocess_record({"bang_theo_doi_dau_hieu_sinh_ton": [
            {"huyet_ap": "110/70"}, {"huyet_ap": "85/50"}, {"huyet_ap": "?"}, "bad-row"]})
        self.assertEqual(out["huyet_ap_tam_thu_thap_nhat"], 85.0)

    def test_invalid_measurement_is_left_for_validation(self):
        out = self.pre.preprocess_record({"huyet_ap_tam_thu_thap_nhat": True})
        self.assertIs(out["huyet_ap_tam_thu_thap_nhat"], True)

    def test_onset_time_not_invented(self):
        self.assertNotIn("thoi_gian_khoi_phat_gio", self.pre.preprocess_record({}))
        self.assertEqual(self.pre.preprocess_record({"thoi_gian_khoi_phat_pv": 2})["thoi_gian_khoi_phat_gio"], 2.0)
        self.assertEqual(self.pre.preprocess_record({"thoi_gian_khoi_phat_gio": 0})["thoi_gian_khoi_phat_gio"], 0.0)

    def test_input_not_mutated(self):
        record = {"tuoi": 5, "trieu_chung_da_hien_tai": {"danh_sach_chon": ["Ngứa"]}}
        snapshot = copy.deepcopy(record)
        self.pre.preprocess_record(record)
        self.assertEqual(record, snapshot)


if __name__ == "__main__":
    unittest.main()
