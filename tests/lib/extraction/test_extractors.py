from django.test import TestCase
from unittest.mock import patch, MagicMock
import tempfile
import os

from lib.extraction.factory import get_extractor
from lib.extraction.pdf_extractor import PdfExtractor
from lib.extraction.text_extractor import TxtExtractor


class ExtractorFactoryTest(TestCase):
    """Test cases for extractor factory"""

    def test_get_pdf_extractor(self):
        """Test getting PDF extractor"""
        extractor = get_extractor("document.pdf")
        self.assertIsInstance(extractor, PdfExtractor)

    def test_get_txt_extractor(self):
        """Test getting text extractor"""
        extractor = get_extractor("document.txt")
        self.assertIsInstance(extractor, TxtExtractor)

    def test_unsupported_file_type(self):
        """Test error with unsupported file type"""
        with self.assertRaises(ValueError) as context:
            get_extractor("document.doc")
        self.assertIn("Unsupported", str(context.exception))

    def test_case_insensitive_extension(self):
        """Test that extension matching is case-insensitive"""
        pdf_extractor = get_extractor("document.PDF")
        txt_extractor = get_extractor("document.TXT")
        
        self.assertIsInstance(pdf_extractor, PdfExtractor)
        self.assertIsInstance(txt_extractor, TxtExtractor)


class PdfExtractorTest(TestCase):
    """Test cases for PDF extractor"""

    def setUp(self):
        """Set up test extractor"""
        self.extractor = PdfExtractor()

    @patch('lib.extraction.pdf_extractor.pdfplumber.open')
    def test_extract_text_from_pdf(self, mock_open):
        """Test extracting text from PDF"""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 text"
        mock_pdf.pages = [mock_page]
        mock_open.return_value.__enter__.return_value = mock_pdf
        
        result = self.extractor.extract("test.pdf")
        
        self.assertEqual(result, "Page 1 text")

    @patch('lib.extraction.pdf_extractor.pdfplumber.open')
    def test_extract_multipage_pdf(self, mock_open):
        """Test extracting text from multi-page PDF"""
        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2"
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_open.return_value.__enter__.return_value = mock_pdf
        
        result = self.extractor.extract("test.pdf")
        
        self.assertIn("Page 1", result)
        self.assertIn("Page 2", result)

    @patch('lib.extraction.pdf_extractor.pdfplumber.open')
    def test_extract_pdf_with_empty_pages(self, mock_open):
        """Test extracting PDF with some empty pages"""
        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None  # Empty page
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_open.return_value.__enter__.return_value = mock_pdf
        
        result = self.extractor.extract("test.pdf")
        
        self.assertEqual(result, "Content")

    @patch('lib.extraction.pdf_extractor.pdfplumber.open')
    def test_extract_with_progress_callback(self, mock_open):
        """Test that progress callback is called"""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Text"
        mock_pdf.pages = [mock_page]
        mock_open.return_value.__enter__.return_value = mock_pdf
        
        callback = MagicMock()
        self.extractor.extract("test.pdf", progress_callback=callback)
        
        # Verify callback was called
        self.assertTrue(callback.called)


class TxtExtractorTest(TestCase):
    """Test cases for text extractor"""

    def setUp(self):
        """Set up test extractor"""
        self.extractor = TxtExtractor()

    def test_extract_text_from_file(self):
        """Test extracting text from text file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content.")
            temp_path = f.name
        
        try:
            result = self.extractor.extract(temp_path)
            self.assertEqual(result, "This is test content.")
        finally:
            os.unlink(temp_path)

    def test_extract_multiline_text(self):
        """Test extracting multiline text"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3")
            temp_path = f.name
        
        try:
            result = self.extractor.extract(temp_path)
            self.assertIn("Line 1", result)
            self.assertIn("Line 2", result)
            self.assertIn("Line 3", result)
        finally:
            os.unlink(temp_path)

    def test_extract_utf8_text(self):
        """Test extracting UTF-8 encoded text"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Special chars: é, ñ, 中文")
            temp_path = f.name
        
        try:
            result = self.extractor.extract(temp_path)
            self.assertIn("é", result)
            self.assertIn("中文", result)
        finally:
            os.unlink(temp_path)

    def test_extract_nonexistent_file(self):
        """Test extracting from nonexistent file"""
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract("/nonexistent/path/file.txt")

    def test_extract_with_progress_callback(self):
        """Test that progress callback is called"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            callback = MagicMock()
            self.extractor.extract(temp_path, progress_callback=callback)
            
            # Verify callback was called
            self.assertTrue(callback.called)
        finally:
            os.unlink(temp_path)
