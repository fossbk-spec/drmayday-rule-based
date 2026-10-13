import os
import unittest
from unittest import mock

from src.anonymize import PatientAnonymizer


class AnonymizeTest(unittest.TestCase):
    """SEC-01: bản xuất không chứa mã gốc; thiếu mã không gộp bệnh nhân."""

    def setUp(self):
        self.anon = PatientAnonymizer(salt="test-salt")

    def test_original_id_removed_and_token_stable(self):
        first = self.anon.anonymize_record({"ma_benh_nhan": "BN001", "tuoi": 30})
        second = self.anon.anonymize_record({"ma_benh_nhan": "BN001"})
        self.assertNotIn("ma_benh_nhan", first)
        self.assertNotIn("BN001", repr(first))
        self.assertTrue(first["patient_token_id"].startswith("PT_"))
        self.assertEqual(first["patient_token_id"], second["patient_token_id"])
        self.assertEqual(first["tuoi"], 30)

    def test_different_ids_get_different_tokens(self):
        a = self.anon.anonymize_record({"ma_benh_nhan": "BN001"})["patient_token_id"]
        b = self.anon.anonymize_record({"ma_benh_nhan": "BN002"})["patient_token_id"]
        self.assertNotEqual(a, b)

    def test_missing_id_is_not_merged(self):
        for record in ({}, {"ma_benh_nhan": None}, {"ma_benh_nhan": "  "}):
            with self.subTest(record=record):
                out = self.anon.anonymize_record(record)
                self.assertIsNone(out["patient_token_id"])
                self.assertNotIn("ma_benh_nhan", out)

    def test_blank_name_does_not_crash(self):
        self.assertEqual(self.anon.anonymize_record({"ho_ten": "   "})["ho_ten"], "UNKNOWN_PATIENT")

    def test_salt_is_required(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                PatientAnonymizer()
        with mock.patch.dict(os.environ, {PatientAnonymizer.SALT_ENV: "env-salt"}, clear=True):
            self.assertEqual(PatientAnonymizer().salt, "env-salt")

    def test_input_not_mutated(self):
        record = {"ma_benh_nhan": "BN001", "ho_ten": "Nguyễn Văn Anh"}
        self.anon.anonymize_record(record)
        self.assertEqual(record, {"ma_benh_nhan": "BN001", "ho_ten": "Nguyễn Văn Anh"})


if __name__ == "__main__":
    unittest.main()
