"""Tests for document handler functionality."""

import tempfile
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
        mock_open.assert_called_once_with(Path("test.txt"), encoding="utf-8")

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
        with (
            patch.object(Path, "exists", return_value=True),
            patch("data4ai.document_handler.MARKDOWN_AVAILABLE", False),
        ):
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
        with (
            patch.object(Path, "exists", return_value=True),
            pytest.raises(ValidationError, match="PDF support not available"),
        ):
            DocumentHandler.extract_text(Path("test.pdf"))

    @patch("data4ai.document_handler.DOCX_AVAILABLE", False)
    def test_extract_docx_without_library(self):
        """Test DOCX extraction without python-docx raises error."""
        with (
            patch.object(Path, "exists", return_value=True),
            pytest.raises(ValidationError, match="DOCX support not available"),
        ):
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
            assert (
                chunks[0]["end"] > chunks[1]["start"]
                or chunks[0]["end"] == chunks[1]["start"]
            )

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
            mock_stat.return_value.st_mode = 33188  # Regular file mode

            with patch.object(Path, "is_dir", return_value=False):
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
            mock_stat.return_value.st_mode = 33188  # Regular file mode

            with patch.object(Path, "is_dir", return_value=False):
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

        # Also patch the import inside the method
        with (
            patch("pypdf.PdfReader", return_value=mock_reader),
            patch.object(Path, "exists", return_value=True),
        ):
            text = DocumentHandler._extract_pdf_text(Path("test.pdf"))

        assert "Page 1 content" in text
        assert "Page 2 content" in text

    @patch("data4ai.document_handler.PDFPLUMBER_AVAILABLE", True)
    @patch("data4ai.document_handler.pdfplumber")
    def test_extract_pdf_with_pdfplumber(self, mock_pdfplumber):
        """Test PDF extraction using pdfplumber (advanced)."""
        # Mock pdfplumber with context manager support
        mock_pdf = Mock()
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Advanced page 1"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Advanced page 2"
        mock_pdf.pages = [mock_page1, mock_page2]

        # Make the mock support context manager protocol
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_pdf)
        mock_context.__exit__ = Mock(return_value=None)

        # Also patch the import inside the method
        with (
            patch("pdfplumber.open", return_value=mock_context),
            patch.object(Path, "exists", return_value=True),
        ):
            text = DocumentHandler._extract_pdf_text(
                Path("test.pdf"), use_advanced=True
            )

        assert "Advanced page 1" in text
        assert "Advanced page 2" in text


class TestDOCXExtraction:
    """Test DOCX-specific extraction."""

    @pytest.mark.skip(reason="DOCX dependencies not available in test environment")
    def test_extract_docx_with_paragraphs(self):
        """Test DOCX extraction with paragraphs."""
        with patch("data4ai.document_handler.DOCX_AVAILABLE", True):
            # Mock the Document class
            mock_doc = Mock()
            mock_para1 = Mock()
            mock_para1.text = "First paragraph"
            mock_para2 = Mock()
            mock_para2.text = "Second paragraph"
            mock_para3 = Mock()
            mock_para3.text = ""  # Empty paragraph should be skipped
            mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
            mock_doc.tables = []

            with (
                patch(
                    "builtins.__import__",
                    side_effect=lambda name, *args, **kwargs: (
                        Mock() if name == "docx" else __import__(name, *args, **kwargs)
                    ),
                ),
                patch("data4ai.document_handler.Document", return_value=mock_doc),
                patch.object(Path, "exists", return_value=True),
            ):
                text = DocumentHandler._extract_docx_text(Path("test.docx"))

            assert "First paragraph" in text
            assert "Second paragraph" in text
            assert text.count("\n\n") >= 1  # Paragraphs separated

    @pytest.mark.skip(reason="DOCX dependencies not available in test environment")
    def test_extract_docx_with_tables(self):
        """Test DOCX extraction with tables."""
        with patch("data4ai.document_handler.DOCX_AVAILABLE", True):
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

            with (
                patch(
                    "builtins.__import__",
                    side_effect=lambda name, *args, **kwargs: (
                        Mock() if name == "docx" else __import__(name, *args, **kwargs)
                    ),
                ),
                patch("data4ai.document_handler.Document", return_value=mock_doc),
                patch.object(Path, "exists", return_value=True),
            ):
                text = DocumentHandler._extract_docx_text(Path("test.docx"))

            assert "Cell 1" in text
            assert "Cell 2" in text
            assert "|" in text  # Table cells separated by |


