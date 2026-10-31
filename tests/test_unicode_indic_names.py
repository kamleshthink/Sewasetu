# -*- coding: utf-8 -*-
"""
Tests for Indian language (Assamese / Indic) name preservation and Unicode PDF generation.
"""
import io
import os
import sys
import unittest
from unittest.mock import MagicMock
import pypdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "app"))

from app import sanitize, generate_acknowledgment


class TestUnicodeIndicNames(unittest.TestCase):

    def test_sanitize_does_not_truncate_multibyte_indic_names(self):
        """
        Verify that sanitize does not chop Indian language names at 20 bytes.
        Assamese/Bengali/Hindi UTF-8 characters are 3 bytes each.
        A name with 16 characters is ~48 bytes and should be preserved in full.
        """
        assamese_name = "কমলেশ কুমাৰ শৰ্মা"
        sanitized = sanitize(assamese_name)
        self.assertEqual(sanitized, assamese_name)

    def test_pdf_renders_indic_characters_without_question_marks(self):
        """
        Verify that acknowledgment PDF renders Indic/Assamese names without replacing with '?'.
        """
        mock_cur = MagicMock()
        assamese_name = "প্ৰণৱ বৰুৱা"
        mock_cur.fetchone.return_value = (
            "SSP26123456",
            assamese_name,
            "9876543210",
            "1950-01-01",
            "Panidihing",
            "Namti",
            "1234567890",
            "SBIN0001234",
            "2026-05-01 10:00:00",
            "PENDING"
        )

        pdf_bytes = generate_acknowledgment(mock_cur, 1)
        self.assertTrue(len(pdf_bytes) > 0)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = reader.pages[0].extract_text()
        # Assert applicant name is NOT replaced by '?'
        self.assertNotIn("Applicant Name ?", text)
        self.assertIn(assamese_name, text)
