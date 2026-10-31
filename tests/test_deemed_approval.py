# -*- coding: utf-8 -*-
"""
Tests for deemed approval job under the Purvanchal Right to Public Services (RTPS) Act.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure app directory is on path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "app"))


class TestDeemedApproval(unittest.TestCase):

    def test_config_path_resolution(self):
        """
        Verify that deemed_approval script finds its configuration file.
        In March 2026, config/settings.ini was consolidated into config/app.ini.
        The script should resolve config without FileNotFoundError.
        """
        import importlib
        try:
            if "scripts.deemed_approval" in sys.modules:
                del sys.modules["scripts.deemed_approval"]
            import scripts.deemed_approval as da
            # Should have loaded SLA_DAYS and SMS_GATEWAY_URL successfully
            self.assertEqual(da.SLA_DAYS, 15)
            self.assertTrue(da.SMS_GATEWAY_URL.startswith("http"))
        except FileNotFoundError as e:
            self.fail(f"deemed_approval failed to locate configuration: {e}")

    @patch("psycopg2.connect")
    @patch("requests.post")
    def test_deemed_approval_execution(self, mock_post, mock_connect):
        """
        Verify that deemed approval updates overdue PENDING applications to DEEMED_APPROVED.
        """
        import scripts.deemed_approval as da

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        # Simulate returning 2 overdue applications
        mock_cur.fetchall.return_value = [("SSP26000001", "9876543210"), ("SSP26000002", "9876543211")]

        da.main()

        # Check that update query was executed with DEEMED_APPROVED and RTPS-AUTO
        mock_cur.execute.assert_called_once()
        query = mock_cur.execute.call_args[0][0]
        self.assertIn("DEEMED_APPROVED", query)
        self.assertIn("RTPS-AUTO", query)
        self.assertEqual(mock_conn.commit.call_count, 1)

        # Check SMS notifications were triggered
        self.assertEqual(mock_post.call_count, 2)
