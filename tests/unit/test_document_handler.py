"""Tests for document handler functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from data4ai.document_handler import DocumentHandler
from data4ai.exceptions import ValidationError


class TestDocumentTypeDetection:
    """Test document type detection."""

    def test_detect_pdf_type(self):
        """Test PDF file type detection."""
        assert DocumentHandler.detect_document_type(Path("test.pdf")) == "pdf"
        assert DocumentHandler.detect_document_type(Path("document.PDF")) == "pdf"

    def test_detect_docx_type(self):
        """Test DOCX file type detection."""
        assert DocumentHandler.detect_document_type(Path("test.docx")) == "docx"
        assert DocumentHandler.detect_document_type(Path("test.doc")) == "docx"
        assert DocumentHandler.detect_document_type(Path("DOCUMENT.DOCX")) == "docx"

    def test_detect_markdown_type(self):
        """Test Markdown file type detection."""
        assert DocumentHandler.detect_document_type(Path("README.md")) == "md"
        assert DocumentHandler.detect_document_type(Path("doc.markdown")) == "md"
        assert DocumentHandler.detect_document_type(Path("TEST.MD")) == "md"

    def test_detect_text_type(self):
        """Test text file type detection."""
        assert DocumentHandler.detect_document_type(Path("file.txt")) == "txt"
        assert DocumentHandler.detect_document_type(Path("readme.text")) == "txt"
        assert DocumentHandler.detect_document_type(Path("FILE.TXT")) == "txt"

    def test_unsupported_type_raises_error(self):
        """Test that unsupported file types raise ValidationError."""
        with pytest.raises(ValidationError, match="Unsupported document type"):
            DocumentHandler.detect_document_type(Path("file.jpg"))
        
        with pytest.raises(ValidationError, match="Unsupported document type"):
            DocumentHandler.detect_document_type(Path("spreadsheet.xlsx"))


class TestTextExtraction:
    """Test text extraction from documents."""

    @patch("builtins.open")
    def test_extract_txt_text(self, mock_open):
        """Test text extraction from TXT file."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "This is a test document."
        )
        
        # Create a mock path that exists
        with patch.object(Path, "exists", return_value=True):
            text = DocumentHandler.extract_text(Path("test.txt"))
        
        assert text == "This is a test document."
        mock_open.assert_called_once_with(Path("test.txt"), "r", encoding="utf-8")

    @patch("builtins.open")
    def test_extract_markdown_text_without_library(self, mock_open):
        """Test markdown extraction without markdown library."""
        markdown_content = """# Header
        
This is **bold** and this is *italic*.

[Link](https://example.com)

```python
code block
```
"""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            markdown_content
        )
        
        # Patch MARKDOWN_AVAILABLE to False
        with patch.object(Path, "exists", return_value=True):
            with patch("data4ai.document_handler.MARKDOWN_AVAILABLE", False):
                text = DocumentHandler.extract_text(Path("test.md"))
        
        # Basic markdown stripping should remove formatting
        assert "# Header" not in text
        assert "**bold**" not in text
        assert "*italic*" not in text
        assert "[Link]" not in text
        assert "```" not in text

    def test_extract_text_file_not_found(self):
        """Test that missing files raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Document not found"):
            DocumentHandler.extract_text(Path("/nonexistent/file.txt"))

    @patch("data4ai.document_handler.PYPDF_AVAILABLE", False)
    def test_extract_pdf_without_library(self):
        """Test PDF extraction without pypdf raises error."""
        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(ValidationError, match="PDF support not available"):
                DocumentHandler.extract_text(Path("test.pdf"))

    @patch("data4ai.document_handler.DOCX_AVAILABLE", False)
    def test_extract_docx_without_library(self):
        """Test DOCX extraction without python-docx raises error."""
        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(ValidationError, match="DOCX support not available"):
                DocumentHandler.extract_text(Path("test.docx"))


class TestChunkExtraction:
    """Test document chunking functionality."""

    @patch.object(DocumentHandler, "extract_text")
    def test_extract_chunks_basic(self, mock_extract):
        """Test basic chunk extraction."""
        mock_extract.return_value = "This is a test document. " * 100  # Long text
        
        chunks = DocumentHandler.extract_chunks(
            Path("test.txt"),
            chunk_size=50,
            overlap=10,
        )
        
        assert len(chunks) > 1
        assert all("id" in chunk for chunk in chunks)
        assert all("text" in chunk for chunk in chunks)
        assert all("start" in chunk for chunk in chunks)
        assert all("end" in chunk for chunk in chunks)
        assert all(chunk["source"] == "test.txt" for chunk in chunks)

    @patch.object(DocumentHandler, "extract_text")
    def test_extract_chunks_with_overlap(self, mock_extract):
        """Test chunk extraction with overlap."""
        # Create text with clear sentence boundaries
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        mock_extract.return_value = text
        
        chunks = DocumentHandler.extract_chunks(
            Path("test.txt"),
            chunk_size=30,
            overlap=10,
        )
        
        # Should create multiple chunks with overlap
        assert len(chunks) >= 2
        
        # Check that chunks have some overlap
        if len(chunks) > 1:
            # The end of first chunk should overlap with start of second
            assert chunks[0]["end"] > chunks[1]["start"] or chunks[0]["end"] == chunks[1]["start"]

    @patch.object(DocumentHandler, "extract_text")
    def test_extract_chunks_empty_document(self, mock_extract):
        """Test chunk extraction from empty document."""
        mock_extract.return_value = ""
        
        chunks = DocumentHandler.extract_chunks(Path("empty.txt"))
        
        assert chunks == []

    @patch.object(DocumentHandler, "extract_text")
    def test_extract_chunks_sentence_boundaries(self, mock_extract):
        """Test that chunks break at sentence boundaries when possible."""
        text = "First sentence. Second sentence. Third sentence."
        mock_extract.return_value = text
        
        chunks = DocumentHandler.extract_chunks(
            Path("test.txt"),
            chunk_size=20,  # Small chunks to force breaks
            overlap=0,
        )
        
        # Chunks should end at sentence boundaries (with period and space)
        for chunk in chunks[:-1]:  # Except possibly the last chunk
            chunk_text = chunk["text"]
            if chunk_text and not chunk_text.endswith(text):
                # Check if it ends at a sentence boundary
                assert (
                    chunk_text.endswith(".")
                    or chunk_text.endswith("!")
                    or chunk_text.endswith("?")
                ), f"Chunk doesn't end at sentence boundary: '{chunk_text}'"


class TestPrepareForGeneration:
    """Test document preparation for generation."""

    @patch.object(DocumentHandler, "extract_chunks")
    @patch.object(DocumentHandler, "detect_document_type")
    def test_prepare_for_generation_basic(self, mock_detect, mock_chunks):
        """Test basic document preparation."""
        mock_detect.return_value = "pdf"
        mock_chunks.return_value = [
            {"id": 0, "text": "chunk1", "start": 0, "end": 10, "source": "test.pdf"},
            {"id": 1, "text": "chunk2", "start": 10, "end": 20, "source": "test.pdf"},
        ]
        
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 1024
            
            result = DocumentHandler.prepare_for_generation(
                Path("test.pdf"),
                extraction_type="qa",
                chunk_size=1000,
            )
        
        assert result["document_type"] == "pdf"
        assert result["document_name"] == "test.pdf"
        assert result["extraction_type"] == "qa"
        assert result["total_chunks"] == 2
        assert len(result["chunks"]) == 2
        assert result["metadata"]["chunk_size"] == 1000
        assert result["metadata"]["file_size"] == 1024

    @patch.object(DocumentHandler, "extract_chunks")
    @patch.object(DocumentHandler, "detect_document_type")
    def test_prepare_for_generation_with_advanced(self, mock_detect, mock_chunks):
        """Test document preparation with advanced extraction."""
        mock_detect.return_value = "pdf"
        mock_chunks.return_value = []
        
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 2048
            
            result = DocumentHandler.prepare_for_generation(
                Path("test.pdf"),
                extraction_type="summary",
                chunk_size=500,
                use_advanced=True,
            )
        
        assert result["extraction_type"] == "summary"
        assert result["metadata"]["chunk_size"] == 500
        assert result["metadata"]["advanced_extraction"] is True
        
        # Verify extract_chunks was called with use_advanced=True
        mock_chunks.assert_called_once_with(
            Path("test.pdf"),
            chunk_size=500,
            use_advanced=True,
        )


class TestPDFExtraction:
    """Test PDF-specific extraction."""

    @patch("data4ai.document_handler.PYPDF_AVAILABLE", True)
    @patch("data4ai.document_handler.pypdf")
    def test_extract_pdf_with_pypdf(self, mock_pypdf):
        """Test PDF extraction using pypdf."""
        # Mock PDF reader
        mock_reader = Mock()
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pypdf.PdfReader.return_value = mock_reader
        
        with patch.object(Path, "exists", return_value=True):
            text = DocumentHandler._extract_pdf_text(Path("test.pdf"))
        
        assert "Page 1 content" in text
        assert "Page 2 content" in text
        assert "--- Page 1 ---" in text
        assert "--- Page 2 ---" in text

    @patch("data4ai.document_handler.PDFPLUMBER_AVAILABLE", True)
    @patch("data4ai.document_handler.pdfplumber")
    def test_extract_pdf_with_pdfplumber(self, mock_pdfplumber):
        """Test PDF extraction using pdfplumber (advanced)."""
        # Mock pdfplumber
        mock_pdf = Mock()
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Advanced page 1"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Advanced page 2"
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        with patch.object(Path, "exists", return_value=True):
            text = DocumentHandler._extract_pdf_text(Path("test.pdf"), use_advanced=True)
        
        assert "Advanced page 1" in text
        assert "Advanced page 2" in text


class TestDOCXExtraction:
    """Test DOCX-specific extraction."""

    @patch("data4ai.document_handler.DOCX_AVAILABLE", True)
    @patch("data4ai.document_handler.Document")
    def test_extract_docx_with_paragraphs(self, mock_document):
        """Test DOCX extraction with paragraphs."""
        # Mock document
        mock_doc = Mock()
        mock_para1 = Mock()
        mock_para1.text = "First paragraph"
        mock_para2 = Mock()
        mock_para2.text = "Second paragraph"
        mock_para3 = Mock()
        mock_para3.text = ""  # Empty paragraph should be skipped
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_doc.tables = []
        mock_document.return_value = mock_doc
        
        with patch.object(Path, "exists", return_value=True):
            text = DocumentHandler._extract_docx_text(Path("test.docx"))
        
        assert "First paragraph" in text
        assert "Second paragraph" in text
        assert text.count("\n\n") >= 1  # Paragraphs separated

    @patch("data4ai.document_handler.DOCX_AVAILABLE", True)
    @patch("data4ai.document_handler.Document")
    def test_extract_docx_with_tables(self, mock_document):
        """Test DOCX extraction with tables."""
        # Mock document with table
        mock_doc = Mock()
        mock_doc.paragraphs = []
        
        # Mock table
        mock_table = Mock()
        mock_row = Mock()
        mock_cell1 = Mock()
        mock_cell1.text = "Cell 1"
        mock_cell2 = Mock()
        mock_cell2.text = "Cell 2"
        mock_row.cells = [mock_cell1, mock_cell2]
        mock_table.rows = [mock_row]
        mock_doc.tables = [mock_table]
        
        mock_document.return_value = mock_doc
        
        with patch.object(Path, "exists", return_value=True):
            text = DocumentHandler._extract_docx_text(Path("test.docx"))
        
        assert "Cell 1" in text
        assert "Cell 2" in text
        assert "|" in text  # Table cells separated by |