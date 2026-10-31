# -*- coding: utf-8 -*-
"""
Tests for security, authorization, IDOR protection, and SQL injection prevention.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "app"))

from app import app


class TestSecurityAndAuth(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "security-test-key"
        self.client = app.test_client()

    @patch("app.get_db")
    def test_idor_citizen_cannot_view_another_citizens_application(self, mock_db):
        """
        Verify that a logged-in citizen cannot view another citizen's application (IDOR).
        Must return 403 Forbidden.
        """
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        # Application 100 belongs to mobile 9876543210
        mock_cur.fetchone.return_value = (
            "SSP26100", "Sunita Das", "9876543210", "1958-01-01",
            "Milanpur", "Borgaon", "1234567890", "SBIN0001234",
            "PENDING", "2026-01-01 10:00:00", None
        )

        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["portal_mobile"] = "8888888888"  # Different user's mobile

        response = self.client.get("/application/100")
        self.assertEqual(response.status_code, 403)

    @patch("app.get_db")
    def test_citizen_cannot_approve_or_reject_applications(self, mock_db):
        """
        Verify that a regular logged-in citizen (non-admin) cannot approve or reject applications.
        Must return 403 Forbidden.
        """
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["admin"] = False  # Regular citizen, not admin

        response_approve = self.client.post("/admin/approve/100")
        self.assertEqual(response_approve.status_code, 403)

        response_reject = self.client.post("/admin/reject/100")
        self.assertEqual(response_reject.status_code, 403)

    @patch("app.get_db")
    def test_sql_injection_on_password_reset(self, mock_db):
        """
        Verify that SQL injection attempt in mobile input on password reset
        is safely parameterized and does not crash or execute raw SQL.
        """
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None

        sqli_payload = "9876543210' OR '1'='1"
        response = self.client.post("/status/reset", data={"mobile": sqli_payload})
        self.assertIn(response.status_code, (200, 302))

        # Check that query was parameterized, NOT raw string formatted with payload
        mock_cur.execute.assert_called()
        first_call = mock_cur.execute.call_args_list[0]
        query_sql = first_call[0][0]
        # In parameterized query, '%s' placeholder is used with tuple parameters
        self.assertIn("%s", query_sql)
        self.assertNotIn(sqli_payload, query_sql)

    @patch("app.get_db")
    def test_unauthenticated_user_cannot_access_ack_pdf(self, mock_db):
        """
        Verify that unauthenticated visitors cannot scrape arbitrary citizen acknowledgment slips.
        """
        response = self.client.get("/ack/100.pdf")
        self.assertIn(response.status_code, (401, 403, 302))
