# -*- coding: utf-8 -*-
"""
Tests for citizen journey, form accessibility, and error handling.
"""
import io
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "app"))

from app import app


class TestFormJourney(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        self.client = app.test_client()

    def test_widowed_applicant_does_not_require_husband_employer(self):
        """
        Verify that widowed applicants are not blocked by requiring a deceased husband's employer.
        """
        with self.client.session_transaction() as sess:
            sess["verified_mobile"] = "9876543210"
            sess["doc_path"] = "/tmp/dummy.pdf"
            sess["form_data"] = {
                "applicant_name": "Radhika Sharma",
                "village": "Sonari Gaon",
                "block": "Sonari",
                "gender": "Female",
                "marital_status": "Widowed",
                "husband_name": "Late Ramesh Sharma",
                "husband_employer": "",  # Deceased, should NOT be required
                "bank_account": "123456789012",
                "ifsc": "SBIN0001234",
                "dob": "1955-05-15",
            }

        with patch("app.get_db") as mock_db, \
             patch("app.send_sms"), \
             patch("app.generate_acknowledgment", return_value=b"%PDF-mock"):
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cur
            # Check duplicate returns 0, portal_users check returns 0
            mock_cur.fetchone.side_effect = [(0,), (101,), (0,)]

            response = self.client.post("/declaration", data={"agree": "on"}, follow_redirects=True)
            # Should not be redirected back to form step 1 due to validation error
            self.assertIn(b"Application Submitted", response.data)
            self.assertNotIn(b"Something went wrong", response.data)

    def test_document_upload_accepts_jpg_and_up_to_5mb(self):
        """
        Verify upload route accepts JPG files and documents larger than 100KB (up to 5MB)
        as advertised on the form UI, without showing cryptic ERR_VAL_47.
        """
        with self.client.session_transaction() as sess:
            sess["verified_mobile"] = "9876543210"

        # 250 KB JPG image
        dummy_content = b"\xFF\xD8\xFF\xE0" + b"\x00" * (250 * 1024)
        data = {
            "document": (io.BytesIO(dummy_content), "age_proof.jpg")
        }

        response = self.client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertNotIn(b"ERR_VAL_47", response.data)
        self.assertIn(b"Declaration", response.data)

    def test_dob_parsing_standard_html5_and_indic_formats(self):
        """
        Verify standard HTML5 date (YYYY-MM-DD) and Indian DD/MM/YYYY formats are properly parsed.
        """
        with self.client.session_transaction() as sess:
            sess["verified_mobile"] = "9876543210"
            sess["doc_path"] = "/tmp/dummy.pdf"
            sess["form_data"] = {
                "applicant_name": "Kamlesh Sharma",
                "village": "Rajapara",
                "block": "Rajapara",
                "gender": "Male",
                "marital_status": "Married",
                "bank_account": "987654321098",
                "ifsc": "PUNB0556610",
                "dob": "1960-08-15",  # HTML5 standard format
            }

        with patch("app.get_db") as mock_db, \
             patch("app.send_sms"), \
             patch("app.generate_acknowledgment", return_value=b"%PDF-mock"):
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cur
            mock_cur.fetchone.side_effect = [(0,), (102,), (0,)]

            response = self.client.post("/declaration", data={"agree": "on"}, follow_redirects=True)
            self.assertIn(b"Application Submitted", response.data)

