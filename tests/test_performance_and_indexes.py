# -*- coding: utf-8 -*-
"""
Tests for database performance, indexing, and connection management.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "app"))


class TestPerformanceAndIndexes(unittest.TestCase):

    def test_schema_includes_performance_indexes(self):
        """
        Verify that schema.sql includes necessary indexes for 100k citizen records
        to eliminate full table scans during month-end traffic spikes.
        """
        schema_path = os.path.join(BASE_DIR, "app", "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("idx_applications_mobile", content)
        self.assertIn("idx_applications_status", content)
        self.assertIn("idx_otps_mobile", content)

    def test_database_connection_pool(self):
        """
        Verify that app.py uses connection pooling to prevent
        'FATAL: sorry, too many clients already' during concurrency spikes.
        """
        import app
        self.assertTrue(
            hasattr(app, "db_pool") or hasattr(app, "get_db_conn"),
            "app.py should provide a connection pool manager to avoid client exhaustion"
        )
