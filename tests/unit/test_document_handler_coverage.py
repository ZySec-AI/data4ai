"""Additional document-handler success and recovery-path tests."""

from types import SimpleNamespace
from unittest.mock import Mock, mock_open, patch

import pytest

from data4ai.document_handler import DocumentHandler
from data4ai.exceptions import ValidationError


def test_docx_paragraphs_tables_and_failure():
    document = Mock()
    document.paragraphs = [
        SimpleNamespace(text="First paragraph"),
        SimpleNamespace(text=""),
    ]
    document.tables = [
        SimpleNamespace(
            rows=[
                SimpleNamespace(
                    cells=[
                        SimpleNamespace(text="Cell one"),
                        SimpleNamespace(text="Cell two"),
                    ]
                )
            ]
        )
    ]
    with (
        patch("data4ai.document_handler.DOCX_AVAILABLE", True),
        patch("data4ai.document_handler.Document", return_value=document),
    ):
        text = DocumentHandler._extract_docx_text(Mock())
    assert "First paragraph" in text
    assert "Cell one | Cell two" in text

    with (
        patch("data4ai.document_handler.DOCX_AVAILABLE", True),
        patch("data4ai.document_handler.Document", side_effect=RuntimeError("broken")),
        pytest.raises(ValidationError, match="Failed to extract DOCX"),
    ):
        DocumentHandler._extract_docx_text(Mock())


def test_pdf_advanced_fallback_and_reader_failure():
    page = Mock()
    page.extract_text.return_value = "fallback text"
    reader = SimpleNamespace(pages=[page])
    with (
        patch("data4ai.document_handler.PDFPLUMBER_AVAILABLE", True),
        patch("pdfplumber.open", side_effect=RuntimeError("advanced failed")),
        patch("data4ai.document_handler.PYPDF_AVAILABLE", True),
        patch("pypdf.PdfReader", return_value=reader),
    ):
        assert "fallback text" in DocumentHandler._extract_pdf_text(
            Mock(), use_advanced=True
        )

    with (
        patch("data4ai.document_handler.PYPDF_AVAILABLE", True),
        patch("pypdf.PdfReader", side_effect=RuntimeError("broken")),
        pytest.raises(ValidationError, match="Failed to extract PDF"),
    ):
        DocumentHandler._extract_pdf_text(Mock())


def test_markdown_library_and_extraction_failure():
    with (
        patch("data4ai.document_handler.MARKDOWN_AVAILABLE", True),
        patch("builtins.open", mock_open(read_data="# Heading\n\nBody")),
    ):
        assert "Heading" in DocumentHandler._extract_markdown_text(Mock())

    with (
        patch("builtins.open", side_effect=OSError("unreadable")),
        pytest.raises(ValidationError, match="Failed to extract Markdown"),
    ):
        DocumentHandler._extract_markdown_text(Mock())


def test_chunk_parameter_clamping():
    with patch.object(DocumentHandler, "extract_text", return_value="abcdef"):
        chunks = DocumentHandler.extract_chunks(
            Mock(name="source.txt"), chunk_size=0, overlap=-1
        )
    assert len(chunks) == 1

    with patch.object(DocumentHandler, "extract_text", return_value="abcdefghij"):
        chunks = DocumentHandler.extract_chunks(
            Mock(name="source.txt"), chunk_size=4, overlap=10
        )
    assert len(chunks) > 1


def test_extract_multiple_and_folder_structure(tmp_path):
    inside = tmp_path / "topic" / "inside.txt"
    root_file = tmp_path / "root.txt"
    outside = tmp_path.parent / "outside.txt"
    inside.parent.mkdir()
    inside.write_text("inside", encoding="utf-8")
    root_file.write_text("root", encoding="utf-8")

    with patch.object(
        DocumentHandler,
        "extract_text",
        side_effect=["inside text", RuntimeError("bad")],
    ):
        combined = DocumentHandler.extract_from_multiple([inside, outside])
    assert "inside.txt" in combined
    with patch.object(DocumentHandler, "extract_text", return_value="root text"):
        mapping = DocumentHandler.extract_from_multiple([root_file], combine=False)
    assert mapping[str(root_file)] == "root text"

    structure = DocumentHandler._analyze_folder_structure(
        tmp_path, [inside, root_file, outside]
    )
    assert structure["has_subfolders"] is True
    assert inside in structure["subfolders"]["topic"]
    assert outside in structure["subfolders"]["root"]


def test_extract_chunks_from_multiple_skips_failures():
    paths = [Mock(name="one.txt"), Mock(name="bad.txt")]
    with patch.object(
        DocumentHandler,
        "extract_chunks",
        side_effect=[[{"id": 0, "text": "one"}], RuntimeError("bad")],
    ):
        chunks = DocumentHandler.extract_chunks_from_multiple(paths)
    assert len(chunks) == 1
    assert "file_path" in chunks[0]


def test_convert_pdf_to_markdown_and_folder(tmp_path):
    pdf = tmp_path / "source.pdf"
    pdf.touch()
    with patch.object(
        DocumentHandler,
        "_extract_pdf_text",
        return_value="--- Page 1 ---\ncamelCase\nword-\nwrap",
    ):
        output = DocumentHandler.convert_pdf_to_markdown(pdf)
    content = output.read_text(encoding="utf-8")
    assert "## Page 1" in content
    assert "camel Case" in content
    assert "wordwrap" in content

    nested = tmp_path / "nested"
    nested.mkdir()
    nested_pdf = nested / "nested.pdf"
    nested_pdf.touch()
    destination = tmp_path / "converted"

    def convert(_source, target, **_kwargs):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("converted", encoding="utf-8")
        return target

    with patch.object(DocumentHandler, "convert_pdf_to_markdown", side_effect=convert):
        converted = DocumentHandler.convert_pdfs_in_folder(
            tmp_path, destination, recursive=True, delete_pdfs=True
        )
    assert len(converted) == 2
    assert not pdf.exists() and not nested_pdf.exists()


def test_convert_folder_validation_and_empty(tmp_path):
    with pytest.raises(FileNotFoundError):
        DocumentHandler.convert_pdfs_in_folder(tmp_path / "missing")
    file_path = tmp_path / "file.txt"
    file_path.write_text("text", encoding="utf-8")
    with pytest.raises(ValidationError, match="Not a directory"):
        DocumentHandler.convert_pdfs_in_folder(file_path)
    assert DocumentHandler.convert_pdfs_in_folder(tmp_path) == []


def test_prepare_multiple_folder_and_string_inputs(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    one = folder / "one.md"
    two = folder / "two.txt"
    one.write_text("one", encoding="utf-8")
    two.write_text("two", encoding="utf-8")
    with patch.object(
        DocumentHandler,
        "extract_chunks_from_multiple",
        return_value=[{"id": 0, "text": "chunk"}],
    ):
        folder_result = DocumentHandler.prepare_for_generation(folder)
        list_result = DocumentHandler.prepare_for_generation([one, two])
    assert folder_result["document_type"] == "mixed"
    assert folder_result["folder_structure"] is not None
    assert list_result["input_type"] == "multiple"

    with patch.object(DocumentHandler, "extract_chunks", return_value=[]):
        string_result = DocumentHandler.prepare_for_generation(str(one))
    assert string_result["input_type"] == "file"

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValidationError, match="No supported documents"):
        DocumentHandler.prepare_for_generation(empty)