class TestFolderSupport:
    """Test folder scanning and multi-document support."""

    def test_is_supported_file(self):
        """Test checking if file is supported."""
        assert DocumentHandler.is_supported_file(Path("test.pdf")) is True
        assert DocumentHandler.is_supported_file(Path("test.docx")) is True
        assert DocumentHandler.is_supported_file(Path("test.md")) is True
        assert DocumentHandler.is_supported_file(Path("test.txt")) is True
        assert DocumentHandler.is_supported_file(Path("test.jpg")) is False
        assert DocumentHandler.is_supported_file(Path("test.xlsx")) is False

    def test_scan_folder_not_found(self):
        """Test scanning non-existent folder raises error."""
        with pytest.raises(FileNotFoundError, match="Folder not found"):
            DocumentHandler.scan_folder(Path("/nonexistent/folder"))

    def test_scan_folder_not_directory(self):
        """Test scanning file instead of folder raises error."""
        with (
            tempfile.NamedTemporaryFile(suffix=".txt") as tmp_file,
            pytest.raises(ValidationError, match="Path is not a directory"),
        ):
            DocumentHandler.scan_folder(Path(tmp_file.name))

    def test_scan_folder_recursive(self):
        """Test recursive folder scanning."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create test structure
            (tmp_path / "doc1.pdf").touch()
            (tmp_path / "doc2.docx").touch()
            (tmp_path / "readme.md").touch()
            (tmp_path / "notes.txt").touch()
            (tmp_path / "image.jpg").touch()  # Should be ignored

            # Create subdirectory with files
            subdir = tmp_path / "subdir"
            subdir.mkdir()
            (subdir / "doc3.pdf").touch()
            (subdir / "doc4.md").touch()

            # Hidden file (should be ignored)
            (tmp_path / ".hidden.pdf").touch()

            # Scan recursively
            documents = DocumentHandler.scan_folder(tmp_path, recursive=True)

            # Check results
            doc_names = {doc.name for doc in documents}
            assert "doc1.pdf" in doc_names
            assert "doc2.docx" in doc_names
            assert "readme.md" in doc_names
            assert "notes.txt" in doc_names
            assert "doc3.pdf" in doc_names
            assert "doc4.md" in doc_names
            assert "image.jpg" not in doc_names
            assert ".hidden.pdf" not in doc_names

            # Should find 6 documents
            assert len(documents) == 6

    def test_scan_folder_non_recursive(self):
        """Test non-recursive folder scanning."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create test structure
            (tmp_path / "doc1.pdf").touch()
            (tmp_path / "doc2.docx").touch()

            # Create subdirectory with files
            subdir = tmp_path / "subdir"
            subdir.mkdir()
            (subdir / "doc3.pdf").touch()

            # Scan non-recursively
            documents = DocumentHandler.scan_folder(tmp_path, recursive=False)

            # Check results
            doc_names = {doc.name for doc in documents}
            assert "doc1.pdf" in doc_names
            assert "doc2.docx" in doc_names
            assert "doc3.pdf" not in doc_names  # In subdirectory

            # Should find only 2 documents
            assert len(documents) == 2

    def test_scan_folder_with_file_types(self):
        """Test scanning with specific file types."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create various file types
            (tmp_path / "doc1.pdf").touch()
            (tmp_path / "doc2.pdf").touch()
            (tmp_path / "doc3.docx").touch()
            (tmp_path / "readme.md").touch()
            (tmp_path / "notes.txt").touch()

            # Scan for only PDFs
            pdf_docs = DocumentHandler.scan_folder(
                tmp_path, recursive=False, file_types=["pdf"]
            )
            assert len(pdf_docs) == 2
            assert all(doc.suffix == ".pdf" for doc in pdf_docs)

            # Scan for PDFs and Markdown
            mixed_docs = DocumentHandler.scan_folder(
                tmp_path, recursive=False, file_types=["pdf", "md"]
            )
            assert len(mixed_docs) == 3

            # Scan for text files
            text_docs = DocumentHandler.scan_folder(
                tmp_path, recursive=False, file_types=["txt"]
            )
            assert len(text_docs) == 1
            assert text_docs[0].name == "notes.txt"

    @patch.object(DocumentHandler, "extract_text")
    def test_extract_from_multiple_combine(self, mock_extract):
        """Test extracting text from multiple documents with combining."""
        # Mock extraction
        mock_extract.side_effect = [
            "Content from doc1",
            "Content from doc2",
            "Content from doc3",
        ]

        file_paths = [
            Path("doc1.pdf"),
            Path("doc2.docx"),
            Path("doc3.md"),
        ]

        result = DocumentHandler.extract_from_multiple(
            file_paths, use_advanced=False, combine=True
        )

        # Check combined result
        assert isinstance(result, str)
        assert "=== Document: doc1.pdf ===" in result
        assert "Content from doc1" in result
        assert "=== Document: doc2.docx ===" in result
        assert "Content from doc2" in result
        assert "=== Document: doc3.md ===" in result
        assert "Content from doc3" in result

    @patch.object(DocumentHandler, "extract_text")
    def test_extract_from_multiple_separate(self, mock_extract):
        """Test extracting text from multiple documents without combining."""
        # Mock extraction
        mock_extract.side_effect = [
            "Content from doc1",
            "Content from doc2",
        ]

        file_paths = [
            Path("doc1.pdf"),
            Path("doc2.docx"),
        ]

        result = DocumentHandler.extract_from_multiple(
            file_paths, use_advanced=False, combine=False
        )

        # Check separate results
        assert isinstance(result, dict)
        assert str(Path("doc1.pdf")) in result
        assert str(Path("doc2.docx")) in result
        assert result[str(Path("doc1.pdf"))] == "Content from doc1"
        assert result[str(Path("doc2.docx"))] == "Content from doc2"

    @patch.object(DocumentHandler, "extract_text")
    def test_extract_from_multiple_with_failures(self, mock_extract):
        """Test extracting from multiple documents with some failures."""
        # Mock extraction with one failure
        mock_extract.side_effect = [
            "Content from doc1",
            Exception("Failed to extract"),
            "Content from doc3",
        ]

        file_paths = [
            Path("doc1.pdf"),
            Path("doc2.docx"),  # This one will fail
            Path("doc3.md"),
        ]

        result = DocumentHandler.extract_from_multiple(
            file_paths, use_advanced=False, combine=True
        )

        # Should still get content from successful extractions
        assert "Content from doc1" in result
        assert "Content from doc3" in result
        # doc2 should not be in result due to failure
        assert "doc2.docx" not in result

    @patch.object(DocumentHandler, "extract_chunks")
    def test_extract_chunks_from_multiple(self, mock_extract_chunks):
        """Test extracting chunks from multiple documents."""
        # Mock chunk extraction
        mock_extract_chunks.side_effect = [
            [
                {
                    "id": 0,
                    "text": "chunk1 from doc1",
                    "start": 0,
                    "end": 10,
                    "source": "doc1.pdf",
                },
                {
                    "id": 1,
                    "text": "chunk2 from doc1",
                    "start": 10,
                    "end": 20,
                    "source": "doc1.pdf",
                },
            ],
            [
                {
                    "id": 0,
                    "text": "chunk1 from doc2",
                    "start": 0,
                    "end": 10,
                    "source": "doc2.docx",
                },
            ],
        ]

        file_paths = [
            Path("doc1.pdf"),
            Path("doc2.docx"),
        ]

        chunks = DocumentHandler.extract_chunks_from_multiple(
            file_paths, chunk_size=100, overlap=10, use_advanced=False
        )

        # Check results
        assert len(chunks) == 3
        assert all("file_path" in chunk for chunk in chunks)
        assert chunks[0]["text"] == "chunk1 from doc1"
        assert chunks[0]["file_path"] == str(Path("doc1.pdf"))
        assert chunks[2]["text"] == "chunk1 from doc2"
        assert chunks[2]["file_path"] == str(Path("doc2.docx"))

    @patch.object(DocumentHandler, "extract_chunks")
    def test_extract_chunks_from_multiple_with_failures(self, mock_extract_chunks):
        """Test extracting chunks from multiple documents with failures."""
        # Mock chunk extraction with one failure
        mock_extract_chunks.side_effect = [
            [
                {
                    "id": 0,
                    "text": "chunk from doc1",
                    "start": 0,
                    "end": 10,
                    "source": "doc1.pdf",
                }
            ],
            Exception("Failed to extract"),
            [
                {
                    "id": 0,
                    "text": "chunk from doc3",
                    "start": 0,
                    "end": 10,
                    "source": "doc3.md",
                }
            ],
        ]

        file_paths = [
            Path("doc1.pdf"),
            Path("doc2.docx"),  # This one will fail
            Path("doc3.md"),
        ]

        chunks = DocumentHandler.extract_chunks_from_multiple(
            file_paths, chunk_size=100
        )

        # Should still get chunks from successful extractions
        assert len(chunks) == 2
        assert chunks[0]["text"] == "chunk from doc1"
        assert chunks[1]["text"] == "chunk from doc3"


class TestPrepareForGenerationMultiple:
    """Test prepare_for_generation with multiple documents."""

    @patch.object(DocumentHandler, "scan_folder")
    @patch.object(DocumentHandler, "extract_chunks_from_multiple")
    @patch.object(DocumentHandler, "detect_document_type")
    def test_prepare_folder_input(self, mock_detect, mock_extract_chunks, mock_scan):
        """Test preparation with folder input."""
        # Mock folder scanning
        mock_scan.return_value = [
            Path("/docs/doc1.pdf"),
            Path("/docs/doc2.docx"),
            Path("/docs/doc3.md"),
        ]

        # Mock chunk extraction
        mock_extract_chunks.return_value = [
            {"id": 0, "text": "chunk1", "file_path": "/docs/doc1.pdf"},
            {"id": 1, "text": "chunk2", "file_path": "/docs/doc2.docx"},
            {"id": 2, "text": "chunk3", "file_path": "/docs/doc3.md"},
        ]

        # Mock document type detection
        mock_detect.side_effect = ["pdf", "docx", "md"]

        # Mock Path methods
        with (
            patch.object(Path, "is_dir", return_value=True),
            patch.object(Path, "stat") as mock_stat,
        ):
            mock_stat.return_value.st_size = 1024

            result = DocumentHandler.prepare_for_generation(
                Path("/docs"), extraction_type="qa", chunk_size=1000, recursive=True
            )

        # Check results
        assert result["input_type"] == "folder"
        assert result["total_documents"] == 3
        assert result["total_chunks"] == 3
        assert result["document_type"] == "mixed"  # Multiple types
        assert len(result["document_names"]) == 3
        assert "doc1.pdf" in result["document_names"]
        # Document types should be sorted
        assert sorted(result["metadata"]["document_types"]) == ["docx", "md", "pdf"]

    @patch.object(DocumentHandler, "extract_chunks")
    @patch.object(DocumentHandler, "detect_document_type")
    def test_prepare_single_file_input(self, mock_detect, mock_extract_chunks):
        """Test preparation with single file input."""
        # Mock document type
        mock_detect.return_value = "pdf"

        # Mock chunk extraction
        mock_extract_chunks.return_value = [
            {"id": 0, "text": "chunk1", "start": 0, "end": 100, "source": "doc.pdf"},
            {"id": 1, "text": "chunk2", "start": 100, "end": 200, "source": "doc.pdf"},
        ]

        # Mock file stats
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 2048
            with patch.object(Path, "is_dir", return_value=False):
                result = DocumentHandler.prepare_for_generation(
                    Path("/docs/doc.pdf"), extraction_type="qa", chunk_size=100
                )

        # Check results
        assert result["input_type"] == "file"
        assert result["total_documents"] == 1
        assert result["total_chunks"] == 2
        assert result["document_type"] == "pdf"
        assert result["document_name"] == "doc.pdf"
        assert result["metadata"]["file_size"] == 2048

    @patch.object(DocumentHandler, "extract_chunks_from_multiple")
    def test_prepare_list_input(self, mock_extract_chunks):
        """Test preparation with list of paths input."""
        # Mock chunk extraction
        mock_extract_chunks.return_value = [
            {"id": 0, "text": "chunk1", "file_path": "/docs/doc1.pdf"},
            {"id": 1, "text": "chunk2", "file_path": "/docs/doc2.md"},
        ]

        file_list = [
            Path("/docs/doc1.pdf"),
            Path("/docs/doc2.md"),
        ]

        # Mock document type detection and file stats
        with patch.object(DocumentHandler, "detect_document_type") as mock_detect:
            mock_detect.side_effect = ["pdf", "md"]
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024

                result = DocumentHandler.prepare_for_generation(
                    file_list, extraction_type="summary", chunk_size=500
                )

        # Check results
        assert result["input_type"] == "multiple"
        assert result["total_documents"] == 2
        assert result["total_chunks"] == 2
        assert result["document_type"] == "mixed"
        assert len(result["document_names"]) == 2
        assert "doc1.pdf" in result["document_names"]
        assert "doc2.md" in result["document_names"]

    @patch.object(DocumentHandler, "scan_folder")
    def test_prepare_empty_folder(self, mock_scan):
        """Test preparation with empty folder raises error."""
        # Mock empty folder scan
        mock_scan.return_value = []

        with (
            patch.object(Path, "is_dir", return_value=True),
            pytest.raises(ValidationError, match="No supported documents found"),
        ):
            DocumentHandler.prepare_for_generation(
                Path("/empty/folder"), extraction_type="qa"
            )
